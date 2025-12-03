"""
Script tự động setup database và import dữ liệu
Thực hiện đầy đủ: Tạo database → Tạo tables → Import dữ liệu từ Excel
"""
import mysql.connector
import pandas as pd
import os
import sys
from werkzeug.security import generate_password_hash
from config import DB_CONFIG

def connect_mysql_server():
    """Kết nối MySQL server (không cần database)"""
    try:
        config = DB_CONFIG.copy()
        if 'database' in config:
            del config['database']
        conn = mysql.connector.connect(**config)
        print("✅ Kết nối MySQL server thành công!")
        return conn
    except mysql.connector.Error as err:
        print(f"❌ Lỗi kết nối MySQL: {err}")
        print("\n⚠️  HƯỚNG DẪN XỬ LÝ:")
        print("1. Mở XAMPP Control Panel")
        print("2. Start MySQL (nút Start bên cạnh MySQL)")
        print("3. Đợi MySQL chạy (chữ 'MySQL' sẽ có nền xanh)")
        print("4. Chạy lại script này")
        sys.exit(1)

def create_database(conn):
    """Tạo database QuanLyHocTap"""
    cursor = conn.cursor()
    try:
        # Tạo database
        cursor.execute("DROP DATABASE IF EXISTS QuanLyHocTap")
        cursor.execute("CREATE DATABASE QuanLyHocTap CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci")
        cursor.execute("USE QuanLyHocTap")
        print("✅ Đã tạo database QuanLyHocTap")
        return True
    except mysql.connector.Error as err:
        print(f"❌ Lỗi tạo database: {err}")
        return False
    finally:
        cursor.close()

def execute_sql_file(conn, sql_file):
    """Thực thi file SQL"""
    cursor = conn.cursor()
    try:
        with open(sql_file, 'r', encoding='utf-8') as f:
            sql_content = f.read()
            
        # Tách các lệnh SQL
        statements = []
        current_statement = ""
        
        for line in sql_content.split('\n'):
            # Bỏ qua comments
            if line.strip().startswith('--') or line.strip().startswith('/*'):
                continue
            
            current_statement += line + '\n'
            
            # Nếu gặp dấu chấm phẩy, đó là kết thúc một statement
            if ';' in line:
                statements.append(current_statement)
                current_statement = ""
        
        # Thực thi từng statement
        for statement in statements:
            statement = statement.strip()
            if statement and not statement.startswith('--'):
                try:
                    # Bỏ qua các lệnh SET đặc biệt
                    if any(x in statement.upper() for x in ['SET SQL_MODE', 'SET time_zone', 'START TRANSACTION', 'COMMIT']):
                        continue
                    cursor.execute(statement)
                except mysql.connector.Error as err:
                    # Chỉ in warning, không dừng
                    if 'already exists' not in str(err) and 'Duplicate' not in str(err):
                        print(f"⚠️  Warning: {str(err)[:100]}")
        
        conn.commit()
        print(f"✅ Đã thực thi: {os.path.basename(sql_file)}")
        return True
        
    except Exception as e:
        print(f"❌ Lỗi đọc file SQL: {e}")
        return False
    finally:
        cursor.close()

def create_tables_from_sql(conn):
    """Tạo các bảng từ file SQL"""
    sql_file = 'QuanLyHocTap.sql'
    
    if not os.path.exists(sql_file):
        print(f"❌ Không tìm thấy file {sql_file}")
        return False
    
    print(f"\n📝 Tạo bảng từ {sql_file}...")
    return execute_sql_file(conn, sql_file)

