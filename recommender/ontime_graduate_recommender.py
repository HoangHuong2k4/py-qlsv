"""
Module gợi ý môn học dựa trên lịch sử học tập của các sinh viên đã tốt nghiệp đúng hạn.
"""
import pandas as pd
import numpy as np
from typing import List, Dict, Set, Tuple
import mysql.connector
from config import DB_CONFIG
from recommender.prerequisite_utils import get_prerequisites


def load_ontime_graduates_data(excel_path: str) -> pd.DataFrame:
    """
    Tải dữ liệu và lọc chỉ lấy các sinh viên đã tốt nghiệp đúng hạn.
    
    Args:
        excel_path: Đường dẫn đến file Excel chứa dữ liệu sinh viên
        
    Returns:
        DataFrame chứa dữ liệu của các sinh viên tốt nghiệp đúng hạn
    """
    df = pd.read_excel(excel_path)
    df = df.dropna(subset=['StudentID'])
    
    # Lọc chỉ lấy sinh viên tốt nghiệp đúng hạn
    ontime_graduates = df[(df['OnTime'] == True) & (df['Grad'] == True)].copy()
    
    # Chuẩn hoá StudentID
    ontime_graduates['StudentID'] = ontime_graduates['StudentID'].astype(str).str.strip()
    
    return ontime_graduates


def get_course_sequence_by_semester(df: pd.DataFrame, student_id: str) -> List[Tuple[int, int, str, float]]:
    """
    Lấy chuỗi môn học của một sinh viên theo thứ tự học kỳ.
    
    Args:
        df: DataFrame chứa dữ liệu học tập
        student_id: Mã sinh viên
        
    Returns:
        List các tuple (Year, Semester, CourseCode, Score) được sắp xếp theo thứ tự thời gian
    """
    student_data = df[df['StudentID'] == str(student_id).strip()].copy()
    if student_data.empty:
        return []
    
    # Sắp xếp theo Year và Semester
    student_data = student_data.sort_values(['Year', 'Semester'])
    
    sequences = []
    for _, row in student_data.iterrows():
        year = int(row['Year']) if pd.notna(row['Year']) else 0
        semester = int(row['Semester']) if pd.notna(row['Semester']) else 0
        course_code = str(row['CourseCode']) if pd.notna(row['CourseCode']) else ''
        score = float(row['Score']) if pd.notna(row['Score']) else 0.0
        
        sequences.append((year, semester, course_code, score))
    
    return sequences


def find_similar_ontime_students(df: pd.DataFrame, current_student_courses: Set[str], 
                                  n_similar: int = 10) -> List[str]:
    """
    Tìm các sinh viên tốt nghiệp đúng hạn có lịch sử học tập tương tự với sinh viên hiện tại.
    
    Args:
        df: DataFrame chứa dữ liệu của các sinh viên tốt nghiệp đúng hạn
        current_student_courses: Set các mã môn học mà sinh viên hiện tại đã học
        n_similar: Số lượng sinh viên tương tự cần tìm
        
    Returns:
        List các StudentID của sinh viên tương tự
    """
    if not current_student_courses:
        return []
    
    # Tính điểm tương đồng dựa trên số môn học chung
    student_ids = df['StudentID'].unique()
    similarities = {}
    
    for student_id in student_ids:
        student_courses = set(df[df['StudentID'] == student_id]['CourseCode'].astype(str).unique())
        
        # Tính Jaccard similarity
        intersection = len(current_student_courses & student_courses)
        union = len(current_student_courses | student_courses)
        
        if union > 0:
            similarity = intersection / union
            similarities[student_id] = similarity
    
    # Sắp xếp và lấy top n_similar sinh viên
    similar_students = sorted(similarities.items(), key=lambda x: x[1], reverse=True)[:n_similar]
    return [sid for sid, score in similar_students if score > 0]


