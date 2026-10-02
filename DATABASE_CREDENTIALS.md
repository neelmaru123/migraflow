# Migraflow Database Credentials & Catalog Architecture

This document provides a single, consolidated reference for all database services, master access credentials, networking hosts across different runtime contexts, and every hosted database across **PostgreSQL**, **MySQL**, and **MongoDB**.

> [!IMPORTANT]
> **Single Container per Database Engine Architecture**:
> To minimize resource overhead and simplify network topology, all databases of a particular engine run inside **exactly one container**:
>
> - **1 PostgreSQL Container** (`migration_platform_postgres`) hosts all PostgreSQL databases.
> - **1 MySQL Container** (`migration_platform_mysql`) hosts all MySQL databases.
> - **1 MongoDB Container** (`migration_platform_mongo`) hosts all MongoDB databases.

---

## 1. Database Host & Quick Credentials Summary Table

Depending on where your code, client, or agent is executing, use the corresponding **Host** address:

| Engine | Container Name | Host (Local Machine) | Host (Docker Agent / UI) | Host (Docker Compose) | Host Port(s) | Internal Port | Username | Password | Auth DB | Volume Name |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **PostgreSQL** | `migration_platform_postgres` | `localhost` / `127.0.0.1` | `host.docker.internal` | `postgres` | `5434`, `5435`, `5436` | `5432` | `postgres` | `postgres_password` | N/A | `postgres_data` |
| **MySQL** | `migration_platform_mysql` | `localhost` / `127.0.0.1` | `host.docker.internal` | `mysql_source` | `3307`, `3306` | `3306` | `root` | `mysql_password` | N/A | `mysql_data` |
| **MongoDB** | `migration_platform_mongo` | `localhost` / `127.0.0.1` | `host.docker.internal` | `mongo_source` | `27017` | `27017` | `root` | `mongo_password` | `admin` | `mongo_data` |
| **Redis** | `migration_platform_redis` | `localhost` / `127.0.0.1` | `host.docker.internal` | `redis` | `6379` | `6379` | N/A | N/A | N/A | N/A |

### Detailed Host Explanations by Network Context:

1. **From Local Host (Host OS / IDE / Python scripts / DBeaver / pgAdmin / Compass)**:
   - **Host**: `localhost` or `127.0.0.1`
   - Use the **Host Port** mapped on your machine:
     - PostgreSQL: `localhost:5434`
     - MySQL: `localhost:3307`
     - MongoDB: `localhost:27017`
     - Redis: `localhost:6379`

2. **From Docker Migration Agent Container (`data-migration-agent:latest`) & Migraflow UI Form (`/agents/create`)**:
   - When the agent runs as a Docker container connecting to databases on your workstation:
     - **Windows & macOS**: Host is `host.docker.internal`
     - **Linux (Docker bridge)**: Host is `host.docker.internal` (with `--add-host host.docker.internal:host-gateway`) or host IP `172.17.0.1`
     - **Linux (`--network host`)**: Host is `localhost`
   - Use the **Host Port**:
     - PostgreSQL: `host.docker.internal:5434`
     - MySQL: `host.docker.internal:3307`
     - MongoDB: `host.docker.internal:27017`

3. **From Inside Docker Compose Network (Inter-service e.g., `web` or `api` to DBs)**:
   - **Host**: The Docker Compose service name:
     - PostgreSQL: `postgres:5432`
     - MySQL: `mysql_source:3306`
     - MongoDB: `mongo_source:27017`
     - Redis: `redis:6379`

---

## 2. Web UI Database Configuration Form Guide (`DatabaseConfigForm`)

When creating an agent or configuring a migration pipeline in the web UI at `http://localhost:3000/agents/create`:

### Source & Destination Inputs:

