import json
import db
import gradio
import requests


def get_student_detail(enrollment: int):
    response = requests.get(f"http://127.0.0.1:8000/student_detail/{enrollment}")
    if response.status_code == 200:
        data = response.json()
        return data
    else:
        return response.status_code


student_detail_interface = gradio.Interface(
    fn=get_student_detail,
    inputs=gradio.Number(label="Enter the enrollment"),
    outputs=gradio.Json(),
    title="Get student detail"
)


def fee_submit(student_id: int, amount: int):
    data = {"student_id": student_id, "amount": amount}
    url = f"http://127.0.0.1:8000/fee_submit"
    response = requests.post(url=url, params=data)
    if response.status_code == 200:
        data = response.json()
        return data
    else:
        return response.status_code


fee_submit_interface = gradio.Interface(
    fn=fee_submit,
    inputs=[gradio.Number(label="Enter the enrollment no"), gradio.Number(label="Enter the amount")],
    outputs=gradio.Json(),
    title="Fee Submit"
)


def get_course_branch():
    url = f"http://127.0.0.1:8000/get_courses_branches"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return data
    else:
        return response.status_code


get_all_courses_interface = gradio.Interface(
    fn=get_course_branch,
    inputs=None,
    outputs=gradio.Json(),
    title="University Course"
)


def format_data_as_table(data):
    print(data)
    if not data:
        return "No data available."
    table_html = "<table><tr><th>Serial Number</th><th>Name</th><th>Enrollment</th></tr>"
    for i, student in enumerate(data['result'], start=1):
        table_html += f"<tr><td>{i}</td><td>{student['student_name']}</td><td>{student['enrollment']}</td></tr>"
    table_html += "</table>"
    return table_html


def format_data_as_table_for_attendance(data):
    if not data:
        return "No data available."
    table_html = "<table><tr><th>Serial Number</th><th>Date</th><th>Attendance</th></tr>"
    for i, (date, attendance) in enumerate(data['attendance'].items(), start=1):
        table_html += f"<tr><td>{i}</td><td>{date}</td><td>{attendance}</td></tr>"
    table_html += "</table>"
    return table_html


def get_student_list_course_wise(course: str):
    url = f"http://127.0.0.1:8000/all_students/{course}"
    response = requests.get(url=url)
    if response.status_code == 200:
        data = response.json()
        table_html = format_data_as_table(data)
        return table_html
    else:
        return str(response.status_code)


async def attendance_record(enrollment: int):
    record = await db.attendance_col.find_one({"_id": enrollment})
    print(record)
    attendance_format = format_data_as_table_for_attendance(record)
    return attendance_format


student_data_course_wise_interface = gradio.Interface(
    fn=get_student_list_course_wise,
    inputs=gradio.Dropdown(choices=["B-Tech", "M-Tech", "CA", "Management"], label="Please choose the course."),
    outputs="html",
    title="Student data of the selected course"
)


def fee_receipt_generator(transaction_id: int):
    url = f"http://127.0.0.1:8000/fee_receipt_for_gradio"
    params = {"transaction_id": transaction_id}
    response = requests.get(url=url, params=params)
    if response.status_code == 200:
        return response.json()['file_path']
    else:
        return response.status_code


fee_receipt_pdf_interface = gradio.Interface(
    fn=fee_receipt_generator,
    inputs=gradio.Number(label="Enter the transaction id"),
    outputs=gradio.File(label="Download receipt"),
    title="Fee receipt generation"
)


def register_student(student_name, age, father_name, phone, course, branch, aadhar, address, pincode, district, state, country, board):
    registration_data = {
        "student_name": student_name,
        "age": age,
        "father_name": father_name,
        "phone": phone,
        "course": course,
        "branch": branch,
        "aadhar": aadhar,
        "address": address,
        "pincode": pincode,
        "district": district,
        "state": state,
        "country": country,
        "board": board
    }

    url = "http://127.0.0.1:8000/registration"
    headers = {'Content-Type': 'application/json'}
    response = requests.post(url, data=json.dumps(registration_data), headers=headers)
    if response.status_code == 200:
        return f"Applicant registered successfully. Enrollment No : {response.json()['enrollment_no']}"
    else:
        return f"Registration failed. Error : {response.json()['detail']}"


