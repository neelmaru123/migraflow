import asyncio
import json
import uuid
from sqlalchemy import select
from sqlalchemy.orm.attributes import flag_modified
from app.core.db import AsyncSessionLocal
import app.modules.agents.agents_models  # noqa: F401
import app.modules.evaluation.evaluation_models  # noqa: F401
import app.modules.execution.execution_models  # noqa: F401
import app.modules.metadata.metadata_models  # noqa: F401
import app.modules.observability.observability_models  # noqa: F401
import app.modules.sources.sources_models  # noqa: F401
import app.modules.migration_plans.migration_plans_models  # noqa: F401
import app.modules.users.users_models  # noqa: F401
from app.modules.migration_plans.migration_plans_models import MigrationPlan

PLAN_ID = "b7737db5-86c4-4b3b-bb1b-4c15ffe661ff"

async def patch():
    async with AsyncSessionLocal() as session:
        res = await session.execute(select(MigrationPlan).where(MigrationPlan.id == uuid.UUID(PLAN_ID)))
        plan = res.scalar_one_or_none()
        if not plan:
            print(f"[ERROR] Plan {PLAN_ID} not found.")
            return

        plan_data = dict(plan.plan_data)
        table_mappings = plan_data.get("table_mappings", [])
        modified_count = 0

        for tm in table_mappings:
            tname = tm.get("target_table_name")
            source_tables = tm.get("source_tables", [])
            num_sources = len(source_tables)

            for col in tm.get("column_mappings", []):
                cname = col.get("target_column_name")
                if cname in ("created_at", "updated_at"):
                    src_cols = col.get("source_columns", [])
                    # If the number of source columns is less than the number of source tables,
                    # or if transformation_type is not new_column_added, some source rows will have NULL.
                    # Setting to 'new_column_added' with CURRENT_TIMESTAMP ensures 100% non-null timestamps.
                    if len(src_cols) < num_sources or col.get("transformation_type") != "new_column_added":
                        print(f"Updating [{tname}.{cname}]: {col.get('transformation_type')} -> new_column_added")
                        col["transformation_type"] = "new_column_added"
                        col["ui_badge_type"] = "new_column_added"
                        col["constant_value"] = "CURRENT_TIMESTAMP"
                        col["source_columns"] = []
                        col["nullable"] = False
                        col["target_data_type"] = "timestamptz"
                        col["expression_template"] = None
                        modified_count += 1

        if modified_count > 0:
            plan.plan_data = plan_data
            flag_modified(plan, "plan_data")
            await session.commit()
            print(f"[SUCCESS] Updated {modified_count} audit column mappings to 'new_column_added' in plan {PLAN_ID}!")
        else:
            print("[INFO] No modifications needed.")

if __name__ == "__main__":
    asyncio.run(patch())