| Field | PostgreSQL | MySQL | MongoDB |
| :--- | :--- | :--- | :--- |
| **Engine** | Select `PostgreSQL` tile | Select `MySQL` tile | Select `MongoDB` tile |
| **Host / IP** | `host.docker.internal` *(or `localhost` for Linux host mode)* | `host.docker.internal` *(or `localhost` for Linux host mode)* | `host.docker.internal` *(or `localhost` for Linux host mode)* |
| **Port** | `5434` | `3307` | `27017` |
| **Username** | `postgres` | `root` | `root` |
| **Password** | `postgres_password` | `mysql_password` | `mongo_password` |
| **Database Name** | `ecommerce_db` (or any PG DB below) | `inventory_db` (or any MySQL DB below) | `analytics_db` (or any Mongo DB below) |
| **Require SSL** | Unchecked (for local Docker) | Unchecked (for local Docker) | Unchecked (for local Docker) |

---

## 3. PostgreSQL Databases Catalog

- **Container Name**: `migration_platform_postgres`
- **Docker Image**: `postgres:16-alpine`
- **Master User**: `postgres`
- **Master Password**: `postgres_password`
- **Hosts by Runtime**:
  - **Local Host OS**: `localhost` (Port: `5434`)
  - **Docker Agent / UI Form**: `host.docker.internal` (Port: `5434`)
  - **Docker Compose Network**: `postgres` (Port: `5432`)
- **Host Ports**:
  - `5434` (Primary control plane port)
  - `5435` (Backward-compatible port for legacy test scripts)
  - `5436` (Backward-compatible port for legacy test scripts)
- **Base Local URL**: `postgresql://postgres:postgres_password@localhost:5434/`
- **Base Agent URL**: `postgresql://postgres:postgres_password@host.docker.internal:5434/`
- **Base Docker Network URL**: `postgresql://postgres:postgres_password@postgres:5432/`
- **Base AsyncPG URL**: `postgresql+asyncpg://postgres:postgres_password@localhost:5434/`

### Hosted Databases:

| Database Name | Purpose / Workload | Tables | Seed Rows | Local URL (`localhost:5434`) | Docker Agent URL (`host.docker.internal:5434`) | Docker Compose URL (`postgres:5432`) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **`migration_platform`** | Control Plane & Application Backend (FastAPI, Auth, Jobs, Agent Registry) | `users`, `projects`, `data_sources`, `data_source_schemas`, `migration_plans`, `migration_jobs`, `migration_job_logs`, `agents`, `agent_heartbeats`, `audit_logs` | Platform Data | `postgresql://postgres:postgres_password@localhost:5434/migration_platform` | `postgresql://postgres:postgres_password@host.docker.internal:5434/migration_platform` | `postgresql://postgres:postgres_password@postgres:5432/migration_platform` |
| **`ecommerce_db`** | E-Commerce Source (Catalog, orders, customers) | `categories`, `products`, `customers`, `orders`, `order_items` | 250 rows | `postgresql://postgres:postgres_password@localhost:5434/ecommerce_db` | `postgresql://postgres:postgres_password@host.docker.internal:5434/ecommerce_db` | `postgresql://postgres:postgres_password@postgres:5432/ecommerce_db` |
| **`crm_db`** | CRM Source (Customer support, leads, tickets, reviews) | `support_agents`, `leads`, `tickets`, `interactions`, `product_reviews` | 250 rows | `postgresql://postgres:postgres_password@localhost:5434/crm_db` | `postgresql://postgres:postgres_password@host.docker.internal:5434/crm_db` | `postgresql://postgres:postgres_password@postgres:5432/crm_db` |
| **`retail_commerce_pg`** | Polyglot Enterprise Commerce Core (Interconnected with MySQL & Mongo) | `customers`, `orders`, `order_items`, `payment_transactions`, `invoices` | 250+ rows | `postgresql://postgres:postgres_password@localhost:5434/retail_commerce_pg` | `postgresql://postgres:postgres_password@host.docker.internal:5434/retail_commerce_pg` | `postgresql://postgres:postgres_password@postgres:5432/retail_commerce_pg` |
| **`complex_pg_db`** | Relational Benchmark Schema (Composite keys & deep relational links) | `pg_customers`, `pg_products`, `pg_orders`, `pg_order_items` | 200 rows | `postgresql://postgres:postgres_password@localhost:5434/complex_pg_db` | `postgresql://postgres:postgres_password@host.docker.internal:5434/complex_pg_db` | `postgresql://postgres:postgres_password@postgres:5432/complex_pg_db` |
| **`ecommerce_production`** | Production-scale transactional benchmark dataset | `categories`, `products`, `customers`, `orders`, `order_items` | 5,000 rows | `postgresql://postgres:postgres_password@localhost:5434/ecommerce_production` | `postgresql://postgres:postgres_password@host.docker.internal:5434/ecommerce_production` | `postgresql://postgres:postgres_password@postgres:5432/ecommerce_production` |
| **`gaming_telemetry_pg`** | Gaming Universe Telemetry (NoSQL/Document Domain in PostgreSQL with JSONB) | `players`, `player_characters`, `inventory_items`, `match_sessions`, `combat_events` | 2,500 rows (500/table) | `postgresql://postgres:postgres_password@localhost:5434/gaming_telemetry_pg` | `postgresql://postgres:postgres_password@host.docker.internal:5434/gaming_telemetry_pg` | `postgresql://postgres:postgres_password@postgres:5432/gaming_telemetry_pg` |