def get_recommended_courses_for_specific_semester(df: pd.DataFrame, student_ids: List[str], 
                                                  target_year: int, target_semester: int) -> Dict[str, Dict]:
    """
    Lấy các môn học được gợi ý dựa trên các sinh viên tương tự ở một học kỳ cụ thể.
    
    Args:
        df: DataFrame chứa dữ liệu của các sinh viên tốt nghiệp đúng hạn
        student_ids: List các StudentID của sinh viên tương tự
        target_year: Năm học mục tiêu
        target_semester: Học kỳ mục tiêu
        
    Returns:
        Dict với key là CourseCode, value là Dict chứa thông tin về môn học (frequency, avg_score, etc.)
    """
    if not student_ids:
        return {}
    
    # Lọc dữ liệu của các sinh viên tương tự ở học kỳ mục tiêu
    target_sem_data = df[
        (df['StudentID'].isin(student_ids)) &
        (df['Year'] == target_year) &
        (df['Semester'] == target_semester)
    ].copy()
    
    if target_sem_data.empty:
        return {}
    
    # Tính tần suất và điểm trung bình cho mỗi môn học
    course_stats = {}
    
    for course_code, group in target_sem_data.groupby('CourseCode'):
        course_code_str = str(course_code)
        frequency = len(group)
        
        # Tính điểm trung bình (chỉ lấy điểm >= 5.0)
        scores = group[group['Score'] >= 5.0]['Score'].values
        avg_score = float(np.mean(scores)) if len(scores) > 0 else 0.0
        
        # Tính tỷ lệ đậu (score >= 5.0)
        pass_rate = len(scores) / frequency if frequency > 0 else 0.0
        
        course_stats[course_code_str] = {
            'frequency': frequency,
            'avg_score': avg_score,
            'pass_rate': pass_rate,
            'total_students': len(student_ids),
            'recommended_year': target_year,
            'recommended_semester': target_semester
        }
    
    return course_stats


def get_target_semesters_for_recommendation(current_year: int, current_semester: int) -> List[Tuple[int, int]]:
    """
    Xác định các học kỳ cần gợi ý dựa trên năm học và học kỳ hiện tại.
    Ưu tiên học kỳ 3 năm 4 và học kỳ 1 năm 5.
    
    Args:
        current_year: Năm học hiện tại
        current_semester: Học kỳ hiện tại
        
    Returns:
        List các tuple (year, semester) cần gợi ý
    """
    target_semesters = []
    
    # Tính học kỳ tiếp theo (hỗ trợ học kỳ 3 trong năm)
    if current_semester < 3:
        next_semester = current_semester + 1
        next_year = current_year
    else:
        # Nếu đang ở học kỳ 3, học kỳ tiếp theo là học kỳ 1 năm sau
        next_semester = 1
        next_year = current_year + 1
    
    # Thêm học kỳ tiếp theo
    target_semesters.append((next_year, next_semester))
    
    # Nếu đang ở năm 4, luôn cần gợi ý cho học kỳ 3 năm 4 và học kỳ 1 năm 5
    if current_year == 4:
        # Luôn thêm học kỳ 1 năm 5 khi ở năm 4
        target_semesters.append((5, 1))
        # Thêm học kỳ 3 năm 4 nếu chưa học đến đó
        if current_semester < 3:
            target_semesters.append((4, 3))
    elif current_year == 3:
        # Nếu đang ở năm 3, chuẩn bị cho năm 4 và năm 5
        if current_semester >= 2:
            target_semesters.append((4, 3))
            target_semesters.append((5, 1))
    
    # Loại bỏ trùng lặp và sắp xếp theo năm, học kỳ
    target_semesters = list(set(target_semesters))
    target_semesters.sort()
    
    return target_semesters


def get_recommended_courses_by_semester(df: pd.DataFrame, student_ids: List[str], 
                                        current_year: int, current_semester: int) -> Dict[str, Dict]:
    """
    Lấy các môn học được gợi ý dựa trên các sinh viên tương tự cho nhiều học kỳ.
    Ưu tiên học kỳ 3 năm 4 và học kỳ 1 năm 5.
    
    Args:
        df: DataFrame chứa dữ liệu của các sinh viên tốt nghiệp đúng hạn
        student_ids: List các StudentID của sinh viên tương tự
        current_year: Năm học hiện tại của sinh viên
        current_semester: Học kỳ hiện tại của sinh viên
        
    Returns:
        Dict với key là (CourseCode, Year, Semester), value là Dict chứa thông tin về môn học
    """
    if not student_ids:
        return {}
    
    # Lấy danh sách các học kỳ cần gợi ý
    target_semesters = get_target_semesters_for_recommendation(current_year, current_semester)
    
    all_course_stats = {}
    
    # Lấy gợi ý cho từng học kỳ
    for target_year, target_semester in target_semesters:
        semester_courses = get_recommended_courses_for_specific_semester(
            df, student_ids, target_year, target_semester
        )
        
        # Thêm vào dict tổng hợp với key là (CourseCode, Year, Semester)
        for course_code, stats in semester_courses.items():
            key = (course_code, target_year, target_semester)
            all_course_stats[key] = stats
    
    return all_course_stats


