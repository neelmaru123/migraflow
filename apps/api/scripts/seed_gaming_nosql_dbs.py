"""
Gaming Telemetry & Virtual Economy Multi-Database Provisioning Script.

Context:
Client requested a data model that would traditionally / ideally reside in MongoDB
(polymorphic combat events, nested hardware telemetry, inventories with variable sockets/affixes,
guild perk trees, dynamic marketplace listings, and multi-stage quest progression trees),
but specifically mandated implementation across PostgreSQL and MySQL for enterprise stack alignment.

Databases Provisioned:
1. PostgreSQL (Port 5434): gaming_telemetry_pg
   - players (500 rows)
   - player_characters (500 rows)
   - inventory_items (500 rows)
   - match_sessions (500 rows)
   - combat_events (500 rows)
   Total: 2,500 rows

2. MySQL (Port 3307): gaming_economy_mysql
   - guilds (500 rows)
   - guild_members (500 rows)
   - auction_listings (500 rows)
   - auction_transactions (500 rows)
   - quest_progressions (500 rows)
   Total: 2,500 rows

Grand Total: 10 tables, each with 500 rows = 5,000 rows.
"""

import os
import sys
import time
import json
import uuid
import random
from datetime import datetime, timezone, timedelta
from sqlalchemy import create_engine, text

# Configuration with environment defaults
PG_USER = os.getenv("POSTGRES_USER", "postgres")
PG_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres_password")
PG_HOST = os.getenv("POSTGRES_HOST", "127.0.0.1")
PG_PORT = os.getenv("POSTGRES_PORT", "5434")
PG_DB_NAME = "gaming_telemetry_pg"

MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "mysql_password")
MYSQL_HOST = os.getenv("MYSQL_HOST", "127.0.0.1")
MYSQL_PORT = os.getenv("MYSQL_PORT", "3307")
MYSQL_DB_NAME = "gaming_economy_mysql"

PG_ADMIN_URL = f"postgresql://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:{PG_PORT}/postgres"
PG_TARGET_URL = f"postgresql://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:{PG_PORT}/{PG_DB_NAME}"

MYSQL_ADMIN_URL = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/mysql"
MYSQL_TARGET_URL = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB_NAME}"


def ensure_postgres_database():
    print(f"\n[PostgreSQL] Connecting to admin DB on {PG_HOST}:{PG_PORT}...")
    engine = create_engine(PG_ADMIN_URL, isolation_level="AUTOCOMMIT", connect_args={"connect_timeout": 5})
    with engine.connect() as conn:
        res = conn.execute(text(f"SELECT 1 FROM pg_database WHERE datname = '{PG_DB_NAME}';"))
        if not res.scalar():
            conn.execute(text(f'CREATE DATABASE "{PG_DB_NAME}";'))
            print(f"  [OK] Created database '{PG_DB_NAME}' successfully.")
        else:
            print(f"  [OK] Database '{PG_DB_NAME}' already exists.")


def ensure_mysql_database():
    print(f"\n[MySQL] Connecting to admin DB on {MYSQL_HOST}:{MYSQL_PORT}...")
    engine = create_engine(MYSQL_ADMIN_URL, isolation_level="AUTOCOMMIT", connect_args={"connect_timeout": 5})
    with engine.connect() as conn:
        conn.execute(text(f"CREATE DATABASE IF NOT EXISTS `{MYSQL_DB_NAME}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"))
        print(f"  [OK] Created / verified database '{MYSQL_DB_NAME}' successfully.")


