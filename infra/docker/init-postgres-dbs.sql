-- ==============================================================================
-- Migraflow Unified PostgreSQL Initialization Script
-- Automatically provisions all PostgreSQL databases in the single Postgres container
-- ==============================================================================

-- 1. E-Commerce Sample Database
SELECT 'CREATE DATABASE ecommerce_db'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'ecommerce_db')\gexec

-- 2. CRM Sample Database
SELECT 'CREATE DATABASE crm_db'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'crm_db')\gexec

-- 3. Polyglot Enterprise Retail Database
SELECT 'CREATE DATABASE retail_commerce_pg'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'retail_commerce_pg')\gexec

-- 4. Complex Relational Benchmark Database
SELECT 'CREATE DATABASE complex_pg_db'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'complex_pg_db')\gexec

-- 5. Production-Scale E-Commerce Database
SELECT 'CREATE DATABASE ecommerce_production'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'ecommerce_production')\gexec

-- 6. Gaming Telemetry Database (NoSQL/Document Domain in PostgreSQL)
SELECT 'CREATE DATABASE gaming_telemetry_pg'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'gaming_telemetry_pg')\gexec

-- 7. Retail Store POS Database (Multi-Source Merge Test Source)
SELECT 'CREATE DATABASE retail_store_pg'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'retail_store_pg')\gexec

-- 8. Retail Merged Target Database (Unified Destination for Multi-Source Merges)
SELECT 'CREATE DATABASE retail_merged_pg'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'retail_merged_pg')\gexec

