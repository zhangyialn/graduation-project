/*
 Navicat Premium Data Transfer

 Source Server         : mybatis
 Source Server Type    : MySQL
 Source Server Version : 80040 (8.0.40)
 Source Host           : localhost:3306
 Source Schema         : graduation-project

 Target Server Type    : MySQL
 Target Server Version : 80040 (8.0.40)
 File Encoding         : 65001

 Date: 21/03/2026 20:07:50
*/

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ====================
-- 用户导入批次（Excel导入追踪）
-- ====================
DROP TABLE IF EXISTS `user_import_batches`;
CREATE TABLE `user_import_batches`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `operator_id` int NULL DEFAULT NULL,
  `file_name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `total_rows` int NOT NULL DEFAULT 0,
  `success_rows` int NOT NULL DEFAULT 0,
  `failed_rows` int NOT NULL DEFAULT 0,
  `remark` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) USING BTREE,
  KEY `idx_operator_id` (`operator_id`) USING BTREE,
  KEY `idx_created_at` (`created_at`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci;

BEGIN;
COMMIT;

-- ====================
-- 用户表（逻辑外键：department_id / created_by / import_batch_id）
-- ====================
DROP TABLE IF EXISTS `users`;
CREATE TABLE `users`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `username` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `password` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `name` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `email` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `phone` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `department_id` int NULL DEFAULT NULL,
  `role` enum('user','driver','approver','dispatcher','leader','admin') CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL DEFAULT 'user',
  `import_batch_id` int NULL DEFAULT NULL,
  `is_active` tinyint(1) NOT NULL DEFAULT 1,
  `is_deleted` tinyint(1) NOT NULL DEFAULT 0,
  `created_by` int NULL DEFAULT NULL,
  `updated_by` int NULL DEFAULT NULL,
  `deleted_by` int NULL DEFAULT NULL,
  `deleted_at` datetime NULL DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `uk_users_username`(`username` ASC) USING BTREE,
  UNIQUE INDEX `uk_users_phone`(`phone` ASC) USING BTREE,
  UNIQUE INDEX `uk_users_email`(`email` ASC) USING BTREE,
  KEY `idx_users_department_id` (`department_id`) USING BTREE,
  KEY `idx_users_role` (`role`) USING BTREE,
  KEY `idx_users_import_batch_id` (`import_batch_id`) USING BTREE,
  KEY `idx_users_created_by` (`created_by`) USING BTREE,
  KEY `idx_users_is_deleted` (`is_deleted`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci;

BEGIN;
COMMIT;

-- ====================
-- 部门表（逻辑外键：leader_id -> users.id）
-- ====================
DROP TABLE IF EXISTS `departments`;
CREATE TABLE `departments`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `leader_id` int NULL DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `uk_departments_name`(`name` ASC) USING BTREE,
  KEY `idx_departments_leader_id` (`leader_id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci;

BEGIN;
COMMIT;

