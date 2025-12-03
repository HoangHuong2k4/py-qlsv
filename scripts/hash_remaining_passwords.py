#!/usr/bin/env python3
"""
Hash remaining plaintext passwords in the SinhVien table.

Usage:
  python3 scripts/hash_remaining_passwords.py [--dry-run]

- Connects using DB_CONFIG from config.py
- Detects whether a password is already a Werkzeug hash (e.g., starts with 'pbkdf2:')
- Hashes only rows that appear to be plaintext
- With --dry-run, prints what would change without writing to DB
"""
import sys
import argparse
import mysql.connector
from werkzeug.security import generate_password_hash
from config import DB_CONFIG


def is_probably_hashed(password_value: str) -> bool:
    if not password_value:
        return False
    # Werkzeug default format: 'pbkdf2:sha256:iterations$salt$hash'
    return password_value.startswith('pbkdf2:') or password_value.startswith('scrypt:')


def fetch_students(conn):
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT StudentID, Password FROM SinhVien")
    rows = cur.fetchall()
    cur.close()
    return rows


essential_fields = ['StudentID', 'Password']


def hash_remaining(dry_run: bool = False) -> int:
    conn = mysql.connector.connect(**DB_CONFIG)
    try:
        students = fetch_students(conn)
        to_update = []
        for s in students:
            sid = str(s.get('StudentID'))
            pwd = s.get('Password') or ''
            if not is_probably_hashed(pwd):
                to_update.append((sid, pwd))

        if dry_run:
            print(f"Found {len(to_update)} accounts with plaintext passwords.")
            for sid, _ in to_update[:20]:
                print(f" - would hash: {sid}")
            if len(to_update) > 20:
                print(f" ... and {len(to_update) - 20} more")
            return 0

        if not to_update:
            print("No plaintext passwords found. Nothing to do.")
            return 0

        cur = conn.cursor()
        for sid, plain in to_update:
            hashed = generate_password_hash(plain, method='pbkdf2:sha256')
            cur.execute("UPDATE SinhVien SET Password=%s WHERE StudentID=%s", (hashed, sid))
        conn.commit()
        cur.close()
        print(f"Updated {len(to_update)} accounts to hashed passwords.")
        return 0
    finally:
        conn.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Hash remaining plaintext passwords in SinhVien table.')
    parser.add_argument('--dry-run', action='store_true', help='Show what would change without updating the database')
    args = parser.parse_args()
    sys.exit(hash_remaining(dry_run=args.dry_run))
