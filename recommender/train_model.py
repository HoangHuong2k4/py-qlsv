import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import joblib
import mysql.connector
from config import DB_CONFIG


def get_all_courses():
    """Lấy danh sách tất cả mã môn học từ database."""
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT CourseCode FROM MonHoc ORDER BY CourseCode")
    courses = [row[0] for row in cursor.fetchall()]
    conn.close()
    return courses


def train_kmeans(excel_path, out_model='models/kmeans_model.pkl', use_graduated_only=True):
    """
    Train K-Means với 5 clusters dựa trên feature vector 53 chiều (mỗi chiều = số tín chỉ đạt được cho mỗi môn).
    
    Args:
        excel_path: Đường dẫn đến file Excel chứa dữ liệu sinh viên
        out_model: Đường dẫn để lưu model
        use_graduated_only: Nếu True, chỉ train với sinh viên tốt nghiệp (đã học CT555 với điểm >= 5.0)
        
    Returns:
        Đường dẫn đến model đã lưu
    """
    # Đọc dữ liệu từ Excel
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
        
        print(f"📊 Chế độ: Chỉ train với sinh viên tốt nghiệp")
        print(f"📚 Tìm thấy {len(graduated_students)} sinh viên tốt nghiệp")
        
        # Chỉ giữ lại dữ liệu của sinh viên tốt nghiệp
        df = df[df['StudentID'].isin(graduated_students)]
    else:
        print(f"📊 Chế độ: Train với tất cả sinh viên")
    
    # Lấy danh sách tất cả môn học
    all_courses = get_all_courses()
    print(f"📖 Tìm thấy {len(all_courses)} môn học")
    
    # Tạo feature matrix: mỗi hàng là một sinh viên, mỗi cột là một môn học
    feature_matrix = []
    student_ids = []
    
    unique_students = df['StudentID'].unique()
    print(f"👥 Số sinh viên sẽ train: {len(unique_students)}")
    
    for student_id in unique_students:
        student_data = df[df['StudentID'] == student_id]
        
        # Tạo feature vector: số tín chỉ đạt được cho mỗi môn
        passed_courses = {}
        for _, row in student_data.iterrows():
            course_code = str(row.get('CourseCode', ''))
            if course_code in all_courses:
                score = float(row.get('Score', 0)) if pd.notna(row.get('Score')) else 0
                credits = float(row.get('Credits', 0)) if pd.notna(row.get('Credits')) else 0
                # Chỉ tính các môn đã đạt (score >= 4.0)
                if score >= 4.0:
                    passed_courses[course_code] = credits
        
        # Tạo vector 53 chiều
        feature_vector = np.array([
            passed_courses.get(course, 0) for course in all_courses
        ])
        
        feature_matrix.append(feature_vector)
        student_ids.append(student_id)
    
    # Chuyển thành numpy array
    X = np.array(feature_matrix)
    print(f"Feature matrix shape: {X.shape} (số sinh viên x số môn học)")
    
    # Normalize dữ liệu
    scaler = StandardScaler()
    X_normalized = scaler.fit_transform(X)
    
    # Train K-Means với 5 clusters
    kmeans = KMeans(n_clusters=5, random_state=42, n_init=10)
    kmeans.fit(X_normalized)
    
    # Lưu model và scaler
    joblib.dump(kmeans, out_model)
    scaler_path = out_model.replace('.pkl', '_scaler.pkl')
    joblib.dump(scaler, scaler_path)
    
    print(f"✅ Đã train K-Means với 5 clusters")
    print(f"✅ Đã lưu model: {out_model}")
    print(f"✅ Đã lưu scaler: {scaler_path}")
    
    # In thống kê clusters
    labels = kmeans.labels_
    for i in range(5):
        count = np.sum(labels == i)
        print(f"  Cluster {i}: {count} sinh viên")
    
    return out_model
