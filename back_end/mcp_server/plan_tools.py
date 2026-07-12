from typing import Any, Dict, List

from back_end.marathon_objects.marathon_plan_manager import MarathonPlan
from back_end.mcp_server.app import mcp
from back_end.mcp_server.context import get_report_manager


@mcp.tool()
def list_marathon_plans() -> List[str]:
    """List the names of all saved marathon plans."""
    return get_report_manager().list_plans()


@mcp.tool()
def get_marathon_plan(name: str) -> Dict[str, Any]:
    """
    Get a marathon plan by name: start/race dates plus a week-by-week breakdown
    of planned distance, run type, and notes for each day (Mon-Sun).
    """
    result = get_report_manager().load_plan(name)
    if result is None:
        return {'found': False, 'name': name}
    plan_name, start, end, df = result

    weeks = []
    for _, row in df.iterrows():
        days = {}
        for day in MarathonPlan.DAY_COLUMNS:
            days[day] = {
                'distance_miles': float(row.get(f'{day}_Dist', 0.0) or 0.0),
                'type': str(row.get(f'{day}_Type', '') or ''),
                'notes': str(row.get(f'{day}_Notes', '') or ''),
            }
        weekly_total = round(sum(d['distance_miles'] for d in days.values()), 2)
        weeks.append({
            'week_number': int(row['Week']),
            'start_date': str(row['First_Monday']),
            'days': days,
            'weekly_total_miles': weekly_total,
        })

    return {
        'found': True,
        'name': plan_name,
        'start_date': str(start),
        'race_date': str(end),
        'weeks': weeks,
    }
