import schema
from db_client import database
from fastapi import HTTPException


# student_data_col = database.get_collection("Student_data")
enrollment_counter_col = database.get_collection("enrollment_counter")
registered_student_col = database.get_collection("registered_students_data")
students_section_col = database.get_collection("students_sections")
teachers_col = database.get_collection("teacher_collection")

# teachers_col.drop()


async def get_registered_students():
    registered_students = await registered_student_col.find().to_list(None)
    return registered_students


async def get_students_in_sections():
    students_in_the_sections = await students_section_col.find().to_list(None)
    return students_in_the_sections


async def registered_collection_delete():
    return await registered_student_col.drop()


async def get_student(_id):
    return await registered_student_col.find_one({"_id": _id})


async def get_section_document(_id):
    return await students_section_col.find_one({"_id": _id})


async def get_teacher_data(teacher_id):
    return await teachers_col.find_one({"_id": teacher_id})


async def delete_section_collection():
    return await students_section_col.drop()


async def add_document(enrollment_no, document_type, file_id):
    await registered_student_col.update_one({"_id": enrollment_no}, {"$set": {document_type: file_id}})


async def set_document_to_none(enroll, document_type):
    await registered_student_col.update_one({"_id": enroll}, {document_type: None})


async def get_students_by_course(course):
    students_data = []

    async for student in registered_student_col.find({"course": course}, {"_id": 1, "student_name": 1}):
        students_data.append({"enrollment": student["_id"], "student_name": student["student_name"]})

    if not students_data:
        raise HTTPException(status_code=404, detail=f"This course {course} not founded in the collection.")
    return students_data


async def get_document_id(enrollment_no, document_type):
    data = await registered_student_col.find_one({"_id": enrollment_no})
    if data is None:
        raise HTTPException(status_code=404, detail="Student not found")
    file_id = data.get(document_type)
    if file_id is None:
        raise HTTPException(status_code=404, detail="File not uploaded")
    return file_id


async def get_new_enrollment_no():
    initial_enrollment_counter = 2100100484

    enrollment_counter = await enrollment_counter_col.find_one(
        {"_id": "enrollment_counter"}
    )

    if enrollment_counter is None:
        await enrollment_counter_col.insert_one(
            {"_id": "enrollment_counter", "value": initial_enrollment_counter})
        return initial_enrollment_counter
    else:
        await enrollment_counter_col.update_one(
            {"_id": "enrollment_counter"},
            {"$inc": {"value": 1}})
        return enrollment_counter["value"] + 1


async def register_student(applicant_detail: schema.RegistrationBody):
    enrollment_no = await get_new_enrollment_no()
    registration_data = {
        "_id": enrollment_no,
        "student_name": applicant_detail.student_name,
        "age": applicant_detail.age,
        "father_name": applicant_detail.father_name,
        "course": applicant_detail.course,
        "branch": applicant_detail.branch,
        "phone": applicant_detail.phone,
        "aadhar": applicant_detail.aadhar,
        "address": applicant_detail.address,
        "pincode": applicant_detail.pincode,
        "district": applicant_detail.district,
        "state": applicant_detail.state,
        "country": applicant_detail.country,
        "board": applicant_detail.board,
    }

    await registered_student_col.insert_one(registration_data)
    return enrollment_no


