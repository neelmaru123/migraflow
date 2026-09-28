# Migraflow Database Credentials & Catalog Architecture

This document provides a single, consolidated reference for all database services, master access credentials, and every hosted database across **PostgreSQL**, **MySQL**, and **MongoDB**.

> [!IMPORTANT]
> **Single Container per Database Engine Architecture**:
> To minimize resource overhead and simplify network topology, all databases of a particular engine run inside **exactly one container**:
>
> - **1 PostgreSQL Container** (`migration_platform_postgres`) hosts all PostgreSQL databases.
> - **1 MySQL Container** (`migration_platform_mysql`) hosts all MySQL databases.
> - **1 MongoDB Container** (`migration_platform_mongo`) hosts all MongoDB databases.

---

## 1. Quick Credentials Summary Table

| Engine         | Container Name                | Host Port(s)           | Internal Port | Username   | Password            | Auth DB | Volume Name     |
| :------------- | :---------------------------- | :--------------------- | :------------ | :--------- | :------------------ | :------ | :-------------- |
| **PostgreSQL** | `migration_platform_postgres` | `5434`, `5435`, `5436` | `5432`        | `postgres` | `postgres_password` | N/A     | `postgres_data` |
| **MySQL**      | `migration_platform_mysql`    | `3307`, `3306`         | `3306`        | `root`     | `mysql_password`    | N/A     | `mysql_data`    |
| **MongoDB**    | `migration_platform_mongo`    | `27017`                | `27017`       | `root`     | `mongo_password`    | `admin` | `mongo_data`    |

### Hostnames by Network Context:

- **From Local Host (Host OS / IDE / Python scripts)**: `localhost` or `127.0.0.1`
- **From Inside Docker Network (`docker-compose`)**:
  - PostgreSQL: `postgres:5432`
  - MySQL: `mysql_source:3306`
  - MongoDB: `mongo_source:27017`
- **From Migration Agent Container (`--network host` or bridge)**:
  - Windows / macOS Bridge: `host.docker.internal:<PORT>`
  - Linux Host Mode: `localhost:<PORT>`

---

## 2. PostgreSQL Databases Catalog

- **Container Name**: `migration_platform_postgres`
- **Image**: `postgres:16-alpine`
- **Default Database**: `migration_platform`
- **Master User**: `postgres`
- **Master Password**: `postgres_password`
- **Host Ports**:
  - `5434` (Primary control plane port)
  - `5435` (Backward-compatible port for legacy test scripts)
  - `5436` (Backward-compatible port for legacy test scripts)
- **Base Local URL**: `postgresql://postgres:postgres_password@localhost:5434/`
- **Base AsyncPG URL**: `postgresql+asyncpg://postgres:postgres_password@localhost:5434/`

### Hosted Databases:

| Database Name              | Purpose / Workload                                                        | Tables / Collections                                                                                                                                              | Seed Rows     | Direct Local Connection URL                                                   |
| :------------------------- | :------------------------------------------------------------------------ | :---------------------------------------------------------------------------------------------------------------------------------------------------------------- | :------------ | :---------------------------------------------------------------------------- |
| **`migration_platform`**   | Control Plane & Application Backend (FastAPI, Auth, Jobs, Agent Registry) | `users`, `projects`, `data_sources`, `data_source_schemas`, `migration_plans`, `migration_jobs`, `migration_job_logs`, `agents`, `agent_heartbeats`, `audit_logs` | Platform Data | `postgresql://postgres:postgres_password@localhost:5434/migration_platform`   |
| **`ecommerce_db`**         | E-Commerce Source (Catalog, orders, customers)                            | `categories`, `products`, `customers`, `orders`, `order_items`                                                                                                    | 250 rows      | `postgresql://postgres:postgres_password@localhost:5434/ecommerce_db`         |
| **`crm_db`**               | CRM Source (Customer support, leads, tickets, reviews)                    | `support_agents`, `leads`, `tickets`, `interactions`, `product_reviews`                                                                                           | 250 rows      | `postgresql://postgres:postgres_password@localhost:5434/crm_db`               |
| **`retail_commerce_pg`**   | Polyglot Enterprise Commerce Core (Interconnected with MySQL & Mongo)     | `customers`, `orders`, `order_items`, `payment_transactions`, `invoices`                                                                                          | 250+ rows     | `postgresql://postgres:postgres_password@localhost:5434/retail_commerce_pg`   |
| **`complex_pg_db`**        | Relational Benchmark Schema (Composite keys & deep relational links)      | `pg_customers`, `pg_products`, `pg_orders`, `pg_order_items`                                                                                                      | 200 rows      | `postgresql://postgres:postgres_password@localhost:5434/complex_pg_db`        |
| **`ecommerce_production`** | Production-scale transactional benchmark dataset                          | `categories`, `products`, `customers`, `orders`, `order_items`                                                                                                    | 5,000 rows    | `postgresql://postgres:postgres_password@localhost:5434/ecommerce_production` |

