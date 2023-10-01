import random
import aiofiles
from pydantic import BaseModel
import schema
from fastapi import FastAPI, HTTPException, UploadFile, File, Depends, status, Header
from typing import Literal
import uvicorn
import asyncio
import os
from fastapi.responses import FileResponse
import db
import secrets
from passlib.context import CryptContext
from jose import JWTError, jwt
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from datetime import datetime, timedelta

Secret_key = secrets.token_hex(32)
ACCESS_TOKEN_EXPIRE_TIME = 15

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

app = FastAPI(title="Arshad University")

os.makedirs("uploads", exist_ok=True)
UPLOAD_FILE_PATH = "uploads"


@app.post("/upload2")
async def upload2(*, file: UploadFile = File(...), enrollment_no: int, document_type: Literal["aadhar", "TC"]):
    if file is None:
        raise HTTPException(status_code=400, detail="File not provided.")
    type_ = file.content_type.split("/")[-1]
    file_id = secrets.token_hex(10) + f".{type_}"
    file_data = await file.read()
    async with aiofiles.open(UPLOAD_FILE_PATH + f"/{file_id}", "wb") as file:
        await file.write(file_data)
    await db.add_document(enrollment_no, document_type, file_id)
    return {"success": True}


@app.get("/file2")
async def get_file2(enrollment_no: int, document_type: Literal["aadhar", "TC"]):
    file_id = await db.get_document_id(enrollment_no, document_type)
    if not os.path.exists(UPLOAD_FILE_PATH + f"/{file_id}"):
        asyncio.get_event_loop().create_task(db.set_document_to_none(enrollment_no, document_type))
        raise HTTPException(status_code=404, detail="File not found")
    content_disposition = 'inline'
    return FileResponse(UPLOAD_FILE_PATH + f"/{file_id}",
                        headers={"Content-Disposition": f"{content_disposition}:filename={file_id}"})


course_branches = {
    "B-Tech": ["Computer Science", "Electrical", "Mechanical", "Civil"],
    "M-Tech": ["Computer Science", "Electrical", "Mechanical", "Civil"],
    "CA": ["BCA", "MCA"],
    "Management": ["BBA", "MBA"]
}


@app.get("/get_courses_branches")
async def get_courses_branches():
    data = {}
    for c, branches_list in course_branches.items():
        data[c] = branches_list
    return data


@app.post("/registration")
async def registration(applicant_detail: schema.RegistrationBody):
    if applicant_detail.branch not in course_branches[applicant_detail.course]:
        raise HTTPException(status_code=400,
                            detail=f"Invalid branch. For {applicant_detail.branch} .Accepts only : {course_branches[applicant_detail.course]}")

    response = await db.register_student(applicant_detail)

    return {"message": f"Applicant registered successfully.", "enrollment_no": response}


@app.get("/student_detail/{enrollment}")
async def get_student_detail(enrollment: int):
    student_data = await db.registered_student_col.find_one({"_id": enrollment})
    if student_data is None:
        raise HTTPException(status_code=404, detail="Student not found.")
    transaction_data = await db.transaction_col.find({"student_id": enrollment}, projection={"student_id": 0}).to_list(length=1000)
    student_data["transaction_record"] = transaction_data
    return {"student_data": student_data}


@app.get("/all_students/{course}")
async def get_students_of_course(course: str):
    data = await db.get_students_by_course(course)
    return {"result": data}


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=10)
    data.update({"exp": expire})
    encoded_token = jwt.encode(data, Secret_key)
    return encoded_token


class Token(BaseModel):
    access_token: str
    token_type: str


async def get_active_teacher(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, Secret_key)
        teacher_id = payload.get("sub")
        if teacher_id is None:
            raise credentials_exception
        return teacher_id
    except JWTError as e:
        print(f"JWT Error: {e}")
        raise credentials_exception


@app.post("/login")
async def teacher_login(
        form_data: OAuth2PasswordRequestForm = Depends()
):
    teacher = await db.teachers_col.find_one({"_id": int(form_data.username)})

    if teacher is None or form_data.password != teacher["password"]:
        raise HTTPException(status_code=401, detail="teacher_id or password is incorrect")

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_TIME)
    access_token = create_access_token(data={"sub": str(teacher.get("_id"))}, expires_delta=access_token_expires)
    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/submit_mark")
async def submit_mark(student_id: int, marks: int, active_teacher=Depends(get_active_teacher)):
    teacher_has_authority = await db.students_section_col.find(
        {"teacher_id": int(active_teacher), "students": {"$in": [student_id]}}).limit(1).to_list(length=1)
    if not teacher_has_authority:
        raise HTTPException(status_code=403, detail="You dont have the authority to mark this student")
    await db.registered_student_col.find_one_and_update({"_id": student_id}, {"$set": {"marks": marks}})
    return dict(message="marks added successfully")


@app.get("/students_data")
async def get_student_data(teacher_id=Depends(get_active_teacher)):
    students = await db.students_section_col.find({"teacher_id": int(teacher_id)}, {"students": 1, "_id": 0}).limit(
        1).to_list(1)
    enrollment_list = students[0].get("students")
    students_data = await db.registered_student_col.find({"_id": {"$in": enrollment_list}},
                                                         {"student_name": 1, "marks": 1, }).to_list(length=1000)
    return {"student_data": students_data}


@app.post("/fee_submit")
async def fee_submit(student_id: int, amount: int):
    if 1 <= amount <= 90000:
        fee: int = 90000
        result = await db.registered_student_col.find_one({"_id": student_id})
        if result:
            current_fee_deposited = result.get("fee_deposited", 0)
            if current_fee_deposited + amount <= fee:
                new_fee_deposited = current_fee_deposited + amount
                due_fees = fee - new_fee_deposited
                await db.registered_student_col.update_one({"_id": student_id}, {"$set": {"fee": fee, "fee_deposited": new_fee_deposited, "due_fees": due_fees}})
                await fee_transaction(student_id, amount)
                return {"result": "Deposited successfully"}
            else:
                raise HTTPException(status_code=400, detail="Total deposition exceed the fee")
        else:
            raise HTTPException(status_code=404, detail="No student found.")
    else:
        raise HTTPException(status_code=400, detail="fee should be in the 1 to 90000 range.")


async def fee_transaction(student_id: int, amount: int):
    data = {"_id": random.randint(1000000, 9999999), "student_id": student_id, "amount": amount, "time": datetime.now()}
    await db.transaction_col.insert_one(data)
    return
