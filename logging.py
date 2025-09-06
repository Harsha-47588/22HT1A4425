import json, time, uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from datetime import datetime, timezone
import os

LOG_PATH = os.getenv("LOG_PATH", "data/access.log.jsonl")

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.time()
        rid = str(uuid.uuid4())
        req_payload = {
            "id": rid,
            "ts": datetime.now(timezone.utc).isoformat(),
            "method": request.method,
            "path": str(request.url),
            "headers": {"user-agent": request.headers.get("user-agent"), "referer": request.headers.get("referer")},
        }
        response: Response | None = None
        try:
            response = await call_next(request)
            return response
        finally:
            duration_ms = int((time.time() - start)*1000)
            log_item = {**req_payload, "status": getattr(response, "status_code", None), "duration_ms": duration_ms}
            os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
            with open(LOG_PATH, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_item, ensure_ascii=False) + "\n")