def seed_postgres():
    print(f"\n================================================================================")
    print(f" >>> PROVISIONING & SEEDING POSTGRESQL: {PG_DB_NAME}")
    print(f"================================================================================")
    engine = create_engine(PG_TARGET_URL, connect_args={"connect_timeout": 5})

    with engine.begin() as conn:
        # 1. Clean existing tables if present
        print("  Dropping legacy tables if any...")
        conn.execute(text("""
            DROP TABLE IF EXISTS combat_events CASCADE;
            DROP TABLE IF EXISTS match_sessions CASCADE;
            DROP TABLE IF EXISTS inventory_items CASCADE;
            DROP TABLE IF EXISTS player_characters CASCADE;
            DROP TABLE IF EXISTS players CASCADE;
        """))

        # 2. Create DDL with JSONB and relational foreign keys
        print("  Creating relational schemas with JSONB document support...")
        conn.execute(text("""
            CREATE TABLE players (
                player_id INT PRIMARY KEY,
                username VARCHAR(100) UNIQUE NOT NULL,
                email VARCHAR(255) UNIQUE NOT NULL,
                region VARCHAR(50) NOT NULL,
                account_tier VARCHAR(30) NOT NULL,
                player_level INT NOT NULL,
                experience_points BIGINT NOT NULL,
                settings_profile JSONB NOT NULL,
                created_at TIMESTAMPTZ NOT NULL,
                last_login_at TIMESTAMPTZ NOT NULL
            );

            CREATE TABLE player_characters (
                character_id INT PRIMARY KEY,
                player_id INT NOT NULL REFERENCES players(player_id) ON DELETE CASCADE,
                character_name VARCHAR(100) NOT NULL,
                character_class VARCHAR(50) NOT NULL,
                level INT NOT NULL,
                gold_balance NUMERIC(12, 2) NOT NULL,
                base_attributes JSONB NOT NULL,
                active_talents JSONB NOT NULL,
                created_at TIMESTAMPTZ NOT NULL
            );

            CREATE TABLE inventory_items (
                item_id INT PRIMARY KEY,
                character_id INT NOT NULL REFERENCES player_characters(character_id) ON DELETE CASCADE,
                item_code VARCHAR(50) NOT NULL,
                item_name VARCHAR(150) NOT NULL,
                item_type VARCHAR(50) NOT NULL,
                rarity VARCHAR(30) NOT NULL,
                is_equipped BOOLEAN NOT NULL DEFAULT FALSE,
                item_payload JSONB NOT NULL,
                acquired_at TIMESTAMPTZ NOT NULL
            );

            CREATE TABLE match_sessions (
                session_id INT PRIMARY KEY,
                player_id INT NOT NULL REFERENCES players(player_id) ON DELETE CASCADE,
                session_uuid UUID NOT NULL,
                game_mode VARCHAR(50) NOT NULL,
                map_name VARCHAR(100) NOT NULL,
                duration_seconds INT NOT NULL,
                match_result VARCHAR(30) NOT NULL,
                hardware_metrics JSONB NOT NULL,
                started_at TIMESTAMPTZ NOT NULL,
                ended_at TIMESTAMPTZ NOT NULL
            );

            CREATE TABLE combat_events (
                event_id INT PRIMARY KEY,
                session_id INT NOT NULL REFERENCES match_sessions(session_id) ON DELETE CASCADE,
                event_type VARCHAR(50) NOT NULL,
                tick_ms BIGINT NOT NULL,
                telemetry_data JSONB NOT NULL,
                occurred_at TIMESTAMPTZ NOT NULL
            );

            -- Helpful GIN indexes for JSONB document querying
            CREATE INDEX idx_players_settings ON players USING GIN (settings_profile);
            CREATE INDEX idx_characters_attributes ON player_characters USING GIN (base_attributes);
            CREATE INDEX idx_inventory_payload ON inventory_items USING GIN (item_payload);
            CREATE INDEX idx_sessions_hardware ON match_sessions USING GIN (hardware_metrics);
            CREATE INDEX idx_combat_telemetry ON combat_events USING GIN (telemetry_data);
        """))
        print("  [OK] DDL and GIN indexes created successfully.")

        # 3. Generate 500 rows for each table
        regions = ["NA_EAST", "NA_WEST", "EU_CENTRAL", "AP_SOUTH", "AP_EAST", "SA_BRAZIL", "EU_WEST"]
        tiers = ["STANDARD", "PRO", "ELITE", "VIP", "FOUNDER"]
        base_time = datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc)

        # Seed players (500)
        print("  Generating 500 rows for 'players'...")
        players_rows = []
        for i in range(1, 501):
            p_id = 1000 + i
            created_dt = base_time + timedelta(hours=i * 4)
            login_dt = created_dt + timedelta(days=random.randint(1, 45), hours=random.randint(1, 12))
            settings = {
                "audio": {
                    "master_volume": random.randint(60, 100),
                    "music_volume": random.randint(30, 80),
                    "voice_chat": random.choice([True, False])
                },
                "graphics": {
                    "resolution": random.choice(["1920x1080", "2560x1440", "3840x2160"]),
                    "ray_tracing": random.choice([True, False]),
                    "fov": random.choice([90, 100, 105, 110])
                },
                "keybinds": {
                    "jump": "SPACE",
                    "ability_1": random.choice(["Q", "MOUSE4"]),
                    "ability_2": random.choice(["E", "MOUSE5"]),
                    "ultimate": "R"
                },
                "privacy": {
                    "allow_party_invites": True,
                    "streamer_mode": (i % 25 == 0)
                }
            }
            players_rows.append({
                "player_id": p_id,
                "username": f"Vanguard_{i:03d}_{random.choice(['Wolf', 'Blade', 'Falcon', 'Shadow', 'Storm'])}",
                "email": f"player_{i:03d}@gamedomain-telemetry.io",
                "region": regions[i % len(regions)],
                "account_tier": tiers[i % len(tiers)],
                "player_level": (i % 99) + 1,
                "experience_points": (i * 2450) + 1500,
                "settings_profile": json.dumps(settings),
                "created_at": created_dt,
                "last_login_at": login_dt
            })
        conn.execute(text("""
            INSERT INTO players (
                player_id, username, email, region, account_tier, player_level,
                experience_points, settings_profile, created_at, last_login_at
            ) VALUES (
                :player_id, :username, :email, :region, :account_tier, :player_level,
                :experience_points, :settings_profile, :created_at, :last_login_at
            )
        """), players_rows)
        print("    -> 500 rows inserted into 'players'.")

        # Seed player_characters (500)
        print("  Generating 500 rows for 'player_characters'...")
        classes = ["WARRIOR", "MAGE", "ROGUE", "PALADIN", "ARCHER", "NECROMANCER", "DRUID"]
        characters_rows = []
        for i in range(1, 501):
            c_id = 2000 + i
            player_ref = 1000 + ((i - 1) % 500 + 1)
            char_class = classes[i % len(classes)]
            attributes = {
                "strength": 50 + (i % 150),
                "agility": 45 + ((i * 2) % 160),
                "intelligence": 40 + ((i * 3) % 180),
                "vitality": 100 + (i % 250),
                "mana_pool": 300 + (i * 5),
                "critical_rate": round(0.05 + ((i % 40) * 0.01), 3),
                "resistances": {
                    "fire": random.randint(10, 75),
                    "frost": random.randint(10, 75),
                    "poison": random.randint(5, 50)
                }
            }
            talents = [
                {"tier": 1, "talent": f"{char_class} Focus", "rank": (i % 5) + 1, "unlocked": True},
                {"tier": 2, "talent": f"{char_class} Mastery", "rank": (i % 3) + 1, "unlocked": (i % 2 == 0)}
            ]
            characters_rows.append({
                "character_id": c_id,
                "player_id": player_ref,
                "character_name": f"Hero_{char_class[:3]}_{i:03d}",
                "character_class": char_class,
                "level": (i % 79) + 1,
                "gold_balance": round(150.0 + (i * 32.75), 2),
                "base_attributes": json.dumps(attributes),
                "active_talents": json.dumps(talents),
                "created_at": base_time + timedelta(hours=i * 5)
            })
        conn.execute(text("""
            INSERT INTO player_characters (
                character_id, player_id, character_name, character_class, level,
                gold_balance, base_attributes, active_talents, created_at
            ) VALUES (
                :character_id, :player_id, :character_name, :character_class, :level,
                :gold_balance, :base_attributes, :active_talents, :created_at
            )
        """), characters_rows)
        print("    -> 500 rows inserted into 'player_characters'.")

        # Seed inventory_items (500)
        print("  Generating 500 rows for 'inventory_items'...")
        types = ["WEAPON", "ARMOR", "SHIELD", "RING", "AMULET", "RELIC"]
        rarities = ["COMMON", "UNCOMMON", "RARE", "EPIC", "LEGENDARY", "MYTHIC"]
        gem_types = ["Crimson Ruby (+Attack)", "Void Amethyst (+Spell Vamp)", "Azure Sapphire (+Mana)", "Topaz (+Speed)"]
        items_rows = []
        for i in range(1, 501):
            it_id = 3000 + i
            char_ref = 2000 + ((i - 1) % 500 + 1)
            rarity = rarities[i % len(rarities)]
            item_type = types[i % len(types)]
            payload = {
                "item_level": 50 + (i % 450),
                "durability": {"current": random.randint(60, 100), "max": 100},
                "sockets": [
                    {"slot": 1, "gem": gem_types[i % len(gem_types)]},
                    {"slot": 2, "gem": gem_types[(i + 1) % len(gem_types)]}
                ] if rarity in ["EPIC", "LEGENDARY", "MYTHIC"] else [],
                "affixes": [
                    f"+{10 + (i % 30)} Primary Stat",
                    f"+{round(1.5 + (i % 10) * 0.5, 1)}% Crit Multiplier"
                ],
                "binding": "ACCOUNT_BOUND" if rarity in ["LEGENDARY", "MYTHIC"] else "EQUIP_BOUND",
                "vendor_value_gold": 25 * (i % 50 + 1)
            }
            items_rows.append({
                "item_id": it_id,
                "character_id": char_ref,
                "item_code": f"ITM-{item_type[:3]}-{i:04d}",
                "item_name": f"{rarity.capitalize()} {item_type.capitalize()} of Valor #{i}",
                "item_type": item_type,
                "rarity": rarity,
                "is_equipped": (i % 3 == 0),
                "item_payload": json.dumps(payload),
                "acquired_at": base_time + timedelta(hours=i * 6)
            })
        conn.execute(text("""
            INSERT INTO inventory_items (
                item_id, character_id, item_code, item_name, item_type,
                rarity, is_equipped, item_payload, acquired_at
            ) VALUES (
                :item_id, :character_id, :item_code, :item_name, :item_type,
                :rarity, :is_equipped, :item_payload, :acquired_at
            )
        """), items_rows)
        print("    -> 500 rows inserted into 'inventory_items'.")

        # Seed match_sessions (500)
        print("  Generating 500 rows for 'match_sessions'...")
        modes = ["BATTLE_ROYALE", "RANKED_ARENA", "RAID_DUNGEON", "COOP_STORY", "DEATHMATCH"]
        maps = ["Crimson Citadel", "Frozen Tundra", "Neon Spire", "Shadow Gorge", "Sunken Temple"]
        results = ["VICTORY", "DEFEAT", "DRAW"]
        gpus = ["NVIDIA RTX 4090", "NVIDIA RTX 4080", "AMD Radeon RX 7900 XTX", "NVIDIA RTX 3070", "Apple M3 Max"]
        sessions_rows = []
        for i in range(1, 501):
            sess_id = 4000 + i
            player_ref = 1000 + ((i - 1) % 500 + 1)
            duration = 300 + (i * 6)
            sess_start = base_time + timedelta(hours=i * 7)
            sess_end = sess_start + timedelta(seconds=duration)
            hw = {
                "client_os": "Windows 11 23H2" if i % 2 == 0 else "macOS Sonoma",
                "gpu": gpus[i % len(gpus)],
                "avg_fps": round(110.0 + (i % 70), 1),
                "latency_ping_ms": round(18.0 + (i % 65), 1),
                "packet_loss_pct": round((i % 5) * 0.05, 2),
                "ram_allocated_gb": random.choice([16, 32, 64])
            }
            sessions_rows.append({
                "session_id": sess_id,
                "player_id": player_ref,
                "session_uuid": str(uuid.uuid4()),
                "game_mode": modes[i % len(modes)],
                "map_name": maps[i % len(maps)],
                "duration_seconds": duration,
                "match_result": results[i % len(results)],
                "hardware_metrics": json.dumps(hw),
                "started_at": sess_start,
                "ended_at": sess_end
            })
        conn.execute(text("""
            INSERT INTO match_sessions (
                session_id, player_id, session_uuid, game_mode, map_name,
                duration_seconds, match_result, hardware_metrics, started_at, ended_at
            ) VALUES (
                :session_id, :player_id, :session_uuid, :game_mode, :map_name,
                :duration_seconds, :match_result, :hardware_metrics, :started_at, :ended_at
            )
        """), sessions_rows)
        print("    -> 500 rows inserted into 'match_sessions'.")

        # Seed combat_events (500)
        print("  Generating 500 rows for 'combat_events'...")
        events = ["PLAYER_KILL", "SPELL_CAST", "DAMAGE_TAKEN", "OBJECTIVE_CAPTURED", "DEBUFF_APPLIED"]
        spells = ["Fireball", "Frostbolt", "Shadowstep", "Holy Shield", "Thunderstrike", "Poison Dart"]
        combat_rows = []
        for i in range(1, 501):
            ev_id = 5000 + i
            sess_ref = 4000 + ((i - 1) % 500 + 1)
            event_type = events[i % len(events)]
            telemetry = {
                "action": event_type,
                "ability": spells[i % len(spells)],
                "damage": round(250.0 + (i * 14.5), 1),
                "critical_strike": (i % 4 == 0),
                "coordinates": {
                    "x": round(100.0 + (i * 3.4), 2),
                    "y": round(200.0 + (i * 2.1), 2),
                    "z": round(15.0 + (i % 20), 2)
                },
                "target": {
                    "entity_type": "PLAYER" if i % 2 == 0 else "RAID_BOSS",
                    "entity_id": f"ENT-{8000 + (i % 100)}"
                },
                "active_buffs": ["BERSERK", "ARCANE_FOCUS"] if i % 3 == 0 else ["SPEED_AURA"]
            }
            combat_rows.append({
                "event_id": ev_id,
                "session_id": sess_ref,
                "event_type": event_type,
                "tick_ms": i * 1500,
                "telemetry_data": json.dumps(telemetry),
                "occurred_at": base_time + timedelta(hours=i * 7, seconds=i * 2)
            })
        conn.execute(text("""
            INSERT INTO combat_events (
                event_id, session_id, event_type, tick_ms, telemetry_data, occurred_at
            ) VALUES (
                :event_id, :session_id, :event_type, :tick_ms, :telemetry_data, :occurred_at
            )
        """), combat_rows)
        print("    -> 500 rows inserted into 'combat_events'.")

    # 4. Verification of counts
    print("\n--- Verifying PostgreSQL Table Row Counts ---")
    with engine.connect() as conn:
        for tbl in ["players", "player_characters", "inventory_items", "match_sessions", "combat_events"]:
            cnt = conn.execute(text(f"SELECT COUNT(*) FROM {tbl};")).scalar()
            print(f"  [PostgreSQL] Table '{tbl}': {cnt} rows")
            assert cnt == 500, f"Expected 500 rows in {tbl}, got {cnt}"