def calculate_credit_distribution(passed_courses_data: List[Dict], total_required_credits: int = 156, 
                                   total_semesters: int = 9) -> Dict:
    """
    Tính toán phân bố tín chỉ và kiểm tra tiến độ học tập.
    
    Args:
        passed_courses_data: List các dict chứa thông tin môn đã học (CourseCode, Credits, Year, Semester)
        total_required_credits: Tổng số tín chỉ yêu cầu (mặc định 156)
        total_semesters: Tổng số học kỳ (4.5 năm = 9 học kỳ)
        
    Returns:
        Dict chứa thông tin về phân bố tín chỉ và khuyến nghị
    """
    total_credits_earned = sum(c.get('Credits', 0) for c in passed_courses_data)
    credits_per_semester_target = total_required_credits / total_semesters
    
    # Tính số tín chỉ theo năm học
    credits_by_year = {}
    for course in passed_courses_data:
        year = course.get('Year', 1)
        if year not in credits_by_year:
            credits_by_year[year] = 0
        credits_by_year[year] += course.get('Credits', 0)
    
    # Tính số học kỳ đã học
    semesters_completed = len(set((c.get('Year', 1), c.get('Semester', 1)) for c in passed_courses_data))
    if semesters_completed == 0:
        semesters_completed = 1
    
    # Tính tiến độ
    progress_percentage = (total_credits_earned / total_required_credits) * 100 if total_required_credits > 0 else 0
    expected_credits_by_now = credits_per_semester_target * semesters_completed
    credits_shortage = max(0, expected_credits_by_now - total_credits_earned)
    
    return {
        'total_credits_earned': total_credits_earned,
        'total_required_credits': total_required_credits,
        'credits_remaining': total_required_credits - total_credits_earned,
        'credits_per_semester_target': round(credits_per_semester_target, 2),
        'semesters_completed': semesters_completed,
        'semesters_remaining': total_semesters - semesters_completed,
        'progress_percentage': round(progress_percentage, 2),
        'credits_by_year': credits_by_year,
        'credits_shortage': round(credits_shortage, 2),
        'on_track': credits_shortage <= credits_per_semester_target * 0.5  # Cho phép sai lệch 0.5 học kỳ
    }