def run_migrations(conn):
    """Chạy các migration để cập nhật schema"""
    cursor = conn.cursor()
    
    try:
        # 1. Thêm cột Password vào bảng SinhVien nếu chưa có
        print("\n🔧 Cập nhật schema SinhVien...")
        try:
            cursor.execute("""
                ALTER TABLE SinhVien 
                ADD COLUMN Password VARCHAR(260) NOT NULL DEFAULT '' COMMENT 'pbkdf2:sha256 hash'
            """)
            print("✅ Đã thêm cột Password")
        except mysql.connector.Error as e:
            if 'Duplicate column' in str(e):
                print("ℹ️  Cột Password đã tồn tại")
            else:
                print(f"⚠️  Lỗi thêm Password: {e}")
        
        # 2. Cập nhật schema TienTrinh
        print("\n🔧 Cập nhật schema TienTrinh...")
        
        # Thêm cột GPA nếu chưa có
        try:
            cursor.execute("""
                ALTER TABLE TienTrinh 
                ADD COLUMN GPA DECIMAL(3,2) NULL COMMENT 'GPA tích lũy' AFTER Score
            """)
            print("✅ Đã thêm cột GPA")
        except mysql.connector.Error as e:
            if 'Duplicate column' in str(e):
                print("ℹ️  Cột GPA đã tồn tại")
            else:
                print(f"⚠️  Lỗi thêm GPA: {e}")
        
        # Thêm cột OnTime nếu chưa có
        try:
            cursor.execute("""
                ALTER TABLE TienTrinh 
                ADD COLUMN OnTime BOOLEAN DEFAULT TRUE COMMENT 'Học đúng tiến độ'
            """)
            print("✅ Đã thêm cột OnTime")
        except mysql.connector.Error as e:
            if 'Duplicate column' in str(e):
                print("ℹ️  Cột OnTime đã tồn tại")
            else:
                print(f"⚠️  Lỗi thêm OnTime: {e}")
        
        # Thêm cột Graduated nếu chưa có
        try:
            cursor.execute("""
                ALTER TABLE TienTrinh 
                ADD COLUMN Graduated BOOLEAN DEFAULT FALSE COMMENT 'Đã tốt nghiệp'
            """)
            print("✅ Đã thêm cột Graduated")
        except mysql.connector.Error as e:
            if 'Duplicate column' in str(e):
                print("ℹ️  Cột Graduated đã tồn tại")
            else:
                print(f"⚠️  Lỗi thêm Graduated: {e}")
        
        conn.commit()
        
    except Exception as e:
        print(f"⚠️  Lỗi khi cập nhật schema: {e}")
    finally:
        cursor.close()
    
    return True

def import_excel_data(conn):
    """Import dữ liệu từ Excel"""
    excel_file = 'data/student_data_100-2.xlsx'
    
    if not os.path.exists(excel_file):
        print(f"❌ Không tìm thấy file {excel_file}")
        return False
    
    print(f"\n📊 Đọc dữ liệu từ {excel_file}...")
    try:
        df = pd.read_excel(excel_file)
        print(f"✅ Đọc được {len(df)} dòng dữ liệu")
        print(f"📋 Các cột: {', '.join(df.columns)}")
    except Exception as e:
        print(f"❌ Lỗi đọc Excel: {e}")
        return False
    
    # Import sinh viên
    print("\n👥 Bước 1: Import danh sách sinh viên...")
    students = df[['StudentID']].drop_duplicates()
    cursor = conn.cursor()
    
    for _, row in students.iterrows():
        student_id = str(row['StudentID']).strip()
        password_hash = generate_password_hash(student_id, method='pbkdf2:sha256')
        
        try:
            cursor.execute("""
                INSERT INTO SinhVien (StudentID, HoTen, Password, GioiTinh, NgaySinh, Email)
                VALUES (%s, %s, %s, 'Nam', '2003-01-01', %s)
                ON DUPLICATE KEY UPDATE HoTen = VALUES(HoTen)
            """, (
                student_id,
                f"Sinh viên {student_id}",
                password_hash,
                f"{student_id}@student.ctu.edu.vn"
            ))
        except mysql.connector.Error as err:
            print(f"⚠️  Lỗi thêm sinh viên {student_id}: {err}")
    
    conn.commit()
    print(f"✅ Đã import {len(students)} sinh viên")
    
    # Import tiến trình
    print("\n📚 Bước 2: Import tiến trình học tập...")
    inserted = 0
    errors = 0
    
    for idx, row in df.iterrows():
        try:
            student_id = str(row['StudentID']).strip()
            year = int(row['Year'])
            semester = int(row['Semester'])
            course_code = str(row['CourseCode']).strip()
            course_name = str(row['CourseName']).strip()
            credits = int(row['Credits'])
            score = float(row['Score']) if pd.notna(row['Score']) else None
            gpa = float(row['GPA']) if pd.notna(row['GPA']) else None
            ontime = bool(row['OnTime']) if 'OnTime' in row and pd.notna(row['OnTime']) else True
            graduated = bool(row['Grad']) if 'Grad' in row and pd.notna(row['Grad']) else False
            
            # Xác định trạng thái
            if score is not None and score >= 4.0:
                status = 'Đã học'
                xep_loai = 'A' if score >= 8.5 else ('B+' if score >= 7.0 else ('B' if score >= 5.5 else 'C+'))
            elif score is not None:
                status = 'Đã học'
                xep_loai = 'F'
            else:
                status = 'Chưa học'
                xep_loai = None
            
            cursor.execute("""
                INSERT INTO TienTrinh 
                (StudentID, HoTen, Year, Semester, CourseCode, CourseName, Credits, 
                 Score, GPA, Status, XepLoai, OnTime, Graduated, Type, CreatedAt)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'Bắt buộc', NOW())
                ON DUPLICATE KEY UPDATE 
                    Score = VALUES(Score), 
                    GPA = VALUES(GPA), 
                    Status = VALUES(Status),
                    XepLoai = VALUES(XepLoai),
                    OnTime = VALUES(OnTime),
                    Graduated = VALUES(Graduated)
            """, (
                student_id, f"Sinh viên {student_id}", year, semester, 
                course_code, course_name, credits, score, gpa, 
                status, xep_loai, ontime, graduated
            ))
            inserted += 1
            
            if inserted % 100 == 0:
                conn.commit()
                print(f"⏳ Đã import {inserted}/{len(df)} dòng...")
                
        except Exception as e:
            errors += 1
            if errors <= 5:  # Chỉ in 5 lỗi đầu
                print(f"⚠️  Lỗi dòng {idx + 1}: {e}")
    
    conn.commit()
    cursor.close()
    
    print(f"✅ Đã import {inserted} records tiến trình ({errors} lỗi)")
    return True

