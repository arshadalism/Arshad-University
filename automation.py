import schema
import asyncio
from faker import Faker
import math
import random
import db
import db_client
from pymongo import UpdateOne


async def generate_random_student_data(num_students):
    fake = Faker()
    students_list = []

    for _ in range(num_students):
        enrollment_no = await db.get_new_enrollment_no()
        students_data = {
            "_id": enrollment_no,
            "student_name": fake.name(),
            "age": random.randint(18, 30),  # Random age between 18 and 30
            "father_name": fake.name(),
            "phone": random.randint(9000000000, 9999999999),
            "course": random.choice(["B-Tech", "M-Tech", "CA", "Management"]),
            "aadhar": random.randint(100000000000, 999999999999),  # 12-digit random number
            "address": fake.address(),
            "pincode": random.randint(226026, 300000),
            "district": fake.city(),
            "state": fake.state(),
            "country": fake.country(),
            "board": fake.company(),
        }

        if students_data["course"] == "B-Tech" or students_data["course"] == "M-Tech":
            students_data["branch"] = random.choice(["Computer Science", "Electrical", "Mechanical", "Civil"])
        elif students_data["course"] == "CA":
            students_data["branch"] = random.choice(["BCA", "MCA"])
        elif students_data["course"] == "Management":
            students_data["branch"] = random.choice(["BBA", "MBA"])

        schema.RegistrationBody(**students_data)
        students_list.append(students_data)

    await db.registered_student_col.insert_many(students_list)
    return


