"""
One-click migration plan patcher for faulty timestamp mappings (e.g. category_id, product_id, item_id mapped to created_at/updated_at).
"""
import asyncio
import json
import uuid
from sqlalchemy import select
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

async def patch_plan():
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
            for col in tm.get("column_mappings", []):
                tcol = col.get("target_column_name")
                ttype = str(col.get("target_data_type", "")).lower()

                if tcol in ("created_at", "updated_at") or any(x in ttype for x in ("timestamp", "datetime", "timestamptz")):
                    # Filter out non-datetime source columns like category_id, product_id, item_id
                    orig_sources = col.get("source_columns", [])
                    cleaned_sources = [
                        sc for sc in orig_sources
                        if not ("id" in sc.get("column_name", "").lower() and sc.get("column_name", "").lower() not in ("created_at", "updated_at"))
                    ]
                    if len(cleaned_sources) != len(orig_sources):
                        removed = [sc.get("column_name") for sc in orig_sources if sc not in cleaned_sources]
                        print(f"[{tname}.{tcol}] Removed invalid source column(s): {removed}")
                        col["source_columns"] = cleaned_sources
                        modified_count += 1

        if modified_count > 0:
            plan.plan_data = plan_data
            # flag as modified in SQLAlchemy
            from sqlalchemy.orm.attributes import flag_modified
            flag_modified(plan, "plan_data")
            await session.commit()
            print(f"[SUCCESS] Patched {modified_count} column mappings in plan {PLAN_ID}!")
        else:
            print("[INFO] No faulty timestamp mappings found in plan.")

if __name__ == "__main__":
    asyncio.run(patch_plan())
