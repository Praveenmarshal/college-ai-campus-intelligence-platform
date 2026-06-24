"""
backend/sample_data/generate_samples.py
Script to generate sample Excel files for testing the campus platform.
"""
import os
import pandas as pd
from datetime import datetime, timedelta, timezone

def generate_all():
    print("Generating sample datasets...")
    os.makedirs("backend/sample_data", exist_ok=True)
    
    # 1. Students
    students_data = [
        {"student_id": "CS01", "name": "Aditya Verma", "email": "aditya@college.edu", "phone": "9876543210", "department": "Computer Science", "batch_year": 2026, "semester": 6, "section": "A", "cgpa": 8.8, "is_hostel": True},
        {"student_id": "CS02", "name": "Bhavna Sharma", "email": "bhavna@college.edu", "phone": "9876543211", "department": "Computer Science", "batch_year": 2026, "semester": 6, "section": "A", "cgpa": 9.2, "is_hostel": False},
        {"student_id": "CS03", "name": "Chirag Patel", "email": "chirag@college.edu", "phone": "9876543212", "department": "Computer Science", "batch_year": 2026, "semester": 6, "section": "B", "cgpa": 6.8, "is_hostel": True},
        {"student_id": "CS04", "name": "Deepika Sen", "email": "deepika@college.edu", "phone": "9876543213", "department": "Computer Science", "batch_year": 2026, "semester": 6, "section": "B", "cgpa": 7.4, "is_hostel": False},
        {"student_id": "EC01", "name": "Eshaan Roy", "email": "eshaan@college.edu", "phone": "9876543214", "department": "Electronics", "batch_year": 2026, "semester": 6, "section": "A", "cgpa": 8.1, "is_hostel": True},
        {"student_id": "EC02", "name": "Farhan Khan", "email": "farhan@college.edu", "phone": "9876543215", "department": "Electronics", "batch_year": 2026, "semester": 6, "section": "A", "cgpa": 7.2, "is_hostel": False},
        {"student_id": "ME01", "name": "Gaurav Joshi", "email": "gaurav@college.edu", "phone": "9876543216", "department": "Mechanical", "batch_year": 2026, "semester": 6, "section": "A", "cgpa": 6.5, "is_hostel": True},
        {"student_id": "ME02", "name": "Himani Gupta", "email": "himani@college.edu", "phone": "9876543217", "department": "Mechanical", "batch_year": 2026, "semester": 6, "section": "A", "cgpa": 8.5, "is_hostel": False},
    ]
    pd.DataFrame(students_data).to_excel("backend/sample_data/students.xlsx", index=False)
    
    # 2. Faculty
    faculty_data = [
        {"faculty_id": "FAC01", "name": "Dr. Amit Sharma", "email": "amit.sharma@college.edu", "phone": "9988776655", "department": "Computer Science", "designation": "Professor", "qualification": "PhD", "experience_years": 15, "subjects": "DBMS,Computer Networks"},
        {"faculty_id": "FAC02", "name": "Dr. Sunita Rao", "email": "sunita.rao@college.edu", "phone": "9988776656", "department": "Computer Science", "designation": "Associate Professor", "qualification": "PhD", "experience_years": 10, "subjects": "Data Structures,Algorithms"},
        {"faculty_id": "FAC03", "name": "Prof. Rajesh Kumar", "email": "rajesh.kumar@college.edu", "phone": "9988776657", "department": "Electronics", "designation": "Professor", "qualification": "MTech", "experience_years": 18, "subjects": "Microprocessors,Embedded Systems"},
        {"faculty_id": "FAC04", "name": "Dr. Vikas Singh", "email": "vikas.singh@college.edu", "phone": "9988776658", "department": "Mechanical", "designation": "Assistant Professor", "qualification": "PhD", "experience_years": 5, "subjects": "Thermodynamics,Fluid Mechanics"},
    ]
    pd.DataFrame(faculty_data).to_excel("backend/sample_data/faculty.xlsx", index=False)
    
    # 3. Attendance
    attendance_data = []
    courses = {
        "Computer Science": ["DBMS", "Computer Networks", "Data Structures"],
        "Electronics": ["Microprocessors", "Embedded Systems"],
        "Mechanical": ["Thermodynamics", "Fluid Mechanics"]
    }
    start_date = datetime.now() - timedelta(days=20)
    for s in students_data:
        s_id = s["student_id"]
        dept = s["department"]
        s_courses = courses.get(dept, ["General"])
        for day in range(15):
            date_val = (start_date + timedelta(days=day)).strftime("%Y-%m-%d")
            # Aditya and Bhavna have high attendance; Chirag and Gaurav have low attendance
            for course in s_courses:
                if s_id in ["CS03", "ME01"] and day % 3 == 0:
                    status = "absent"
                elif s_id in ["CS03", "ME01"] and day % 5 == 0:
                    status = "absent"
                else:
                    status = "present"
                    
                attendance_data.append({
                    "student_id": s_id,
                    "date": date_val,
                    "status": status,
                    "course": course,
                    "department": dept
                })
    pd.DataFrame(attendance_data).to_excel("backend/sample_data/attendance.xlsx", index=False)
    
    # 4. Placements
    placements_data = [
        {"student_id": "CS01", "name": "Aditya Verma", "company": "Google", "package": 25.5, "status": "placed", "year": 2026, "department": "Computer Science"},
        {"student_id": "CS02", "name": "Bhavna Sharma", "company": "Microsoft", "package": 22.0, "status": "placed", "year": 2026, "department": "Computer Science"},
        {"student_id": "CS03", "name": "Chirag Patel", "company": "TCS", "package": 4.5, "status": "placed", "year": 2026, "department": "Computer Science"},
        {"student_id": "CS04", "name": "Deepika Sen", "company": "Infosys", "package": 4.0, "status": "placed", "year": 2026, "department": "Computer Science"},
        {"student_id": "EC01", "name": "Eshaan Roy", "company": "Intel", "package": 15.0, "status": "placed", "year": 2026, "department": "Electronics"},
        {"student_id": "EC02", "name": "Farhan Khan", "company": "None", "package": 0.0, "status": "unplaced", "year": 2026, "department": "Electronics"},
        {"student_id": "ME01", "name": "Gaurav Joshi", "company": "Tata Motors", "package": 6.5, "status": "placed", "year": 2026, "department": "Mechanical"},
        {"student_id": "ME02", "name": "Himani Gupta", "company": "None", "package": 0.0, "status": "unplaced", "year": 2026, "department": "Mechanical"},
    ]
    pd.DataFrame(placements_data).to_excel("backend/sample_data/placements.xlsx", index=False)
    
    # 5. Results
    results_data = []
    for s in students_data:
        s_id = s["student_id"]
        dept = s["department"]
        s_courses = courses.get(dept, ["General"])
        for course in s_courses:
            results_data.append({
                "student_id": s_id,
                "subject": course,
                "marks": 85 if s["cgpa"] > 8 else (70 if s["cgpa"] > 7 else 60),
                "cgpa": s["cgpa"],
                "semester": s["semester"]
            })
    pd.DataFrame(results_data).to_excel("backend/sample_data/results.xlsx", index=False)
    
    # 6. Fees
    fees_data = [
        {"student_id": "CS01", "fee_type": "Tuition Fee", "amount": 60000, "due": 0, "payment_status": "paid", "semester": 6, "academic_year": "2025-2026"},
        {"student_id": "CS02", "fee_type": "Tuition Fee", "amount": 60000, "due": 0, "payment_status": "paid", "semester": 6, "academic_year": "2025-2026"},
        {"student_id": "CS03", "fee_type": "Tuition Fee", "amount": 60000, "due": 15000, "payment_status": "pending", "semester": 6, "academic_year": "2025-2026"},
        {"student_id": "CS04", "fee_type": "Tuition Fee", "amount": 60000, "due": 0, "payment_status": "paid", "semester": 6, "academic_year": "2025-2026"},
        {"student_id": "EC01", "fee_type": "Tuition Fee", "amount": 55000, "due": 55000, "payment_status": "overdue", "semester": 6, "academic_year": "2025-2026"},
        {"student_id": "EC02", "fee_type": "Tuition Fee", "amount": 55000, "due": 0, "payment_status": "paid", "semester": 6, "academic_year": "2025-2026"},
        {"student_id": "ME01", "fee_type": "Tuition Fee", "amount": 50000, "due": 50000, "payment_status": "overdue", "semester": 6, "academic_year": "2025-2026"},
        {"student_id": "ME02", "fee_type": "Tuition Fee", "amount": 50000, "due": 0, "payment_status": "paid", "semester": 6, "academic_year": "2025-2026"},
    ]
    pd.DataFrame(fees_data).to_excel("backend/sample_data/fees.xlsx", index=False)
    
    # 7. Timetable
    timetable_data = [
        {"day": "Monday", "period": "Period 1", "subject": "DBMS", "time": "09:00 - 10:00", "slot": "CS-1", "department": "Computer Science", "faculty_name": "Dr. Amit Sharma"},
        {"day": "Monday", "period": "Period 2", "subject": "Computer Networks", "time": "10:00 - 11:00", "slot": "CS-2", "department": "Computer Science", "faculty_name": "Dr. Amit Sharma"},
        {"day": "Tuesday", "period": "Period 1", "subject": "Data Structures", "time": "09:00 - 10:00", "slot": "CS-3", "department": "Computer Science", "faculty_name": "Dr. Sunita Rao"},
        {"day": "Wednesday", "period": "Period 3", "subject": "DBMS", "time": "11:15 - 12:15", "slot": "CS-1", "department": "Computer Science", "faculty_name": "Dr. Amit Sharma"},
        {"day": "Thursday", "period": "Period 4", "subject": "Microprocessors", "time": "12:15 - 01:15", "slot": "EC-1", "department": "Electronics", "faculty_name": "Prof. Rajesh Kumar"},
        {"day": "Friday", "period": "Period 2", "subject": "Thermodynamics", "time": "10:00 - 11:00", "slot": "ME-1", "department": "Mechanical", "faculty_name": "Dr. Vikas Singh"},
    ]
    pd.DataFrame(timetable_data).to_excel("backend/sample_data/timetable.xlsx", index=False)
    
    # 8. Library
    library_data = [
        {"title": "Clean Code", "author": "Robert C. Martin", "isbn": "978-0132350884", "category": "Software Engineering", "available_copies": 3, "total_copies": 5, "status": "available", "due_date": ""},
        {"title": "Introduction to Algorithms", "author": "Thomas H. Cormen", "isbn": "978-0262033848", "category": "Algorithms", "available_copies": 0, "total_copies": 3, "status": "borrowed", "due_date": "2026-07-10"},
        {"title": "Database System Concepts", "author": "Abraham Silberschatz", "isbn": "978-0073523323", "category": "Database", "available_copies": 2, "total_copies": 4, "status": "available", "due_date": ""},
        {"title": "Computer Networking", "author": "James Kurose", "isbn": "978-0132856201", "category": "Networking", "available_copies": 1, "total_copies": 2, "status": "overdue", "due_date": "2026-06-15"},
    ]
    pd.DataFrame(library_data).to_excel("backend/sample_data/library.xlsx", index=False)
    
    # 9. Hostel
    hostel_data = [
        {"student_id": "CS01", "room_number": "101", "block": "Block A", "room_type": "Double", "payment_status": "paid"},
        {"student_id": "CS03", "room_number": "102", "block": "Block A", "room_type": "Double", "payment_status": "paid"},
        {"student_id": "EC01", "room_number": "201", "block": "Block B", "room_type": "Single", "payment_status": "paid"},
        {"student_id": "ME01", "room_number": "202", "block": "Block B", "room_type": "Single", "payment_status": "pending"},
        {"student_id": "", "room_number": "103", "block": "Block A", "room_type": "Double", "payment_status": "vacant"},
        {"student_id": "", "room_number": "203", "block": "Block B", "room_type": "Single", "payment_status": "vacant"},
    ]
    pd.DataFrame(hostel_data).to_excel("backend/sample_data/hostel.xlsx", index=False)
    
    # 10. Events
    events_data = [
        {"title": "Tech Fest 2026", "event_type": "Technical", "event_date": "2026-09-15 10:00:00", "venue": "Main Auditorium", "department": "Computer Science"},
        {"title": "Cultural Night", "event_type": "Cultural", "event_date": "2026-10-20 18:00:00", "venue": "Open Air Theater", "department": "General"},
        {"title": "Robotics Seminar", "event_type": "Workshop", "event_date": "2026-08-05 14:00:00", "venue": "Seminar Hall 2", "department": "Electronics"},
        {"title": "AutoCAD Workshop", "event_type": "Workshop", "event_date": "2026-07-12 09:30:00", "venue": "CAD Lab", "department": "Mechanical"},
    ]
    pd.DataFrame(events_data).to_excel("backend/sample_data/events.xlsx", index=False)
    
    print("Sample datasets generated successfully!")

if __name__ == "__main__":
    generate_all()
