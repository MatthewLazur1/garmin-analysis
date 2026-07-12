from datetime import date, datetime, timedelta
from typing import List, Optional

from sqlalchemy import text
from sqlalchemy.engine import Engine

from back_end.marathon_objects.marathon_plan_manager import MarathonPlan, PlanRun, PlanWeek

_SCHEMA_STATEMENTS = [
    "create extension if not exists pgcrypto",
    """
    create table if not exists marathon_plans (
        id uuid primary key default gen_random_uuid(),
        name text unique not null,
        start_date date not null,
        race_date date not null,
        created_at timestamptz not null default now(),
        updated_at timestamptz not null default now()
    )
    """,
    """
    create table if not exists plan_weeks (
        id uuid primary key default gen_random_uuid(),
        plan_id uuid not null references marathon_plans(id) on delete cascade,
        week_number int not null,
        start_date date not null,
        unique (plan_id, week_number)
    )
    """,
    """
    create table if not exists plan_runs (
        id uuid primary key default gen_random_uuid(),
        week_id uuid not null references plan_weeks(id) on delete cascade,
        day_name text not null,
        run_date date not null,
        distance numeric not null default 0,
        run_type text not null default 'Rest',
        notes text not null default '',
        unique (week_id, day_name)
    )
    """,
    "create index if not exists idx_plan_weeks_plan_id on plan_weeks(plan_id)",
    "create index if not exists idx_plan_runs_week_id on plan_runs(week_id)",
    "create index if not exists idx_plan_runs_run_date on plan_runs(run_date)",
]


def ensure_schema(engine: Engine) -> None:
    with engine.begin() as conn:
        for statement in _SCHEMA_STATEMENTS:
            conn.execute(text(statement))


def list_plan_names(engine: Engine) -> List[str]:
    with engine.connect() as conn:
        rows = conn.execute(text("select name from marathon_plans order by name")).fetchall()
    return [row[0] for row in rows]


def load_plan(engine: Engine, name: str) -> Optional[MarathonPlan]:
    with engine.connect() as conn:
        plan_row = conn.execute(
            text("select id, name, start_date, race_date from marathon_plans where name = :name"),
            {"name": name},
        ).mappings().first()
        if plan_row is None:
            return None

        week_rows = conn.execute(
            text(
                "select id, week_number from plan_weeks where plan_id = :plan_id order by week_number"
            ),
            {"plan_id": plan_row["id"]},
        ).mappings().all()

        plan = MarathonPlan(plan_row["name"], plan_row["start_date"], plan_row["race_date"])
        plan_start = plan_row["start_date"]
        if isinstance(plan_start, datetime):
            plan_start = plan_start.date()
        plan_start_monday = plan_start - timedelta(days=plan_start.weekday())

        plan.weeks = []
        for week_row in week_rows:
            run_rows = conn.execute(
                text(
                    "select day_name, run_date, distance, run_type, notes "
                    "from plan_runs where week_id = :week_id"
                ),
                {"week_id": week_row["id"]},
            ).mappings().all()
            runs_by_day = {
                r["day_name"]: PlanRun(r["run_date"], float(r["distance"]), r["run_type"], r["notes"])
                for r in run_rows
            }
            week = PlanWeek(week_row["week_number"], plan_start_monday, MarathonPlan.RUN_TYPES, runs_by_day)
            plan.weeks.append(week)
        plan.df = plan.to_dataframe()
    return plan


def save_plan(engine: Engine, plan: MarathonPlan) -> None:
    with engine.begin() as conn:
        plan_id = conn.execute(
            text(
                """
                insert into marathon_plans (name, start_date, race_date)
                values (:name, :start_date, :race_date)
                on conflict (name) do update set
                    start_date = excluded.start_date,
                    race_date = excluded.race_date,
                    updated_at = now()
                returning id
                """
            ),
            {"name": plan.name, "start_date": plan.start, "race_date": plan.end},
        ).scalar_one()

        # Full replace of weeks/runs on every save, mirroring the prior CSV-overwrite behavior.
        conn.execute(text("delete from plan_weeks where plan_id = :plan_id"), {"plan_id": plan_id})

        for week in plan.weeks:
            week_id = conn.execute(
                text(
                    """
                    insert into plan_weeks (plan_id, week_number, start_date)
                    values (:plan_id, :week_number, :start_date)
                    returning id
                    """
                ),
                {"plan_id": plan_id, "week_number": week.week_number, "start_date": week.start_date},
            ).scalar_one()

            for day in MarathonPlan.DAY_COLUMNS:
                run = week.get_run(day)
                conn.execute(
                    text(
                        """
                        insert into plan_runs (week_id, day_name, run_date, distance, run_type, notes)
                        values (:week_id, :day_name, :run_date, :distance, :run_type, :notes)
                        """
                    ),
                    {
                        "week_id": week_id,
                        "day_name": day,
                        "run_date": run.get_date(),
                        "distance": run.get_distance(),
                        "run_type": run.get_type(),
                        "notes": run.get_notes(),
                    },
                )
