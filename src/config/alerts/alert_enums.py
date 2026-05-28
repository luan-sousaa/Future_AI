from enum import Enum


class AlertTypeEnum(Enum):
    CRITICAL = "critical"
    LOW_STOCK = "low_stock"
    ZERO_STOCK = "zero_stock"
    RUPTURE_RISK = "rupture_risk"
    NEGATIVE_STOCK = "negative_stock"
    OUT_OF_STOCK = "out_of_stock"
    INACTIVE = "inactive"
    OVERSTOCKED = "overstocked"
    HIGH_MOVEMENT = "high_movement"
    LOW_MOVEMENT = "low_movement"