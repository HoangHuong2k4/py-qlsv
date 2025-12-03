"""
Script import dữ liệu từ Excel vào MySQL Database
Chuyển đổi dữ liệu từ student_data_100-2.xlsx vào bảng TienTrinh và SinhVien
"""
import pandas as pd
import mysql.connector
from datetime import datetime
import sys
import os

# Thêm thư mục gốc vào path để import config
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DB_CONFIG

def connect_db():
    """Kết nối đến MySQL database"""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        print("✅ Kết nối database thành công!")
        return conn
    except mysql.connector.Error as err:
        print(f"❌ Lỗi kết nối database: {err}")
        print("⚠️  Vui lòng kiểm tra:")
        print("   - MySQL đã được khởi động trong XAMPP chưa")
        print("   - Database 'QuanLyHocTap' đã được tạo chưa")
        print("   - Thông tin kết nối trong config.py đúng chưa")
        sys.exit(1)

def create_database_if_not_exists(conn):
    """Tạo database nếu chưa tồn tại"""
    cursor = conn.cursor()
    try:
        cursor.execute("CREATE DATABASE IF NOT EXISTS QuanLyHocTap CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci")
        cursor.execute("USE QuanLyHocTap")
        print("✅ Database QuanLyHocTap đã sẵn sàng")
    except mysql.connector.Error as err:
        print(f"❌ Lỗi tạo database: {err}")
    finally:
        cursor.close()

def run_migration(conn, migration_file):
    """Chạy file migration SQL"""
    cursor = conn.cursor()
    try:
        with open(migration_file, 'r', encoding='utf-8') as f:
            sql_commands = f.read()
            # Tách và thực thi từng lệnh SQL
            for command in sql_commands.split(';'):
                command = command.strip()
                if command and not command.startswith('--'):
                    try:
                        cursor.execute(command)
                    except mysql.connector.Error as err:
                        # Bỏ qua lỗi cột đã tồn tại
                        if 'Duplicate column name' not in str(err):
                            print(f"⚠️  Warning: {err}")
        conn.commit()
        print(f"✅ Đã chạy migration: {migration_file}")
    except Exception as e:
        print(f"❌ Lỗi chạy migration: {e}")
    finally:
        cursor.close()

def load_excel_data(file_path):
    """Đọc dữ liệu từ file Excel"""
    try:
        df = pd.read_excel(file_path)
        print(f"✅ Đọc file Excel thành công: {len(df)} dòng dữ liệu")
        print(f"📊 Các cột: {list(df.columns)}")
        return df
    except FileNotFoundError:
        print(f"❌ Không tìm thấy file: {file_path}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Lỗi đọc file Excel: {e}")
        sys.exit(1)

def import_students(conn, df):
    """Import danh sách sinh viên vào bảng SinhVien"""
    cursor = conn.cursor()
    
    # Lấy danh sách sinh viên duy nhất
    students = df[['StudentID']].drop_duplicates()
    
    inserted = 0
    skipped = 0
    
    for _, row in students.iterrows():
        student_id = row['StudentID']
        
        # Kiểm tra sinh viên đã tồn tại chưa
        cursor.execute("SELECT StudentID FROM SinhVien WHERE StudentID = %s", (student_id,))
        if cursor.fetchone():
            skipped += 1
            continue
        
        # Tạo mật khẩu mặc định (password = mã sinh viên)
        from werkzeug.security import generate_password_hash
        default_password = generate_password_hash(student_id, method='pbkdf2:sha256')
        
        # Thêm sinh viên mới
        try:
            cursor.execute("""
                INSERT INTO SinhVien (StudentID, HoTen, Password, GioiTinh, NgaySinh, Email)
                VALUES (%s, %s, %s, 'Nam', '2003-01-01', %s)
            """, (
                student_id,
                f"Sinh viên {student_id}",
                default_password,
                f"{student_id}@student.ctu.edu.vn"
            ))
            inserted += 1
        except mysql.connector.Error as err:
            if 'Duplicate entry' not in str(err):
                print(f"⚠️  Lỗi thêm sinh viên {student_id}: {err}")
    
    conn.commit()
    cursor.close()
    
    print(f"✅ Import sinh viên: {inserted} mới, {skipped} đã tồn tại")

