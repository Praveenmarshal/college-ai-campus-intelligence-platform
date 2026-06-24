"""
Sample Data Generator for AI Campus Intelligence Platform.

Generates realistic Excel (.xlsx) files with Indian college data
for testing all platform modules.

Usage:
    python generate_sample_data.py
"""

import os
import random
from datetime import datetime, timedelta

import pandas as pd

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
DEPARTMENTS = ["CSE", "ECE", "ME", "CE", "EEE"]
SECTIONS = ["A", "B"]
BATCH_YEARS = [2022, 2023, 2024, 2025]

FIRST_NAMES_MALE = [
    "Aarav", "Vivaan", "Aditya", "Vihaan", "Arjun", "Sai", "Reyansh",
    "Ayaan", "Krishna", "Ishaan", "Shaurya", "Atharva", "Advik", "Pranav",
    "Advait", "Dhruv", "Kabir", "Ritvik", "Anirudh", "Harsh", "Rohan",
    "Karthik", "Manish", "Rahul", "Vikram", "Suresh", "Rajesh", "Amit",
]

FIRST_NAMES_FEMALE = [
    "Ananya", "Diya", "Myra", "Sara", "Aadhya", "Isha", "Priya",
    "Kavya", "Anika", "Navya", "Riya", "Sneha", "Pooja", "Neha",
    "Meera", "Tanvi", "Shreya", "Divya", "Pallavi", "Swathi",
    "Lakshmi", "Bhavana",
]

LAST_NAMES = [
    "Sharma", "Verma", "Patel", "Gupta", "Singh", "Kumar", "Reddy",
    "Nair", "Joshi", "Mishra", "Chauhan", "Rao", "Iyer", "Mehta",
    "Agarwal", "Bhat", "Das", "Pillai", "Menon", "Kulkarni",
    "Deshmukh", "Patil", "Saxena", "Chopra", "Malhotra",
]

COMPANIES = [
    "TCS", "Infosys", "Wipro", "Google", "Microsoft", "Amazon",
    "Cognizant", "HCL Technologies", "Tech Mahindra", "Capgemini",
    "Accenture", "Deloitte", "Zoho", "Flipkart", "Razorpay",
    "PhonePe", "Swiggy", "Oracle", "IBM", "Samsung",
]

PACKAGES = {
    "TCS": (3.5, 7.0),
    "Infosys": (3.6, 8.0),
    "Wipro": (3.5, 6.5),
    "Google": (25.0, 45.0),
    "Microsoft": (18.0, 42.0),
    "Amazon": (15.0, 38.0),
    "Cognizant": (4.0, 8.0),
    "HCL Technologies": (3.5, 7.0),
    "Tech Mahindra": (3.5, 6.5),
    "Capgemini": (4.0, 8.5),
    "Accenture": (4.5, 9.0),
    "Deloitte": (6.0, 12.0),
    "Zoho": (5.0, 14.0),
    "Flipkart": (12.0, 28.0),
    "Razorpay": (10.0, 22.0),
    "PhonePe": (10.0, 20.0),
    "Swiggy": (8.0, 18.0),
    "Oracle": (8.0, 16.0),
    "IBM": (5.0, 12.0),
    "Samsung": (8.0, 18.0),
}

DEPT_SUBJECTS = {
    "CSE": [
        "Data Structures", "Algorithms", "DBMS", "Operating Systems",
        "Computer Networks", "Machine Learning", "Web Development",
        "Software Engineering",
    ],
    "ECE": [
        "Digital Electronics", "Signals & Systems", "VLSI Design",
        "Microprocessors", "Communication Systems", "Embedded Systems",
        "Analog Circuits", "Control Systems",
    ],
    "ME": [
        "Thermodynamics", "Fluid Mechanics", "Strength of Materials",
        "Manufacturing Technology", "Machine Design", "Heat Transfer",
        "CAD/CAM", "Engineering Drawing",
    ],
    "CE": [
        "Structural Analysis", "Concrete Technology", "Surveying",
        "Geotechnical Engineering", "Transportation Engineering",
        "Environmental Engineering", "Hydraulics", "Building Materials",
    ],
    "EEE": [
        "Power Systems", "Electrical Machines", "Power Electronics",
        "Control Systems", "Renewable Energy", "Circuit Theory",
        "Instrumentation", "High Voltage Engineering",
    ],
}

