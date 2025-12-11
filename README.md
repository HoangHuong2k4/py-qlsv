# 🎓 HỆ THỐNG QUẢN LÝ HỌC TẬP & GỢI Ý MÔN HỌC

> Hệ thống gợi ý môn học thông minh sử dụng K-Means Clustering + Flask + MySQL

---

## ⚡ SETUP NHANH (3 BƯỚC)

### 1️⃣ Cài thư viện
```bash
pip3 install -r requirements.txt
```

### 2️⃣ Import database
```bash
mysql -u root < QuanLyHocTap_Full.sql
```

### 3️⃣ Chạy app
```bash
python3 app.py
```

**→ Mở:** http://localhost:5001

---

## 🔐 TÀI KHOẢN TEST

### 👤 SINH VIÊN (Test gợi ý môn học):

| Tài khoản | Mật khẩu | Năm | TC | Gợi ý |
|-----------|----------|-----|-------|-------|
| **B2200001** | B2200001 | Năm 2 | 52 TC | ✅ 4-5 môn |
| **B2200100** | B2200100 | Năm 1 | 13 TC | ✅ 5-8 môn |
| **B2200200** | B2200200 | Năm 3 | 70 TC | ✅ 5-8 môn |
| **B2200300** | B2200300 | Năm 4 | 120 TC | ✅ 5-8 môn |

### 🔐 ADMIN (Quản lý hệ thống):

| Username | Password | Quyền |
|----------|----------|-------|
| **admin** | **admin123** | Full quyền |

**Chức năng Admin:**
- ✅ Dashboard thống kê
- ✅ Quản lý sinh viên (thêm, xóa)
- ✅ Quản lý môn học (xem)

### ⚠️ Không có gợi ý:
- **B2100001** → Đã tốt nghiệp (156/156 TC)

---

## 📊 Database (987KB - ĐÃ CẬP NHẬT MỚI NHẤT)

```
✅ 107 sinh viên (với thông tin đầy đủ)
   - 92 sinh viên tốt nghiệp (Status = 'Tốt nghiệp') ← Dùng cho training K-Means
   - 15 sinh viên đang học (Status = 'Đang học') ← Dùng để đăng nhập và test
   - Thông tin cá nhân: Họ tên, giới tính, ngày sinh, email, SĐT
   - Thông tin học tập: Lớp, ngành, khoa, khóa học
   - Thông tin gia đình: Cha, mẹ, địa chỉ, SĐT
✅ 89 môn học (đã update từ MonHoc.sql)
✅ 5,200+ records tiến trình
✅ 1 tài khoản admin
✅ 7 bảng (Admin, SinhVien, MonHoc, TienTrinh, TienQuyet, HocKy, KeHoachHocTap)
✅ Cột Status trong SinhVien: Phân biệt 'Đang học' vs 'Tốt nghiệp'
```

---

## 🎯 Chức năng

### 👤 Dành cho Sinh viên:

1. **Đăng nhập** - Tab "Sinh viên" trên trang login
2. **Dashboard** - Tiến độ + Lịch sử + **5 Kế Hoạch Học Tập**
   - Biểu đồ tín chỉ theo học kỳ
   - Thông tin tổng quan (tổng TC, TB TC/kỳ)
3. **Profile** - Thông tin cá nhân
4. **Study Plan** - 5 Kế Hoạch Học Tập chi tiết
   - Mỗi kế hoạch có biểu đồ riêng
   - Chi tiết môn học theo từng học kỳ
   - Khoảng cách đến mỗi cluster
   - Download PDF cho mỗi kế hoạch

### 🔐 Dành cho Admin:

1. **Đăng nhập** - Tab "Admin" trên trang login
2. **Dashboard** - Thống kê (SV, môn học, tiến trình)
3. **Quản lý Sinh viên:** ✨ ĐẦY ĐỦ
   - Xem danh sách (103 SV)
   - Thêm sinh viên mới (form đầy đủ)
   - Xem chi tiết từng sinh viên:
     • Thông tin cá nhân (họ tên, giới tính, ngày sinh, email, SĐT)
     • Thông tin học tập (lớp, ngành, khoa, tổng TC)
     • Thông tin gia đình (cha, mẹ, địa chỉ, SĐT)
     • Tiến trình học tập theo từng học kỳ
   - Xóa sinh viên
4. **Quản lý Môn học:** ✨ ĐẦY ĐỦ
   - Xem danh sách (89 môn + số SV học)
   - Thêm môn học mới
   - Xem chi tiết môn học:
     • Thông tin môn (mã, tên, TC, loại)
     • Danh sách SV học môn này (theo học kỳ)
     • Điểm số và trạng thái
   - Xóa môn học

---

## 🤖 AI - Gợi ý thông minh

**Cách hoạt động:**
1. Phân tích lịch sử học tập của sinh viên
2. Tính khoảng cách đến 5 clusters (K-Means)
3. Lấy top student từ mỗi cluster (chỉ từ sinh viên tốt nghiệp)
4. Tạo 5 kế hoạch học tập dựa trên lịch sử của top students
5. Hiển thị biểu đồ tín chỉ cho mỗi kế hoạch

**K-Means Model (ĐÃ TRAIN MỚI):**
- ✅ 5 clusters (nhóm mô hình học tập)
- ✅ 89 features (tín chỉ mỗi môn)
- ✅ Train với 91 sinh viên tốt nghiệp (chỉ lấy từ Status = 'Tốt nghiệp')
- ✅ Phân bố clusters:
  - Cluster 0: 47 sinh viên (51.6%)
  - Cluster 1: 24 sinh viên (26.4%)
  - Cluster 2: 1 sinh viên (1.1%)
  - Cluster 3: 1 sinh viên (1.1%)
  - Cluster 4: 18 sinh viên (19.8%)
