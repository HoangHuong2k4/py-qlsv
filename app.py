from flask import Flask, request, jsonify, render_template, redirect, url_for, flash, session
import os
from werkzeug.security import check_password_hash
import mysql.connector
from config import DB_CONFIG
from recommender.train_model import train_kmeans
from recommender.recommend import recommend_next_courses
from recommender.kmeans_clustering import (
    get_learning_plans_for_student,
    calculate_distance_to_clusters,
    get_student_progress_by_semester
)

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # cần thiết cho flash messages và session

# Tự động train model khi khởi động
DEFAULT_EXCEL = 'data/student_data_100-2.xlsx'  # đường dẫn tới file Excel mặc định
MODEL_PATH = os.path.join(os.path.dirname(__file__), 'models', 'kmeans_model.pkl')

# Đảm bảo thư mục models tồn tại
os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)

# Train model từ file Excel mặc định nếu model chưa tồn tại
if os.path.exists(DEFAULT_EXCEL) and not os.path.exists(MODEL_PATH):
    print(f"Training model from {DEFAULT_EXCEL}...")
    train_kmeans(DEFAULT_EXCEL, MODEL_PATH)

# File extensions cho phép
ALLOWED_EXT = {'.xlsx', '.xls', '.csv'}

def allowed_file(filename):
    _, ext = os.path.splitext(filename)
    return ext.lower() in ALLOWED_EXT

