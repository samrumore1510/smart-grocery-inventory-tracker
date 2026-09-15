-- ============================================================================
-- SMART GROCERY INVENTORY & EXPIRY TRACKER
-- Relational Database Schema (MySQL 8.0+ Compatible)
-- MCA Project Portfolio Submission
-- ============================================================================

CREATE DATABASE IF NOT EXISTS `smart_grocery` 
CHARACTER SET utf8mb4 
COLLATE utf8mb4_unicode_ci;

USE `smart_grocery`;

-- ----------------------------------------------------------------------------
-- Table 1: Users (User Management & Authentication)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `users` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `username` VARCHAR(50) NOT NULL UNIQUE,
    `email` VARCHAR(120) NOT NULL UNIQUE,
    `full_name` VARCHAR(100) NULL,
    `hashed_password` VARCHAR(255) NOT NULL,
    `role` VARCHAR(20) DEFAULT 'user' COMMENT 'admin or user',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX `idx_users_username` (`username`),
    INDEX `idx_users_email` (`email`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ----------------------------------------------------------------------------
-- Table 2: Categories (Product Classification)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `categories` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `name` VARCHAR(60) NOT NULL UNIQUE,
    `icon` VARCHAR(10) DEFAULT '📦',
    `description` VARCHAR(255) NULL,
    INDEX `idx_categories_name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ----------------------------------------------------------------------------
-- Table 3: Products (Grocery Inventory & Expiry Tracking)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `products` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `user_id` INT NOT NULL,
    `category_id` INT NOT NULL,
    `name` VARCHAR(120) NOT NULL,
    `brand` VARCHAR(80) NULL,
    `quantity` DECIMAL(8, 2) NOT NULL DEFAULT 1.00,
    `unit` VARCHAR(20) DEFAULT 'kg' COMMENT 'kg, g, L, ml, pcs, packets',
    `min_quantity` DECIMAL(8, 2) DEFAULT 1.00 COMMENT 'Low stock alert threshold',
    `unit_price` DECIMAL(10, 2) DEFAULT 0.00 COMMENT 'Price in INR',
    `purchase_date` DATE NOT NULL,
    `expiry_date` DATE NOT NULL,
    `barcode` VARCHAR(64) NULL,
    `storage_location` VARCHAR(50) DEFAULT 'Pantry' COMMENT 'Pantry, Refrigerator, Freezer',
    `notes` TEXT NULL,
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT `fk_products_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_products_category` FOREIGN KEY (`category_id`) REFERENCES `categories` (`id`) ON DELETE RESTRICT,
    INDEX `idx_products_user_id` (`user_id`),
    INDEX `idx_products_category_id` (`category_id`),
    INDEX `idx_products_expiry_date` (`expiry_date`),
    INDEX `idx_products_barcode` (`barcode`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ----------------------------------------------------------------------------
-- Table 4: Shopping Items (Smart Shopping List & Auto-Restock)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `shopping_items` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `user_id` INT NOT NULL,
    `product_id` INT NULL,
    `product_name` VARCHAR(120) NOT NULL,
    `category_id` INT NULL,
    `target_quantity` DECIMAL(8, 2) DEFAULT 1.00,
    `unit` VARCHAR(20) DEFAULT 'kg',
    `estimated_price` DECIMAL(10, 2) DEFAULT 0.00,
    `is_purchased` BOOLEAN DEFAULT FALSE,
    `auto_added` BOOLEAN DEFAULT FALSE COMMENT 'Generated automatically by low stock alert',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT `fk_shopping_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_shopping_category` FOREIGN KEY (`category_id`) REFERENCES `categories` (`id`) ON DELETE SET NULL,
    INDEX `idx_shopping_user_id` (`user_id`),
    INDEX `idx_shopping_is_purchased` (`is_purchased`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ----------------------------------------------------------------------------
-- Table 5: Expense Logs (Grocery Expense & Financial Tracking)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `expense_logs` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `user_id` INT NOT NULL,
    `product_id` INT NULL,
    `product_name` VARCHAR(120) NOT NULL,
    `category_id` INT NULL,
    `amount` DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
    `expense_date` DATE NOT NULL,
    `payment_method` VARCHAR(30) DEFAULT 'UPI',
    `notes` VARCHAR(255) NULL,
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT `fk_expenses_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_expenses_category` FOREIGN KEY (`category_id`) REFERENCES `categories` (`id`) ON DELETE SET NULL,
    INDEX `idx_expenses_user_id` (`user_id`),
    INDEX `idx_expenses_date` (`expense_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================================================
-- SAMPLE SQL QUERIES (FOR MCA EXAM & VIVA DEMONSTRATION)
-- ============================================================================

-- 1. Find all products expiring in the next 7 days:
-- SELECT name, quantity, unit, expiry_date, DATEDIFF(expiry_date, CURDATE()) as days_left 
-- FROM products 
-- WHERE expiry_date BETWEEN CURDATE() AND DATE_ADD(CURDATE(), INTERVAL 7 DAY) 
-- ORDER BY expiry_date ASC;

-- 2. Find low stock and out-of-stock products:
-- SELECT name, quantity, min_quantity, unit, 
--        CASE WHEN quantity <= 0 THEN 'Out of Stock' ELSE 'Low Stock' END as status
-- FROM products 
-- WHERE quantity <= min_quantity;

-- 3. Calculate total grocery spending for the current month:
-- SELECT SUM(amount) as monthly_spending 
-- FROM expense_logs 
-- WHERE expense_date >= DATE_FORMAT(CURDATE(), '%Y-%m-01');

-- 4. Category-wise expense breakdown:
-- SELECT c.name as category, SUM(e.amount) as total_spent 
-- FROM expense_logs e 
-- JOIN categories c ON e.category_id = c.id 
-- GROUP BY c.name 
-- ORDER BY total_spent DESC;