def import_progress(conn, df):
    """Import tiến trình học tập vào bảng TienTrinh"""
    cursor = conn.cursor()
    
    # Xóa dữ liệu cũ (tùy chọn - bỏ comment nếu muốn làm mới hoàn toàn)
    # cursor.execute("TRUNCATE TABLE TienTrinh")
    # print("🗑️  Đã xóa dữ liệu cũ trong bảng TienTrinh")
    
    inserted = 0
    updated = 0
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
            elif score is not None:
                status = 'Đã học'  # Điểm dưới 4 vẫn đánh dấu đã học (có thể học lại)
            else:
                status = 'Chưa học'
            
            # Xác định xếp loại
            xep_loai = None
            if score is not None:
                if score >= 8.5:
                    xep_loai = 'A'
                elif score >= 7.0:
                    xep_loai = 'B+'
                elif score >= 5.5:
                    xep_loai = 'B'
                elif score >= 4.0:
                    xep_loai = 'C+'
                else:
                    xep_loai = 'F'
            
            # Kiểm tra record đã tồn tại
            cursor.execute("""
                SELECT ID FROM TienTrinh 
                WHERE StudentID = %s AND Year = %s AND Semester = %s AND CourseCode = %s
            """, (student_id, year, semester, course_code))
            
            existing = cursor.fetchone()
            
            if existing:
                # Update nếu đã tồn tại
                cursor.execute("""
                    UPDATE TienTrinh 
                    SET CourseName = %s, Credits = %s, Score = %s, GPA = %s,
                        Status = %s, XepLoai = %s, OnTime = %s, Graduated = %s
                    WHERE ID = %s
                """, (course_name, credits, score, gpa, status, xep_loai, ontime, graduated, existing[0]))
                updated += 1
            else:
                # Insert nếu chưa tồn tại
                cursor.execute("""
                    INSERT INTO TienTrinh 
                    (StudentID, HoTen, Year, Semester, CourseCode, CourseName, Credits, 
                     Score, GPA, Status, XepLoai, OnTime, Graduated, Type, CreatedAt)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'Bắt buộc', NOW())
                """, (
                    student_id, f"Sinh viên {student_id}", year, semester, 
                    course_code, course_name, credits, score, gpa, 
                    status, xep_loai, ontime, graduated
                ))
                inserted += 1
            
            # Commit mỗi 100 dòng
            if (inserted + updated) % 100 == 0:
                conn.commit()
                print(f"⏳ Đã xử lý {inserted + updated} dòng...")
                
        except Exception as e:
            errors += 1
            print(f"⚠️  Lỗi dòng {idx + 1}: {e}")
            continue
    
    conn.commit()
    cursor.close()
    
    print(f"✅ Import tiến trình: {inserted} mới, {updated} cập nhật, {errors} lỗi")

def main():
    """Hàm chính"""
    print("=" * 60)
    print("🚀 BẮT ĐẦU IMPORT DỮ LIỆU TỪ EXCEL VÀO DATABASE")
    print("=" * 60)
    
    # Đường dẫn file Excel
    excel_file = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'data',
        'student_data_100-2.xlsx'
    )
    
    # Kết nối database
    conn = connect_db()
    
    # Tạo database nếu chưa có
    create_database_if_not_exists(conn)
    
    # Chạy migrations
    migrations_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'migrations'
    )
    
    # Chạy migration cập nhật schema
    migration_file = os.path.join(migrations_dir, '002_update_tientrinh_schema.sql')
    if os.path.exists(migration_file):
        run_migration(conn, migration_file)
    
    # Đọc dữ liệu Excel
    df = load_excel_data(excel_file)
    
    # Import dữ liệu
    print("\n📝 Bước 1: Import danh sách sinh viên...")
    import_students(conn, df)
    
    print("\n📝 Bước 2: Import tiến trình học tập...")
    import_progress(conn, df)
    
    # Thống kê
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(DISTINCT StudentID) FROM TienTrinh")
    student_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM TienTrinh")
    record_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(DISTINCT CourseCode) FROM TienTrinh")
    course_count = cursor.fetchone()[0]
    
    cursor.close()
    
    print("\n" + "=" * 60)
    print("✅ HOÀN THÀNH IMPORT DỮ LIỆU")
    print("=" * 60)
    print(f"📊 Tổng số sinh viên: {student_count}")
    print(f"📊 Tổng số môn học: {course_count}")
    print(f"📊 Tổng số records: {record_count}")
    print(f"📊 Trung bình: {record_count / student_count:.1f} records/sinh viên")
    print("\n💡 Mật khẩu mặc định của sinh viên: [Mã sinh viên]")
    print("   Ví dụ: B2100001 → password: B2100001")
    print("\n🎯 Bạn có thể đăng nhập vào hệ thống ngay bây giờ!")
    print("=" * 60)
    
    conn.close()

if __name__ == "__main__":
    main()

