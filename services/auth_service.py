"""Registration and login."""
from mysql.connector import errors as mysql_errors
from werkzeug.security import check_password_hash, generate_password_hash

from database.db_connection import execute, fetch_one
from utils.validators import join_list, validate_registration

PUBLIC_COLUMNS = (
    "id, full_name, email, college_name, course, academic_year, technical_interests, "
    "skills, preferred_categories, career_interests, role, created_at"
)


def email_exists(email: str) -> bool:
    return fetch_one("SELECT id FROM students WHERE email = %s", (email.strip().lower(),)) is not None


def register_student(data: dict) -> tuple:
    """Create a student account. Returns (success, list_of_messages)."""
    errors = validate_registration(data)
    if errors:
        return False, errors
    email = data["email"].strip().lower()
    if email_exists(email):
        return False, ["An account with this email already exists."]
    try:
        execute(
            """INSERT INTO students (full_name, email, password_hash, college_name, course,
               academic_year, technical_interests, skills, preferred_categories, career_interests, role)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'student')""",
            (
                data["full_name"].strip(), email, generate_password_hash(data["password"]),
                data["college_name"].strip(), data["course"], data["academic_year"],
                join_list(data["technical_interests"]), join_list(data["skills"]),
                join_list(data["preferred_categories"]), join_list(data["career_interests"]),
            ),
        )
    except mysql_errors.IntegrityError:
        return False, ["An account with this email already exists."]
    return True, ["Account created successfully. You can log in now."]


def login(email: str, password: str) -> tuple:
    """Verify credentials. Returns (user_dict_or_None, message)."""
    email = (email or "").strip().lower()
    if not email or not password:
        return None, "Enter your email and password."
    row = fetch_one("SELECT password_hash FROM students WHERE email = %s", (email,))
    if not row or not check_password_hash(row["password_hash"], password):
        return None, "Invalid email or password."
    user = fetch_one(f"SELECT {PUBLIC_COLUMNS} FROM students WHERE email = %s", (email,))
    return user, "Login successful."