DESIGNATIONS = [
    "Professor", "Associate Professor", "Assistant Professor",
    "Senior Lecturer", "Lecturer",
]

QUALIFICATIONS = ["Ph.D.", "M.Tech", "M.E.", "M.S."]

BOOK_CATEGORIES = [
    "Computer Science", "Electronics", "Mechanical", "Civil",
    "Electrical", "Mathematics", "Physics", "General Engineering",
]

BOOKS = [
    ("Introduction to Algorithms", "Thomas H. Cormen"),
    ("Design Patterns", "Erich Gamma"),
    ("Clean Code", "Robert C. Martin"),
    ("Computer Networking", "James Kurose"),
    ("Database System Concepts", "Abraham Silberschatz"),
    ("Operating System Concepts", "Abraham Silberschatz"),
    ("Digital Design", "M. Morris Mano"),
    ("Microelectronic Circuits", "Adel S. Sedra"),
    ("Engineering Mechanics", "R.C. Hibbeler"),
    ("Strength of Materials", "R.K. Rajput"),
    ("Fluid Mechanics", "Frank M. White"),
    ("Thermodynamics", "Yunus A. Cengel"),
    ("Structural Analysis", "R.C. Hibbeler"),
    ("Surveying and Levelling", "T.P. Kanetkar"),
    ("Electric Machinery", "Stephen D. Umans"),
    ("Power System Engineering", "I.J. Nagrath"),
    ("Linear Algebra", "Gilbert Strang"),
    ("Engineering Mathematics", "B.S. Grewal"),
    ("Discrete Mathematics", "Kenneth H. Rosen"),
    ("Artificial Intelligence", "Stuart Russell"),
    ("Machine Learning", "Tom M. Mitchell"),
    ("Data Structures using C", "Reema Thareja"),
    ("Theory of Computation", "Michael Sipser"),
    ("Compiler Design", "Alfred V. Aho"),
    ("Computer Organization", "Carl Hamacher"),
    ("Signals and Systems", "Alan V. Oppenheim"),
    ("Control Systems Engineering", "Norman S. Nise"),
    ("VLSI Design", "Wayne Wolf"),
    ("Concrete Technology", "M.S. Shetty"),
    ("Environmental Engineering", "S.K. Garg"),
]

EVENT_TYPES = [
    "Technical", "Cultural", "Sports", "Workshop",
    "Seminar", "Hackathon", "Guest Lecture",
]

VENUES = [
    "Main Auditorium", "Seminar Hall A", "Seminar Hall B",
    "Indoor Stadium", "Open Air Theatre", "Computer Lab 1",
    "Conference Room", "Library Hall",
]

TIME_SLOTS = [
    ("09:00 - 09:50", "1"),
    ("09:50 - 10:40", "2"),
    ("10:50 - 11:40", "3"),
    ("11:40 - 12:30", "4"),
    ("13:30 - 14:20", "5"),
    ("14:20 - 15:10", "6"),
    ("15:20 - 16:10", "7"),
]

DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
random.seed(42)

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))


def _random_name() -> str:
    first_pool = FIRST_NAMES_MALE + FIRST_NAMES_FEMALE
    return f"{random.choice(first_pool)} {random.choice(LAST_NAMES)}"


def _random_phone() -> str:
    return f"+91 {random.randint(70000, 99999)}{random.randint(10000, 99999)}"


def _random_email(name: str, domain: str = "college.edu.in") -> str:
    parts = name.lower().split()
    return f"{parts[0]}.{parts[1]}{random.randint(1, 99)}@{domain}"


def _save(df: pd.DataFrame, filename: str) -> None:
    path = os.path.join(OUTPUT_DIR, filename)
    df.to_excel(path, index=False, engine="openpyxl")
    print(f"  ✔ Created {filename}  ({len(df)} rows)")


# ---------------------------------------------------------------------------
# Generators
# ---------------------------------------------------------------------------