@app.route('/')
def index():
    """Trang chủ - Redirect về login hoặc dashboard"""
    if 'student_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    student_id = (request.form.get('student_id') or '').strip()
    password = request.form.get('password') or ''

    if not student_id or not password:
        flash('Vui lòng nhập đầy đủ thông tin', 'error')
        return redirect(url_for('index'))

    try:
        conn = mysql.connector.connect(**DB_CONFIG)
    except mysql.connector.Error as e:
        flash('Không thể kết nối đến database. Vui lòng kiểm tra MySQL đã được khởi động trong XAMPP chưa.', 'error')
        print(f"Database connection error: {e}")
        return redirect(url_for('index'))
    
    cursor = conn.cursor(dictionary=True)
    # So khop StudentID bo khoang trang dau/cuoi
    cursor.execute("SELECT * FROM SinhVien WHERE TRIM(StudentID)=%s", (student_id,))
    user = cursor.fetchone()
    
    if not user:
        flash('Mã số sinh viên hoặc mật khẩu không đúng', 'error')
        return redirect(url_for('index'))

    # Hỗ trợ trường hợp mật khẩu vẫn còn plaintext trong DB
    def _is_hashed(p):
        return isinstance(p, str) and (p.startswith('pbkdf2:') or p.startswith('scrypt:'))

    stored_password = user.get('Password') or ''
    if _is_hashed(stored_password):
        valid = check_password_hash(stored_password, password)
    else:
        valid = stored_password == password
        # Nếu khớp plaintext, tự động chuyển sang hash để lần sau đăng nhập chuẩn
        if valid:
            from werkzeug.security import generate_password_hash
            new_hash = generate_password_hash(password, method='pbkdf2:sha256')
            cursor2 = conn.cursor()
            cursor2.execute("UPDATE SinhVien SET Password=%s WHERE StudentID=%s", (new_hash, user['StudentID']))
            conn.commit()
            cursor2.close()

    if not valid:
        flash('Mã số sinh viên hoặc mật khẩu không đúng', 'error')
        conn.close()
        return redirect(url_for('index'))

    # Lưu thông tin vào session
    session['student_id'] = student_id
    session['student_name'] = user['HoTen']
    
    conn.close()
    return redirect(url_for('dashboard'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/dashboard')
def dashboard():
    if 'student_id' not in session:
        return redirect(url_for('index'))
        
    student_id = session['student_id']
    model_path = MODEL_PATH  # use global constant defined above

    try:
        try:
            conn = mysql.connector.connect(**DB_CONFIG)
        except mysql.connector.Error as e:
            flash('Không thể kết nối đến database. Vui lòng kiểm tra MySQL đã được khởi động trong XAMPP chưa.', 'error')
            print(f"Database connection error: {e}")
            return render_template('student_dashboard.html',
                                 student_id=session.get('student_id'),
                                 student_name=session.get('student_name'),
                                 courses=[],
                                 recs=[],
                                 credit_summary=None)
        
        cursor = conn.cursor(dictionary=True)
        
        # Lấy thông tin các môn đã học từ TienTrinh
        cursor.execute("""
            SELECT tt.*, mh.CourseName 
            FROM TienTrinh tt
            JOIN MonHoc mh ON tt.CourseCode = mh.CourseCode
            WHERE tt.StudentID=%s 
            ORDER BY tt.Year, tt.Semester
        """, (student_id,))
        courses = cursor.fetchall()

        # Tính tổng tín chỉ đã học
        total_credits_earned = sum(c.get('Credits', 0) or 0 for c in courses if c.get('Status') in ('Đã học', 'Đã qua'))
        total_required_credits = 156  # 156 tín chỉ yêu cầu
        credits_remaining = max(0, total_required_credits - total_credits_earned)
        
        # Lấy gợi ý môn học tiếp theo
        recs = recommend_next_courses(student_id, model_path=model_path)
        
        # Debug: Kiểm tra recommendation_group
        if recs:
            print(f"DEBUG app.py: Số gợi ý nhận được: {len(recs)}")
            thesis_count = len([r for r in recs if r.get('recommendation_group') == 'Học kỳ 1 năm 5 - Luận văn tốt nghiệp'])
            additional_count = len([r for r in recs if r.get('recommendation_group') == 'Học kỳ 1 năm 5 - Các môn bổ sung'])
            print(f"DEBUG app.py: Thesis: {thesis_count}, Additional: {additional_count}, Other: {len(recs) - thesis_count - additional_count}")
        
        # Thêm thông tin chi tiết cho các môn được gợi ý (không ghi đè recommendation_group)
        if recs:
            course_codes = [r['CourseCode'] for r in recs]
            placeholders = ','.join(['%s'] * len(course_codes))
            cursor.execute(f"""
                SELECT mh.*, tq.PrerequisiteCode
                FROM MonHoc mh
                LEFT JOIN TienQuyet tq ON mh.CourseCode = tq.CourseCode
                WHERE mh.CourseCode IN ({placeholders})
            """, tuple(course_codes))
            course_details = cursor.fetchall()
            
            # Map thông tin chi tiết vào recommendations (giữ lại recommendation_group)
            course_info = {c['CourseCode']: c for c in course_details}
            for rec in recs:
                if rec['CourseCode'] in course_info:
                    # Lưu recommendation_group trước khi update
                    saved_group = rec.get('recommendation_group')
                    saved_type = rec.get('recommendation_type')
                    # Update thông tin
                    rec.update(course_info[rec['CourseCode']])
                    # Khôi phục recommendation_group nếu có
                    if saved_group:
                        rec['recommendation_group'] = saved_group
                    if saved_type:
                        rec['recommendation_type'] = saved_type

        conn.close()
        
        # Tính toán thông tin về tiến độ
        credit_summary = {
            'earned': total_credits_earned,
            'required': total_required_credits,
            'remaining': credits_remaining,
            'percentage': round((total_credits_earned / total_required_credits * 100), 1) if total_required_credits > 0 else 0
        }

    except Exception as e:
        print(f"Error in dashboard: {e}")
        import traceback
        traceback.print_exc()
        flash('Có lỗi xảy ra khi tải dữ liệu', 'error')
        courses = []
        recs = []
        credit_summary = None

    return render_template('student_dashboard.html',
                         student_id=session['student_id'],
                         student_name=session['student_name'],
                         courses=courses,
                         recs=recs,
                         credit_summary=credit_summary)


@app.route('/recommendations')
def recommendations():
    if 'student_id' not in session:
        return redirect(url_for('index'))
    return redirect(url_for('dashboard'))

@app.route('/study-plan')
def study_plan():
    """Hiển thị 5 kế hoạch học tập dựa trên K-Means clustering"""
    if 'student_id' not in session:
        return redirect(url_for('index'))
    
    student_id = session['student_id']
    
    try:
        # Kiểm tra sinh viên mới (B22) hay cũ (B21)
        is_new_student = student_id.startswith('B22')
        
        # Lấy tiến trình hiện tại
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT COUNT(*) as count FROM TienTrinh WHERE StudentID = %s", (student_id,))
        progress_count = cursor.fetchone()['count']
        conn.close()
        
        # Nếu là sinh viên mới hoặc chưa có tiến trình
        if is_new_student or progress_count == 0:
            # Hiển thị 5 kế hoạch đầy đủ từ HK1 Y1 đến HK1 Y5
            plans_data = get_learning_plans_for_student(student_id)
            
            # Tạo metadata cho 5 kế hoạch
            plan_names = [
                'Kế hoạch Chuẩn (Ổn định)',
                'Kế hoạch Nhanh (Tốt nghiệp sớm)',
                'Kế hoạch Vừa phải (Cân bằng)',
                'Kế hoạch Chậm (Tích lũy từ từ)',
                'Kế hoạch Tùy chỉnh (Linh hoạt)'
            ]
            plan_colors = ['#4CAF50', '#FF9800', '#2196F3', '#9C27B0', '#607D8B']
            plan_descriptions = [
                'Phù hợp cho sinh viên muốn học đều theo kỳ, không áp lực',
                'Học nhiều tín chỉ mỗi kỳ để tốt nghiệp sớm',
                'Cân bằng giữa học tập và cuộc sống',
                'Học ít TC mỗi kỳ, tập trung chất lượng',
                'Tự điều chỉnh theo từng kỳ học'
            ]
            
            plans = []
            for i, plan_data in enumerate(plans_data):
                # Tính số tín chỉ trung bình mỗi kỳ
                semesters_raw = plan_data.get('semesters', {})
                # Convert tuple keys thành string keys cho Jinja2 và tính tín chỉ mỗi kỳ
                semesters = {}
                chart_data = []  # Dữ liệu cho biểu đồ: [{'label': 'Năm 1 HK1', 'credits': 13}, ...]
                
                for (year, semester), courses in semesters_raw.items():
                    # Tính tổng tín chỉ cho học kỳ này
                    semester_credits = sum(c.get('Credits', 0) or 0 for c in courses)
                    key = f"{year}_{semester}"
                    semesters[key] = {
                        'year': year,
                        'semester': semester,
                        'courses': courses,
                        'credits': semester_credits
                    }
                    chart_data.append({
                        'label': f'Năm {year} HK{semester}',
                        'credits': semester_credits
                    })
                
                # Sắp xếp chart_data theo năm và học kỳ
                chart_data.sort(key=lambda x: (int(x['label'].split('Năm ')[1].split(' HK')[0]), 
                                               int(x['label'].split('HK')[1])))
                
                total_credits = plan_data.get('total_credits', 0)
                num_semesters = len(semesters) if semesters else 1
                avg_credits = total_credits / num_semesters if num_semesters > 0 else 0
                
                plans.append({
                    'cluster_id': plan_data.get('cluster_id', i),
                    'name': plan_names[i],
                    'color': plan_colors[i],
                    'description': plan_descriptions[i],
                    'distance': plan_data.get('distance', 999.0),
                    'semesters': semesters,
                    'chart_data': chart_data,  # Dữ liệu cho biểu đồ
                    'total_credits': total_credits,
                    'target_credits': 156,
                    'avg_credits_per_semester': round(avg_credits, 1),
                    'num_semesters': num_semesters,
                    'top_student_id': plan_data.get('top_student_id')
                })
        else:
            # Sinh viên cũ: gợi ý tiếp theo để đủ 156 TC
            plans_data = get_learning_plans_for_student(student_id)
            
            # Lấy tiến trình hiện tại
            current_progress = get_student_progress_by_semester(student_id)
            current_total_credits = sum(
                sum(c.get('Credits', 0) or 0 for c in courses)
                for courses in current_progress.values()
            )
            
            plan_names = [
                'Kế hoạch Chuẩn (Ổn định)',
                'Kế hoạch Nhanh (Tốt nghiệp sớm)',
                'Kế hoạch Vừa phải (Cân bằng)',
                'Kế hoạch Chậm (Tích lũy từ từ)',
                'Kế hoạch Tùy chỉnh (Linh hoạt)'
            ]
            plan_colors = ['#4CAF50', '#FF9800', '#2196F3', '#9C27B0', '#607D8B']
            
            plans = []
            for i, plan_data in enumerate(plans_data):
                # Lọc các môn chưa học từ kế hoạch
                semesters_raw = plan_data.get('semesters', {})
                recommended_semesters_raw = {}
                
                # Tìm học kỳ tiếp theo
                if current_progress:
                    max_year = max(y for y, s in current_progress.keys())
                    max_semester = max(s for y, s in current_progress.keys() if y == max_year)
                    
                    # Lọc các học kỳ từ học kỳ tiếp theo trở đi
                    for (year, semester), courses in semesters_raw.items():
                        if year > max_year or (year == max_year and semester > max_semester):
                            # Lọc các môn chưa học
                            current_courses = set()
                            for cs in current_progress.values():
                                current_courses.update(c.get('CourseCode') for c in cs)
                            
                            recommended_courses = [
                                c for c in courses
                                if c.get('CourseCode') not in current_courses
                            ]
                            
                            if recommended_courses:
                                recommended_semesters_raw[(year, semester)] = recommended_courses
                
                # Convert tuple keys thành string keys cho Jinja2 và tính tín chỉ
                recommended_semesters = {}
                chart_data = []  # Dữ liệu cho biểu đồ
                
                for (year, semester), courses in recommended_semesters_raw.items():
                    semester_credits = sum(c.get('Credits', 0) or 0 for c in courses)
                    key = f"{year}_{semester}"
                    recommended_semesters[key] = {
                        'year': year,
                        'semester': semester,
                        'courses': courses,
                        'credits': semester_credits
                    }
                    chart_data.append({
                        'label': f'Năm {year} HK{semester}',
                        'credits': semester_credits
                    })
                
                # Sắp xếp chart_data
                chart_data.sort(key=lambda x: (int(x['label'].split('Năm ')[1].split(' HK')[0]), 
                                               int(x['label'].split('HK')[1])))
                
                recommended_total = sum(
                    sum(c.get('Credits', 0) or 0 for c in courses)
                    for courses in recommended_semesters_raw.values()
                )
                
                plans.append({
                    'cluster_id': plan_data.get('cluster_id', i),
                    'name': plan_names[i],
                    'color': plan_colors[i],
                    'description': f'Gợi ý tiếp theo để đủ 156 TC (hiện tại: {current_total_credits} TC)',
                    'distance': plan_data.get('distance', 999.0),
                    'semesters': recommended_semesters,
                    'chart_data': chart_data,  # Dữ liệu cho biểu đồ
                    'current_credits': current_total_credits,
                    'recommended_credits': recommended_total,
                    'total_credits': current_total_credits + recommended_total,
                    'target_credits': 156,
                    'top_student_id': plan_data.get('top_student_id')
                })
        
        # Tính khoảng cách đến các cluster
        distances = calculate_distance_to_clusters(student_id)
        
        return render_template('study_plan.html', 
                             student_id=student_id,
                             student_name=session.get('student_name'),
                             plans=plans,
                             distances=distances,
                             is_new_student=is_new_student)
        
    except Exception as e:
        print(f"Error in study_plan: {e}")
        import traceback
        traceback.print_exc()
        flash('Có lỗi xảy ra khi tải kế hoạch học tập', 'error')
        return redirect(url_for('dashboard'))

@app.route('/download-plan-pdf/<int:cluster_id>')
def download_plan_pdf(cluster_id):
    """Download kế hoạch học tập dạng PDF"""
    if 'student_id' not in session:
        return redirect(url_for('index'))
    
    student_id = session['student_id']
    
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.lib.units import cm
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        from reportlab.lib.enums import TA_CENTER, TA_LEFT
        from io import BytesIO
        from flask import Response
        import os
        import platform
        
        # Đăng ký font tiếng Việt
        font_registered = False
        vietnamese_font_name = 'VietnameseFont'
        
        # Tìm font hỗ trợ tiếng Việt trên hệ thống
        font_paths = []
        
        if platform.system() == 'Darwin':  # macOS
            font_paths = [
                '/System/Library/Fonts/Supplemental/Arial Unicode.ttf',
                '/Library/Fonts/Arial Unicode.ttf',
                '/System/Library/Fonts/Helvetica.ttc',
                '/System/Library/Fonts/STHeiti Light.ttc',
                '/System/Library/Fonts/STHeiti Medium.ttc',
            ]
        elif platform.system() == 'Windows':
            font_paths = [
                'C:/Windows/Fonts/arial.ttf',
                'C:/Windows/Fonts/arialuni.ttf',
                'C:/Windows/Fonts/times.ttf',
                'C:/Windows/Fonts/timesi.ttf',
            ]
        else:  # Linux
            font_paths = [
                '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
                '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf',
                '/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf',
            ]
        
        # Thử đăng ký font
        for font_path in font_paths:
            if os.path.exists(font_path):
                try:
                    # Xử lý file .ttc (TrueType Collection) trên macOS
                    if font_path.endswith('.ttc'):
                        # TTFont có thể xử lý TTC nhưng cần chỉ định index
                        pdfmetrics.registerFont(TTFont(vietnamese_font_name, font_path, subfontIndex=0))
                    else:
                        pdfmetrics.registerFont(TTFont(vietnamese_font_name, font_path))
                    font_registered = True
                    print(f"✅ Đã đăng ký font: {font_path}")
                    break
                except Exception as e:
                    print(f"⚠️ Không thể đăng ký font {font_path}: {e}")
                    continue
        
        # Nếu không tìm thấy font hệ thống, thử dùng DejaVu Sans từ reportlab
        if not font_registered:
            try:
                from reportlab.pdfbase.cidfonts import UnicodeCIDFont
                # Thử dùng font CJK (hỗ trợ Unicode tốt hơn)
                pdfmetrics.registerFont(UnicodeCIDFont('STSong-Light'))
                vietnamese_font_name = 'STSong-Light'
                font_registered = True
                print("✅ Đã đăng ký font CJK")
            except:
                pass
        
        # Fallback cuối cùng: dùng Helvetica (có thể không hiển thị đúng tiếng Việt)
        if not font_registered:
            print("⚠️ Không tìm thấy font tiếng Việt, sử dụng Helvetica (có thể không hiển thị đúng)")
            vietnamese_font_name = 'Helvetica'
            font_registered = False  # Đánh dấu không có font Unicode
        
        # Lấy kế hoạch học tập
        plans_data = get_learning_plans_for_student(student_id)
        
        if cluster_id >= len(plans_data):
            flash('Không tìm thấy kế hoạch', 'error')
            return redirect(url_for('study_plan'))
        
        plan_data = plans_data[cluster_id]
        semesters_raw = plan_data.get('semesters', {})
        
        # Convert về dạng tuple keys nếu là string keys
        semesters = {}
        for key, value in semesters_raw.items():
            if isinstance(key, tuple):
                semesters[key] = value if isinstance(value, list) else value.get('courses', [])
            elif isinstance(key, str) and '_' in key:
                # String key format: "year_semester"
                parts = key.split('_')
                if len(parts) == 2:
                    year, semester = int(parts[0]), int(parts[1])
                    courses = value if isinstance(value, list) else value.get('courses', [])
                    semesters[(year, semester)] = courses
        
        # Tạo PDF
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, 
                                rightMargin=2*cm, leftMargin=2*cm,
                                topMargin=2*cm, bottomMargin=2*cm)
        
        # Styles với font tiếng Việt
        styles = getSampleStyleSheet()
        
        # Tạo custom styles với font tiếng Việt
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontName=vietnamese_font_name,
            fontSize=18,
            textColor=colors.HexColor('#1f5ca9'),
            spaceAfter=30,
            alignment=TA_CENTER
        )
        
        normal_style = ParagraphStyle(
            'VietnameseNormal',
            parent=styles['Normal'],
            fontName=vietnamese_font_name,
            fontSize=10
        )
        
        heading2_style = ParagraphStyle(
            'VietnameseHeading2',
            parent=styles['Heading2'],
            fontName=vietnamese_font_name,
            fontSize=14
        )
        
        # Nội dung PDF
        story = []
        
        # Tiêu đề
        plan_names = [
            'Kế hoạch Chuẩn (Ổn định)',
            'Kế hoạch Nhanh (Tốt nghiệp sớm)',
            'Kế hoạch Vừa phải (Cân bằng)',
            'Kế hoạch Chậm (Tích lũy từ từ)',
            'Kế hoạch Tùy chỉnh (Linh hoạt)'
        ]
        
        title = Paragraph(f"KẾ HOẠCH HỌC TẬP - {plan_names[cluster_id]}", title_style)
        story.append(title)
        story.append(Spacer(1, 0.5*cm))
        
        # Thông tin sinh viên
        info_text = f"""
        <b>Sinh viên:</b> {session.get('student_name', student_id)} ({student_id})<br/>
        <b>Ngày tạo:</b> {__import__('datetime').datetime.now().strftime('%d/%m/%Y %H:%M')}<br/>
        <b>Tổng tín chỉ:</b> {plan_data.get('total_credits', 0)} / 156 TC
        """
        info_para = Paragraph(info_text, normal_style)
        story.append(info_para)
        story.append(Spacer(1, 1*cm))
        
        # Bảng môn học theo học kỳ
        for (year, semester), courses in sorted(semesters.items()):
            semester_title = Paragraph(
                f"<b>Năm {year} - Học kỳ {semester}</b>",
                heading2_style
            )
            story.append(semester_title)
            story.append(Spacer(1, 0.3*cm))
            
            # Tạo bảng với Paragraph để hỗ trợ font tiếng Việt
            table_data = [[
                Paragraph('STT', normal_style),
                Paragraph('Mã môn', normal_style),
                Paragraph('Tên môn học', normal_style),
                Paragraph('Tín chỉ', normal_style),
                Paragraph('Điểm', normal_style)
            ]]
            
            for idx, course in enumerate(courses, 1):
                course_name = course.get('CourseName', '') or ''
                course_code = course.get('CourseCode', '') or ''
                credits = str(course.get('Credits', 0) or 0)
                score = str(course.get('Score', '-') or '-')
                
                table_data.append([
                    Paragraph(str(idx), normal_style),
                    Paragraph(course_code, normal_style),
                    Paragraph(course_name, normal_style),
                    Paragraph(credits, normal_style),
                    Paragraph(score, normal_style)
                ])
            
            # Tính tổng tín chỉ học kỳ
            semester_credits = sum(c.get('Credits', 0) or 0 for c in courses)
            table_data.append([
                Paragraph('', normal_style),
                Paragraph('', normal_style),
                Paragraph('<b>Tổng</b>', normal_style),
                Paragraph(f'<b>{semester_credits}</b>', normal_style),
                Paragraph('', normal_style)
            ])
            
            table = Table(table_data, colWidths=[1*cm, 2*cm, 8*cm, 2*cm, 2*cm])
            
            # Tạo style cho bảng với font tiếng Việt
            table_style = [
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f5ca9')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), vietnamese_font_name),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -2), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]
            
            # Thêm font cho các dòng dữ liệu
            if font_registered:
                table_style.extend([
                    ('FONTNAME', (0, 1), (-1, -1), vietnamese_font_name),
                    ('FONTSIZE', (0, 1), (-1, -1), 9),
                ])
            
            table.setStyle(TableStyle(table_style))
            
            story.append(table)
            story.append(Spacer(1, 0.5*cm))
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        
        # Trả về PDF
        return Response(
            buffer.getvalue(),
            mimetype='application/pdf',
            headers={
                'Content-Disposition': f'attachment;filename=KeHoach_Nhom{cluster_id}_{student_id}.pdf'
            }
        )
        
    except Exception as e:
        print(f"Error generating PDF: {e}")
        import traceback
        traceback.print_exc()
        flash(f'Lỗi tạo PDF: {e}', 'error')
        return redirect(url_for('study_plan'))

@app.route('/download-recommendations')
def download_recommendations():
    """Download gợi ý môn học dạng text"""
    if 'student_id' not in session:
        return redirect(url_for('index'))
    
    student_id = session['student_id']
    model_path = MODEL_PATH
    
    try:
        recs = recommend_next_courses(student_id, model_path=model_path)
        
        # Tạo nội dung file text
        from datetime import datetime
        now = datetime.now().strftime('%d/%m/%Y %H:%M')
        
        content = f"""
╔═══════════════════════════════════════════════════════════╗
║  GỢI Ý MÔN HỌC CHO SINH VIÊN {student_id}              ║
╚═══════════════════════════════════════════════════════════╝

Sinh viên: {session.get('student_name', student_id)}
Ngày tạo: {now}

═══════════════════════════════════════════════════════════
DANH SÁCH MÔN ĐƯỢC GỢI Ý ({len(recs)} môn)
═══════════════════════════════════════════════════════════

"""
        
        for i, rec in enumerate(recs, 1):
            content += f"""
{i}. {rec.get('CourseCode')} - {rec.get('CourseName')}
   Tín chỉ: {rec.get('Credits')} TC
   Năm/Kỳ: Năm {rec.get('recommended_year')} - HK{rec.get('recommended_semester')}
   Lý do: {rec.get('recommendation_reason', 'Gợi ý dựa trên AI')}
   ---
"""
        
        content += f"""
═══════════════════════════════════════════════════════════
HỆ THỐNG GỢI Ý HỌC TẬP - CTU
═══════════════════════════════════════════════════════════
"""
        
        from flask import Response
        return Response(
            content,
            mimetype='text/plain',
            headers={'Content-Disposition': f'attachment;filename=GoiY_MonHoc_{student_id}.txt'}
        )
        
    except Exception as e:
        flash(f'Lỗi tải gợi ý: {e}', 'error')
        return redirect(url_for('dashboard'))

@app.route('/profile')
def profile():
    if 'student_id' not in session:
        return redirect(url_for('index'))
    return render_template('profile.html',
                         student_id=session.get('student_id'),
                         student_name=session.get('student_name'))

@app.route('/recommendations/hk1-nam5')
def recommendations_hk1_nam5():
    if 'student_id' not in session:
        return redirect(url_for('index'))

    student_id = session['student_id']
    model_path = MODEL_PATH

    try:
        try:
            conn = mysql.connector.connect(**DB_CONFIG)
        except mysql.connector.Error as e:
            flash('Không thể kết nối đến database. Vui lòng kiểm tra MySQL đã được khởi động trong XAMPP chưa.', 'error')
            print(f"Database connection error: {e}")
            return render_template('recommendations_hk1_nam5.html',
                                 student_id=session.get('student_id'),
                                 student_name=session.get('student_name'),
                                 additional_recs=[])
        
        cursor = conn.cursor(dictionary=True)

        # Lấy gợi ý môn học tiếp theo
        recs = recommend_next_courses(student_id, model_path=model_path)

        # Lấy thêm thông tin chi tiết cho các môn được gợi ý
        if recs:
            course_codes = [r['CourseCode'] for r in recs]
            placeholders = ','.join(['%s'] * len(course_codes))
            cursor.execute(f"""
                SELECT mh.*, tq.PrerequisiteCode
                FROM MonHoc mh
                LEFT JOIN TienQuyet tq ON mh.CourseCode = tq.CourseCode
                WHERE mh.CourseCode IN ({placeholders})
            """, tuple(course_codes))
            course_details = cursor.fetchall()

            course_info = {c['CourseCode']: c for c in course_details}
            for rec in recs:
                if rec['CourseCode'] in course_info:
                    saved_group = rec.get('recommendation_group')
                    saved_type = rec.get('recommendation_type')
                    rec.update(course_info[rec['CourseCode']])
                    if saved_group:
                        rec['recommendation_group'] = saved_group
                    if saved_type:
                        rec['recommendation_type'] = saved_type

        conn.close()

        # Lọc ra các môn bổ sung HK1 năm 5 (loại bỏ CT555 nếu có)
        additional_recs = [
            r for r in (recs or [])
            if (
                (r.get('recommendation_group') == 'Học kỳ 1 năm 5 - Các môn bổ sung') or
                (r.get('recommended_year') == 5 and r.get('recommended_semester') == 1)
            ) and r.get('CourseCode') != 'CT555'
        ]

    except Exception as e:
        print(f"Error in recommendations_hk1_nam5: {e}")
        import traceback
        traceback.print_exc()
        flash('Có lỗi xảy ra khi tải gợi ý', 'error')
        additional_recs = []

    return render_template(
        'recommendations_hk1_nam5.html',
        student_id=session['student_id'],
        student_name=session.get('student_name'),
        additional_recs=additional_recs
    )

@app.route('/train', methods=['POST'])
def train():
    excel_path = request.form.get('excel_path') or None
    if not excel_path:
        return jsonify({'status': 'error', 'message': 'excel_path is required'}), 400
    path = train_kmeans(excel_path)
    return jsonify({'status': 'ok', 'model_path': path})


@app.route('/recommend', methods=['GET'])
def recommend():
    student_id = request.args.get('student_id')
    recs = recommend_next_courses(student_id)
    return jsonify({'student_id': student_id, 'recommendations': recs})


@app.route('/test/login')
def test_login():
    """Route test để xem giao diện đăng nhập"""
    return render_template('login.html')

@app.route('/test/dashboard')
def test_dashboard():
    """Route test để xem giao diện dashboard"""
    # Dữ liệu mẫu để test
    mock_courses = [
        {'CourseCode': 'CT101', 'CourseName': 'Lập trình cơ bản', 'Year': 1, 'Semester': 1, 'Credits': 3, 'Status': 'Đã qua', 'Score': '8.5'},
        {'CourseCode': 'CT102', 'CourseName': 'Cấu trúc dữ liệu', 'Year': 1, 'Semester': 2, 'Credits': 3, 'Status': 'Đã qua', 'Score': '7.8'},
        {'CourseCode': 'CT201', 'CourseName': 'Lập trình hướng đối tượng', 'Year': 2, 'Semester': 1, 'Credits': 3, 'Status': 'Đã qua', 'Score': '8.2'},
    ]
    
    mock_recs = [
        {'CourseCode': 'CT301', 'CourseName': 'Cơ sở dữ liệu', 'Credits': 3, 'recommended_year': 3, 'recommended_semester': 1, 'avg_score': 7.5, 'pass_rate': 85.2, 'recommendation_reason': 'Được học bởi 45 sinh viên tốt nghiệp đúng hạn tương tự'},
        {'CourseCode': 'CT302', 'CourseName': 'Mạng máy tính', 'Credits': 3, 'recommended_year': 3, 'recommended_semester': 1, 'avg_score': 7.8, 'pass_rate': 88.5, 'recommendation_reason': 'Được học bởi 42 sinh viên tốt nghiệp đúng hạn tương tự'},
    ]
    
    mock_credit_summary = {
        'earned': 120,
        'required': 156,
        'remaining': 36,
        'percentage': 76.9
    }
    
    return render_template('student_dashboard.html',
                         student_id='B2101234',
                         student_name='Nguyễn Văn A',
                         courses=mock_courses,
                         recs=mock_recs,
                         credit_summary=mock_credit_summary)

@app.route('/test/study-plan')
def test_study_plan():
    """Route test để xem giao diện kế hoạch học tập"""
    return render_template('study_plan.html',
                         student_id='B2101234',
                         student_name='Nguyễn Văn A')

@app.route('/test/profile')
def test_profile():
    """Route test để xem giao diện thông tin cá nhân"""
    return render_template('profile.html',
                         student_id='B2110936',
                         student_name='Nguyễn Thị Kim Đào')

# ============================================
# ADMIN ROUTES
# ============================================

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """Đăng nhập admin"""
    if request.method == 'GET':
        return render_template('admin_login.html')
    
    admin_id = (request.form.get('admin_id') or '').strip()
    password = request.form.get('password') or ''
    
    if not admin_id or not password:
        flash('Vui lòng nhập đầy đủ thông tin', 'error')
        return redirect(url_for('admin_login'))
    
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM Admin WHERE AdminID=%s", (admin_id,))
        admin = cursor.fetchone()
        conn.close()
        
        if not admin:
            flash('Tài khoản admin không đúng', 'error')
            return redirect(url_for('admin_login'))
        
        if not check_password_hash(admin['Password'], password):
            flash('Mật khẩu không đúng', 'error')
            return redirect(url_for('admin_login'))
        
        # Lưu session admin
        session['admin_id'] = admin_id
        session['admin_name'] = admin['Username']
        session['is_admin'] = True
        
        return redirect(url_for('admin_dashboard'))
        
    except Exception as e:
        flash(f'Lỗi đăng nhập: {e}', 'error')
        return redirect(url_for('admin_login'))

@app.route('/admin/logout')
def admin_logout():
    """Đăng xuất admin"""
    session.clear()
    flash('Đã đăng xuất', 'success')
    return redirect(url_for('admin_login'))

@app.route('/admin/dashboard')
def admin_dashboard():
    """Dashboard admin"""
    if 'is_admin' not in session:
        return redirect(url_for('admin_login'))
    
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        
        # Thống kê
        cursor.execute("SELECT COUNT(*) as count FROM SinhVien")
        student_count = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM MonHoc")
        course_count = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM TienTrinh")
        progress_count = cursor.fetchone()['count']
        
        conn.close()
        
        stats = {
            'students': student_count,
            'courses': course_count,
            'progress': progress_count
        }
        
        return render_template('admin_dashboard.html',
                             admin_name=session.get('admin_name'),
                             stats=stats)
    except Exception as e:
        flash(f'Lỗi tải dữ liệu: {e}', 'error')
        return render_template('admin_dashboard.html',
                             admin_name=session.get('admin_name'),
                             stats={'students': 0, 'courses': 0, 'progress': 0})

@app.route('/admin/students')
def admin_students():
    """Quản lý sinh viên"""
    if 'is_admin' not in session:
        return redirect(url_for('admin_login'))
    
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        
        # Lấy danh sách sinh viên với thống kê
        cursor.execute("""
            SELECT 
                sv.StudentID,
                sv.HoTen,
                sv.Email,
                sv.GioiTinh,
                COUNT(DISTINCT tt.CourseCode) as total_courses,
                SUM(tt.Credits) as total_credits
            FROM SinhVien sv
            LEFT JOIN TienTrinh tt ON sv.StudentID = tt.StudentID AND tt.Status = 'Đã học'
            GROUP BY sv.StudentID, sv.HoTen, sv.Email, sv.GioiTinh
            ORDER BY sv.StudentID
        """)
        students = cursor.fetchall()
        conn.close()
        
        return render_template('admin_students.html',
                             admin_name=session.get('admin_name'),
                             students=students)
    except Exception as e:
        flash(f'Lỗi tải danh sách sinh viên: {e}', 'error')
        return render_template('admin_students.html',
                             admin_name=session.get('admin_name'),
                             students=[])

@app.route('/admin/students/add', methods=['GET', 'POST'])
def admin_add_student():
    """Thêm sinh viên mới"""
    if 'is_admin' not in session:
        return redirect(url_for('admin_login'))
    
    if request.method == 'GET':
        return render_template('admin_add_student.html',
                             admin_name=session.get('admin_name'))
    
    # POST - Xử lý thêm sinh viên
    student_id = request.form.get('student_id', '').strip()
    ho_ten = request.form.get('ho_ten', '').strip()
    gioi_tinh = request.form.get('gioi_tinh', 'Nam')
    ngay_sinh = request.form.get('ngay_sinh', '2003-01-01')
    email = request.form.get('email', '').strip()
    password = request.form.get('password', student_id)  # Mặc định = mã SV
    
    if not student_id or not ho_ten:
        flash('Vui lòng nhập đầy đủ Mã SV và Họ tên', 'error')
        return redirect(url_for('admin_add_student'))
    
    try:
        from werkzeug.security import generate_password_hash
        password_hash = generate_password_hash(password, method='pbkdf2:sha256')
        
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO SinhVien (StudentID, HoTen, Password, GioiTinh, NgaySinh, Email)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (student_id, ho_ten, password_hash, gioi_tinh, ngay_sinh, email))
        
        conn.commit()
        conn.close()
        
        flash(f'Đã thêm sinh viên {student_id} thành công!', 'success')
        return redirect(url_for('admin_students'))
        
    except mysql.connector.Error as e:
        if 'Duplicate entry' in str(e):
            flash(f'Sinh viên {student_id} đã tồn tại!', 'error')
        else:
            flash(f'Lỗi thêm sinh viên: {e}', 'error')
        return redirect(url_for('admin_add_student'))