---

## 3. MySQL Databases Catalog

- **Container Name**: `migration_platform_mysql`
- **Image**: `mysql:8.0`
- **Default Database**: `inventory_db`
- **Master User**: `root`
- **Master Password**: `mysql_password`
- **Host Ports**:
  - `3307` (Default host-mapped port to avoid host MySQL conflicts)
  - `3306` (Direct MySQL port)
- **Base Local URL**: `mysql+pymysql://root:mysql_password@localhost:3307/`
- **Standard URI**: `mysql://root:mysql_password@localhost:3307/`

### Hosted Databases:

| Database Name                | Purpose / Workload                                                  | Tables                                                                                 | Seed Rows  | Direct Local Connection URL                                                 |
| :--------------------------- | :------------------------------------------------------------------ | :------------------------------------------------------------------------------------- | :--------- | :-------------------------------------------------------------------------- |
| **`inventory_db`**           | Supply & Warehouse Sample Source (Warehouses, stock levels)         | `warehouses`, `inventory_items`                                                        | 100 rows   | `mysql+pymysql://root:mysql_password@localhost:3307/inventory_db`           |
| **`retail_logistics_mysql`** | Polyglot Enterprise Logistics & Fulfillment (Linked with PG orders) | `warehouses`, `products_catalog`, `shipment_consignments`, `carriers`, `dispatch_logs` | 250+ rows  | `mysql+pymysql://root:mysql_password@localhost:3307/retail_logistics_mysql` |
| **`complex_mysql_db`**       | Legacy ERP Enterprise System (Chart of accounts, journals)          | `mysql_accounts`, `mysql_inventory`, `mysql_audit_logs`                                | 300+ rows  | `mysql+pymysql://root:mysql_password@localhost:3307/complex_mysql_db`       |
| **`inventory_production`**   | High-volume production supply chain dataset                         | `warehouses`, `suppliers`, `products_catalog`, `inventory_items`, `stock_transfers`    | 5,000 rows | `mysql+pymysql://root:mysql_password@localhost:3307/inventory_production`   |

---

## 4. MongoDB Databases Catalog

- **Container Name**: `migration_platform_mongo`
- **Image**: `mongo:7.0`
- **Default Database**: `analytics_db`
- **Master User**: `root`
- **Master Password**: `mongo_password`
- **Auth Database**: `admin`
- **Host Port**: `27017`
- **Base Local URL**: `mongodb://root:mongo_password@localhost:27017/?authSource=admin`

### Hosted Databases:

