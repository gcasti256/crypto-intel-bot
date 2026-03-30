from __future__ import annotations

import datetime

from pydantic import BaseModel, Field


class PriceAlert(BaseModel):
    user_id: str
    guild_id: str = ""
    token: str
    condition: str  # "above" or "below"
    threshold: float
    active: bool = True
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.now)
    triggered_at: datetime.datetime | None = None

    def check(self, current_price: float) -> bool:
        if not self.active:
            return False
        if self.condition == "above":
            return current_price >= self.threshold
        elif self.condition == "below":
            return current_price <= self.threshold
        return False
