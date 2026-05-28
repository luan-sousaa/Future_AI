from enum import Enum
from typing import Dict, List

from src.config.alerts.alert_configs import (
    ALERT_TYPES,
    VALID_ALERT_TYPES,
    ALERTS_BY_SEVERITY,
)

from src.config.alerts.alert_aliases import (
    ALERT_TYPE_ALIASES,
)


class AlertTypeManager:

    @staticmethod
    def normalize(alert_type) -> str:
        if isinstance(alert_type, Enum):
            return alert_type.value

        normalized = str(alert_type).strip().lower()

        return ALERT_TYPE_ALIASES.get(
            normalized,
            normalized,
        )

    @staticmethod
    def is_valid(alert_type: str) -> bool:
        return alert_type in VALID_ALERT_TYPES

    @staticmethod
    def get_all() -> List[str]:
        return VALID_ALERT_TYPES

    @staticmethod
    def get_by_severity(severity: str) -> List[str]:
        return ALERTS_BY_SEVERITY.get(severity, [])

    @staticmethod
    def get_config(alert_type: str) -> Dict:
        normalized = AlertTypeManager.normalize(alert_type)

        if normalized not in VALID_ALERT_TYPES:
            raise ValueError(
                f"Invalid alert_type: {alert_type}"
            )

        return ALERT_TYPES[normalized]

    @staticmethod
    def get_mongodb_query(alert_type: str) -> Dict:
        config = AlertTypeManager.get_config(alert_type)

        return config.get(
            "mongodb_query",
            {},
        )

    @staticmethod
    def get_description(alert_type: str) -> str:
        config = AlertTypeManager.get_config(alert_type)

        return (
            f"{config['name']}: "
            f"{config['pt_br_explanation']}"
        )