| Database Name                  | Purpose / Workload                         | Collections & Special Features                                                                                                                                                                                                                              | Seed Docs             | Direct Local Connection URL                                                               |
| :----------------------------- | :----------------------------------------- | :---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | :-------------------- | :---------------------------------------------------------------------------------------- |
| **`analytics_db`**             | Clickstream & User Engagement Telemetry    | `events`, `user_metrics`                                                                                                                                                                                                                                    | 100 docs              | `mongodb://root:mongo_password@localhost:27017/analytics_db?authSource=admin`             |
| **`complex_nosql_enterprise`** | Advanced NoSQL Impedance Benchmark         | • `smart_iot_fleet` (Level 7 nested hierarchies, GeoJSON 2dsphere)<br>• `omnichannel_customer_graph` (Polymorphic documents)<br>• `clinical_genomics_records` (2D jagged arrays of arrays)<br>• `polymorphic_event_bus` (Dynamic typing, BSON Regex/Binary) | 620 complex BSON docs | `mongodb://root:mongo_password@localhost:27017/complex_nosql_enterprise?authSource=admin` |
| **`retail_experience_mongo`**  | Polyglot Enterprise Omnichannel Experience | `customer_profiles`, `support_tickets`, `product_reviews`, `session_events` (Foreign references to PG and MySQL)                                                                                                                                            | 200+ docs             | `mongodb://root:mongo_password@localhost:27017/retail_experience_mongo?authSource=admin`  |
| **`complex_mongo_db`**         | Multi-tier Nested Document Store           | `user_profiles` (Level 3 nesting), `events_stream`, `product_reviews_nosql`                                                                                                                                                                                 | 150 docs              | `mongodb://root:mongo_password@localhost:27017/complex_mongo_db?authSource=admin`         |
| **`analytics_production`**     | High-Volume Production Telemetry Stream    | `user_sessions`, `page_events`, `cart_abandonment`, `device_fingerprints`                                                                                                                                                                                   | 4,000 docs            | `mongodb://root:mongo_password@localhost:27017/analytics_production?authSource=admin`     |

---

## 5. Docker Compose Service Definitions