register_student_interface = gradio.Interface(
    fn=register_student,
    inputs=[
        gradio.Textbox(label="Student Name"),
        gradio.Number(minimum=18, maximum=25, label="Age"),
        gradio.Textbox(label="Father' s Name"),
        gradio.Number(label="Phone"),
        gradio.Dropdown(["B-Tech", "M-Tech", "CA", "Management"], label="Course"),
        gradio.Dropdown(["Computer Science", "Electrical", "Mechanical", "Civil", "BCA", "MCA", "BBA", "MBA"], label="Branch"),
        gradio.Number(label="Aadhar"),
        gradio.Textbox(label="Address"),
        gradio.Number(label="Pincode"),
        gradio.Textbox(label="District"),
        gradio.Textbox(label="State"),
        gradio.Textbox(label="Country"),
        gradio.Textbox(label="Board"),
    ],
    outputs=gradio.Textbox()
)


def teacher_login(username: int, password: str):
    url = "http://127.0.0.1:8000/login"
    body = {
        "username": int(username),
        "password": password
    }
    print(body)
    response = requests.post(url, json=body)
    return response.json()['access_token']



teacher_login_interface = gradio.Interface(
    fn=teacher_login,
    inputs=[
        gradio.Number(description="Enter the teacher ID"),
        gradio.Textbox(description="Enter the password")
    ],
    outputs=gradio.Textbox(),
    title="Teacher Login",
    description="Enter your username and password to login as a teacher"

)


def teacher_gets_student_data(token: str):
    url = f"http://127.0.0.1:8000/students_data/"
    params = {
        "token": token
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        return response.status_code


teacher_gets_student_data_interface = gradio.Interface(
    fn=teacher_gets_student_data,
    inputs=gradio.Textbox(description="Enter the token."),
    outputs=gradio.Json(),
    title="Teacher-gets-student-data",
)


def attendance_mark(student_id: int, date: str, attendance_status: str, token: str):
    url = f"http://127.0.0.1:8000/attendance-mark-by-teacher/"
    data = {
        "student_id": int(student_id),
        "date": date,
        "attendance_status": attendance_status,
        "token": token,
    }
    response = requests.post(url, json=data)
    print(response)
    print(response.content)
    if response.status_code == 200:
        return response.json()
    else:
        return response.status_code


student_attendance_mark_interface = gradio.Interface(
    fn=attendance_mark,
    inputs=[
        gradio.Number(placeholder="Enter the enrollment of the student...."),
        gradio.Textbox(placeholder="Enter the date format(%Y-%m-%d) ex.(2023-11-01)"),
        gradio.Textbox(placeholder="Enter the attendance (present or absent)..."),
        gradio.Textbox(placeholder="Enter the token."),
    ],
    outputs=gradio.Json(),
    title="Student-Attendance-Mark",
)


attendance_record_interface = gradio.Interface(
    fn=attendance_record,
    inputs=gradio.Number(description="Enter the enrollment....."),
    outputs="html",
    title="Student-Attendance-Record"
)


gradio.TabbedInterface(
     [student_detail_interface, fee_submit_interface, get_all_courses_interface, student_data_course_wise_interface, fee_receipt_pdf_interface, register_student_interface, teacher_login_interface, teacher_gets_student_data_interface, student_attendance_mark_interface, attendance_record_interface], ["Student detail", "fee submit", "get all courses", "student data course wise", "fee receipt downloader", "Register Student", "Teacher login", "Teacher-gets-student-data", "Student-Attendance-Mark", "Attendance-Record"], title="Arshad University", theme=gradio.themes.Glass()).launch(debug=True)
