"""
Script tạo 3 sinh viên demo để test đầy đủ các chức năng gợi ý
"""
import mysql.connector
from werkzeug.security import generate_password_hash
from config import DB_CONFIG

def create_demo_students():
    """Tạo 3 sinh viên demo ở các giai đoạn khác nhau"""
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    print("=" * 60)
    print("🎓 TẠO SINH VIÊN DEMO ĐỂ TEST HỆ THỐNG")
    print("=" * 60)
    
    # ============================================
    # 1. SINH VIÊN MỚI - Năm 1 HK1 (vừa hoàn thành)
    # ============================================
    student_id = 'B2200100'
    student_name = 'Sinh viên Test - Năm 1 (Mới)'
    password_hash = generate_password_hash(student_id, method='pbkdf2:sha256')
    
    print(f"\n👤 1. Tạo sinh viên MỚI: {student_id}")
    cursor.execute("""
        INSERT INTO SinhVien (StudentID, HoTen, Password, GioiTinh, NgaySinh, Email)
        VALUES (%s, %s, %s, 'Nam', '2004-01-01', %s)
        ON DUPLICATE KEY UPDATE HoTen = VALUES(HoTen)
    """, (student_id, student_name, password_hash, f"{student_id}@student.ctu.edu.vn"))
    
    cursor.execute("DELETE FROM TienTrinh WHERE StudentID = %s", (student_id,))
    
    # Năm 1 HK1 - 6 môn cơ bản (13 TC)
    courses = [
        ('CT100', 'Kỹ năng học đại học (khối ngành CNTT)', 2, 8.0, 1, 1),
        ('TN010', 'Xác suất thống kê', 3, 7.5, 1, 1),
        ('QP010', 'Giáo dục quốc phòng và An ninh 1', 2, 8.2, 1, 1),
        ('QP011', 'Giáo dục quốc phòng và An ninh 2', 2, 8.0, 1, 1),
        ('QP012', 'Giáo dục quốc phòng và An ninh 3', 2, 7.8, 1, 1),
        ('QP013', 'Giáo dục quốc phòng và An ninh 4', 2, 7.5, 1, 1),
    ]
    
    for course_code, course_name, credits, score, year, semester in courses:
        cursor.execute("""
            INSERT INTO TienTrinh 
            (StudentID, HoTen, Year, Semester, CourseCode, CourseName, Credits, Score, GPA, Status, OnTime, Graduated, Type)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 7.8, 'Đã học', TRUE, FALSE, 'Bắt buộc')
        """, (student_id, student_name, year, semester, course_code, course_name, credits, score))
    
    print(f"   ✅ Năm 1 HK1: 6 môn (13 TC) - Sẽ được gợi ý môn cho HK2")
    
    # ============================================
    # 2. SINH VIÊN NĂM 3 - Đang học năm 3 HK1
    # ============================================
    student_id = 'B2200200'
    student_name = 'Sinh viên Test - Năm 3'
    password_hash = generate_password_hash(student_id, method='pbkdf2:sha256')
    
    print(f"\n👤 2. Tạo sinh viên NĂM 3: {student_id}")
    cursor.execute("""
        INSERT INTO SinhVien (StudentID, HoTen, Password, GioiTinh, NgaySinh, Email)
        VALUES (%s, %s, %s, 'Nữ', '2004-05-15', %s)
        ON DUPLICATE KEY UPDATE HoTen = VALUES(HoTen)
    """, (student_id, student_name, password_hash, f"{student_id}@student.ctu.edu.vn"))
    
    cursor.execute("DELETE FROM TienTrinh WHERE StudentID = %s", (student_id,))
    
    # Tổng ~70 TC (năm 1 + năm 2 + năm 3 HK1 một phần)
    courses = [
        # Năm 1
        ('CT100', 'Kỹ năng học đại học', 2, 8.5, 1, 1),
        ('TN010', 'Xác suất thống kê', 3, 8.0, 1, 1),
        ('QP010', 'GDQP 1', 2, 8.0, 1, 1),
        ('QP011', 'GDQP 2', 2, 8.5, 1, 1),
        ('QP012', 'GDQP 3', 2, 8.0, 1, 1),
        ('QP013', 'GDQP 4', 2, 7.8, 1, 1),
        ('ML014', 'Triết học Mác - Lênin', 3, 7.5, 1, 2),
        ('CT101', 'Lập trình căn bản A', 4, 8.2, 1, 2),
        ('CT172', 'Toán rời rạc', 4, 7.8, 1, 2),
        ('CT200', 'Nền tảng CNTT', 4, 8.0, 1, 2),
        ('XH011', 'Cơ sở văn hóa VN', 2, 8.5, 1, 2),
        ('ML016', 'Kinh tế chính trị', 2, 7.5, 1, 3),
        # Năm 2
        ('CT173', 'Kiến trúc máy tính', 3, 7.8, 2, 1),
        ('ML018', 'CNXHKH', 2, 8.0, 2, 1),
        ('TN001', 'Vi-tích phân A1', 3, 7.0, 2, 1),
        ('TN012', 'Đại số tuyến tính', 4, 7.5, 2, 1),
        ('XH001', 'Anh văn 1', 3, 7.8, 2, 1),
        ('CT176', 'LT hướng đối tượng', 3, 8.5, 2, 2),
        ('CT177', 'Cấu trúc dữ liệu', 3, 8.0, 2, 2),
        ('CT178', 'HĐH', 3, 7.8, 2, 2),
        ('ML019', 'Lịch sử Đảng', 2, 7.5, 2, 2),
        ('KL001', 'Pháp luật', 2, 8.0, 2, 2),
        ('TN002', 'Vi-tích phân A2', 4, 7.2, 2, 2),
        ('ML021', 'Tư tưởng HCM', 2, 7.8, 2, 3),
    ]
    
    for course_code, course_name, credits, score, year, semester in courses:
        cursor.execute("""
            INSERT INTO TienTrinh 
            (StudentID, HoTen, Year, Semester, CourseCode, CourseName, Credits, Score, GPA, Status, OnTime, Graduated, Type)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 7.8, 'Đã học', TRUE, FALSE, 'Bắt buộc')
        """, (student_id, student_name, year, semester, course_code, course_name, credits, score))
    
    print(f"   ✅ Đã học: 23 môn (~70 TC) - Sẽ gợi ý môn cho năm 3")
    
    # ============================================
    # 3. SINH VIÊN NĂM 4 - Sắp tốt nghiệp
    # ============================================
    student_id = 'B2200300'
    student_name = 'Sinh viên Test - Năm 4'
    password_hash = generate_password_hash(student_id, method='pbkdf2:sha256')
    
    print(f"\n👤 3. Tạo sinh viên NĂM 4: {student_id}")
    cursor.execute("""
        INSERT INTO SinhVien (StudentID, HoTen, Password, GioiTinh, NgaySinh, Email)
        VALUES (%s, %s, %s, 'Nam', '2004-03-20', %s)
        ON DUPLICATE KEY UPDATE HoTen = VALUES(HoTen)
    """, (student_id, student_name, password_hash, f"{student_id}@student.ctu.edu.vn"))
    
    cursor.execute("DELETE FROM TienTrinh WHERE StudentID = %s", (student_id,))
    
    # Copy dữ liệu từ B2101234 (sinh viên đã học đến năm 4 HK1)
    cursor.execute("""
        INSERT INTO TienTrinh 
        (StudentID, HoTen, Year, Semester, CourseCode, CourseName, Credits, Score, GPA, Status, OnTime, Graduated, Type, CreatedAt)
        SELECT %s, %s, Year, Semester, CourseCode, CourseName, Credits, Score, GPA, Status, OnTime, FALSE, Type, NOW()
        FROM TienTrinh 
        WHERE StudentID = 'B2101234' AND (Year < 4 OR (Year = 4 AND Semester = 1))
    """, (student_id, student_name))
    
    print(f"   ✅ Đã học đến năm 4 HK1 (~120 TC) - Sẽ gợi ý môn cho năm 4 HK2 và năm 5")
    
    conn.commit()
    cursor.close()
    conn.close()
    
    print("\n" + "=" * 60)
    print("✅ ĐÃ TẠO 3 SINH VIÊN DEMO")
    print("=" * 60)
    print("\n🔐 THÔNG TIN ĐĂNG NHẬP:")
    print("-" * 60)
    print("\n1️⃣  SINH VIÊN MỚI (Năm 1):")
    print("   Tài khoản: B2200100")
    print("   Mật khẩu: B2200100")
    print("   Gợi ý: Môn cho HK2 năm 1")
    
    print("\n2️⃣  SINH VIÊN NĂM 2:")
    print("   Tài khoản: B2200001")
    print("   Mật khẩu: B2200001")
    print("   Gợi ý: Môn cho HK2 năm 2")
    
    print("\n3️⃣  SINH VIÊN NĂM 3:")
    print("   Tài khoản: B2200200")
    print("   Mật khẩu: B2200200")
    print("   Gợi ý: Môn cho năm 3")
    
    print("\n4️⃣  SINH VIÊN NĂM 4:")
    print("   Tài khoản: B2200300")
    print("   Mật khẩu: B2200300")
    print("   Gợi ý: Môn cho năm 4 HK2 và năm 5")
    
    print("\n" + "=" * 60)
    print("🎯 BÂY GIỜ HÃY:")
    print("   1. Chạy: python3 app.py")
    print("   2. Mở: http://localhost:5000")
    print("   3. Đăng nhập với 1 trong 4 tài khoản trên")
    print("   4. Xem gợi ý môn học trên Dashboard")
    print("=" * 60)

if __name__ == "__main__":
    create_demo_students()