def seed_mysql():
    print(f"\n================================================================================")
    print(f" >>> PROVISIONING & SEEDING MYSQL: {MYSQL_DB_NAME}")
    print(f"================================================================================")
    engine = create_engine(MYSQL_TARGET_URL, connect_args={"connect_timeout": 5})

    with engine.begin() as conn:
        # 1. Clean existing tables if present
        print("  Dropping legacy tables if any...")
        conn.execute(text("SET FOREIGN_KEY_CHECKS = 0;"))
        conn.execute(text("DROP TABLE IF EXISTS quest_progressions;"))
        conn.execute(text("DROP TABLE IF EXISTS auction_transactions;"))
        conn.execute(text("DROP TABLE IF EXISTS auction_listings;"))
        conn.execute(text("DROP TABLE IF EXISTS guild_members;"))
        conn.execute(text("DROP TABLE IF EXISTS guilds;"))
        conn.execute(text("SET FOREIGN_KEY_CHECKS = 1;"))

        # 2. Create DDL with native MySQL JSON document columns
        print("  Creating MySQL relational schemas with native JSON document support...")
        conn.execute(text("""
            CREATE TABLE guilds (
                guild_id INT PRIMARY KEY,
                guild_name VARCHAR(100) UNIQUE NOT NULL,
                guild_tag VARCHAR(10) NOT NULL,
                realm_name VARCHAR(50) NOT NULL,
                guild_level INT NOT NULL,
                treasury_gold DECIMAL(15, 2) NOT NULL,
                member_count INT NOT NULL,
                perk_tree JSON NOT NULL,
                created_at DATETIME NOT NULL
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """))

        conn.execute(text("""
            CREATE TABLE guild_members (
                member_id INT PRIMARY KEY,
                guild_id INT NOT NULL,
                player_tag VARCHAR(100) NOT NULL,
                guild_role VARCHAR(50) NOT NULL,
                contribution_points INT NOT NULL,
                role_permissions JSON NOT NULL,
                joined_at DATETIME NOT NULL,
                last_active_at DATETIME NOT NULL,
                CONSTRAINT fk_guild_member_guild FOREIGN KEY (guild_id) REFERENCES guilds (guild_id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """))

        conn.execute(text("""
            CREATE TABLE auction_listings (
                listing_id INT PRIMARY KEY,
                seller_tag VARCHAR(100) NOT NULL,
                item_name VARCHAR(150) NOT NULL,
                category VARCHAR(50) NOT NULL,
                starting_bid_gold DECIMAL(12, 2) NOT NULL,
                buyout_gold DECIMAL(12, 2) NOT NULL,
                status VARCHAR(30) NOT NULL,
                item_attributes JSON NOT NULL,
                created_at DATETIME NOT NULL,
                expires_at DATETIME NOT NULL
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """))

        conn.execute(text("""
            CREATE TABLE auction_transactions (
                transaction_id INT PRIMARY KEY,
                listing_id INT NOT NULL,
                buyer_tag VARCHAR(100) NOT NULL,
                seller_tag VARCHAR(100) NOT NULL,
                final_price_gold DECIMAL(12, 2) NOT NULL,
                house_fee_gold DECIMAL(10, 2) NOT NULL,
                net_seller_payout DECIMAL(12, 2) NOT NULL,
                transaction_details JSON NOT NULL,
                settled_at DATETIME NOT NULL,
                CONSTRAINT fk_trans_listing FOREIGN KEY (listing_id) REFERENCES auction_listings (listing_id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """))

        conn.execute(text("""
            CREATE TABLE quest_progressions (
                progress_id INT PRIMARY KEY,
                player_tag VARCHAR(100) NOT NULL,
                quest_code VARCHAR(50) NOT NULL,
                quest_title VARCHAR(150) NOT NULL,
                difficulty VARCHAR(30) NOT NULL,
                is_completed TINYINT(1) NOT NULL DEFAULT 0,
                milestones_tree JSON NOT NULL,
                started_at DATETIME NOT NULL,
                last_progress_at DATETIME NOT NULL
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """))
        print("  [OK] MySQL DDL created successfully.")

        # 3. Generate 500 rows for each table
        realms = ["Elysium-Prime", "Shadow-Reach", "Iron-Keep", "Silver-Spire", "Obsidian-Peak"]
        roles = ["GUILD_MASTER", "OFFICER", "VETERAN", "MEMBER", "RECRUIT"]
        categories = ["WEAPON", "ARMOR", "CRAFTING_MATERIAL", "POTION", "ENCHANTMENT"]
        statuses = ["ACTIVE", "SOLD", "EXPIRED", "CANCELLED"]
        difficulties = ["NOVICE", "INTERMEDIATE", "HEROIC", "MYTHIC"]
        base_time = datetime(2026, 1, 1, 0, 0, 0)

        # Seed guilds (500)
        print("  Generating 500 rows for 'guilds'...")
        guild_rows = []
        for i in range(1, 501):
            g_id = 1000 + i
            perks = {
                "tier": (i % 5) + 1,
                "unlocked_perks": [
                    {"perk_code": f"VAULT_EXPANSION_{i%3+1}", "multiplier": 1.25, "active": True},
                    {"perk_code": f"EXP_AURA_{i%4+1}", "bonus_pct": 5 + (i % 15), "active": True}
                ],
                "crest": {
                    "primary_color": random.choice(["#E63946", "#F1FAEE", "#A8DADC", "#457B9D", "#1D3557"]),
                    "symbol": random.choice(["LION", "PHOENIX", "DRAGON", "WOLF", "EAGLE"])
                },
                "alliance_id": f"ALLIANCE-{(i % 20) + 1:03d}"
            }
            guild_rows.append({
                "guild_id": g_id,
                "guild_name": f"Guild_Legion_{i:03d}_{random.choice(['Vanguard', 'Syndicate', 'Order', 'Covenant'])}",
                "guild_tag": f"L{i:03d}",
                "realm_name": realms[i % len(realms)],
                "guild_level": (i % 49) + 1,
                "treasury_gold": round(1000.0 + (i * 245.5), 2),
                "member_count": 10 + (i % 90),
                "perk_tree": json.dumps(perks),
                "created_at": base_time + timedelta(days=i // 3, hours=i % 24)
            })
        conn.execute(text("""
            INSERT INTO guilds (
                guild_id, guild_name, guild_tag, realm_name, guild_level,
                treasury_gold, member_count, perk_tree, created_at
            ) VALUES (
                :guild_id, :guild_name, :guild_tag, :realm_name, :guild_level,
                :treasury_gold, :member_count, :perk_tree, :created_at
            )
        """), guild_rows)
        print("    -> 500 rows inserted into 'guilds'.")

        # Seed guild_members (500)
        print("  Generating 500 rows for 'guild_members'...")
        member_rows = []
        for i in range(1, 501):
            m_id = 2000 + i
            guild_ref = 1000 + ((i - 1) % 500 + 1)
            role = roles[i % len(roles)]
            permissions = {
                "can_invite": role in ["GUILD_MASTER", "OFFICER"],
                "can_kick": role in ["GUILD_MASTER"],
                "can_access_vault": role != "RECRUIT",
                "daily_withdraw_limit_gold": 1000 if role in ["GUILD_MASTER", "OFFICER"] else 100,
                "can_declare_war": (role == "GUILD_MASTER")
            }
            joined_dt = base_time + timedelta(days=i // 2, hours=i % 20)
            active_dt = joined_dt + timedelta(days=random.randint(1, 30))
            member_rows.append({
                "member_id": m_id,
                "guild_id": guild_ref,
                "player_tag": f"Tag_Knight_{i:03d}",
                "guild_role": role,
                "contribution_points": (i * 125) + 300,
                "role_permissions": json.dumps(permissions),
                "joined_at": joined_dt,
                "last_active_at": active_dt
            })
        conn.execute(text("""
            INSERT INTO guild_members (
                member_id, guild_id, player_tag, guild_role,
                contribution_points, role_permissions, joined_at, last_active_at
            ) VALUES (
                :member_id, :guild_id, :player_tag, :guild_role,
                :contribution_points, :role_permissions, :joined_at, :last_active_at
            )
        """), member_rows)
        print("    -> 500 rows inserted into 'guild_members'.")

        # Seed auction_listings (500)
        print("  Generating 500 rows for 'auction_listings'...")
        auction_rows = []
        for i in range(1, 501):
            auc_id = 3000 + i
            cat = categories[i % len(categories)]
            start_price = round(50.0 + (i * 12.0), 2)
            buyout_price = round(start_price * 1.5, 2)
            created_dt = base_time + timedelta(hours=i * 5)
            expires_dt = created_dt + timedelta(hours=48)
            attributes = {
                "rarity": random.choice(["RARE", "EPIC", "LEGENDARY"]),
                "durability_pct": 100,
                "required_level": 20 + (i % 60),
                "custom_enchantment": f"Frostfire Spark +{15 + (i % 25)}",
                "crafting_tags": [cat, "VERIFIED_AUTHENTIC", "HIGH_DEMAND"],
                "creator_signature": f"Artisan_Blacksmith_{i % 50:02d}"
            }
            auction_rows.append({
                "listing_id": auc_id,
                "seller_tag": f"Merchant_Seller_{(i % 100) + 1:03d}",
                "item_name": f"Imperial {cat.capitalize()} of the Dawn #{i}",
                "category": cat,
                "starting_bid_gold": start_price,
                "buyout_gold": buyout_price,
                "status": statuses[i % len(statuses)],
                "item_attributes": json.dumps(attributes),
                "created_at": created_dt,
                "expires_at": expires_dt
            })
        conn.execute(text("""
            INSERT INTO auction_listings (
                listing_id, seller_tag, item_name, category,
                starting_bid_gold, buyout_gold, status, item_attributes,
                created_at, expires_at
            ) VALUES (
                :listing_id, :seller_tag, :item_name, :category,
                :starting_bid_gold, :buyout_gold, :status, :item_attributes,
                :created_at, :expires_at
            )
        """), auction_rows)
        print("    -> 500 rows inserted into 'auction_listings'.")

        # Seed auction_transactions (500)
        print("  Generating 500 rows for 'auction_transactions'...")
        trans_rows = []
        for i in range(1, 501):
            tx_id = 4000 + i
            listing_ref = 3000 + ((i - 1) % 500 + 1)
            final_price = round(80.0 + (i * 18.0), 2)
            fee = round(final_price * 0.05, 2)
            net_payout = round(final_price - fee, 2)
            details = {
                "escrow_id": f"ESC-AUCT-{i:05d}",
                "payment_type": "INSTANT_BUYOUT" if i % 2 == 0 else "BID_HAMMER",
                "tax_rate_pct": 5.0,
                "settlement_currency": "IMPERIAL_GOLD",
                "audit_hash": f"sha256_mock_{i:04d}_{uuid.uuid4().hex[:12]}"
            }
            trans_rows.append({
                "transaction_id": tx_id,
                "listing_id": listing_ref,
                "buyer_tag": f"Collector_Buyer_{(i % 120) + 1:03d}",
                "seller_tag": f"Merchant_Seller_{(i % 100) + 1:03d}",
                "final_price_gold": final_price,
                "house_fee_gold": fee,
                "net_seller_payout": net_payout,
                "transaction_details": json.dumps(details),
                "settled_at": base_time + timedelta(hours=i * 5, minutes=30)
            })
        conn.execute(text("""
            INSERT INTO auction_transactions (
                transaction_id, listing_id, buyer_tag, seller_tag,
                final_price_gold, house_fee_gold, net_seller_payout,
                transaction_details, settled_at
            ) VALUES (
                :transaction_id, :listing_id, :buyer_tag, :seller_tag,
                :final_price_gold, :house_fee_gold, :net_seller_payout,
                :transaction_details, :settled_at
            )
        """), trans_rows)
        print("    -> 500 rows inserted into 'auction_transactions'.")

        # Seed quest_progressions (500)
        print("  Generating 500 rows for 'quest_progressions'...")
        quest_rows = []
        for i in range(1, 501):
            q_id = 5000 + i
            is_comp = 1 if (i % 3 == 0) else 0
            milestones = {
                "current_stage": 5 if is_comp else (i % 4) + 1,
                "total_stages": 5,
                "branches": [
                    {"objective": f"Defeat Dungeon Boss Level {i % 10 + 1}", "target": 1, "progress": 1 if is_comp else 0, "done": bool(is_comp)},
                    {"objective": f"Recover Lost Artifact #{i}", "target": 10, "progress": 10 if is_comp else (i % 9), "done": bool(is_comp)}
                ],
                "lore_discoveries": [f"LORE_TOME_{i % 50:02d}", "LORE_PROPHECY_ANCIENTS"],
                "bonus_challenges": {
                    "completed_within_timer": bool(i % 2 == 0),
                    "zero_deaths": bool(i % 4 == 0)
                }
            }
            quest_rows.append({
                "progress_id": q_id,
                "player_tag": f"Quester_Hero_{(i % 150) + 1:03d}",
                "quest_code": f"QST-ARC-{i:04d}",
                "quest_title": f"Chronicles of the Astral Realm: Chapter {i}",
                "difficulty": difficulties[i % len(difficulties)],
                "is_completed": is_comp,
                "milestones_tree": json.dumps(milestones),
                "started_at": base_time + timedelta(hours=i * 3),
                "last_progress_at": base_time + timedelta(hours=i * 3, minutes=45)
            })
        conn.execute(text("""
            INSERT INTO quest_progressions (
                progress_id, player_tag, quest_code, quest_title,
                difficulty, is_completed, milestones_tree, started_at, last_progress_at
            ) VALUES (
                :progress_id, :player_tag, :quest_code, :quest_title,
                :difficulty, :is_completed, :milestones_tree, :started_at, :last_progress_at
            )
        """), quest_rows)
        print("    -> 500 rows inserted into 'quest_progressions'.")

    # 4. Verification of counts
    print("\n--- Verifying MySQL Table Row Counts ---")
    with engine.connect() as conn:
        for tbl in ["guilds", "guild_members", "auction_listings", "auction_transactions", "quest_progressions"]:
            cnt = conn.execute(text(f"SELECT COUNT(*) FROM `{tbl}`;")).scalar()
            print(f"  [MySQL] Table '{tbl}': {cnt} rows")
            assert cnt == 500, f"Expected 500 rows in {tbl}, got {cnt}"


def main():
    print("================================================================================")
    print(" >>> STARTING MULTI-DB PROVISIONING (POSTGRESQL & MYSQL)")
    print("     Topic: Gaming Telemetry & Virtual Economy (Document/NoSQL Domain in RDBMS)")
    print("================================================================================")

    # 1. PostgreSQL setup
    ensure_postgres_database()
    seed_postgres()

    # 2. MySQL setup
    ensure_mysql_database()
    seed_mysql()

    print("\n================================================================================")
    print(" [ALL COMPLETE] 2 New Databases Provisioned & Seeded!")
    print("  1. PostgreSQL: 'gaming_telemetry_pg' -> 5 tables x 500 rows = 2,500 rows")
    print("  2. MySQL:      'gaming_economy_mysql' -> 5 tables x 500 rows = 2,500 rows")
    print("  Total rows populated: 5,000 across 10 tables.")
    print("================================================================================")


if __name__ == "__main__":
    main()
