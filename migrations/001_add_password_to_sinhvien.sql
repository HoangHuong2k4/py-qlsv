-- Migration: add Password column to SinhVien (nullable)
-- Run on your MySQL/MariaDB instance connected to the QuanLyHocTap database.
-- Format: pbkdf2:sha256:NUM_ITERATIONS$SALT$HASH - needs 260 chars to be safe

ALTER TABLE `SinhVien`
  ADD COLUMN `Password` VARCHAR(260) NOT NULL COMMENT 'pbkdf2:sha256 hash';

-- After adding the column, use the provided script scripts/set_password.py to set hashed passwords for accounts.
