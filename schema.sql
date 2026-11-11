-- Database: placement_db
CREATE DATABASE IF NOT EXISTS `placement_db`;
USE `placement_db`;

-- 1. Students Table
CREATE TABLE IF NOT EXISTS `students` (
    `student_id` INT AUTO_INCREMENT PRIMARY KEY,
    `roll_number` VARCHAR(30) NOT NULL UNIQUE,
    `full_name` VARCHAR(100) NOT NULL,
    `department` ENUM('Computer Science', 'Information Technology', 'Electronics & Comm', 'Mechanical', 'Civil', 'Electrical') NOT NULL,
    `graduation_year` INT NOT NULL,
    `cgpa` DECIMAL(3, 2) NOT NULL CHECK (`cgpa` >= 0.0 AND `cgpa` <= 10.0),
    `active_backlogs` INT DEFAULT 0,
    `is_eligible` BOOLEAN DEFAULT TRUE,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Skills Table
CREATE TABLE IF NOT EXISTS `skills` (
    `skill_id` INT AUTO_INCREMENT PRIMARY KEY,
    `skill_name` VARCHAR(50) NOT NULL UNIQUE
);

-- 3. Student Skills Mapping (Many-to-Many)
CREATE TABLE IF NOT EXISTS `student_skills` (
    `student_id` INT NOT NULL,
    `skill_id` INT NOT NULL,
    PRIMARY KEY (`student_id`, `skill_id`),
    FOREIGN KEY (`student_id`) REFERENCES `students`(`student_id`) ON DELETE CASCADE,
    FOREIGN KEY (`skill_id`) REFERENCES `skills`(`skill_id`) ON DELETE CASCADE
);

-- 4. Placements Table
CREATE TABLE IF NOT EXISTS `placements` (
    `placement_id` INT AUTO_INCREMENT PRIMARY KEY,
    `student_id` INT NOT NULL,
    `company_name` VARCHAR(100) NOT NULL,
    `role` VARCHAR(100) NOT NULL,
    `package_lpa` DECIMAL(5, 2) NOT NULL CHECK (`package_lpa` > 0),
    `placement_date` DATE NOT NULL,
    `status` ENUM('Placed', 'In Process', 'Offer Accepted', 'Offer Rejected') NOT NULL DEFAULT 'Offer Accepted',
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (`student_id`) REFERENCES `students`(`student_id`) ON DELETE CASCADE
);

-- 5. Users Authentication Table
CREATE TABLE IF NOT EXISTS `users` (
    `user_id` INT AUTO_INCREMENT PRIMARY KEY,
    `username` VARCHAR(50) NOT NULL UNIQUE,
    `email` VARCHAR(100) NOT NULL UNIQUE,
    `password_hash` VARCHAR(255) NOT NULL,
    `role` VARCHAR(50) DEFAULT 'Admin',
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX idx_student_dept_year ON `students`(`department`, `graduation_year`);
CREATE INDEX idx_placement_status ON `placements`(`status`);
