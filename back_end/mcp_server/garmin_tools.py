from typing import Any, Dict, List

from back_end.mcp_server.app import mcp
from back_end.mcp_server.context import get_garmin_client, get_report_builder
from back_end.mcp_server.serialization import df_to_record, df_to_records


@mcp.tool()
def get_weekly_mileage(start_date: str, end_date: str) -> List[Dict[str, Any]]:
    """Get weekly running mileage totals between two dates (YYYY-MM-DD)."""
    client = get_garmin_client()
    df = get_report_builder().aggregate_weekly_mileage(client, start_date, end_date)
    if df.empty:
        return []
    df = df.reset_index().rename(columns={
        'Total_Miles': 'total_miles',
        'Activity_Count': 'activity_count',
    })
    return df_to_records(df)


@mcp.tool()
def get_personal_records() -> List[Dict[str, str]]:
    """Get all-time personal records (5K, 10K, Half Marathon, Marathon) with time and pace."""
    client = get_garmin_client()
    df = get_report_builder().get_all_time_prs(client)
    df = df.rename(columns={'Distance': 'distance', 'Time': 'time', 'Pace': 'pace'})
    return df_to_records(df)


@mcp.tool()
def list_activities(start_date: str, end_date: str) -> List[Dict[str, Any]]:
    """
    List individual running activities between two dates (YYYY-MM-DD), with
    activity_id, name, date, type, distance, average heart rate, and pace.
    """
    client = get_garmin_client()
    df = get_report_builder().list_activities(client, start_date, end_date)
    return df_to_records(df)


@mcp.tool()
def get_activity_detail(activity_id: int) -> Dict[str, Any]:
    """
    Get details for a single activity by its Garmin activity ID: distance,
    pace, average heart rate, elevation gain, start/finish time.
    """
    client = get_garmin_client()
    df = get_report_builder().get_activity_summary(client, activity_id)
    return df_to_record(df)


@mcp.tool()
def get_health_snapshot(target_date: str) -> Dict[str, Any]:
    """Get sleep score, HRV, and resting heart rate for a given date (YYYY-MM-DD)."""
    client = get_garmin_client()
    df = get_report_builder().get_health_snapshot(client, target_date)
    return df_to_record(df)
