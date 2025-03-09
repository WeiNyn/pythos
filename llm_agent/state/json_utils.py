"""
JSON utilities for state management
"""
from datetime import datetime
from json import JSONEncoder
from typing import Any

class DateTimeJSONEncoder(JSONEncoder):
    """JSON encoder that can handle datetime objects"""
    def default(self, obj: Any) -> Any:
        if isinstance(obj, datetime):
            return {
                "__type__": "datetime",
                "value": obj.isoformat()
            }
        return super().default(obj)

def json_decoder_hook(obj: dict) -> Any:
    """Hook for decoding special JSON objects"""
    if "__type__" in obj:
        if obj["__type__"] == "datetime":
            return datetime.fromisoformat(obj["value"])
    return obj