-- ====================
-- 车辆表（逻辑外键：created_by/deleted_by -> users.id）
-- ====================
DROP TABLE IF EXISTS `vehicles`;
CREATE TABLE `vehicles`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `plate_number` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `model` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `brand` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `color` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `seat_count` int NOT NULL DEFAULT 5,
  `status` enum('available','in_use','maintenance','unavailable') CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT 'available',
  `purchase_date` date NOT NULL,
  `last_maintenance_date` date NULL DEFAULT NULL,
  `annual_inspection_date` date NULL DEFAULT NULL,
  `fuel_type` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `fuel_consumption_per_100km` decimal(6,2) NULL DEFAULT NULL,
  `is_deleted` tinyint(1) NOT NULL DEFAULT 0,
  `created_by` int NULL DEFAULT NULL,
  `deleted_by` int NULL DEFAULT NULL,
  `deleted_at` datetime NULL DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `uk_vehicles_plate_number`(`plate_number` ASC) USING BTREE,
  KEY `idx_vehicles_status` (`status`) USING BTREE,
  KEY `idx_vehicles_fuel_type` (`fuel_type`) USING BTREE,
  KEY `idx_vehicles_is_deleted` (`is_deleted`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci;

BEGIN;
COMMIT;

-- ====================
-- 司机表（逻辑外键：created_by/deleted_by -> users.id）
-- ====================
DROP TABLE IF EXISTS `drivers`;
CREATE TABLE `drivers`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `vehicle_id` int NOT NULL,
  `name` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `phone` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `license_number` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `status` enum('available','busy','unavailable') CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT 'available',
  `hire_date` date NULL DEFAULT NULL,
  `is_deleted` tinyint(1) NOT NULL DEFAULT 0,
  `created_by` int NULL DEFAULT NULL,
  `deleted_by` int NULL DEFAULT NULL,
  `deleted_at` datetime NULL DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `uk_drivers_user_id`(`user_id` ASC) USING BTREE,
  UNIQUE INDEX `uk_drivers_vehicle_id`(`vehicle_id` ASC) USING BTREE,
  UNIQUE INDEX `uk_drivers_license_number`(`license_number` ASC) USING BTREE,
  UNIQUE INDEX `uk_drivers_phone`(`phone` ASC) USING BTREE,
  KEY `idx_drivers_status` (`status`) USING BTREE,
  KEY `idx_drivers_is_deleted` (`is_deleted`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci;

BEGIN;
COMMIT;

-- ====================
-- 用车申请表（逻辑外键：applicant_id/department_id/approved_by）
-- ====================
DROP TABLE IF EXISTS `car_applications`;
CREATE TABLE `car_applications`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `applicant_id` int NOT NULL,
  `department_id` int NULL DEFAULT NULL,
  `driver_id` int NOT NULL,
  `start_point` varchar(120) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `start_time` datetime NOT NULL,
  `end_time` datetime NOT NULL,
  `purpose` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `destination` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `passenger_count` int NOT NULL,
  `expected_distance_km` decimal(10, 2) NULL DEFAULT NULL,
  `status` enum('pending','approved','rejected','dispatched','completed','cancelled') CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT 'pending',
  `approval_comment` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `approved_by` int NULL DEFAULT NULL,
  `approved_at` datetime NULL DEFAULT NULL,
  `cancelled_by` int NULL DEFAULT NULL,
  `cancelled_at` datetime NULL DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) USING BTREE,
  KEY `idx_car_applications_applicant_id` (`applicant_id`) USING BTREE,
  KEY `idx_car_applications_department_id` (`department_id`) USING BTREE,
  KEY `idx_car_applications_driver_id` (`driver_id`) USING BTREE,
  KEY `idx_car_applications_status` (`status`) USING BTREE,
  KEY `idx_car_applications_start_time` (`start_time`) USING BTREE,
  KEY `idx_car_applications_created_at` (`created_at`) USING BTREE,
  KEY `idx_car_applications_approved_by` (`approved_by`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci;

BEGIN;
COMMIT;

-- ====================
-- 审批记录表（逻辑外键：application_id/approver_id）
-- ====================
DROP TABLE IF EXISTS `approvals`;
CREATE TABLE `approvals`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `application_id` int NOT NULL,
  `approver_id` int NOT NULL,
  `status` enum('approved','rejected') CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `comment` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `approved_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) USING BTREE,
  KEY `idx_approvals_application_id` (`application_id`) USING BTREE,
  KEY `idx_approvals_approver_id` (`approver_id`) USING BTREE,
  KEY `idx_approvals_status` (`status`) USING BTREE,
  KEY `idx_approvals_approved_at` (`approved_at`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci;

BEGIN;
COMMIT;

-- ====================
-- 调度表（逻辑外键：application_id/vehicle_id/driver_id/dispatcher_id）
-- ====================
DROP TABLE IF EXISTS `dispatches`;
CREATE TABLE `dispatches`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `application_id` int NOT NULL,
  `vehicle_id` int NOT NULL,
  `driver_id` int NOT NULL,
  `dispatcher_id` int NOT NULL,
  `dispatch_time` datetime NULL DEFAULT CURRENT_TIMESTAMP,
  `status` enum('scheduled','in_progress','completed','cancelled') CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT 'scheduled',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) USING BTREE,
  KEY `idx_dispatches_application_id` (`application_id`) USING BTREE,
  KEY `idx_dispatches_vehicle_id` (`vehicle_id`) USING BTREE,
  KEY `idx_dispatches_driver_id` (`driver_id`) USING BTREE,
  KEY `idx_dispatches_dispatcher_id` (`dispatcher_id`) USING BTREE,
  KEY `idx_dispatches_status` (`status`) USING BTREE,
  KEY `idx_dispatches_dispatch_time` (`dispatch_time`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci;

BEGIN;
COMMIT;

-- ====================
-- 出车记录表（逻辑外键：dispatch_id/ended_by）
-- ====================
DROP TABLE IF EXISTS `trips`;
CREATE TABLE `trips`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `dispatch_id` int NOT NULL,
  `start_mileage` decimal(10, 2) NOT NULL,
  `end_mileage` decimal(10, 2) NULL DEFAULT NULL,
  `distance_km` decimal(10, 2) NULL DEFAULT NULL,
  `start_fuel` decimal(10, 2) NOT NULL,
  `end_fuel` decimal(10, 2) NULL DEFAULT NULL,
  `actual_start_time` datetime NULL DEFAULT NULL,
  `actual_end_time` datetime NULL DEFAULT NULL,
  `ended_by` int NULL DEFAULT NULL,
  `status` enum('started','completed') CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT 'started',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) USING BTREE,
  KEY `idx_trips_dispatch_id` (`dispatch_id`) USING BTREE,
  KEY `idx_trips_status` (`status`) USING BTREE,
  KEY `idx_trips_actual_start_time` (`actual_start_time`) USING BTREE,
  KEY `idx_trips_actual_end_time` (`actual_end_time`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci;

BEGIN;
COMMIT;

-- ====================
-- 费用表（可视化统计友好）
-- 费用建议：total_cost = fuel_cost + maintenance_cost + other_cost
-- fuel_cost 可由 mileage_km * cost_per_km 计算
-- ====================
DROP TABLE IF EXISTS `expenses`;
CREATE TABLE `expenses`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `trip_id` int NOT NULL,
  `mileage_km` decimal(10, 2) NOT NULL DEFAULT 0.00,
  `cost_per_km` decimal(10, 4) NOT NULL DEFAULT 0.0000,
  `fuel_price` decimal(10, 2) NOT NULL DEFAULT 0.00,
  `fuel_cost` decimal(10, 2) NULL DEFAULT 0.00,
  `maintenance_cost` decimal(10, 2) NULL DEFAULT 0.00,
  `other_cost` decimal(10, 2) NULL DEFAULT 0.00,
  `total_cost` decimal(10, 2) NULL DEFAULT 0.00,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `uk_expenses_trip_id`(`trip_id` ASC) USING BTREE,
  KEY `idx_expenses_created_at` (`created_at`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci;

BEGIN;
COMMIT;

-- ====================
-- 燃油价格表（可选缓存，前端在线获取时可回写）
-- ====================
DROP TABLE IF EXISTS `fuel_prices`;
CREATE TABLE `fuel_prices`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `fuel_type` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `price` decimal(10, 2) NOT NULL,
  `effective_date` date NOT NULL,
  `source` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `uk_fuel_prices_type_date`(`fuel_type` ASC, `effective_date` ASC) USING BTREE,
  KEY `idx_fuel_prices_effective_date` (`effective_date`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci;

BEGIN;
COMMIT;

SET FOREIGN_KEY_CHECKS = 1;
