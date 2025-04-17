from pydantic import BaseModel, Field, field_validator
from typing import Literal
from datetime import date

class HarvestPayload(BaseModel):
    area: float = Field(..., gt=0, description="Hectares harvested")
    production: float = Field(..., ge=0, description="Total tons harvested")
    loss_percentage: float = Field(..., ge=0, le=100)
    duration_hours: float = Field(..., gt=0)
    harvest_method: Literal["manual", "mechanical"] = Field(..., description="Harvest method")
    moisture_percentage: float = Field(..., ge=0, le=100)
    harvest_date: date = Field(..., description="Date of harvest")
    operator_id: str = Field(..., min_length=1, description="Operator identifier")
    equipment_id: str = Field(..., min_length=1, description="Equipment identifier")
    variety: str = Field(..., min_length=1, description="Cane variety")
    ambient_temperature: float = Field(..., description="Ambient temp (°C)")
    brix_percentage: float = Field(..., ge=0, le=30, description="°Brix sugar content")

    @field_validator("operator_id", "equipment_id", "variety")
    def strip_strings(cls, v):
        return v.strip()