@app.route('/admin/students/view/<student_id>')
def admin_view_student(student_id):
    """Xem chi tiết sinh viên"""
    if 'is_admin' not in session:
        return redirect(url_for('admin_login'))
    
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        
        # Lấy thông tin sinh viên
        cursor.execute("SELECT * FROM SinhVien WHERE StudentID = %s", (student_id,))
        student = cursor.fetchone()
        
        if not student:
            flash(f'Không tìm thấy sinh viên {student_id}', 'error')
            return redirect(url_for('admin_students'))
        
        # Lấy tiến trình học tập
        cursor.execute("""
            SELECT CourseCode, CourseName, Year, Semester, Credits, Score, Status
            FROM TienTrinh
            WHERE StudentID = %s
            ORDER BY Year, Semester
        """, (student_id,))
        progress = cursor.fetchall()
        
        # Tính tổng tín chỉ
        total_credits = sum(p['Credits'] for p in progress if p['Status'] == 'Đã học')
        
        conn.close()
        
        return render_template('admin_student_detail.html',
                             admin_name=session.get('admin_name'),
                             student=student,
                             progress=progress,
                             total_credits=total_credits)
    except Exception as e:
        flash(f'Lỗi tải thông tin sinh viên: {e}', 'error')
        return redirect(url_for('admin_students'))