def extract_teacher(data):
    # data = [{'_id': 935807, 'teacher_name': 'Betty Garcia', 'course': 'B-Tech', 'branch': 'Computer Science', 'section': 'B-Tech-Computer Science-1'}, {'_id': 862086, 'teacher_name': 'Laura Walker', 'course': 'B-Tech', 'branch': 'Computer Science'}, {'_id': 313762, 'teacher_name': 'Jeffrey Shah', 'course': 'B-Tech', 'branch': 'Computer Science'}, {'_id': 627189, 'teacher_name': 'Paul Robbins', 'course': 'B-Tech', 'branch': 'Computer Science'}, {'_id': 595891, 'teacher_name': 'Heidi Harper', 'course': 'B-Tech', 'branch': 'Computer Science'}, {'_id': 995341, 'teacher_name': 'Madison Harmon', 'course': 'B-Tech', 'branch': 'Civil', 'section': 'B-Tech-Civil-1'}, {'_id': 191079, 'teacher_name': 'Kimberly Gonzalez', 'course': 'B-Tech', 'branch': 'Civil'}, {'_id': 843826, 'teacher_name': 'Adam Christensen', 'course': 'B-Tech', 'branch': 'Civil'}, {'_id': 475157, 'teacher_name': 'Jeremy Figueroa', 'course': 'B-Tech', 'branch': 'Civil'}, {'_id': 576568, 'teacher_name': 'Jessica Allen DDS', 'course': 'B-Tech', 'branch': 'Civil'}, {'_id': 965895, 'teacher_name': 'Melanie Norton', 'course': 'B-Tech', 'branch': 'Mechanical', 'section': 'B-Tech-Mechanical-1'}, {'_id': 386134, 'teacher_name': 'Jamie Washington', 'course': 'B-Tech', 'branch': 'Mechanical'}, {'_id': 862879, 'teacher_name': 'Richard Boyd', 'course': 'B-Tech', 'branch': 'Mechanical'}, {'_id': 997866, 'teacher_name': 'Kristine Franklin', 'course': 'B-Tech', 'branch': 'Mechanical'}, {'_id': 379624, 'teacher_name': 'John Alexander', 'course': 'B-Tech', 'branch': 'Mechanical'}, {'_id': 283848, 'teacher_name': 'Virginia Huff', 'course': 'B-Tech', 'branch': 'Electrical', 'section': 'B-Tech-Electrical-1'}, {'_id': 865233, 'teacher_name': 'Chad Cooper', 'course': 'B-Tech', 'branch': 'Electrical'}, {'_id': 839838, 'teacher_name': 'Anthony Zimmerman', 'course': 'B-Tech', 'branch': 'Electrical'}, {'_id': 286824, 'teacher_name': 'Charles Dickson', 'course': 'B-Tech', 'branch': 'Electrical'}, {'_id': 301945, 'teacher_name': 'Shirley Gill', 'course': 'B-Tech', 'branch': 'Electrical'}, {'_id': 800741, 'teacher_name': 'Jeremy Miller', 'course': 'M-Tech', 'branch': 'Computer Science', 'section': 'M-Tech-Computer Science-1'}, {'_id': 131862, 'teacher_name': 'Paul Morrison', 'course': 'M-Tech', 'branch': 'Computer Science'}, {'_id': 345632, 'teacher_name': 'Tracy Smith', 'course': 'M-Tech', 'branch': 'Computer Science'}, {'_id': 161643, 'teacher_name': 'James Parker', 'course': 'M-Tech', 'branch': 'Computer Science'}, {'_id': 963671, 'teacher_name': 'Kimberly Robertson', 'course': 'M-Tech', 'branch': 'Computer Science'}, {'_id': 383407, 'teacher_name': 'Ruben Taylor', 'course': 'M-Tech', 'branch': 'Civil', 'section': 'M-Tech-Civil-1'}, {'_id': 259409, 'teacher_name': 'Benjamin Wallace', 'course': 'M-Tech', 'branch': 'Civil'}, {'_id': 177825, 'teacher_name': 'Peter Thompson', 'course': 'M-Tech', 'branch': 'Civil'}, {'_id': 136525, 'teacher_name': 'Marissa Wright', 'course': 'M-Tech', 'branch': 'Civil'}, {'_id': 454073, 'teacher_name': 'Sarah Luna', 'course': 'M-Tech', 'branch': 'Civil'}, {'_id': 402892, 'teacher_name': 'Tiffany Howell', 'course': 'M-Tech', 'branch': 'Mechanical'}, {'_id': 257001, 'teacher_name': 'Matthew Thomas', 'course': 'M-Tech', 'branch': 'Mechanical'}, {'_id': 938311, 'teacher_name': 'Kevin Roth', 'course': 'M-Tech', 'branch': 'Mechanical'}, {'_id': 264482, 'teacher_name': 'Summer King', 'course': 'M-Tech', 'branch': 'Mechanical'}, {'_id': 893184, 'teacher_name': 'Tamara Brennan', 'course': 'M-Tech', 'branch': 'Mechanical'}, {'_id': 468730, 'teacher_name': 'Joseph Austin', 'course': 'M-Tech', 'branch': 'Electrical', 'section': 'M-Tech-Electrical-1'}, {'_id': 788110, 'teacher_name': 'Sandy Robinson', 'course': 'M-Tech', 'branch': 'Electrical'}, {'_id': 424800, 'teacher_name': 'Jesse Kim II', 'course': 'M-Tech', 'branch': 'Electrical'}, {'_id': 931087, 'teacher_name': 'Donald Ibarra', 'course': 'M-Tech', 'branch': 'Electrical'}, {'_id': 427486, 'teacher_name': 'Pamela Ellis', 'course': 'M-Tech', 'branch': 'Electrical'}, {'_id': 393559, 'teacher_name': 'Rebecca Shea', 'course': 'CA', 'branch': 'BCA', 'section': 'CA-BCA-1'}, {'_id': 123915, 'teacher_name': 'Bradley Cooper', 'course': 'CA', 'branch': 'BCA', 'section': 'CA-BCA-2'}, {'_id': 658047, 'teacher_name': 'Stephanie Snyder', 'course': 'CA', 'branch': 'BCA'}, {'_id': 333192, 'teacher_name': 'Randy Riley', 'course': 'CA', 'branch': 'BCA'}, {'_id': 592810, 'teacher_name': 'Elizabeth Brown', 'course': 'CA', 'branch': 'BCA'}, {'_id': 590642, 'teacher_name': 'Patricia Mendoza', 'course': 'CA', 'branch': 'MCA', 'section': 'CA-MCA-1'}, {'_id': 169814, 'teacher_name': 'Kimberly Garcia', 'course': 'CA', 'branch': 'MCA'}, {'_id': 253977, 'teacher_name': 'Casey Morris', 'course': 'CA', 'branch': 'MCA'}, {'_id': 226759, 'teacher_name': 'Steven Elliott', 'course': 'CA', 'branch': 'MCA'}, {'_id': 662535, 'teacher_name': 'Frederick Arnold', 'course': 'CA', 'branch': 'MCA'}, {'_id': 152820, 'teacher_name': 'Rebecca Holland', 'course': 'Management', 'branch': 'BBA', 'section': 'Management-BBA-1'}, {'_id': 286169, 'teacher_name': 'Alexander King', 'course': 'Management', 'branch': 'BBA', 'section': 'Management-BBA-2'}, {'_id': 236774, 'teacher_name': 'Robert Lewis', 'course': 'Management', 'branch': 'BBA'}, {'_id': 796987, 'teacher_name': 'Anthony Soto', 'course': 'Management', 'branch': 'BBA'}, {'_id': 352110, 'teacher_name': 'Nicholas Dawson', 'course': 'Management', 'branch': 'BBA'}, {'_id': 179738, 'teacher_name': 'Jason Mcdonald', 'course': 'Management', 'branch': 'MBA', 'section': 'Management-MBA-1'}, {'_id': 323583, 'teacher_name': 'Tiffany Dickerson', 'course': 'Management', 'branch': 'MBA', 'section': 'Management-MBA-2'}, {'_id': 956431, 'teacher_name': 'Joanne Hughes', 'course': 'Management', 'branch': 'MBA'}, {'_id': 180971, 'teacher_name': 'Ashley Boyd', 'course': 'Management', 'branch': 'MBA'}, {'_id': 739247, 'teacher_name': 'Thomas Roy', 'course': 'Management', 'branch': 'MBA'}]
    teachers = {}
    for teacher_data in data:
        branch = teacher_data.get("branch")
        course = teacher_data.get("course")
        teacher_id = teacher_data.get("_id")

        if (course, branch) not in teachers:
            teachers[(course, branch)] = []
        teachers[(course, branch)].append(teacher_id)
    return teachers


