"""
Script để update database MonHoc từ file MonHoc.sql
"""
import mysql.connector
from config import DB_CONFIG
import re

def update_monhoc_from_sql():
    """Update bảng MonHoc từ file MonHoc.sql"""
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    try:
        # Đọc file SQL
        with open('MonHoc.sql', 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        # Tìm phần INSERT
        insert_match = re.search(r'INSERT INTO `MonHoc`.*?VALUES\s*(.*?);', sql_content, re.DOTALL)
        if not insert_match:
            print("❌ Không tìm thấy INSERT statement")
            return
        
        # Không xóa dữ liệu cũ vì có foreign key constraint
        # Sẽ dùng INSERT ... ON DUPLICATE KEY UPDATE để update
        print("🔄 Cập nhật dữ liệu MonHoc...")
        
        # Parse và insert dữ liệu mới
        values_str = insert_match.group(1)
        
        # Parse từng dòng INSERT
        pattern = r'\((\d+),\s*\'([^\']+)\',\s*\'([^\']+)\',\s*(\d+),\s*\'?([^\']*)\'?,\s*([^)]+)\)'
        matches = re.findall(pattern, values_str)
        
        print(f"📚 Tìm thấy {len(matches)} môn học")
        
        for match in matches:
            id_val, course_code, course_name, credits, course_type, note = match
            
            # Xử lý note (có thể là NULL hoặc string)
            note_val = note.strip()
            if note_val.upper() == 'NULL':
                note_val = None
            else:
                note_val = note_val.strip("'\"")
            
            # Xử lý Type
            if not course_type or course_type.upper() == 'NULL':
                course_type = None
            
            try:
                cursor.execute("""
                    INSERT INTO MonHoc (CourseCode, CourseName, Credits, Type, Note)
                    VALUES (%s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                        CourseName = VALUES(CourseName),
                        Credits = VALUES(Credits),
                        Type = VALUES(Type),
                        Note = VALUES(Note)
                """, (course_code, course_name, int(credits), course_type, note_val))
            except Exception as e:
                print(f"⚠️  Lỗi insert {course_code}: {e}")
        
        conn.commit()
        print(f"✅ Đã update {len(matches)} môn học vào database")
        
    except Exception as e:
        print(f"❌ Lỗi: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    update_monhoc_from_sql()

