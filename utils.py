import os, random, string
from datetime import datetime, timedelta, timezone
from typing import Optional

DEFAULT_VALIDITY_MINUTES = int(os.getenv("DEFAULT_VALIDITY_MINUTES", "30"))

def now_utc():
    return datetime.now(timezone.utc)

def calc_expiry(validity_minutes: Optional[int]) -> datetime:
    mins = validity_minutes if validity_minutes is not None else DEFAULT_VALIDITY_MINUTES
    return now_utc() + timedelta(minutes=int(mins))

def gen_shortcode(n: int = 6) -> str:
    alphabet = string.ascii_letters + string.digits
    return ''.join(random.choice(alphabet) for _ in range(n))

def build_base_url(scheme: str, host: str, base_env: Optional[str] = None) -> str:
    if base_env:
        return base_env.rstrip('/')
    return f"{scheme}://{host}".rstrip('/')
