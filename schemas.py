from pydantic import BaseModel, HttpUrl, Field, field_validator
from typing import Optional, List
from datetime import datetime

SHORTCODE_REGEX = r"^[A-Za-z0-9]{4,20}$"

class CreateShortURLRequest(BaseModel):
    url: HttpUrl
    validity: Optional[int] = Field(default=None, description="in minutes")
    shortcode: Optional[str] = None

    @field_validator("shortcode")
    @classmethod
    def validate_shortcode(cls, v):
        import re
        if v is None:
            return v
        if not re.fullmatch(SHORTCODE_REGEX, v):
            raise ValueError("shortcode must be alphanumeric (4-20 chars)")
        return v

class ShortURLResponse(BaseModel):
    shortcode: str
    shortLink: str
    expiry: datetime
    createdAt: datetime
    url: HttpUrl

class ClickInfo(BaseModel):
    timestamp: datetime
    referrer: Optional[str] = None
    ip: Optional[str] = None
    country: Optional[str] = None

class StatsResponse(BaseModel):
    shortcode: str
    url: HttpUrl
    createdAt: datetime
    expiry: datetime
    totalClicks: int
    clicks: List[ClickInfo]