def recommend_based_on_ontime_graduates(student_id: str, excel_path: str = 'data/student_data_100-2.xlsx') -> List[Dict]:
    """
    Gợi ý môn học cho sinh viên dựa trên lịch sử học tập của các sinh viên đã tốt nghiệp đúng hạn.
    
    Args:
        student_id: Mã sinh viên cần gợi ý
        excel_path: Đường dẫn đến file Excel chứa dữ liệu
        
    Returns:
        List các Dict chứa thông tin môn học được gợi ý
    """
    conn = None
    cursor = None
    
    try:
        # Kết nối DB
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        
        # Lấy thông tin học tập hiện tại của sinh viên
        cursor.execute("""
            SELECT CourseCode, Year, Semester, Status, Score, Credits
            FROM TienTrinh 
            WHERE StudentID=%s 
            ORDER BY Year, Semester
        """, (student_id,))
        current_courses = cursor.fetchall()
        
        if not current_courses:
            return []
        
        # Lấy danh sách môn đã học (đã pass) và tính tổng tín chỉ
        passed_courses = set()
        passed_courses_data = []
        current_year = 1
        current_semester = 1
        
        # Tìm năm và học kỳ mới nhất mà sinh viên đã hoàn thành
        latest_year_sem = (1, 1)
        for course in current_courses:
            if course.get('Status') in ('Đã học', 'Đã qua'):
                passed_courses.add(str(course['CourseCode']))
                passed_courses_data.append({
                    'CourseCode': course.get('CourseCode'),
                    'Credits': course.get('Credits', 0) or 0,
                    'Year': course.get('Year', 1),
                    'Semester': course.get('Semester', 1)
                })
                # Cập nhật năm và học kỳ mới nhất
                if course.get('Year') and course.get('Semester'):
                    year = int(course['Year'])
                    semester = int(course['Semester'])
                    if (year, semester) > latest_year_sem:
                        latest_year_sem = (year, semester)
                        current_year = year
                        current_semester = semester
        
        # Tính toán phân bố tín chỉ
        credit_info = calculate_credit_distribution(passed_courses_data, total_required_credits=156, total_semesters=9)
        
        # Tải dữ liệu sinh viên tốt nghiệp đúng hạn
        try:
            ontime_df = load_ontime_graduates_data(excel_path)
        except Exception as e:
            print(f"Lỗi khi đọc file Excel: {e}")
            return []
        
        # Tính học kỳ tiếp theo (hỗ trợ học kỳ 3 trong năm)
        if current_semester < 3:
            next_semester = current_semester + 1
            next_year = current_year
        else:
            # Nếu đang ở học kỳ 3, học kỳ tiếp theo là học kỳ 1 năm sau
            next_semester = 1
            next_year = current_year + 1
        
        # Debug: In thông tin để kiểm tra
        print(f"DEBUG: Sinh viên {student_id} - Năm hiện tại: {current_year}, Học kỳ hiện tại: {current_semester}")
        print(f"DEBUG: Số môn đã học: {len(passed_courses)}")
        
        # Tìm sinh viên tương tự
        similar_students = find_similar_ontime_students(ontime_df, passed_courses, n_similar=10)
        
        if not similar_students:
            print(f"DEBUG: Không tìm thấy sinh viên tương tự")
            return []
        
        print(f"DEBUG: Tìm thấy {len(similar_students)} sinh viên tương tự")
        
        # Xác định các học kỳ cần gợi ý
        target_semesters = get_target_semesters_for_recommendation(current_year, current_semester)
        print(f"DEBUG: Các học kỳ cần gợi ý: {target_semesters}")
        
        # Lấy gợi ý môn học từ các sinh viên tương tự
        course_recommendations = get_recommended_courses_by_semester(
            ontime_df, similar_students, current_year, current_semester
        )
        
        print(f"DEBUG: Số môn được gợi ý (tổng): {len(course_recommendations)}")
        # Đếm theo học kỳ
        year5_sem1_count = sum(1 for k in course_recommendations.keys() 
                               if isinstance(k, tuple) and k[1] == 5 and k[2] == 1)
        print(f"DEBUG: Số môn được gợi ý cho HK1 năm 5: {year5_sem1_count}")
        
        # Sắp xếp theo năm, học kỳ, tần suất và điểm trung bình
        sorted_courses = sorted(
            course_recommendations.items(),
            key=lambda x: (
                x[0][1] if isinstance(x[0], tuple) else 999,  # Year
                x[0][2] if isinstance(x[0], tuple) else 999,  # Semester
                x[1]['frequency'],
                x[1]['avg_score']
            ),
            reverse=False  # Sắp xếp theo năm/học kỳ tăng dần
        )
        
        # Lấy thông tin chi tiết từ database và kiểm tra điều kiện tiên quyết
        # Với học kỳ 1 năm 5, cho phép hiển thị cả môn đã được gợi ý ở học kỳ khác nếu frequency đủ cao
        course_by_code_and_semester = {}  # Key: (course_code, year, semester)
        
        for key, stats in sorted_courses:
            # Xử lý key có thể là tuple (CourseCode, Year, Semester) hoặc CourseCode
            if isinstance(key, tuple):
                course_code = key[0]
                recommended_year = key[1]
                recommended_semester = key[2]
            else:
                course_code = key
                recommended_year = stats.get('recommended_year', next_year)
                recommended_semester = stats.get('recommended_semester', next_semester)
            
            if course_code in passed_courses:
                continue
            
            # Với học kỳ 1 năm 5, luôn thêm vào danh sách (không bị thay thế)
            if recommended_year == 5 and recommended_semester == 1:
                course_key = (course_code, recommended_year, recommended_semester)
                # Kiểm tra xem đã có môn này ở học kỳ khác chưa
                existing_key = None
                for k in list(course_by_code_and_semester.keys()):
                    if k[0] == course_code:
                        # Nếu đã có ở học kỳ khác, giữ cả hai (cho phép trùng)
                        # Nhưng nếu đã có ở HK1 năm 5 rồi thì bỏ qua
                        if k[1] == 5 and k[2] == 1:
                            existing_key = k
                            break
                
                if existing_key is None:
                    # Chưa có ở HK1 năm 5, thêm mới
                    course_by_code_and_semester[course_key] = {
                        'key': key,
                        'stats': stats,
                        'year': recommended_year,
                        'semester': recommended_semester
                    }
                    print(f"DEBUG: Thêm môn HK1 năm 5 vào course_by_code_and_semester: {course_code}")
            else:
                # Với các học kỳ khác, chỉ thêm nếu chưa có ở HK1 năm 5
                # Kiểm tra xem đã có môn này ở HK1 năm 5 chưa
                has_year5_sem1 = False
                for k in course_by_code_and_semester.keys():
                    if k[0] == course_code and k[1] == 5 and k[2] == 1:
                        has_year5_sem1 = True
                        break
                
                # Nếu đã có ở HK1 năm 5, không thêm học kỳ khác (trừ khi frequency cao hơn đáng kể)
                if has_year5_sem1:
                    # Không thêm học kỳ khác nếu đã có ở HK1 năm 5
                    continue
                
                # Kiểm tra xem đã có môn này ở học kỳ khác chưa
                existing_key = None
                for k in course_by_code_and_semester.keys():
                    if k[0] == course_code:
                        existing_key = k
                        break
                
                if existing_key is None:
                    # Chưa có, thêm mới
                    course_key = (course_code, recommended_year, recommended_semester)
                    course_by_code_and_semester[course_key] = {
                        'key': key,
                        'stats': stats,
                        'year': recommended_year,
                        'semester': recommended_semester
                    }
                else:
                    # Đã có, chỉ thay thế nếu học kỳ mới sớm hơn hoặc frequency cao hơn 20%
                    existing = course_by_code_and_semester[existing_key]
                    if (recommended_year, recommended_semester) < (existing['year'], existing['semester']) or \
                       stats['frequency'] > existing['stats']['frequency'] * 1.2:
                        del course_by_code_and_semester[existing_key]
                        course_key = (course_code, recommended_year, recommended_semester)
                        course_by_code_and_semester[course_key] = {
                            'key': key,
                            'stats': stats,
                            'year': recommended_year,
                            'semester': recommended_semester
                        }
        
        recommendations = []
        
        # Debug: Đếm số môn HK1 năm 5 trong course_by_code_and_semester
        year5_sem1_in_dict = sum(1 for (code, y, s) in course_by_code_and_semester.keys() if y == 5 and s == 1)
        print(f"DEBUG: Số môn HK1 năm 5 trong course_by_code_and_semester: {year5_sem1_in_dict}")
        
        for (course_code, year, semester), data in course_by_code_and_semester.items():
            stats = data['stats']
            recommended_year = data['year']
            recommended_semester = data['semester']
            
            if recommended_year == 5 and recommended_semester == 1:
                print(f"DEBUG: Xử lý môn HK1 năm 5: {course_code}")
            
            # Lấy thông tin chi tiết môn học từ database
            cursor.execute("""
                SELECT CourseCode, CourseName, Credits
                FROM MonHoc
                WHERE CourseCode=%s
            """, (course_code,))
            course_info = cursor.fetchone()
            
            # Nếu không tìm thấy trong database, thử lấy từ Excel (đặc biệt cho HK1 năm 5)
            if not course_info:
                if recommended_year == 5 and recommended_semester == 1:
                    print(f"DEBUG: {course_code} (HK1 năm 5) không tìm thấy trong MonHoc, thử lấy từ Excel")
                    # Lấy thông tin từ Excel
                    course_from_excel = ontime_df[
                        (ontime_df['CourseCode'] == course_code) & 
                        (ontime_df['Year'] == 5) & 
                        (ontime_df['Semester'] == 1)
                    ].iloc[0] if len(ontime_df[
                        (ontime_df['CourseCode'] == course_code) & 
                        (ontime_df['Year'] == 5) & 
                        (ontime_df['Semester'] == 1)
                    ]) > 0 else None
                    
                    if course_from_excel is not None:
                        course_info = {
                            'CourseCode': course_from_excel['CourseCode'],
                            'CourseName': course_from_excel.get('CourseName', str(course_code)),
                            'Credits': int(course_from_excel.get('Credits', 0)) if pd.notna(course_from_excel.get('Credits')) else 0
                        }
                        print(f"DEBUG: Lấy {course_code} từ Excel: {course_info.get('CourseName')}, {course_info.get('Credits')} tín chỉ")
                    else:
                        print(f"DEBUG: Bỏ qua {course_code} (HK1 năm 5) vì không tìm thấy trong cả MonHoc và Excel")
                        continue
                else:
                    continue
            
            # Kiểm tra điều kiện tiên quyết (nới lỏng hơn cho học kỳ 1 năm 5)
            prereqs = get_prerequisites(course_code)
            # Cho học kỳ 1 năm 5, bỏ qua điều kiện tiên quyết hoàn toàn (vì là năm cuối)
            if recommended_year == 5 and recommended_semester == 1:
                # Bỏ qua kiểm tra điều kiện tiên quyết cho HK1 năm 5
                if prereqs:
                    print(f"DEBUG: {course_code} (HK1 năm 5) có điều kiện tiên quyết {prereqs} nhưng sẽ bỏ qua")
            else:
                # Các học kỳ khác yêu cầu tất cả điều kiện tiên quyết
                if not all(p in passed_courses for p in prereqs):
                    print(f"DEBUG: Bỏ qua {course_code} (HK{recommended_semester} năm {recommended_year}) vì thiếu điều kiện tiên quyết: {[p for p in prereqs if p not in passed_courses]}")
                    continue
            
            # Nới lỏng điều kiện: pass_rate >= 0.6 (60%) cho học kỳ 1 năm 5, >= 0.7 cho các học kỳ khác
            min_pass_rate = 0.6 if recommended_year == 5 and recommended_semester == 1 else 0.7
            if stats['pass_rate'] < min_pass_rate:
                if recommended_year == 5 and recommended_semester == 1:
                    print(f"DEBUG: Bỏ qua {course_code} (HK1 năm 5) vì pass_rate {stats['pass_rate']:.2%} < {min_pass_rate:.2%} (frequency={stats['frequency']}, total={stats['total_students']})")
                else:
                    print(f"DEBUG: Bỏ qua {course_code} (HK{recommended_semester} năm {recommended_year}) vì pass_rate {stats['pass_rate']:.2%} < {min_pass_rate:.2%}")
                continue
            
            if recommended_year == 5 and recommended_semester == 1:
                print(f"DEBUG: {course_code} (HK1 năm 5) đã vượt qua tất cả điều kiện, thêm vào recommendations")
            
            course_credits = course_info.get('Credits', 0) or 0
            
            rec = {
                'CourseCode': course_info['CourseCode'],
                'CourseName': course_info['CourseName'],
                'Credits': course_credits,
                'frequency': stats['frequency'],
                'avg_score': round(stats['avg_score'], 2),
                'pass_rate': round(stats['pass_rate'] * 100, 1),
                'recommended_year': recommended_year,
                'recommended_semester': recommended_semester,
                'credit_info': {
                    'total_earned': credit_info['total_credits_earned'],
                    'remaining': credit_info['credits_remaining'],
                    'target_per_semester': credit_info['credits_per_semester_target'],
                    'on_track': credit_info['on_track']
                },
                'recommendation_reason': f"Được học bởi {stats['frequency']}/{stats['total_students']} sinh viên tốt nghiệp đúng hạn tương tự với điểm trung bình {stats['avg_score']:.2f}"
            }
            recommendations.append(rec)
            if recommended_year == 5 and recommended_semester == 1:
                print(f"DEBUG: Thêm gợi ý HK1 năm 5: {course_code} - {course_info.get('CourseName', 'N/A')}")
        
        # Sắp xếp lại theo năm, học kỳ, và tần suất (ưu tiên HK1 năm 5)
        # Tách thành 3 nhóm: 
        # 1. CT555 (Luận văn) cho sinh viên đã đủ/gần đủ tín chỉ
        # 2. Các môn khác HK1 năm 5 cho sinh viên cần thêm tín chỉ
        # 3. Các học kỳ khác
        year5_sem1_ct555 = [r for r in recommendations if r.get('recommended_year') == 5 and r.get('recommended_semester') == 1 and r.get('CourseCode') == 'CT555']
        year5_sem1_other = [r for r in recommendations if r.get('recommended_year') == 5 and r.get('recommended_semester') == 1 and r.get('CourseCode') != 'CT555']
        other_recs = [r for r in recommendations if not (r.get('recommended_year') == 5 and r.get('recommended_semester') == 1)]
        
        # Sắp xếp từng nhóm
        year5_sem1_other.sort(key=lambda x: (-x.get('frequency', 0), -x.get('avg_score', 0)))
        other_recs.sort(key=lambda x: (
            x.get('recommended_year', 999),
            x.get('recommended_semester', 999),
            -x.get('frequency', 0),
            -x.get('avg_score', 0)
        ))
        
        # Kiểm tra tổng tín chỉ hiện tại
        total_credits_earned = credit_info.get('total_credits_earned', 0)
        credits_needed = 156 - total_credits_earned
        
        print(f"DEBUG: Tổng tín chỉ đã học: {total_credits_earned}, Cần thêm: {credits_needed}")
        print(f"DEBUG: Sau khi xử lý - CT555: {len(year5_sem1_ct555)}, HK1 năm 5 khác: {len(year5_sem1_other)}, Các học kỳ khác: {len(other_recs)}")
        
        # Xây dựng danh sách gợi ý cuối cùng
        # Luôn hiển thị cả 2 nhóm riêng biệt: CT555 và các môn bổ sung
        final_recs = []
        
        # Gợi ý 1: CT555 (Luận văn) - luôn hiển thị nếu có
        if year5_sem1_ct555:
            final_recs.extend(year5_sem1_ct555)
            print(f"DEBUG: Gợi ý 1 - CT555 (Luận văn)")
        
        # Gợi ý 2: Các môn bổ sung HK1 năm 5 - luôn hiển thị nếu có
        if current_year == 4 and len(year5_sem1_other) > 0:
            final_recs.extend(year5_sem1_other[:10])  # Tăng lên 10 môn để có nhiều lựa chọn
            print(f"DEBUG: Gợi ý 2 - Các môn bổ sung HK1 năm 5: {[r.get('CourseCode') for r in year5_sem1_other[:10]]}")
        
        # Thêm các môn học kỳ khác
        final_recs.extend(other_recs[:10])
        
        # Đảm bảo có đánh dấu loại gợi ý TRƯỚC KHI cắt
        for rec in final_recs:
            if rec.get('recommended_year') == 5 and rec.get('recommended_semester') == 1:
                if rec.get('CourseCode') == 'CT555':
                    rec['recommendation_type'] = 'thesis_only'  # Chỉ luận văn
                    rec['recommendation_group'] = 'Học kỳ 1 năm 5 - Luận văn tốt nghiệp'
                else:
                    rec['recommendation_type'] = 'additional_courses'  # Các môn bổ sung
                    rec['recommendation_group'] = 'Học kỳ 1 năm 5 - Các môn bổ sung'
            else:
                # Đảm bảo các môn khác không có recommendation_group
                if 'recommendation_group' in rec:
                    del rec['recommendation_group']
        
        # Cắt sau khi đã đánh dấu
        final_recs = final_recs[:15]
        
        # Kiểm tra xem có gợi ý cho HK1 năm 5 không
        year5_sem1_recs_final = [r for r in final_recs if r.get('recommended_year') == 5 and r.get('recommended_semester') == 1]
        print(f"DEBUG: Tổng số gợi ý cuối cùng: {len(final_recs)}")
        print(f"DEBUG: Số gợi ý cho HK1 năm 5: {len(year5_sem1_recs_final)} (CT555: {len([r for r in year5_sem1_recs_final if r.get('CourseCode') == 'CT555'])}, Khác: {len([r for r in year5_sem1_recs_final if r.get('CourseCode') != 'CT555'])})")
        if year5_sem1_recs_final:
            print(f"DEBUG: Các môn HK1 năm 5: {[r['CourseCode'] for r in year5_sem1_recs_final]}")
        elif current_year == 4:
            print(f"DEBUG: CẢNH BÁO: Đang ở năm 4 nhưng không có gợi ý HK1 năm 5 trong kết quả cuối!")
            print(f"DEBUG: Danh sách recommendations đầy đủ: {[(r.get('CourseCode'), r.get('recommended_year'), r.get('recommended_semester')) for r in recommendations[:10]]}")
        
        return final_recs
        
    except Exception as e:
        print(f"Lỗi khi tạo gợi ý: {e}")
        import traceback
        traceback.print_exc()
        return []
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

