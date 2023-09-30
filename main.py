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
from typing import Annotated

Secret_key = secrets.token_hex(32)

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
async def get_detail(enrollment: int):
    doc = await db.registered_student_col.find_one({"_id": enrollment})
    return {"doc": doc}


@app.get("/all_students/{course}")
async def get_students_of_course(course: str):
    data = await db.get_students_by_course(course)
    return {"result": data}


def create_access_token(data: dict):
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

    access_token = create_access_token(data={"sub": str(teacher.get("_id"))})
    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/submit_mark")
async def submit_mark(student_id: int, marks: int, active_teacher=Depends(get_active_teacher)):
    teacher_has_authority = await db.students_section_col.find_one(
        {"teacher_id": int(active_teacher), "students": {"$in": [student_id]}})

    if teacher_has_authority is None:
        raise HTTPException(status_code=403, detail="You dont have the authority to mark this student")
    result = await db.registered_student_col.find_one_and_update({"_id": student_id}, {"$set": {"marks": marks}})
    return dict(message="marks added successfully")


@app.get("/students_data")
async def get_student_data(student_id: int):
    student_data = await db.registered_student_col.find_one({"_id": student_id}, {"student_name": 1, "marks": 1})
    return {**student_data}


if __name__ == '__main__':
    uvicorn.run("main:app")
