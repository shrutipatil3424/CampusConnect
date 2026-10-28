"""Student profile management."""
from werkzeug.security import check_password_hash, generate_password_hash

from database.db_connection import execute, fetch_all, fetch_one
from services.auth_service import PUBLIC_COLUMNS
from utils.validators import join_list, validate_password, validate_profile_fields


def get_student(student_id: int):
    return fetch_one(f"SELECT {PUBLIC_COLUMNS} FROM students WHERE id = %s", (student_id,))


def update_profile(student_id: int, data: dict) -> tuple:
    errors = validate_profile_fields(data)
    if errors:
        return False, errors
    execute(
        """UPDATE students SET full_name=%s, college_name=%s, course=%s, academic_year=%s,
           technical_interests=%s, skills=%s, preferred_categories=%s, career_interests=%s
           WHERE id=%s""",
        (
            data["full_name"].strip(), data["college_name"].strip(), data["course"], data["academic_year"],
            join_list(data["technical_interests"]), join_list(data["skills"]),
            join_list(data["preferred_categories"]), join_list(data["career_interests"]), student_id,
        ),
    )
    return True, ["Profile updated."]


def change_password(student_id: int, current: str, new: str, confirm: str) -> tuple:
    row = fetch_one("SELECT password_hash FROM students WHERE id = %s", (student_id,))
    if not row or not check_password_hash(row["password_hash"], current or ""):
        return False, ["Current password is incorrect."]
    errors = validate_password(new)
    if new != confirm:
        errors.append("New password and confirmation do not match.")
    if new == current:
        errors.append("New password must differ from the current password.")
    if errors:
        return False, errors
    execute("UPDATE students SET password_hash=%s WHERE id=%s", (generate_password_hash(new), student_id))
    return True, ["Password changed."]


def list_students() -> list:
    return fetch_all(
        """SELECT s.id, s.full_name, s.email, s.college_name, s.course, s.academic_year, s.role,
                  s.created_at,
                  (SELECT COUNT(*) FROM registrations r
                    WHERE r.student_id = s.id AND r.status <> 'Cancelled') AS active_registrations
           FROM students s ORDER BY s.created_at DESC"""
    )
