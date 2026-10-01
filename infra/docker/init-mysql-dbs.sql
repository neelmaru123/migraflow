-- ==============================================================================
-- Migraflow Unified MySQL Initialization Script
-- Automatically provisions all MySQL databases in the single MySQL container
-- ==============================================================================

-- 1. Inventory & Warehouse Sample Database
CREATE DATABASE IF NOT EXISTS `inventory_db`;

-- 2. Polyglot Enterprise Retail Logistics Database
CREATE DATABASE IF NOT EXISTS `retail_logistics_mysql`;

-- 3. Complex Legacy ERP Database
CREATE DATABASE IF NOT EXISTS `complex_mysql_db`;

-- 4. Production-Scale Inventory Database
CREATE DATABASE IF NOT EXISTS `inventory_production`;

-- 5. Gaming Economy & Virtual Marketplace Database (NoSQL/Document Domain in MySQL)
CREATE DATABASE IF NOT EXISTS `gaming_economy_mysql` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Ensure root user has full permissions across all databases
GRANT ALL PRIVILEGES ON *.* TO 'root'@'%' WITH GRANT OPTION;
FLUSH PRIVILEGES;