@app.route('/admin/students/delete/<student_id>')
def admin_delete_student(student_id):
    """Xóa sinh viên"""
    if 'is_admin' not in session:
        return redirect(url_for('admin_login'))
    
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Xóa tiến trình trước
        cursor.execute("DELETE FROM TienTrinh WHERE StudentID = %s", (student_id,))
        # Xóa sinh viên
        cursor.execute("DELETE FROM SinhVien WHERE StudentID = %s", (student_id,))
        
        conn.commit()
        conn.close()
        
        flash(f'Đã xóa sinh viên {student_id}', 'success')
    except Exception as e:
        flash(f'Lỗi xóa sinh viên: {e}', 'error')
    
    return redirect(url_for('admin_students'))

@app.route('/admin/courses')
def admin_courses():
    """Quản lý môn học"""
    if 'is_admin' not in session:
        return redirect(url_for('admin_login'))
    
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        
        # Lấy danh sách môn học với số sinh viên đang học
        cursor.execute("""
            SELECT 
                mh.CourseCode,
                mh.CourseName,
                mh.Credits,
                mh.Type,
                mh.Note,
                COUNT(DISTINCT tt.StudentID) as student_count
            FROM MonHoc mh
            LEFT JOIN TienTrinh tt ON mh.CourseCode = tt.CourseCode
            GROUP BY mh.CourseCode, mh.CourseName, mh.Credits, mh.Type, mh.Note
            ORDER BY mh.CourseCode
        """)
        courses = cursor.fetchall()
        conn.close()
        
        return render_template('admin_courses.html',
                             admin_name=session.get('admin_name'),
                             courses=courses)
    except Exception as e:
        flash(f'Lỗi tải danh sách môn học: {e}', 'error')
        return render_template('admin_courses.html',
                             admin_name=session.get('admin_name'),
                             courses=[])

