import io
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
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

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
    content_disposition = f'attachment; filename="{file_id}"'
    return FileResponse(UPLOAD_FILE_PATH + f"/{file_id}",
                        headers={"Content-Disposition": content_disposition})


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
    transaction_data = await db.transaction_col.find({"student_id": enrollment}, projection={"student_id": 0}).to_list(
        length=1000)
    student_data["transaction_record"] = transaction_data
    return {"student_data": student_data}


@app.get("/all_students/{course}")
async def get_students_of_course(course: str):
    data = await db.get_students_by_course(course)
    return {"result": data}


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=10))
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
    if not bool(teacher_has_authority):
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


@app.get("/Download_transaction_receipt")
async def pdf_generator_function(transaction_id: int):
    document = await db.transaction_col.find_one({"_id": transaction_id})
    student_data = await db.registered_student_col.find_one({"_id": document.get("student_id")}, projection={"_id": 0, "student_name":1, "course":1, "branch":1})
    if not document:
        raise HTTPException(status_code=404, detail="Document not found.")

    canvas1 = canvas.Canvas(f"{document.get('_id')}.pdf")

    canvas1.setFont("Times-Bold", 32)
    canvas1.drawString(140, 750, "Arshad University")
    canvas1.line(x1=140, y1=740, x2=410, y2=740)

    canvas1.setFont('Helvetica', size=20)
    canvas1.drawString(220, 710, "fee receipt")

    canvas1.line(x1=90, y1=675, x2=480, y2=675)

    canvas1.setFont('Helvetica', 15)
    canvas1.drawString(90, y=650, text="Voucher no : ")
    canvas1.drawString(290, 650, text=str(random.randint(1000000, 9000000)))

    canvas1.drawString(90, 620, text="Student Name :")
    canvas1.drawString(290, 620, text=str(student_data.get("student_name")))

    canvas1.drawString(90, 590, text="Student ID :")
    canvas1.drawString(290, 590, text=str(document.get("student_id")))

    canvas1.drawString(90, 560, text="Course :")
    canvas1.drawString(290, 560, text=str(student_data.get("course")))

    canvas1.drawString(90, 530, text="Branch :")
    canvas1.drawString(290, 530, text=str(student_data.get("branch")))

    canvas1.drawString(90, 500, text="Transaction ID :")
    canvas1.drawString(290, 500, text=str(document.get("_id")))

    canvas1.drawString(90, 470, text="Time")
    canvas1.drawString(290, 470, text=str(document.get("time")))

    canvas1.line(x1=90, y1=440, x2=480, y2=440)

    canvas1.setFont('Helvetica', 18)
    canvas1.drawString(90, 400, text="Fee Description")
    canvas1.line(x1=90, y1=390, x2=220, y2=390)

    canvas1.setFont('Helvetica', 16)
    canvas1.drawString(90, 370, text="S.No.")
    canvas1.drawString(90, 340, text="1")
    canvas1.drawString(240, 370, text="Fee head.")
    canvas1.drawString(240, 340, text="Tuition Fee")
    canvas1.drawString(390, 370, text="Amount(Rs)")
    canvas1.drawString(390, 340, text=str(document.get("amount")))

    canvas1.line(x1=90, y1=360, x2=480, y2=360)

    canvas1.line(x1=90, y1=230, x2=480, y2=230)

    canvas1.drawString(240, 200, text="Total")

    canvas1.drawString(390, 200, text=str(document.get("amount")))

    canvas1.drawString(90, 100, text="Payment Mode")
    canvas1.line(x1=90, y1=85, x2=200, y2=85)
    canvas1.drawString(90, 60, text="Online")

    canvas1.drawString(240, 100, text="Date")
    canvas1.line(x1=240, y1=85, x2=280, y2=85)
    current_time = datetime.now()
    canvas1.drawString(240, 60, text=str(current_time.date()))

    canvas1.drawString(390, 100, text="Status")
    canvas1.line(x1=390, y1=85, x2=440, y2=85)
    canvas1.drawString(390, 60, text="Success")

    canvas1.setFont('Helvetica', 18)
    canvas1.setFillColorRGB(0, 1, 0)
    canvas1.drawString(400, 30, text="Thank You.")

    image_path = "University_logo.jpg"
    image = ImageReader(image_path)

    x_position = 400
    y_position = 680
    width = 200
    height = 200

    canvas1.drawImage(image, x_position, y_position, width, height)

    canvas1.save()

    # canvas.output(f"{document.get('_id')}.pdf")
    content_disposition = f'attachment; filename="{document.get("_id")}"'
    return FileResponse(f"{document.get('_id')}.pdf",
                        headers={"Content-Disposition": content_disposition})


@app.post("/fee_submit")
async def fee_submit(student_id: int, amount: int):
    if 10000 <= amount <= 90000:
        fee: int = 90000
        result = await db.registered_student_col.find_one({"_id": student_id})
        if result:
            current_fee_deposited = result.get("fee_deposited", 0)
            if current_fee_deposited + amount <= fee:
                new_fee_deposited = current_fee_deposited + amount
                due_fees = fee - new_fee_deposited
                await db.registered_student_col.update_one({"_id": student_id}, {
                    "$set": {"fee": fee, "fee_deposited": new_fee_deposited, "due_fees": due_fees}})
                transaction_id = await fee_transaction(student_id, amount)
                return {"result": "Deposited successfully", "transaction_id": transaction_id}
            else:
                raise HTTPException(status_code=400, detail="Total deposition exceed the fee")
        else:
            raise HTTPException(status_code=404, detail="No student found.")
    else:
        raise HTTPException(status_code=400, detail="fee should be in the 10000 to 90000 range.")


async def fee_transaction(student_id: int, amount: int):
    data = {"_id": random.randint(1000000, 9999999), "student_id": student_id, "amount": amount, "time": datetime.now()}
    await db.transaction_col.insert_one(data)
    return data["_id"]
