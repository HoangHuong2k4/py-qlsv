import mysql.connector
from config import DB_CONFIG

def get_prerequisites(course_code):
    """
    Map to SQL schema: use table `TienQuyet` with columns `CourseCode` and `PrerequisiteCode`.
    Return a list of prerequisite course codes for the given course_code.
    """
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT PrerequisiteCode FROM TienQuyet WHERE CourseCode=%s", (course_code,))
    rows = [r['PrerequisiteCode'] for r in cursor.fetchall()]
    conn.close()
    return rows
