from typing import TypedDict


class InventoryAlertReport(TypedDict):
    has_critical_alerts: bool
    summary: dict
    low_stock_products: list[dict]
    out_of_stock_products: list[dict]
    negative_stock_products: list[dict]
    
class InventoryOverviewSummary(TypedDict):
    total_produtos: int
    abaixo_estoque_minimo: int
    sem_estoque: int
    estoque_negativo: int
    inativos: int

class InventoryOverviewResponse(TypedDict):
    summary: InventoryOverviewSummary
    status: str