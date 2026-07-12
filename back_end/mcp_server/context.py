from functools import lru_cache

from back_end.report_objects.report_builder import ReportBuilder
from back_end.report_objects.report_manager import ReportManager
from back_end.report_objects.report_reader import ReportReader

_garmin_client = None


def get_garmin_client():
    """Authenticate with Garmin on first call; reuse the client for the life of the process."""
    global _garmin_client
    if _garmin_client is None:
        _garmin_client = ReportReader().fetch_garmin_data()
    return _garmin_client


@lru_cache(maxsize=1)
def get_report_manager() -> ReportManager:
    return ReportManager()


@lru_cache(maxsize=1)
def get_report_builder() -> ReportBuilder:
    return ReportBuilder()
