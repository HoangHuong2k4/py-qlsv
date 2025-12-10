#!/usr/bin/env python3
"""
Script để export database QuanLyHocTap ra file SQL
"""
import subprocess
import sys
import os
from config import DB_CONFIG

def export_database():
    """Export database ra file SQL"""
    output_file = "QuanLyHocTap_Full.sql"
    
    # Xóa file cũ nếu có
    if os.path.exists(output_file):
        os.remove(output_file)
        print(f"🗑️  Đã xóa file cũ: {output_file}")
    
    # Lấy password từ config hoặc môi trường
    password = DB_CONFIG.get('password', '')
    
    # Tạo lệnh mysqldump
    cmd = [
        'mysqldump',
        '-u', DB_CONFIG['user'],
        f"--password={password}" if password else '',
        '--single-transaction',
        '--routines',
        '--triggers',
        '--add-drop-database',
        '--create-options',
        DB_CONFIG['database']
    ]
    
    # Loại bỏ phần tử rỗng
    cmd = [c for c in cmd if c]
    
    print(f"📤 Đang export database {DB_CONFIG['database']}...")
    
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            result = subprocess.run(
                cmd,
                stdout=f,
                stderr=subprocess.PIPE,
                text=True
            )
        
        if result.returncode == 0:
            # Đếm số dòng
            with open(output_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            file_size = os.path.getsize(output_file)
            print(f"✅ Export thành công!")
            print(f"   📄 File: {output_file}")
            print(f"   📊 Số dòng: {len(lines):,}")
            print(f"   💾 Kích thước: {file_size / 1024:.2f} KB")
            return True
        else:
            print(f"❌ Lỗi khi export:")
            print(result.stderr)
            return False
            
    except FileNotFoundError:
        print("❌ Không tìm thấy mysqldump. Vui lòng cài đặt MySQL client.")
        return False
    except Exception as e:
        print(f"❌ Lỗi: {e}")
        return False

if __name__ == "__main__":
    success = export_database()
    sys.exit(0 if success else 1)

