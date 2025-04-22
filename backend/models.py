from datetime import date
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class HarvestPayload(BaseModel):
    """
    Pydantic model for validating and serializing agricultural harvest event data.
    Enforces strict type and value constraints on each field.
    """

    area: float = Field(..., gt=0, description="Hectares harvested", strict=True)
    production: float = Field(
        ..., ge=0, description="Total tons harvested", strict=True
    )
    loss_percentage: float = Field(
        ...,
        ge=0,
        le=100,
        description="Percentage of crop lost during harvest",
        strict=True,
    )
    duration_hours: float = Field(
        ..., gt=0, description="Total hours spent harvesting", strict=True
    )
    harvest_method: Literal["manual", "mechanical"] = Field(
        ..., description="Harvest method"
    )
    moisture_percentage: float = Field(
        ...,
        ge=0,
        le=100,
        description="Moisture content percentage at harvest",
        strict=True,
    )
    harvest_date: date = Field(..., description="Date of harvest")
    operator_id: str = Field(
        ..., min_length=1, max_length=64, description="Operator identifier"
    )
    equipment_id: str = Field(
        ..., min_length=1, max_length=64, description="Equipment identifier"
    )
    variety: str = Field(..., min_length=1, max_length=64, description="Cane variety")
    ambient_temperature: float = Field(
        ..., description="Ambient temp (°C)", strict=True
    )
    brix_percentage: float = Field(
        ..., ge=0, le=30, description="°Brix sugar content", strict=True
    )

    @field_validator("operator_id", "equipment_id", "variety")
    @classmethod
    def _strip_strings(cls, v: str) -> str:
        """Strip leading/trailing whitespace from string fields."""
        return v.strip()

    @field_validator("harvest_date")
    @classmethod
    def date_not_in_future(cls, v: date) -> date:
        """Ensure harvest_date is not set in the future."""
        if v > date.today():
            raise ValueError("harvest_date cannot be in the future")
        return v
