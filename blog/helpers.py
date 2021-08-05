import datetime
import json


class CustomDateTimeJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime.datetime):
            s = o.isoformat()
            s = s[:23] + s[26:]
            return s[:-6] + "Z" if s.endswith("+00:00") else s
        else:
            return super().default(o)
