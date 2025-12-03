#!/usr/bin/env python3
"""
Set or update a student's password (hashed) in the database.
Usage:
  python3 scripts/set_password.py STUDENT_ID NEW_PASSWORD

This will compute a salted hash using werkzeug.security.generate_password_hash
and update the SinhVien.Password column. Requires the app's DB_CONFIG in config.py.
"""
import sys
import mysql.connector
from werkzeug.security import generate_password_hash
from config import DB_CONFIG


def set_password(student_id: str, new_password: str):
    h = generate_password_hash(new_password, method='pbkdf2:sha256')
    conn = mysql.connector.connect(**DB_CONFIG)
    cur = conn.cursor()
    cur.execute("SELECT StudentID FROM SinhVien WHERE StudentID=%s", (student_id,))
    if cur.fetchone() is None:
        print(f"Student {student_id} not found.")
        conn.close()
        return 2
    cur.execute("UPDATE SinhVien SET Password=%s WHERE StudentID=%s", (h, student_id))
    conn.commit()
    conn.close()
    print(f"Password for {student_id} updated (hashed).")
    return 0


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Usage: python3 scripts/set_password.py STUDENT_ID NEW_PASSWORD")
        sys.exit(1)
    sid = sys.argv[1]
    pwd = sys.argv[2]
    sys.exit(set_password(sid, pwd))