def generate_students(n: int = 50) -> pd.DataFrame:
    """Generate student records."""
    rows = []
    for i in range(1, n + 1):
        dept = DEPARTMENTS[(i - 1) % len(DEPARTMENTS)]
        name = _random_name()
        rows.append({
            "student_id": f"STU{i:04d}",
            "name": name,
            "email": _random_email(name),
            "department": dept,
            "batch_year": random.choice(BATCH_YEARS),
            "semester": random.randint(1, 8),
            "cgpa": round(random.uniform(5.5, 9.8), 2),
            "phone": _random_phone(),
            "section": random.choice(SECTIONS),
        })
    return pd.DataFrame(rows)


def generate_faculty(n: int = 20) -> pd.DataFrame:
    """Generate faculty records."""
    rows = []
    for i in range(1, n + 1):
        dept = DEPARTMENTS[(i - 1) % len(DEPARTMENTS)]
        name = _random_name()
        subjects = ", ".join(random.sample(DEPT_SUBJECTS[dept], k=min(3, len(DEPT_SUBJECTS[dept]))))
        rows.append({
            "faculty_id": f"FAC{i:04d}",
            "name": name,
            "email": _random_email(name, "faculty.college.edu.in"),
            "department": dept,
            "designation": random.choice(DESIGNATIONS),
            "qualification": random.choice(QUALIFICATIONS),
            "experience_years": random.randint(2, 30),
            "subjects": subjects,
        })
    return pd.DataFrame(rows)


def generate_attendance(students_df: pd.DataFrame, n: int = 500) -> pd.DataFrame:
    """Generate attendance records spanning 30 days."""
    base_date = datetime(2026, 5, 25)
    rows = []
    for _ in range(n):
        student = students_df.sample(1).iloc[0]
        dept = student["department"]
        course = random.choice(DEPT_SUBJECTS[dept])
        date = base_date + timedelta(days=random.randint(0, 29))
        rows.append({
            "student_id": student["student_id"],
            "date": date.strftime("%Y-%m-%d"),
            "status": random.choices(["present", "absent"], weights=[80, 20])[0],
            "course": course,
            "department": dept,
        })
    return pd.DataFrame(rows)


def generate_placements(students_df: pd.DataFrame, n: int = 30) -> pd.DataFrame:
    """Generate placement records."""
    eligible = students_df[students_df["semester"] >= 6]
    if len(eligible) < n:
        eligible = students_df  # fallback
    selected = eligible.sample(n=min(n, len(eligible)), replace=True)

    rows = []
    for _, stu in selected.iterrows():
        company = random.choice(COMPANIES)
        lo, hi = PACKAGES[company]
        status = random.choices(["placed", "unplaced"], weights=[75, 25])[0]
        package = round(random.uniform(lo, hi), 2) if status == "placed" else 0.0
        rows.append({
            "student_id": stu["student_id"],
            "name": stu["name"],
            "company_name": company,
            "package_lpa": package,
            "status": status,
            "year": random.choice([2025, 2026]),
            "department": stu["department"],
        })
    return pd.DataFrame(rows)


def generate_results(students_df: pd.DataFrame, n: int = 50) -> pd.DataFrame:
    """Generate exam result records."""
    rows = []
    for _ in range(n):
        stu = students_df.sample(1).iloc[0]
        dept = stu["department"]
        subject = random.choice(DEPT_SUBJECTS[dept])
        marks = random.randint(35, 100)
        cgpa = round(random.uniform(5.0, 10.0), 2)
        rows.append({
            "student_id": stu["student_id"],
            "subject": subject,
            "marks": marks,
            "cgpa": cgpa,
            "semester": stu["semester"],
        })
    return pd.DataFrame(rows)