def verify_data(conn):
    """Kiểm tra dữ liệu đã import"""
    cursor = conn.cursor()
    
    print("\n" + "=" * 60)
    print("📊 THỐNG KÊ DỮ LIỆU")
    print("=" * 60)
    
    # Đếm sinh viên
    cursor.execute("SELECT COUNT(*) FROM SinhVien")
    student_count = cursor.fetchone()[0]
    print(f"👥 Tổng số sinh viên: {student_count}")
    
    # Đếm môn học
    cursor.execute("SELECT COUNT(*) FROM MonHoc")
    course_count = cursor.fetchone()[0]
    print(f"📚 Tổng số môn học: {course_count}")
    
    # Đếm tiến trình
    cursor.execute("SELECT COUNT(*) FROM TienTrinh")
    progress_count = cursor.fetchone()[0]
    print(f"📝 Tổng số records tiến trình: {progress_count}")
    
    # Đếm sinh viên có dữ liệu
    cursor.execute("SELECT COUNT(DISTINCT StudentID) FROM TienTrinh")
    students_with_data = cursor.fetchone()[0]
    print(f"👤 Sinh viên có dữ liệu: {students_with_data}")
    
    if students_with_data > 0:
        avg_records = progress_count / students_with_data
        print(f"📊 Trung bình: {avg_records:.1f} records/sinh viên")
    
    # Thông tin đăng nhập
    print("\n" + "=" * 60)
    print("🔐 THÔNG TIN ĐĂNG NHẬP")
    print("=" * 60)
    print("💡 Mật khẩu mặc định: [Mã sinh viên]")
    print("\n📝 Ví dụ đăng nhập:")
    
    cursor.execute("SELECT StudentID, HoTen FROM SinhVien ORDER BY StudentID LIMIT 3")
    for student_id, ho_ten in cursor.fetchall():
        print(f"   - Tài khoản: {student_id}")
        print(f"     Mật khẩu: {student_id}")
        print(f"     Họ tên: {ho_ten}")
    
    cursor.close()

def main():
    """Hàm chính"""
    print("\n" + "=" * 60)
    print("🚀 SETUP DATABASE - HỆ THỐNG QUẢN LÝ HỌC TẬP")
    print("=" * 60)
    print("\n📋 Script này sẽ:")
    print("   1. Tạo database QuanLyHocTap")
    print("   2. Tạo các bảng (SinhVien, MonHoc, TienTrinh, ...)")
    print("   3. Import dữ liệu từ Excel")
    print("   4. Tạo tài khoản đăng nhập cho sinh viên")
    
    input("\n⏸️  Nhấn Enter để tiếp tục...")
    
    # Kết nối MySQL
    print("\n🔌 Bước 1: Kết nối MySQL server...")
    conn = connect_mysql_server()
    
    # Tạo database
    print("\n🗄️  Bước 2: Tạo database...")
    if not create_database(conn):
        conn.close()
        sys.exit(1)
    
    # Kết nối lại với database mới
    conn.close()
    conn = mysql.connector.connect(**DB_CONFIG)
    
    # Tạo tables
    print("\n📋 Bước 3: Tạo các bảng...")
    if not create_tables_from_sql(conn):
        conn.close()
        sys.exit(1)
    
    # Chạy migrations
    print("\n🔧 Bước 4: Chạy migrations...")
    run_migrations(conn)
    
    # Import dữ liệu
    print("\n📥 Bước 5: Import dữ liệu từ Excel...")
    if not import_excel_data(conn):
        conn.close()
        sys.exit(1)
    
    # Verify
    verify_data(conn)
    
    print("\n" + "=" * 60)
    print("✅ HOÀN THÀNH SETUP DATABASE!")
    print("=" * 60)
    print("\n🎯 Bước tiếp theo:")
    print("   1. Chạy: python app.py")
    print("   2. Mở browser: http://localhost:5000")
    print("   3. Đăng nhập bằng mã sinh viên")
    print("\n" + "=" * 60)
    
    conn.close()

if __name__ == "__main__":
    main()
