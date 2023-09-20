from pydantic import BaseModel, field_validator, Field
from typing import Literal


class FileUpload(BaseModel):
    file_name: str
    file_data: bytes


class UploadFileRequest:
    enrollment: int


class Teacher_registration(BaseModel):
    _id: int
    teacher_name: str
    course: Literal["B-Tech", "M-Tech", "CA", "Management"]
    branch: Literal["Computer Science", "Electrical", "Mechanical", "Civil", "BCA", "MCA", "BBA", "MBA"]


class RegistrationBody(BaseModel):
    student_name: str
    age: int = Field(ge=18)
    father_name: str
    phone: int
    course: Literal["B-Tech", "M-Tech", "CA", "Management"]
    branch: Literal["Computer Science", "Electrical", "Mechanical", "Civil", "BCA", "MCA", "BBA", "MBA"]
    aadhar: int
    address: str
    pincode: int
    district: str
    state: str
    country: str
    board: str

    # @field_validator('phone')
    # def phone_validator(cls, value):
    #     if len(str(value)) != 10:
    #         raise ValueError("phone number must be of 10 digits!")
    #     return value
    #
    # @field_validator('aadhar')
    # def aadhar_validator(cls, value):
    #     if len(str(value)) != 12:
    #         raise ValueError("aadhar number must be of 12 digits!")
    #     return value
    #
    # @field_validator('pincode')
    # def pincode_validator(cls, value):
    #     if len(str(value)) != 6:
    #         raise ValueError("pincode number must be of 6 digits!")
    #     return value