All database engines are orchestrated in [`docker-compose.yml`](file:///d:/GitHub/Ai_data_migration_platform/docker-compose.yml) under the single-container architecture:

```yaml
services:
  # --------------------------------------------------------------------------
  # 1. PostgreSQL (Single container for ALL PostgreSQL databases)
  # --------------------------------------------------------------------------
  postgres:
    image: postgres:16-alpine
    container_name: migration_platform_postgres
    environment:
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres_password
      - POSTGRES_DB=migration_platform
    ports:
      - "5434:5432"
      - "5435:5432"
      - "5436:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./infra/docker/init-postgres-dbs.sql:/docker-entrypoint-initdb.d/init-postgres-dbs.sql:ro
    restart: unless-stopped

  # --------------------------------------------------------------------------
  # 2. MySQL (Single container for ALL MySQL databases)
  # --------------------------------------------------------------------------
  mysql_source:
    image: mysql:8.0
    container_name: migration_platform_mysql
    environment:
      - MYSQL_ROOT_PASSWORD=mysql_password
      - MYSQL_DATABASE=inventory_db
    ports:
      - "3307:3306"
      - "3306:3306"
    volumes:
      - mysql_data:/var/lib/mysql
      - ./infra/docker/init-mysql-dbs.sql:/docker-entrypoint-initdb.d/init-mysql-dbs.sql:ro
    restart: unless-stopped

  # --------------------------------------------------------------------------
  # 3. MongoDB (Single container for ALL MongoDB databases)
  # --------------------------------------------------------------------------
  mongo_source:
    image: mongo:7.0
    container_name: migration_platform_mongo
    environment:
      - MONGO_INITDB_ROOT_USERNAME=root
      - MONGO_INITDB_ROOT_PASSWORD=mongo_password
      - MONGO_INITDB_DATABASE=analytics_db
    ports:
      - "27017:27017"
    volumes:
      - mongo_data:/data/db
      - ./infra/docker/init-mongo-dbs.js:/docker-entrypoint-initdb.d/init-mongo-dbs.js:ro
    restart: unless-stopped

volumes:
  postgres_data:
  mysql_data:
  mongo_data:
```

---

## 6. Copy-Paste Ready Environment Variables (`.env`)

Add or reference these in your local `.env` or CI/CD secrets:

```bash
# ------------------------------------------------------------------------------
# PostgreSQL (Single Container: migration_platform_postgres)
# ------------------------------------------------------------------------------
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres_password
POSTGRES_HOST=localhost
POSTGRES_PORT=5434
POSTGRES_DB=migration_platform
DATABASE_URL="postgresql+asyncpg://postgres:postgres_password@localhost:5434/migration_platform"

# Sample / Benchmark PostgreSQL URLs
PG_ECOMMERCE_URL="postgresql://postgres:postgres_password@localhost:5434/ecommerce_db"
PG_CRM_URL="postgresql://postgres:postgres_password@localhost:5434/crm_db"
PG_RETAIL_COMMERCE_URL="postgresql://postgres:postgres_password@localhost:5434/retail_commerce_pg"
PG_COMPLEX_URL="postgresql://postgres:postgres_password@localhost:5434/complex_pg_db"
PG_PRODUCTION_URL="postgresql://postgres:postgres_password@localhost:5434/ecommerce_production"

# ------------------------------------------------------------------------------
# MySQL (Single Container: migration_platform_mysql)
# ------------------------------------------------------------------------------
MYSQL_USER=root
MYSQL_PASSWORD=mysql_password
MYSQL_HOST=localhost
MYSQL_PORT=3307
MYSQL_DATABASE=inventory_db

# Sample / Benchmark MySQL URLs
MYSQL_INVENTORY_URL="mysql+pymysql://root:mysql_password@localhost:3307/inventory_db"
MYSQL_RETAIL_LOGISTICS_URL="mysql+pymysql://root:mysql_password@localhost:3307/retail_logistics_mysql"
MYSQL_COMPLEX_URL="mysql+pymysql://root:mysql_password@localhost:3307/complex_mysql_db"
MYSQL_PRODUCTION_URL="mysql+pymysql://root:mysql_password@localhost:3307/inventory_production"

# ------------------------------------------------------------------------------
# MongoDB (Single Container: migration_platform_mongo)
# ------------------------------------------------------------------------------
MONGO_USER=root
MONGO_PASSWORD=mongo_password
MONGO_HOST=localhost
MONGO_PORT=27017
MONGO_AUTH_DB=admin

# Sample / Benchmark MongoDB URLs
MONGO_ANALYTICS_URL="mongodb://root:mongo_password@localhost:27017/analytics_db?authSource=admin"
MONGO_COMPLEX_NOSQL_URL="mongodb://root:mongo_password@localhost:27017/complex_nosql_enterprise?authSource=admin"
MONGO_RETAIL_EXPERIENCE_URL="mongodb://root:mongo_password@localhost:27017/retail_experience_mongo?authSource=admin"
MONGO_COMPLEX_URL="mongodb://root:mongo_password@localhost:27017/complex_mongo_db?authSource=admin"
MONGO_PRODUCTION_URL="mongodb://root:mongo_password@localhost:27017/analytics_production?authSource=admin"
```

---

## 7. CLI Quick Verification Commands

### Test PostgreSQL (Single Container)

```bash
# List all databases inside the single PostgreSQL container
docker exec -it migration_platform_postgres psql -U postgres -c "\l"
```

### Test MySQL (Single Container)

```bash
# List all databases inside the single MySQL container
docker exec -it migration_platform_mysql mysql -u root -pmysql_password -e "SHOW DATABASES;"
```

### Test MongoDB (Single Container)

```bash
# List all databases inside the single MongoDB container
docker exec -it migration_platform_mongo mongosh -u root -p mongo_password --authenticationDatabase admin --eval "db.adminCommand('listDatabases')"
```
