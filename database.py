import sqlite3
import os

DATABASE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "students.db"
)


def get_connection():
    return sqlite3.connect(DATABASE)


def initialize_database():
    with get_connection() as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS students (
                student_id TEXT PRIMARY KEY,
                full_name TEXT NOT NULL,
                course TEXT NOT NULL,
                year_level TEXT NOT NULL
            )
        """)

        connection.execute("""
            CREATE TABLE IF NOT EXISTS registration_queue (
                queue_id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id TEXT NOT NULL,
                full_name TEXT NOT NULL,
                course TEXT NOT NULL,
                year_level TEXT NOT NULL
            )
        """)


def load_students():
    with get_connection() as connection:
        rows = connection.execute("""
            SELECT student_id, full_name, course, year_level
            FROM students
            ORDER BY student_id
        """).fetchall()

    return [
        {
            "student_id": row[0],
            "full_name": row[1],
            "course": row[2],
            "year_level": row[3]
        }
        for row in rows
    ]


def add_student(student):
    with get_connection() as connection:
        connection.execute("""
            INSERT INTO students
            (student_id, full_name, course, year_level)
            VALUES (?, ?, ?, ?)
        """, (
            student["student_id"],
            student["full_name"],
            student["course"],
            student["year_level"]
        ))


def update_student(student):
    with get_connection() as connection:
        connection.execute("""
            UPDATE students
            SET full_name = ?, course = ?, year_level = ?
            WHERE student_id = ?
        """, (
            student["full_name"],
            student["course"],
            student["year_level"],
            student["student_id"]
        ))


def delete_student(student_id):
    with get_connection() as connection:
        connection.execute("""
            DELETE FROM students
            WHERE student_id = ?
        """, (student_id,))


def load_queue():
    with get_connection() as connection:
        rows = connection.execute("""
            SELECT student_id, full_name, course, year_level
            FROM registration_queue
            ORDER BY queue_id
        """).fetchall()

    return [
        {
            "student_id": row[0],
            "full_name": row[1],
            "course": row[2],
            "year_level": row[3]
        }
        for row in rows
    ]


def add_to_queue(student):
    with get_connection() as connection:
        connection.execute("""
            INSERT INTO registration_queue
            (student_id, full_name, course, year_level)
            VALUES (?, ?, ?, ?)
        """, (
            student["student_id"],
            student["full_name"],
            student["course"],
            student["year_level"]
        ))


def remove_from_queue():
    with get_connection() as connection:
        connection.execute("""
            DELETE FROM registration_queue
            WHERE queue_id = (
                SELECT queue_id
                FROM registration_queue
                ORDER BY queue_id
                LIMIT 1
            )
        """)


def delete_from_queue(student_id):
    with get_connection() as connection:
        connection.execute("""
            DELETE FROM registration_queue
            WHERE student_id = ?
        """, (student_id,))