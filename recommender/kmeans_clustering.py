"""
Module K-Means Clustering để phân nhóm sinh viên và tính khoảng cách đến các cluster.
Tạo 5 kế hoạch học tập dựa trên sinh viên trội nhất mỗi cluster.
"""
import mysql.connector
import joblib
import os
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from config import DB_CONFIG
from typing import List, Dict, Tuple, Optional


def get_all_courses() -> List[str]:
    """Lấy danh sách tất cả mã môn học từ database."""
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT CourseCode FROM MonHoc ORDER BY CourseCode")
    courses = [row[0] for row in cursor.fetchall()]
    conn.close()
    return courses


def get_student_feature_vector(student_id: str) -> np.ndarray:
    """
    Tạo feature vector cho sinh viên: vector 53 chiều (số tín chỉ đạt được cho mỗi môn).
    
    Args:
        student_id: Mã sinh viên
        
    Returns:
        numpy array với shape (53,) chứa số tín chỉ đã đạt cho mỗi môn
    """
    all_courses = get_all_courses()
    
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor(dictionary=True)
    
    # Lấy các môn đã học và đạt (Score >= 4.0 hoặc Status = 'Đã qua')
    cursor.execute("""
        SELECT CourseCode, Credits 
        FROM TienTrinh 
        WHERE StudentID = %s 
        AND (Score >= 4.0 OR Status IN ('Đã học', 'Đã qua'))
    """, (student_id,))
    
    passed_courses = {row['CourseCode']: row['Credits'] or 0 for row in cursor.fetchall()}
    conn.close()
    
    # Tạo feature vector
    feature_vector = np.array([
        passed_courses.get(course, 0) for course in all_courses
    ])
    
    return feature_vector


def load_kmeans_model(model_path: str = 'models/kmeans_model.pkl') -> Tuple[KMeans, StandardScaler]:
    """
    Load K-Means model và scaler.
    
    Returns:
        Tuple (kmeans_model, scaler)
    """
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model không tồn tại: {model_path}")
    
    model = joblib.load(model_path)
    
    # Load scaler nếu có
    scaler_path = model_path.replace('.pkl', '_scaler.pkl')
    if os.path.exists(scaler_path):
        scaler = joblib.load(scaler_path)
    else:
        # Tạo scaler mới nếu chưa có
        scaler = StandardScaler()
    
    return model, scaler


def calculate_distance_to_clusters(student_id: str, model_path: str = 'models/kmeans_model.pkl') -> Dict[int, float]:
    """
    Tính khoảng cách từ sinh viên đến tâm của mỗi cluster.
    
    Args:
        student_id: Mã sinh viên
        model_path: Đường dẫn đến model
        
    Returns:
        Dict với key là cluster_id (0-4), value là khoảng cách (Euclidean distance)
    """
    try:
        model, scaler = load_kmeans_model(model_path)
        feature_vector = get_student_feature_vector(student_id)
        
        # Normalize feature vector
        feature_normalized = scaler.transform([feature_vector])[0]
        
        # Lấy tâm của các cluster
        cluster_centers = model.cluster_centers_
        
        # Tính khoảng cách đến mỗi cluster
        distances = {}
        for cluster_id in range(len(cluster_centers)):
            distance = np.linalg.norm(feature_normalized - cluster_centers[cluster_id])
            distances[cluster_id] = float(distance)
        
        return distances
    except Exception as e:
        print(f"Lỗi tính khoảng cách: {e}")
        return {i: 999.0 for i in range(5)}


def get_top_student_per_cluster(excel_path: str = 'data/student_data_100-2.xlsx', use_graduated_only: bool = True) -> Dict[int, str]:
    """
    Lấy sinh viên trội nhất (có GPA cao nhất) của mỗi cluster.
    Chỉ lấy từ sinh viên tốt nghiệp nếu use_graduated_only=True.
    
    Args:
        excel_path: Đường dẫn đến file Excel
        use_graduated_only: Nếu True, chỉ lấy từ sinh viên tốt nghiệp (đã học CT555 với điểm >= 5.0)
        
    Returns:
        Dict với key là cluster_id (0-4), value là StudentID của sinh viên trội nhất
    """
    try:
        # Load model
        model_path = 'models/kmeans_model.pkl'
        if not os.path.exists(model_path):
            print(f"⚠️  Model chưa tồn tại: {model_path}. Cần train model trước.")
            return {i: None for i in range(5)}
        
        model, scaler = load_kmeans_model(model_path)
        
        # Đọc dữ liệu từ Excel
        if not os.path.exists(excel_path):
            print(f"⚠️  File Excel không tồn tại: {excel_path}")
            return {i: None for i in range(5)}
        
        df = pd.read_excel(excel_path)
        df = df.dropna(subset=['StudentID'])
        df['StudentID'] = df['StudentID'].astype(str).str.strip()
        
        # Nếu chỉ dùng sinh viên tốt nghiệp, lọc dữ liệu
        if use_graduated_only:
            # Lấy danh sách sinh viên đã tốt nghiệp (có CT555 với điểm >= 5.0)
            graduated_students = df[
                (df['CourseCode'] == 'CT555') & 
                (df['Score'] >= 5.0)
            ]['StudentID'].unique()
            
            print(f"📊 Chỉ lấy top student từ {len(graduated_students)} sinh viên tốt nghiệp")
            
            # Chỉ giữ lại dữ liệu của sinh viên tốt nghiệp
            df = df[df['StudentID'].isin(graduated_students)]
        
        # Lấy danh sách tất cả môn học
        all_courses = get_all_courses()
        
        # Tính feature vector cho mỗi sinh viên và assign cluster
        student_clusters = {}
        student_gpas = {}
        
        unique_students = df['StudentID'].unique()
        print(f"👥 Xử lý {len(unique_students)} sinh viên để tìm top student")
        
        for student_id in unique_students:
            try:
                # Lấy dữ liệu của sinh viên này
                student_data = df[df['StudentID'] == student_id]
                
                # Tạo feature vector
                passed_courses = {}
                for _, row in student_data.iterrows():
                    course_code = str(row.get('CourseCode', ''))
                    if course_code in all_courses:
                        score = float(row.get('Score', 0)) if pd.notna(row.get('Score')) else 0
                        credits = float(row.get('Credits', 0)) if pd.notna(row.get('Credits')) else 0
                        if score >= 4.0:
                            passed_courses[course_code] = credits
                
                feature_vector = np.array([
                    passed_courses.get(course, 0) for course in all_courses
                ])
                
                # Normalize và predict cluster
                if len(feature_vector) == len(all_courses):
                    feature_normalized = scaler.transform([feature_vector])[0]
                    cluster_id = model.predict([feature_normalized])[0]
                    
                    student_clusters[student_id] = cluster_id
                    
                    # Tính GPA trung bình
                    scores = student_data[student_data['Score'] >= 4.0]['Score'].values
                    if len(scores) > 0:
                        student_gpas[student_id] = float(np.mean(scores))
                    else:
                        student_gpas[student_id] = 0.0
                    
            except Exception as e:
                print(f"Lỗi xử lý sinh viên {student_id}: {e}")
                continue
        
        # Tìm sinh viên trội nhất mỗi cluster
        top_students = {}
        for cluster_id in range(5):
            cluster_students = [
                (sid, gpa) for sid, gpa in student_gpas.items()
                if student_clusters.get(sid) == cluster_id
            ]
            if cluster_students:
                top_student = max(cluster_students, key=lambda x: x[1])
                top_students[cluster_id] = top_student[0]
            else:
                # Fallback: lấy sinh viên đầu tiên nếu không có
                top_students[cluster_id] = None
        
        return top_students
        
    except Exception as e:
        print(f"Lỗi lấy sinh viên trội nhất: {e}")
        import traceback
        traceback.print_exc()
        return {i: None for i in range(5)}


