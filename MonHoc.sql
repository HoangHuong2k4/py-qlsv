-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Máy chủ: localhost
-- Thời gian đã tạo: Th12 04, 2025 lúc 04:18 PM
-- Phiên bản máy phục vụ: 10.4.28-MariaDB
-- Phiên bản PHP: 8.2.4

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Cơ sở dữ liệu: `QuanLyHocTap`
--

-- --------------------------------------------------------

--
-- Cấu trúc bảng cho bảng `MonHoc`
--

CREATE TABLE `MonHoc` (
  `id` int(11) NOT NULL,
  `CourseCode` varchar(10) NOT NULL,
  `CourseName` varchar(200) NOT NULL,
  `Credits` int(11) NOT NULL,
  `Type` enum('Bắt buộc','Tự chọn','Cơ sở','Chuyên ngành') DEFAULT NULL,
  `Note` text DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Đang đổ dữ liệu cho bảng `MonHoc`
--

INSERT INTO `MonHoc` (`id`, `CourseCode`, `CourseName`, `Credits`, `Type`, `Note`) VALUES
(1, 'CC009', 'TOEIC', 10, 'Bắt buộc', 'Môn bắt buộc, Tiên quyết TC002'),
(2, 'CT100', 'Kỹ năng học đại học', 2, 'Bắt buộc', 'Môn bắt buộc'),
(3, 'CT101', 'Lập trình căn bản', 4, 'Cơ sở', 'Môn cơ sở nền tảng'),
(4, 'CT112', 'Mạng máy tính', 3, 'Chuyên ngành', 'Tiên quyết CT178'),
(5, 'CT121', 'Tin học lý thuyết', 3, 'Tự chọn', NULL),
(6, 'CT124', 'Phương pháp tính – CNTT', 2, 'Tự chọn', NULL),
(7, 'CT126', 'Lý thuyết xếp hàng', 2, 'Tự chọn', 'Môn tự chọn'),
(8, 'CT127', 'Lý thuyết thông tin', 2, 'Tự chọn', 'Môn tự chọn'),
(9, 'CT172', 'Toán rời rạc', 4, 'Cơ sở', 'Kiến thức cơ bản'),
(10, 'CT173', 'Kiến trúc máy tính', 3, 'Chuyên ngành', 'Môn cơ sở ngành'),
(11, 'CT174', 'Phân tích và thiết kế thuật toán', 3, 'Chuyên ngành', 'Tiên quyết CT177'),
(12, 'CT175', 'Lý thuyết đồ thị', 3, 'Bắt buộc', 'Môn bắt buộc'),
(13, 'CT176', 'Lập trình hướng đối tượng', 3, 'Chuyên ngành', 'Tiên quyết CT101'),
(14, 'CT177', 'Cấu trúc dữ liệu', 3, 'Chuyên ngành', 'Tiên quyết CT173'),
(15, 'CT178', 'Nguyên lý hệ điều hành', 3, 'Chuyên ngành', 'Tiên quyết CT173'),
(16, 'CT179', 'Quản trị hệ thống', 3, 'Bắt buộc', 'Môn bắt buộc'),
(17, 'CT180', 'Cơ sở dữ liệu', 3, 'Chuyên ngành', 'Tiên quyết CT177'),
(18, 'CT182', 'Ngôn ngữ mô hình hoá', 3, 'Bắt buộc', 'Môn bắt buộc'),
(19, 'CT188', 'Nhập môn lập trình Web', 3, 'Bắt buộc', 'Môn bắt buộc'),
(20, 'CT190', 'Nhập môn trí tuệ nhân tạo', 2, 'Bắt buộc', 'Môn bắt buộc'),
(21, 'CT200', 'Nền tảng công nghệ thông tin', 4, 'Cơ sở', 'Kiến thức nhập môn CNTT'),
(22, 'CT202', 'Nguyên lý máy học', 3, 'Tự chọn', NULL),
(23, 'CT205', 'Quản trị cơ sở dữ liệu', 3, 'Tự chọn', NULL),
(24, 'CT206', 'Phát triển ứng dụng trên Linux', 3, 'Tự chọn', NULL),
(25, 'CT207', 'Phát triển phần mềm mã nguồn mở', 3, 'Tự chọn', NULL),
(26, 'CT211', 'An ninh mạng', 3, 'Chuyên ngành', 'Tiên quyết CT112'),
(27, 'CT212', 'Quản trị mạng', 3, 'Chuyên ngành', 'Tiên quyết CT112'),
(28, 'CT221', 'Lập trình mạng', 3, 'Chuyên ngành', 'Tiên quyết CT112, CT176'),
(29, 'CT222', 'An toàn hệ thống', 3, 'Chuyên ngành', 'Tiên quyết CT172'),
(30, 'CT223', 'Quản lý dự án phần mềm', 3, 'Tự chọn', NULL),
(31, 'CT224', 'Công nghệ J2EE', 2, 'Tự chọn', NULL),
(32, 'CT225', 'Lập trình Python', 2, 'Chuyên ngành', 'Tiên quyết CT176'),
(33, 'CT226', 'Niên luận cơ sở ngành mạng máy tính và truyền thông', 3, 'Bắt buộc', '>=90 TC'),
(34, 'CT227', 'Kỹ thuật phát hiện và tấn công mạng', 3, 'Tự chọn', 'Môn tự chọn'),
(35, 'CT228', 'Tường lửa', 3, 'Tự chọn', NULL),
(36, 'CT229', 'Bảo mật website', 2, 'Tự chọn', NULL),
(37, 'CT230', 'Phát triển ứng dụng hướng dịch vụ', 3, 'Tự chọn', NULL),
(38, 'CT231', 'Lập trình song song', 3, 'Tự chọn', NULL),
(39, 'CT232', 'Đánh giá hiệu năng mạng', 3, 'Tự chọn', 'Môn tự chọn'),
(40, 'CT233', 'Điện toán đám mây', 3, 'Tự chọn', NULL),
(41, 'CT234', 'Phát triển phần mềm nhúng', 3, 'Tự chọn', NULL),
(42, 'CT235', 'Quản trị mang trên MS Windows', 3, 'Tự chọn', NULL),
(43, 'CT237', 'Nguyên lý hệ quản trị cơ sở dữ liệu', 3, 'Tự chọn', NULL),
(44, 'CT238', 'Phân lớp dữ liệu lớn', 3, 'Tự chọn', NULL),
(45, 'CT251', 'Phát triển ứng dụng trên Windows', 3, 'Tự chọn', NULL),
(46, 'CT272', 'Thương mại điện tử -CNTT', 3, 'Tự chọn', NULL),
(47, 'CT273', 'Giao diện người - máy', 3, 'Tự chọn', NULL),
(48, 'CT274', 'Lập trình cho thiết bị di động', 3, 'Tự chọn', NULL),
(49, 'CT296', 'Phân tích và thiết kế hệ thống thông tin', 3, 'Bắt buộc', 'Môn bắt buộc'),
(50, 'CT332', 'Trí tuệ nhân tạo', 3, 'Tự chọn', NULL),
(51, 'CT335', 'Thiết kế và cài đặt mạng', 3, 'Chuyên ngành', 'Tiên quyết CT112'),
(52, 'CT338', 'Mạng không dây và di động', 2, 'Tự chọn', NULL),
(53, 'CT344', 'Giải quyết sự cố mạng', 2, 'Tự chọn', NULL),
(54, 'CT428', 'Lập trình Web', 3, 'Chuyên ngành', 'Tiên quyết CT180, CT176'),
(55, 'CT439', 'Niên luận Mạng máy tính và truyền thông', 3, 'Bắt buộc', 'Môn bắt buộc, Tiên quyết CT226'),
(56, 'CT476', 'Thực tập thực tế - TT&MMT', 3, 'Bắt buộc', '>= 120 TC'),
(57, 'CT482', 'Xử lý dữ liệu lớn', 3, 'Tự chọn', NULL),
(58, 'CT507', 'Tiểu luận tốt nghiệp – TT&MMT', 6, 'Bắt buộc', '≥ 120 TC'),
(59, 'CT555', 'Luận văn', 10, NULL, NULL),
(60, 'FL001', 'Pháp văn căn bản 1', 4, 'Tự chọn', NULL),
(61, 'FL002', 'Pháp văn căn bản 2', 3, 'Tự chọn', NULL),
(62, 'FL003', 'Pháp văn căn bản 3', 3, 'Tự chọn', NULL),
(63, 'KL001', 'Pháp luật đại cương', 2, 'Bắt buộc', 'Môn chung'),
(64, 'KN001', 'Kỹ năng mềm', 2, 'Tự chọn', NULL),
(65, 'KN002', 'Đổi mới sáng tạo và khởi nghiệp', 2, 'Tự chọn', NULL),
(66, 'ML007', 'Logic học đại cương', 2, 'Tự chọn', NULL),
(67, 'ML014', 'Triết học Mác – Lênin', 3, 'Bắt buộc', 'Lý luận chính trị'),
(68, 'ML016', 'Kinh tế chính trị Mác – Lênin', 2, 'Bắt buộc', 'Tiên quyết ML014'),
(69, 'ML018', 'Chủ nghĩa xã hội khoa học', 2, 'Bắt buộc', 'Tiên quyết ML016'),
(70, 'ML019', 'Lịch sử Đảng Cộng sản Việt Nam', 2, 'Bắt buộc', 'Tiên quyết ML018'),
(71, 'ML021', 'Tư tưởng Hồ Chí Minh', 2, 'Bắt buộc', 'Tiên quyết ML019'),
(72, 'MTH201', 'Xác suất thống kê', 3, 'Cơ sở', 'Môn cơ sở'),
(73, 'QP010', 'Giáo dục quốc phòng và An ninh 1', 2, 'Bắt buộc', 'Môn bắt buộc'),
(74, 'QP011', 'Giáo dục quốc phòng và An ninh 2', 2, 'Bắt buộc', 'Môn bắt buộc'),
(75, 'QP012', 'Giáo dục quốc phòng và An ninh 3', 2, 'Bắt buộc', 'Môn bắt buộc'),
(76, 'QP013', 'Giáo dục quốc phòng và An ninh 4', 2, 'Bắt buộc', 'Môn bắt buộc'),
(77, 'TC001', 'Điền kinh 1', 1, 'Bắt buộc', 'Môn bắt buộc'),
(78, 'TC002', 'Điền kinh 2', 1, 'Bắt buộc', 'Môn bắt buộc, Tiên quyết TC001'),
(79, 'TC024', 'Điền kinh 3', 1, 'Bắt buộc', 'Môn bắt buộc, Tiên quyết TC002'),
(80, 'TC100', 'Giáo dục thể chất 1', 1, 'Tự chọn', NULL),
(81, 'TN001', 'Vi - tích phân A1', 3, 'Cơ sở', 'Môn cơ sở'),
(82, 'TN002', 'Vi - tích phân A2', 4, 'Bắt buộc', 'Môn bắt buộc, Tiên quyết TN001'),
(83, 'TN012', 'Đại số tuyến tính và hình học', 4, 'Cơ sở', 'Môn cơ sở'),
(84, 'XH011', 'Cơ sở văn hoá Việt Nam', 2, 'Tự chọn', 'Môn tự chọn'),
(85, 'XH012', 'Tiếng Việt thực hành', 2, 'Tự chọn', NULL),
(86, 'XH014', 'Văn bản và lưu trữ đại cương', 2, 'Tự chọn', NULL),
(87, 'XH023', 'Anh văn căn bản 1', 4, 'Tự chọn', NULL),
(88, 'XH024', 'Anh văn căn bản 2', 3, 'Tự chọn', NULL),
(89, 'XH025', 'Anh văn căn bản 3', 3, 'Tự chọn', NULL),
(90, 'XH028', 'Xã hội học đại cương', 2, 'Tự chọn', NULL);

--
-- Chỉ mục cho các bảng đã đổ
--

--
-- Chỉ mục cho bảng `MonHoc`
--
ALTER TABLE `MonHoc`
  ADD PRIMARY KEY (`CourseCode`),
  ADD UNIQUE KEY `id` (`id`);

--
-- AUTO_INCREMENT cho các bảng đã đổ
--

--
-- AUTO_INCREMENT cho bảng `MonHoc`
--
ALTER TABLE `MonHoc`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=91;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