---

## 4. MySQL Databases Catalog

- **Container Name**: `migration_platform_mysql`
- **Docker Image**: `mysql:8.0`
- **Master User**: `root`
- **Master Password**: `mysql_password`
- **Hosts by Runtime**:
  - **Local Host OS**: `localhost` (Port: `3307`)
  - **Docker Agent / UI Form**: `host.docker.internal` (Port: `3307`)
  - **Docker Compose Network**: `mysql_source` (Port: `3306`)
- **Host Ports**:
  - `3307` (Default host-mapped port to avoid host MySQL conflicts)
  - `3306` (Direct MySQL port)
- **Base Local URL**: `mysql+pymysql://root:mysql_password@localhost:3307/`
- **Base Agent URL**: `mysql+pymysql://root:mysql_password@host.docker.internal:3307/`
- **Base Docker Network URL**: `mysql+pymysql://root:mysql_password@mysql_source:3306/`

### Hosted Databases:

| Database Name | Purpose / Workload | Tables | Seed Rows | Local URL (`localhost:3307`) | Docker Agent URL (`host.docker.internal:3307`) | Docker Compose URL (`mysql_source:3306`) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **`inventory_db`** | Supply & Warehouse Sample Source (Warehouses, stock levels) | `warehouses`, `inventory_items` | 100 rows | `mysql+pymysql://root:mysql_password@localhost:3307/inventory_db` | `mysql+pymysql://root:mysql_password@host.docker.internal:3307/inventory_db` | `mysql+pymysql://root:mysql_password@mysql_source:3306/inventory_db` |
| **`retail_logistics_mysql`** | Polyglot Enterprise Logistics & Fulfillment (Linked with PG orders) | `warehouses`, `products_catalog`, `shipment_consignments`, `carriers`, `dispatch_logs` | 250+ rows | `mysql+pymysql://root:mysql_password@localhost:3307/retail_logistics_mysql` | `mysql+pymysql://root:mysql_password@host.docker.internal:3307/retail_logistics_mysql` | `mysql+pymysql://root:mysql_password@mysql_source:3306/retail_logistics_mysql` |
| **`complex_mysql_db`** | Legacy ERP Enterprise System (Chart of accounts, journals) | `mysql_accounts`, `mysql_inventory`, `mysql_audit_logs` | 300+ rows | `mysql+pymysql://root:mysql_password@localhost:3307/complex_mysql_db` | `mysql+pymysql://root:mysql_password@host.docker.internal:3307/complex_mysql_db` | `mysql+pymysql://root:mysql_password@mysql_source:3306/complex_mysql_db` |
| **`inventory_production`** | High-volume production supply chain dataset | `warehouses`, `suppliers`, `products_catalog`, `inventory_items`, `stock_transfers` | 5,000 rows | `mysql+pymysql://root:mysql_password@localhost:3307/inventory_production` | `mysql+pymysql://root:mysql_password@host.docker.internal:3307/inventory_production` | `mysql+pymysql://root:mysql_password@mysql_source:3306/inventory_production` |
| **`gaming_economy_mysql`** | Gaming Virtual Economy & Auctions (NoSQL/Document Domain in MySQL with JSON) | `guilds`, `guild_members`, `auction_listings`, `auction_transactions`, `quest_progressions` | 2,500 rows (500/table) | `mysql+pymysql://root:mysql_password@localhost:3307/gaming_economy_mysql` | `mysql+pymysql://root:mysql_password@host.docker.internal:3307/gaming_economy_mysql` | `mysql+pymysql://root:mysql_password@mysql_source:3306/gaming_economy_mysql` |