def get_student_progress_by_semester(student_id: str) -> Dict[Tuple[int, int], List[Dict]]:
    """
    Lấy tiến trình học tập của sinh viên, nhóm theo (Year, Semester).
    
    Args:
        student_id: Mã sinh viên
        
    Returns:
        Dict với key là (Year, Semester), value là list các môn học
    """
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("""
        SELECT Year, Semester, CourseCode, CourseName, Credits, Score, Status
        FROM TienTrinh
        WHERE StudentID = %s
        ORDER BY Year, Semester
    """, (student_id,))
    
    records = cursor.fetchall()
    conn.close()
    
    # Nhóm theo (Year, Semester)
    grouped = {}
    for record in records:
        key = (int(record['Year']), int(record['Semester']))
        if key not in grouped:
            grouped[key] = []
        grouped[key].append(record)
    
    return grouped


def create_learning_plan_from_student(student_id: str, target_credits: int = 156) -> Dict:
    """
    Tạo kế hoạch học tập từ lịch sử của một sinh viên.
    
    Args:
        student_id: Mã sinh viên để lấy kế hoạch
        target_credits: Tổng số tín chỉ mục tiêu (mặc định 156)
        
    Returns:
        Dict chứa kế hoạch học tập với các semester từ HK1 Y1 đến HK1 Y5
    """
    progress = get_student_progress_by_semester(student_id)
    
    # Tạo kế hoạch đầy đủ từ HK1 Y1 đến HK1 Y5
    plan = {
        'student_id': student_id,
        'semesters': {}
    }
    
    # Điền dữ liệu từ progress
    for (year, semester), courses in progress.items():
        plan['semesters'][(year, semester)] = courses
    
    # Tính tổng tín chỉ
    total_credits = sum(
        sum(c.get('Credits', 0) or 0 for c in courses)
        for courses in plan['semesters'].values()
    )
    
    plan['total_credits'] = total_credits
    plan['target_credits'] = target_credits
    
    return plan


def get_learning_plans_for_student(student_id: str, excel_path: str = 'data/student_data_100-2.xlsx') -> List[Dict]:
    """
    Tạo 5 kế hoạch học tập cho sinh viên dựa trên 5 cluster.
    
    Args:
        student_id: Mã sinh viên
        excel_path: Đường dẫn đến file Excel
        
    Returns:
        List 5 kế hoạch học tập, mỗi kế hoạch tương ứng với 1 cluster
    """
    # Lấy sinh viên trội nhất mỗi cluster
    top_students = get_top_student_per_cluster(excel_path)
    
    # Tính khoảng cách đến các cluster
    distances = calculate_distance_to_clusters(student_id)
    
    # Tạo 5 kế hoạch
    plans = []
    for cluster_id in range(5):
        top_student_id = top_students.get(cluster_id)
        
        if top_student_id:
            plan = create_learning_plan_from_student(top_student_id)
            plan['cluster_id'] = cluster_id
            plan['distance'] = distances.get(cluster_id, 999.0)
            plan['top_student_id'] = top_student_id
            plans.append(plan)
        else:
            # Fallback: tạo kế hoạch rỗng
            plans.append({
                'cluster_id': cluster_id,
                'distance': distances.get(cluster_id, 999.0),
                'top_student_id': None,
                'semesters': {},
                'total_credits': 0,
                'target_credits': 156
            })
    
    # Sắp xếp theo khoảng cách (gần nhất trước)
    plans.sort(key=lambda x: x.get('distance', 999.0))
    
    return plans