async def generate_random_teacher_data(num_teachers: int):
    # noinspection PyGlobalUndefined
    global branches
    fake = Faker()
    courses = ["B-Tech", "M-Tech", "CA", "Management"]
    for course in courses:
        if course in ["B-Tech", "M-Tech"]:
            branches = ["Computer Science", "Civil", "Mechanical", "Electrical"]
        elif course == "CA":
            branches = ["BCA", "MCA"]
        elif course == "Management":
            branches = ["BBA", "MBA"]

        teacher_list = []
        for branch in branches:
            for _ in range(num_teachers):
                teachers_data = {
                    "_id": random.randint(100000, 999999),
                    "teacher_name": fake.name(),
                    "course": course,
                    "branch": branch
                }
                teacher_list.append(teachers_data)
        await db.teachers_col.insert_many(teacher_list)

    return


async def create_sections_for_all_students():
    if db.students_section_col.name in await db_client.database.list_collection_names():
        print(f"The collection '{db.students_section_col.name}' already exists.")
        return

    course_branch_students = {}
    registered_students = await db.registered_student_col.find().to_list(length=1000)
    for student in registered_students:
        course = student["course"]
        branch = student.get("branch")
        key = (course, branch)
        if key not in course_branch_students:
            course_branch_students[key] = []
        course_branch_students[key].append(student)

    teachers = await db.teachers_col.find().to_list(length=1000)
    teachers_data = extract_teacher(teachers)

    section_list = []
    requests = []
    for (course, branch), students in course_branch_students.items():  # This line iterate over the dictionary in which key is a tuple of (course, branch) and students is the students with that course and branch
        num_sections = math.ceil(len(students) / 5)  # This creates sections on the basis of no of students
        for section_num in range(num_sections):  # This line iterate over the num_section variable
            section_name = f"{course}-{branch}-{section_num + 1}"  # This line create the section name with the help of course and section
            section_students = students[section_num * 5: (section_num + 1) * 5]  # Slicing of from 0-4 index so that 5 students gets in one section
            section_doc = {
                "_id": random.randint(1, 10000),
                "course": course,
                "branch": branch,
                "section": section_name,
                "students": [student["_id"] for student in section_students],  # This line create a list of students with section id
                "teacher_id": teachers_data[(course, branch)][section_num]   # this line fetch the teacher id from the teachers_data list with the key as (course, branch)
            }
            section_list.append(section_doc)  # We are appending the data to the section_list
            requests.append(UpdateOne({"_id": teachers_data[(course, branch)][section_num]}, {"$set": {"section": section_name}})) # This line of code is taking the teacher id of the teacher and updating in the teacher collection adding field section with section_name
    await db.teachers_col.bulk_write(requests)
    await db.students_section_col.insert_many(section_list)  # This line insert all the data of the list into the database collection.


# loop = asyncio.get_event_loop()
# loop.run_until_complete(generate_random_student_data(50))
