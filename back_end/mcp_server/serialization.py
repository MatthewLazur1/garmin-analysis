import json
from typing import Any, Dict, List

import pandas as pd


def df_to_records(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """Convert a DataFrame to a list of JSON-safe dicts (native types, NaN -> None)."""
    if df is None or df.empty:
        return []
    return json.loads(df.to_json(orient='records', date_format='iso'))


def df_to_record(df: pd.DataFrame) -> Dict[str, Any]:
    """Convert a one-row DataFrame to a single JSON-safe dict."""
    records = df_to_records(df)
    return records[0] if records else {}
