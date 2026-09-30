"""Creates college.db (SQLite) with sample data. Run once: python setup_db.py"""
import sqlite3

con = sqlite3.connect("college.db")
con.executescript("""
DROP TABLE IF EXISTS exams;
DROP TABLE IF EXISTS timetable;
DROP TABLE IF EXISTS students;
DROP TABLE IF EXISTS tickets;

CREATE TABLE exams (semester TEXT, subject TEXT, date TEXT, time TEXT, venue TEXT);
CREATE TABLE timetable (day TEXT, period TEXT, subject TEXT);
CREATE TABLE students (student_id TEXT PRIMARY KEY, name TEXT, total_fee INTEGER,
                       paid INTEGER, due_date TEXT);
CREATE TABLE tickets (id INTEGER PRIMARY KEY AUTOINCREMENT, student_id TEXT, issue TEXT,
                      created_at TEXT DEFAULT CURRENT_TIMESTAMP);
""")

con.executemany("INSERT INTO exams VALUES (?,?,?,?,?)", [
    ("semester 1", "Python Programming", "2026-11-10", "10:00 AM", "Hall A"),
    ("semester 1", "Statistics", "2026-11-13", "10:00 AM", "Hall B"),
    ("semester 1", "Database Management", "2026-11-17", "02:00 PM", "Hall A"),
    ("semester 2", "Machine Learning", "2027-04-08", "10:00 AM", "Hall C"),
    ("semester 2", "Data Visualization", "2027-04-12", "02:00 PM", "Hall A"),
])

con.executemany("INSERT INTO timetable VALUES (?,?,?)", [
    ("monday", "09:00-10:00", "Python Programming"),
    ("monday", "10:15-11:15", "Statistics"),
    ("monday", "11:30-12:30", "DBMS Lab"),
    ("tuesday", "09:00-10:00", "Machine Learning"),
    ("tuesday", "10:15-11:15", "Data Visualization"),
    ("wednesday", "09:00-10:00", "Statistics"),
    ("wednesday", "10:15-11:15", "DBMS"),
    ("thursday", "09:00-10:00", "Machine Learning"),
    ("friday", "09:00-10:00", "Data Visualization"),
    ("friday", "10:15-11:15", "Python Programming"),
])

con.executemany("INSERT INTO students VALUES (?,?,?,?,?)", [
    ("S1001", "Aarav Sharma", 223000, 150000, "2026-10-15"),
    ("S1002", "Diya Patel", 223000, 223000, None),
    ("S1003", "Rohan Mehta", 223000, 100000, "2026-10-15"),
])

con.commit()
con.close()
print("college.db created")