-- Migration: Cập nhật bảng TienTrinh để phù hợp với dữ liệu từ Excel
-- Thêm các cột GPA, OnTime, Graduated

USE QuanLyHocTap;

-- Thêm cột GPA nếu chưa có (tương thích MySQL/MariaDB cũ)
SET @exist := (SELECT COUNT(*) FROM information_schema.COLUMNS 
WHERE TABLE_SCHEMA = 'QuanLyHocTap' AND TABLE_NAME = 'TienTrinh' AND COLUMN_NAME = 'GPA');
SET @sqlstmt := IF(@exist > 0, 'SELECT ''Column GPA already exists''', 
'ALTER TABLE TienTrinh ADD COLUMN GPA DECIMAL(3,2) NULL COMMENT ''GPA tích lũy'' AFTER Score');
PREPARE stmt FROM @sqlstmt;
EXECUTE stmt;

-- Thêm cột OnTime nếu chưa có
SET @exist := (SELECT COUNT(*) FROM information_schema.COLUMNS 
WHERE TABLE_SCHEMA = 'QuanLyHocTap' AND TABLE_NAME = 'TienTrinh' AND COLUMN_NAME = 'OnTime');
SET @sqlstmt := IF(@exist > 0, 'SELECT ''Column OnTime already exists''', 
'ALTER TABLE TienTrinh ADD COLUMN OnTime BOOLEAN DEFAULT TRUE COMMENT ''Học đúng tiến độ'' AFTER Score');
PREPARE stmt FROM @sqlstmt;
EXECUTE stmt;

-- Thêm cột Graduated nếu chưa có
SET @exist := (SELECT COUNT(*) FROM information_schema.COLUMNS 
WHERE TABLE_SCHEMA = 'QuanLyHocTap' AND TABLE_NAME = 'TienTrinh' AND COLUMN_NAME = 'Graduated');
SET @sqlstmt := IF(@exist > 0, 'SELECT ''Column Graduated already exists''', 
'ALTER TABLE TienTrinh ADD COLUMN Graduated BOOLEAN DEFAULT FALSE COMMENT ''Đã tốt nghiệp'' AFTER Score');
PREPARE stmt FROM @sqlstmt;
EXECUTE stmt;

