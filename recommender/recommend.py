import mysql.connector
import joblib
import os
import numpy as np
from sklearn.cluster import KMeans
import pandas as pd
from config import DB_CONFIG
from recommender.prerequisite_utils import get_prerequisites
from recommender.ontime_graduate_recommender import recommend_based_on_ontime_graduates


def get_similar_students(student_data, student_id, n_similar=5):
    """Tìm n sinh viên có lịch sử học tập tương tự nhất.

    Trả về danh sách StudentID (cùng kiểu như trong file) của những sinh viên tương tự.
    Nếu student_id không có trong dữ liệu, trả về danh sách rỗng.
    """
    # Chuẩn hoá cột StudentID thành string để tránh mismatch (ví dụ: số vs str)
    student_data = student_data.copy()
    if 'StudentID' not in student_data.columns or 'CourseCode' not in student_data.columns:
        return []
    student_data['StudentID'] = student_data['StudentID'].astype(str).str.strip()
    student_id = str(student_id).strip()

    # Pivot table để có ma trận sinh viên-môn học (dùng Score nếu có, else 1/0)
    value_col = 'Score' if 'Score' in student_data.columns else None
    if value_col:
        student_course_matrix = pd.pivot_table(
            student_data, values='Score', index='StudentID', columns='CourseCode', fill_value=0
        )
    else:
        # nếu không có điểm, chỉ đánh dấu đã học = 1
        student_data['_taken'] = 1
        student_course_matrix = pd.pivot_table(
            student_data, values='_taken', index='StudentID', columns='CourseCode', fill_value=0
        )

    if student_id not in student_course_matrix.index:
        return []

    current_student = student_course_matrix.loc[student_id].values
    similarities = {}
    for other_id in student_course_matrix.index:
        if other_id == student_id:
            continue
        other_student = student_course_matrix.loc[other_id].values
        dot_product = np.dot(current_student, other_student)
        norm_product = np.linalg.norm(current_student) * np.linalg.norm(other_student)
        if norm_product == 0:
            continue
        similarities[other_id] = dot_product / norm_product

    similar_students = sorted(similarities.items(), key=lambda x: x[1], reverse=True)[:n_similar]
    return [sid for sid, _ in similar_students]


def recommend_next_courses(student_id, model_path='models/kmeans_model.pkl', excel_path='data/student_data_100-2.xlsx', use_ontime_graduates=True):
    """Trả về danh sách môn học gợi ý cho `student_id`.

    Hàm này ưu tiên sử dụng dữ liệu từ các sinh viên đã tốt nghiệp đúng hạn.
    Nếu không có kết quả, sẽ fallback về phương pháp cũ.

    Args:
        student_id: Mã sinh viên
        model_path: Đường dẫn đến model (không dùng nữa nhưng giữ để tương thích)
        excel_path: Đường dẫn đến file Excel chứa dữ liệu
        use_ontime_graduates: Có sử dụng hệ thống gợi ý dựa trên sinh viên tốt nghiệp đúng hạn không

    Returns:
        List các dict chứa thông tin môn học được gợi ý
    """
    # Ưu tiên sử dụng hệ thống gợi ý dựa trên sinh viên tốt nghiệp đúng hạn
    if use_ontime_graduates and os.path.exists(excel_path):
        try:
            ontime_recs = recommend_based_on_ontime_graduates(student_id, excel_path)
            if ontime_recs:
                # Chỉ giữ lại các trường cần thiết để tương thích với code cũ
                return [
                    {
                        'CourseCode': r.get('CourseCode'),
                        'CourseName': r.get('CourseName'),
                        'Credits': r.get('Credits', 0),
                        'frequency': r.get('frequency', 0),
                        'avg_score': r.get('avg_score', 0),
                        'pass_rate': r.get('pass_rate', 0),
                        'recommended_year': r.get('recommended_year'),
                        'recommended_semester': r.get('recommended_semester'),
                        'recommendation_reason': r.get('recommendation_reason', '')
                    }
                    for r in ontime_recs
                ]
        except Exception as e:
            print(f"Cảnh báo: Không thể sử dụng hệ thống gợi ý tốt nghiệp đúng hạn: {e}")
            # Fallback về phương pháp cũ
    
    # Fallback về phương pháp cũ (giữ nguyên logic cũ)
    conn = None
    cursor = None
    try:
        # Kết nối DB
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)

        # Lấy danh sách môn học đã qua của sinh viên hiện tại
        cursor.execute("SELECT * FROM TienTrinh WHERE StudentID=%s", (student_id,))
        results = cursor.fetchall()
        passed_courses = [r['CourseCode'] for r in results if r.get('Status') in ("Đã học", 'Đã học')]

        # Đọc dữ liệu từ file Excel (nếu có). Nếu thiếu, trả về [] chứ không raise
        if os.path.exists(excel_path):
            student_data = pd.read_excel(excel_path)
        else:
            # file không có -> không phá vỡ dashboard, trả về []
            print(f"Cảnh báo: file Excel '{excel_path}' không tồn tại. Bỏ qua gợi ý theo sinh viên tương tự.")
            return []

        # Chuẩn hoá StudentID trong Excel
        student_data['StudentID'] = student_data['StudentID'].astype(str).str.strip()
        sid_str = str(student_id).strip()

        similar_students = get_similar_students(student_data, sid_str)
        if not similar_students:
            # không tìm thấy sinh viên tương tự (hoặc student_id không có trong Excel)
            return []

        # Tính học kỳ tiếp theo dựa trên tiến trình hiện tại
        next_semester = max([r['Semester'] for r in results]) + 1 if results else 1

        # Lấy các môn mà sinh viên tương tự đã qua ở học kỳ tiếp theo
        # đảm bảo các cột tồn tại trước khi lọc
        if 'Semester' in student_data.columns and 'CourseCode' in student_data.columns:
            mask = (
                student_data['StudentID'].isin(similar_students)
            )
            if 'Semester' in student_data.columns:
                mask &= (student_data['Semester'] == next_semester)
            if 'Score' in student_data.columns:
                mask &= (student_data['Score'] >= 5.0)

            similar_courses = student_data[mask]['CourseCode'].unique()
        else:
            similar_courses = []

        # Lấy thông tin chi tiết của các môn học được đề xuất từ bảng MonHoc
        potential_courses = []
        if len(similar_courses) > 0:
            placeholders = ','.join(['%s'] * len(similar_courses))
            cursor.execute(f"""
                SELECT DISTINCT CourseCode, CourseName, Credits 
                FROM MonHoc 
                WHERE CourseCode IN ({placeholders})
            """, tuple(similar_courses))
            potential_courses = cursor.fetchall()

        # Lọc theo điều kiện tiên quyết và loại bỏ môn đã học
        recs = []
        for course in potential_courses:
            code = course.get('CourseCode')
            if not code:
                continue
            if code in passed_courses:
                continue
            prereqs = get_prerequisites(code)
            if all(p in passed_courses for p in prereqs):
                recs.append(course)

        return recs
    except Exception as e:
        # Ghi log ngắn; không làm vỡ giao diện người dùng
        print(f"Lỗi khi tạo gợi ý: {e}")
        return []
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