@app.route('/admin/courses/add', methods=['GET', 'POST'])
def admin_add_course():
    """Thêm môn học mới"""
    if 'is_admin' not in session:
        return redirect(url_for('admin_login'))
    
    if request.method == 'GET':
        return render_template('admin_add_course.html',
                             admin_name=session.get('admin_name'))
    
    # POST
    course_code = request.form.get('course_code', '').strip().upper()
    course_name = request.form.get('course_name', '').strip()
    credits = request.form.get('credits', '0')
    course_type = request.form.get('course_type', 'Bắt buộc')
    note = request.form.get('note', '').strip()
    
    if not course_code or not course_name:
        flash('Vui lòng nhập đầy đủ Mã môn và Tên môn', 'error')
        return redirect(url_for('admin_add_course'))
    
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO MonHoc (CourseCode, CourseName, Credits, Type, Note)
            VALUES (%s, %s, %s, %s, %s)
        """, (course_code, course_name, int(credits), course_type, note))
        
        conn.commit()
        conn.close()
        
        flash(f'Đã thêm môn học {course_code} thành công!', 'success')
        return redirect(url_for('admin_courses'))
        
    except mysql.connector.Error as e:
        if 'Duplicate entry' in str(e):
            flash(f'Môn học {course_code} đã tồn tại!', 'error')
        else:
            flash(f'Lỗi thêm môn học: {e}', 'error')
        return redirect(url_for('admin_add_course'))

@app.route('/admin/courses/view/<course_code>')
def admin_view_course(course_code):
    """Xem chi tiết môn học - sinh viên nào học môn này"""
    if 'is_admin' not in session:
        return redirect(url_for('admin_login'))
    
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        
        # Thông tin môn học
        cursor.execute("SELECT * FROM MonHoc WHERE CourseCode = %s", (course_code,))
        course = cursor.fetchone()
        
        if not course:
            flash(f'Không tìm thấy môn học {course_code}', 'error')
            return redirect(url_for('admin_courses'))
        
        # Danh sách sinh viên học môn này, nhóm theo học kỳ
        cursor.execute("""
            SELECT StudentID, HoTen, Year, Semester, Score, Status
            FROM TienTrinh
            WHERE CourseCode = %s
            ORDER BY Year, Semester, StudentID
        """, (course_code,))
        students = cursor.fetchall()
        
        conn.close()
        
        return render_template('admin_course_detail.html',
                             admin_name=session.get('admin_name'),
                             course=course,
                             students=students)
    except Exception as e:
        flash(f'Lỗi tải thông tin môn học: {e}', 'error')
        return redirect(url_for('admin_courses'))

@app.route('/admin/courses/delete/<course_code>')
def admin_delete_course(course_code):
    """Xóa môn học"""
    if 'is_admin' not in session:
        return redirect(url_for('admin_login'))
    
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Xóa tiến trình liên quan trước
        cursor.execute("DELETE FROM TienTrinh WHERE CourseCode = %s", (course_code,))
        # Xóa tiên quyết
        cursor.execute("DELETE FROM TienQuyet WHERE CourseCode = %s OR PrerequisiteCode = %s", (course_code, course_code))
        # Xóa môn học
        cursor.execute("DELETE FROM MonHoc WHERE CourseCode = %s", (course_code,))
        
        conn.commit()
        conn.close()
        
        flash(f'Đã xóa môn học {course_code}', 'success')
    except Exception as e:
        flash(f'Lỗi xóa môn học: {e}', 'error')
    
    return redirect(url_for('admin_courses'))

if __name__ == '__main__':
    app.run(debug=True, port=5001, host='0.0.0.0')