---

## 5. MongoDB Databases Catalog

- **Container Name**: `migration_platform_mongo`
- **Docker Image**: `mongo:7.0`
- **Master User**: `root`
- **Master Password**: `mongo_password`
- **Auth Database**: `admin`
- **Hosts by Runtime**:
  - **Local Host OS**: `localhost` (Port: `27017`)
  - **Docker Agent / UI Form**: `host.docker.internal` (Port: `27017`)
  - **Docker Compose Network**: `mongo_source` (Port: `27017`)
- **Host Port**: `27017`
- **Base Local URL**: `mongodb://root:mongo_password@localhost:27017/?authSource=admin`
- **Base Agent URL**: `mongodb://root:mongo_password@host.docker.internal:27017/?authSource=admin`
- **Base Docker Network URL**: `mongodb://root:mongo_password@mongo_source:27017/?authSource=admin`

### Hosted Databases:

| Database Name | Purpose / Workload | Collections & Features | Seed Docs | Local URL (`localhost:27017`) | Docker Agent URL (`host.docker.internal:27017`) | Docker Compose URL (`mongo_source:27017`) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **`analytics_db`** | Clickstream & User Engagement Telemetry | `events`, `user_metrics` | 100 docs | `mongodb://root:mongo_password@localhost:27017/analytics_db?authSource=admin` | `mongodb://root:mongo_password@host.docker.internal:27017/analytics_db?authSource=admin` | `mongodb://root:mongo_password@mongo_source:27017/analytics_db?authSource=admin` |
| **`complex_nosql_enterprise`** | Advanced NoSQL Impedance Benchmark | Nested hierarchies (L7), GeoJSON 2dsphere, polymorphic documents, 2D jagged arrays | 620 complex BSON docs | `mongodb://root:mongo_password@localhost:27017/complex_nosql_enterprise?authSource=admin` | `mongodb://root:mongo_password@host.docker.internal:27017/complex_nosql_enterprise?authSource=admin` | `mongodb://root:mongo_password@mongo_source:27017/complex_nosql_enterprise?authSource=admin` |
| **`retail_experience_mongo`** | Polyglot Enterprise Omnichannel Experience | `customer_profiles`, `support_tickets`, `product_reviews`, `session_events` (Foreign references to PG and MySQL) | 200+ docs | `mongodb://root:mongo_password@localhost:27017/retail_experience_mongo?authSource=admin` | `mongodb://root:mongo_password@host.docker.internal:27017/retail_experience_mongo?authSource=admin` | `mongodb://root:mongo_password@mongo_source:27017/retail_experience_mongo?authSource=admin` |
| **`complex_mongo_db`** | Multi-tier Nested Document Store | `user_profiles` (Level 3 nesting), `events_stream`, `product_reviews_nosql` | 150 docs | `mongodb://root:mongo_password@localhost:27017/complex_mongo_db?authSource=admin` | `mongodb://root:mongo_password@host.docker.internal:27017/complex_mongo_db?authSource=admin` | `mongodb://root:mongo_password@mongo_source:27017/complex_mongo_db?authSource=admin` |
| **`analytics_production`** | High-Volume Production Telemetry Stream | `user_sessions`, `page_events`, `cart_abandonment`, `device_fingerprints` | 4,000 docs | `mongodb://root:mongo_password@localhost:27017/analytics_production?authSource=admin` | `mongodb://root:mongo_password@host.docker.internal:27017/analytics_production?authSource=admin` | `mongodb://root:mongo_password@mongo_source:27017/analytics_production?authSource=admin` |

---

## 6. Docker Compose Service Definitions