- ✅ File: `models/kmeans_model.pkl` + `models/kmeans_model_scaler.pkl`

**5 Kế Hoạch Học Tập:**
- Mỗi kế hoạch dựa trên top student của 1 cluster
- Hiển thị đầy đủ từ HK1 Y1 → HK1 Y5 (sinh viên mới B22)
- Gợi ý tiếp theo để đủ 156 TC (sinh viên cũ B21)
- Biểu đồ tín chỉ theo học kỳ (Chart.js)
- Download PDF cho mỗi kế hoạch

---

## 🌐 Routes

### Sinh viên:
```
/                    → Login (2 tabs: SV + Admin)
/dashboard           → Dashboard + Gợi ý
/profile             → Profile
/study-plan          → Kế hoạch
/logout              → Logout
```

### Admin:
```
/admin/login                    → Login admin
/admin/dashboard                → Dashboard thống kê
/admin/students                 → Quản lý SV (danh sách)
/admin/students/add             → Thêm SV mới
/admin/students/view/:id        → Xem chi tiết SV (đầy đủ)
/admin/students/delete/:id      → Xóa SV
/admin/courses                  → Quản lý môn học (danh sách)
/admin/courses/add              → Thêm môn mới
/admin/courses/view/:code       → Xem chi tiết môn (ai học)
/admin/courses/delete/:code     → Xóa môn
/admin/logout                   → Logout admin
```

**⚠️ Tất cả route (trừ login) YÊU CẦU ĐĂNG NHẬP**

---

## 📁 Files chính

```
README.md                      ← File này
INSTALL.md                     ← Hướng dẫn chi tiết
QuanLyHocTap_Full.sql         ← Database (987KB) - IMPORT NÀY
app.py                         ← Flask app
config.py                      ← DB config
create_demo_students.py        ← Tạo SV test
export_database.py             ← Script export DB
update_monhoc.py               ← Script update MonHoc từ MonHoc.sql
update_graduated_students.sql  ← Script update Status sinh viên
EXPLANATION_BIEU_DO_VA_DB.md   ← Giải thích biểu đồ & DB
TOM_TAT_CHO_WORD.md            ← Tóm tắt cho Word document
```

---

## 🐛 Xử lý lỗi

### ❌ "Can't connect to MySQL"
→ Start MySQL trong XAMPP

### ❌ "Port in use"
```bash
lsof -ti:5001 | xargs kill -9
python3 app.py
```

### ❌ "Không có gợi ý"
→ Dùng B2200001, KHÔNG dùng B2100001

### ❌ "Redirect về login"
→ Đăng nhập trước, sau đó mới vào các trang khác

---

## 🚀 Quick Start

```bash
# 1. Import DB
mysql -u root < QuanLyHocTap_Full.sql

# 2. Run app
python3 app.py

# 3. Test Sinh viên
open http://localhost:5001
Login: B2200001 / B2200001

# 4. Test Admin
open http://localhost:5001
Click tab "Admin"
Login: admin / admin123
```

---

## 🎮 TEST CÁC CHỨC NĂNG

### Test Sinh viên:
1. Login → B2200001 / B2200001
2. Dashboard → Thấy gợi ý 4-5 môn ✅
3. Profile → Thông tin SV
4. Study plan → Kế hoạch học tập

### Test Admin:
1. Login → Tab "Admin" → admin / admin123
2. Dashboard → Thống kê hệ thống
3. Students → Danh sách 103 SV
4. Add Student → Form thêm SV mới
5. Courses → Danh sách 51 môn

---

## ✅ Đã hoàn thành

- [x] Database setup (107 SV, 89 môn, 5,200+ records)
- [x] Cột Status phân biệt sinh viên tốt nghiệp (92) vs đang học (15)
- [x] K-Means training chỉ với sinh viên tốt nghiệp (91 SV)
- [x] 5 Kế hoạch học tập với biểu đồ tín chỉ
- [x] Download PDF cho mỗi kế hoạch
- [x] Tính khoảng cách đến 5 clusters
- [x] 4 sinh viên test có gợi ý
- [x] Tài khoản admin
- [x] Gợi ý AI hoạt động (K-Means clustering)
- [x] Quản lý sinh viên (CRUD)
- [x] Quản lý môn học (CRUD)
- [x] Login 2 tabs (SV + Admin)
- [x] Export database đầy đủ (987KB)

---

**🎉 Hệ thống hoàn chỉnh! Sẵn sàng test!**

**URL:** http://localhost:5001  
**Port:** 5001  
**Ngày cập nhật:** 11/12/2025

---

## 📚 TÀI LIỆU THAM KHẢO

- `EXPLANATION_BIEU_DO_VA_DB.md` - Giải thích chi tiết về biểu đồ tín chỉ và cấu trúc database
- `TOM_TAT_CHO_WORD.md` - Tóm tắt ngắn gọn để ghi vào Word document
- `README_BIEU_DO_DB.md` - Hướng dẫn về biểu đồ và database

---

## 🔧 SETUP NÂNG CAO

### Train lại K-Means model:
```bash
python3 -c "from recommender.train_model import train_kmeans; train_kmeans('data/student_data_100-2.xlsx', use_graduated_only=True)"
```

### Update database MonHoc:
```bash
python3 update_monhoc.py
```

### Export database:
```bash
python3 export_database.py
```
