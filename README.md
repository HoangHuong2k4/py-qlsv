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

## 📊 Database (983KB - ĐÃ CẬP NHẬT)

```
✅ 103 sinh viên (với thông tin đầy đủ)
   - Thông tin cá nhân: Họ tên, giới tính, ngày sinh, email, SĐT
   - Thông tin học tập: Lớp, ngành, khoa, khóa học
   - Thông tin gia đình: Cha, mẹ, địa chỉ, SĐT
✅ 51 môn học
✅ 5,209 records tiến trình
✅ 1 tài khoản admin
✅ 7 bảng (Admin, SinhVien, MonHoc, TienTrinh, TienQuyet, HocKy, KeHoachHocTap)
```

---

## 🎯 Chức năng

### 👤 Dành cho Sinh viên:

1. **Đăng nhập** - Tab "Sinh viên" trên trang login
2. **Dashboard** - Tiến độ + Lịch sử + **Gợi ý AI**
3. **Profile** - Thông tin cá nhân
4. **Study Plan** - Kế hoạch học tập

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
   - Xem danh sách (51 môn + số SV học)
   - Thêm môn học mới
   - Xem chi tiết môn học:
     • Thông tin môn (mã, tên, TC, loại)
     • Danh sách SV học môn này (theo học kỳ)
     • Điểm số và trạng thái
   - Xóa môn học

---

## 🤖 AI - Gợi ý thông minh

**Cách hoạt động:**
1. Phân tích lịch sử học tập
2. Tìm sinh viên tốt nghiệp đúng hạn tương tự
3. Xem họ học gì ở kỳ tiếp theo
4. Gợi ý top 5-8 môn phù hợp

**K-Means Model:**
- 5 clusters (nhóm mô hình học tập)
- 53 features (tín chỉ mỗi môn)
- File: `models/kmeans_model.pkl`

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
README.md                  ← File này
INSTALL.md                 ← Hướng dẫn chi tiết
QuanLyHocTap_Full.sql     ← Database (965KB) - IMPORT NÀY
app.py                     ← Flask app
config.py                  ← DB config
create_demo_students.py    ← Tạo SV test
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

- [x] Database setup (103 SV, 51 môn, 5,209 records)
- [x] 4 sinh viên test có gợi ý
- [x] Tài khoản admin
- [x] Gợi ý AI hoạt động
- [x] Quản lý sinh viên (CRUD)
- [x] Quản lý môn học
- [x] Login 2 tabs (SV + Admin)
- [x] Export database đầy đủ

---

**🎉 Hệ thống hoàn chỉnh! Sẵn sàng test!**

**URL:** http://localhost:5001  
**Port:** 5001  
**Ngày:** 03/12/2025