def generate_timetable(faculty_df: pd.DataFrame, n: int = 30) -> pd.DataFrame:
    """Generate timetable slots for 3 departments."""
    depts = random.sample(DEPARTMENTS, 3)
    rows = []
    for _ in range(n):
        dept = random.choice(depts)
        day = random.choice(DAYS)
        time_str, slot = random.choice(TIME_SLOTS)
        subject = random.choice(DEPT_SUBJECTS[dept])
        dept_faculty = faculty_df[faculty_df["department"] == dept]
        if dept_faculty.empty:
            faculty_name = _random_name()
        else:
            faculty_name = dept_faculty.sample(1).iloc[0]["name"]
        rows.append({
            "day": day,
            "period": int(slot),
            "subject": subject,
            "time": time_str,
            "slot": slot,
            "department": dept,
            "faculty": faculty_name,
        })
    return pd.DataFrame(rows)


def generate_library(n: int = 30) -> pd.DataFrame:
    """Generate library book records."""
    selected = random.sample(BOOKS, k=min(n, len(BOOKS)))
    rows = []
    for title, author in selected:
        total = random.randint(3, 15)
        rows.append({
            "title": title,
            "author": author,
            "isbn": f"978-{random.randint(1000, 9999)}-{random.randint(1000, 9999)}-{random.randint(10, 99)}",
            "category": random.choice(BOOK_CATEGORIES),
            "available": random.randint(0, total),
            "total": total,
        })
    return pd.DataFrame(rows)


def generate_hostel(students_df: pd.DataFrame, n: int = 20) -> pd.DataFrame:
    """Generate hostel room allocation records."""
    selected = students_df.sample(n=min(n, len(students_df)))
    blocks = ["A", "B"]
    room_types = ["Single", "Double", "Triple"]
    rows = []
    for idx, (_, stu) in enumerate(selected.iterrows(), start=1):
        block = blocks[idx % len(blocks)]
        room = f"{block}{100 + idx}"
        rows.append({
            "student_id": stu["student_id"],
            "room_number": room,
            "block": block,
            "type": random.choice(room_types),
            "payment": random.choice(["Paid", "Pending", "Partial"]),
        })
    return pd.DataFrame(rows)


def generate_events(n: int = 10) -> pd.DataFrame:
    """Generate upcoming campus events."""
    base_date = datetime(2026, 7, 1)
    rows = []
    for i in range(n):
        event_date = base_date + timedelta(days=random.randint(1, 60))
        rows.append({
            "title": f"Event {i + 1} - {random.choice(['TechFest', 'CodeSprint', 'RoboWars', 'Symposium', 'Cultural Night', 'Sports Meet', 'Innovate', 'DesignThon', 'AI Summit', 'Startup Pitch'])}",
            "event_type": random.choice(EVENT_TYPES),
            "event_date": event_date.strftime("%Y-%m-%d"),
            "venue": random.choice(VENUES),
            "department": random.choice(DEPARTMENTS + ["All"]),
        })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    print("=" * 60)
    print("  AI Campus Intelligence Platform — Sample Data Generator")
    print("=" * 60)
    print(f"  Output directory: {OUTPUT_DIR}\n")

    print("[1/9] Generating students.xlsx …")
    students_df = generate_students(50)
    _save(students_df, "students.xlsx")

    print("[2/9] Generating faculty.xlsx …")
    faculty_df = generate_faculty(20)
    _save(faculty_df, "faculty.xlsx")

    print("[3/9] Generating attendance.xlsx …")
    attendance_df = generate_attendance(students_df, 500)
    _save(attendance_df, "attendance.xlsx")

    print("[4/9] Generating placements.xlsx …")
    placements_df = generate_placements(students_df, 30)
    _save(placements_df, "placements.xlsx")

    print("[5/9] Generating results.xlsx …")
    results_df = generate_results(students_df, 50)
    _save(results_df, "results.xlsx")

    print("[6/9] Generating timetable.xlsx …")
    timetable_df = generate_timetable(faculty_df, 30)
    _save(timetable_df, "timetable.xlsx")

    print("[7/9] Generating library.xlsx …")
    library_df = generate_library(30)
    _save(library_df, "library.xlsx")

    print("[8/9] Generating hostel.xlsx …")
    hostel_df = generate_hostel(students_df, 20)
    _save(hostel_df, "hostel.xlsx")

    print("[9/9] Generating events.xlsx …")
    events_df = generate_events(10)
    _save(events_df, "events.xlsx")

    print("\n" + "=" * 60)
    print("  ✅  All 9 sample data files generated successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()
