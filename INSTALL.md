# ⚡ HƯỚNG DẪN CÀI ĐẶT - 3 PHÚT

## 📋 Yêu cầu
- Python 3.8+
- MySQL (XAMPP)

---

## 🚀 3 BƯỚC SETUP

### 1️⃣ Cài thư viện
```bash
pip3 install -r requirements.txt
```

### 2️⃣ Import database
```bash
# Cách 1: Dùng command line
mysql -u root < QuanLyHocTap_Full.sql

# Cách 2: Dùng phpMyAdmin
# - Mở http://localhost/phpmyadmin
# - Import file QuanLyHocTap_Full.sql
```

### 3️⃣ Chạy app
```bash
python3 app.py
```

**→ Mở:** http://localhost:5001

---

## 🔐 TÀI KHOẢN TEST

### ✅ CÓ GỢI Ý (Dùng để test):
```
B2200001 / B2200001  ← Năm 2 (52 TC) - KHUYẾN NGHỊ
B2200100 / B2200100  ← Năm 1 (13 TC)
B2200200 / B2200200  ← Năm 3 (70 TC)
B2200300 / B2200300  ← Năm 4 (120 TC)
```

### ❌ KHÔNG có gợi ý (Đã tốt nghiệp):
```
B2100001 / B2100001  ← Đã hoàn thành 156/156 TC
```

**💡 Quy tắc:** Mật khẩu = Mã sinh viên

---

## 🎯 TEST NHANH

```bash
# 1. Mở browser
open http://localhost:5001

# 2. Đăng nhập
Tài khoản: B2200001
Mật khẩu: B2200001

# 3. Xem Dashboard
→ Thấy tiến độ: 52/156 TC
→ Thấy lịch sử: 20 môn
→ Thấy "5 Kế Hoạch Học Tập" với biểu đồ tín chỉ
→ Click "Xem Chi Tiết" để xem 5 kế hoạch đầy đủ
→ Mỗi kế hoạch có nút "📥 Tải PDF"
```

---

## 🐛 Lỗi thường gặp

### ❌ "Can't connect to MySQL"
→ Start MySQL trong XAMPP

### ❌ "Port 5001 in use"
```bash
lsof -ti:5001 | xargs kill -9
python3 app.py
```

### ❌ "Không có gợi ý"
→ Dùng B2200001 (KHÔNG dùng B2100001)

### ❌ "/study-plan redirect về login"
→ Đăng nhập trước, sau đó mới vào /study-plan

---

## 📁 Files quan trọng

```
QuanLyHocTap_Full.sql    ← Database đầy đủ (IMPORT)
app.py                   ← Flask app
config.py                ← Cấu hình DB
README.md                ← File này
```

---

## 📊 Database Structure

```
SinhVien (107 sinh viên)
├── StudentID, Status (Đang học/Tốt nghiệp/Nghỉ học) ← MỚI
├── HoTen, Password, Email
└── GioiTinh, NgaySinh, Lop, Nganh, Khoa
   - 92 sinh viên tốt nghiệp (dùng cho training K-Means)
   - 15 sinh viên đang học (dùng để đăng nhập)

MonHoc (89 môn) ← ĐÃ UPDATE
├── CourseCode, CourseName, Credits
└── Type (Bắt buộc/Tự chọn/Cơ sở/Chuyên ngành)

TienTrinh (5,200+ records)
├── StudentID, Year, Semester
├── CourseCode, Score, GPA, Credits
└── Status (Đã học/Đang học/Chưa học)

TienQuyet (23 ràng buộc tiên quyết)
HocKy (15 học kỳ: 5 năm × 3 kỳ)
KeHoachHocTap (Kế hoạch học tập)
```

---

## ⚙️ Config

### Database (config.py):
```python
DB_CONFIG = {
    'host': '127.0.0.1',
    'user': 'root',
    'password': '',
    'database': 'QuanLyHocTap'
}
```

### Port (app.py):
```python
app.run(debug=True, port=5001)  # Đổi port tại đây
```

---

## 🎮 Các route chính

| URL | Login? | Mô tả |
|-----|--------|-------|
| `/` | ❌ | Trang đăng nhập |
| `/dashboard` | ✅ | Dashboard + Gợi ý |
| `/profile` | ✅ | Thông tin SV |
| `/study-plan` | ✅ | Kế hoạch học tập |
| `/logout` | ❌ | Đăng xuất |

---

## ✅ Checklist

- [ ] MySQL đã start (XAMPP)
- [ ] Import QuanLyHocTap_Full.sql thành công (987KB)
- [ ] Cài pip3 install -r requirements.txt
- [ ] (Tùy chọn) Train lại K-Means model:
  ```bash
  python3 -c "from recommender.train_model import train_kmeans; train_kmeans('data/student_data_100-2.xlsx', use_graduated_only=True)"
  ```
- [ ] Chạy python3 app.py
- [ ] Truy cập http://localhost:5001
- [ ] Đăng nhập B2200001/B2200001
- [ ] Thấy 5 Kế hoạch học tập trên Dashboard
- [ ] Xem biểu đồ tín chỉ trong mỗi kế hoạch
- [ ] Test download PDF cho mỗi kế hoạch

---

## 🔧 SETUP NÂNG CAO

### Train lại K-Means model (chỉ với sinh viên tốt nghiệp):
```bash
python3 -c "from recommender.train_model import train_kmeans; train_kmeans('data/student_data_100-2.xlsx', use_graduated_only=True)"
```

### Update database MonHoc từ MonHoc.sql:
```bash
python3 update_monhoc.py
```

### Export database mới nhất:
```bash
python3 export_database.py
```

---

**🎉 Hoàn thành! Chúc test tốt!**

Ngày cập nhật: 11/12/2025 | Port: 5001 | DB: QuanLyHocTap (987KB)