All database engines are orchestrated in [`docker-compose.yml`](file:///d:/GitHub/Ai_data_migration_platform/docker-compose.yml) under the single-container architecture:

```yaml
services:
  # --------------------------------------------------------------------------
  # 1. PostgreSQL (Single container for ALL PostgreSQL databases)
  # Host: postgres (internal) | localhost (external) | host.docker.internal (agent)
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
  # Host: mysql_source (internal) | localhost (external) | host.docker.internal (agent)
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
  # Host: mongo_source (internal) | localhost (external) | host.docker.internal (agent)
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

## 7. Copy-Paste Ready Environment Variables (`.env`)

### For Local Execution (Host Machine):

```bash
# ------------------------------------------------------------------------------
# PostgreSQL (Host: localhost)
# ------------------------------------------------------------------------------
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres_password
POSTGRES_HOST=localhost
POSTGRES_PORT=5434
POSTGRES_DB=migration_platform
DATABASE_URL="postgresql+asyncpg://postgres:postgres_password@localhost:5434/migration_platform"

PG_ECOMMERCE_URL="postgresql://postgres:postgres_password@localhost:5434/ecommerce_db"
PG_CRM_URL="postgresql://postgres:postgres_password@localhost:5434/crm_db"
PG_RETAIL_COMMERCE_URL="postgresql://postgres:postgres_password@localhost:5434/retail_commerce_pg"
PG_COMPLEX_URL="postgresql://postgres:postgres_password@localhost:5434/complex_pg_db"
PG_PRODUCTION_URL="postgresql://postgres:postgres_password@localhost:5434/ecommerce_production"
PG_GAMING_TELEMETRY_URL="postgresql://postgres:postgres_password@localhost:5434/gaming_telemetry_pg"


# ------------------------------------------------------------------------------
# MySQL (Host: localhost)
# ------------------------------------------------------------------------------
MYSQL_USER=root
MYSQL_PASSWORD=mysql_password
MYSQL_HOST=localhost
MYSQL_PORT=3307
MYSQL_DATABASE=inventory_db

MYSQL_INVENTORY_URL="mysql+pymysql://root:mysql_password@localhost:3307/inventory_db"
MYSQL_RETAIL_LOGISTICS_URL="mysql+pymysql://root:mysql_password@localhost:3307/retail_logistics_mysql"
MYSQL_COMPLEX_URL="mysql+pymysql://root:mysql_password@localhost:3307/complex_mysql_db"
MYSQL_PRODUCTION_URL="mysql+pymysql://root:mysql_password@localhost:3307/inventory_production"
MYSQL_GAMING_ECONOMY_URL="mysql+pymysql://root:mysql_password@localhost:3307/gaming_economy_mysql"


# ------------------------------------------------------------------------------
# MongoDB (Host: localhost)
# ------------------------------------------------------------------------------
MONGO_USER=root
MONGO_PASSWORD=mongo_password
MONGO_HOST=localhost
MONGO_PORT=27017
MONGO_AUTH_DB=admin

MONGO_ANALYTICS_URL="mongodb://root:mongo_password@localhost:27017/analytics_db?authSource=admin"
MONGO_COMPLEX_NOSQL_URL="mongodb://root:mongo_password@localhost:27017/complex_nosql_enterprise?authSource=admin"
MONGO_RETAIL_EXPERIENCE_URL="mongodb://root:mongo_password@localhost:27017/retail_experience_mongo?authSource=admin"
MONGO_COMPLEX_URL="mongodb://root:mongo_password@localhost:27017/complex_mongo_db?authSource=admin"
MONGO_PRODUCTION_URL="mongodb://root:mongo_password@localhost:27017/analytics_production?authSource=admin"
```

### For Docker Agent / Container Execution:

```bash
# PostgreSQL Host for Docker Agent
POSTGRES_HOST=host.docker.internal
POSTGRES_PORT=5434

# MySQL Host for Docker Agent
MYSQL_HOST=host.docker.internal
MYSQL_PORT=3307

# MongoDB Host for Docker Agent
MONGO_HOST=host.docker.internal
MONGO_PORT=27017
```

---

## 8. CLI Quick Verification Commands

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
