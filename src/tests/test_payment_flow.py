from unittest.mock import MagicMock, patch

from src.tools.mongo_tools import check_product_availability
from src.tools.payment_tools import processar_pagamento


class FakeToolContext:
    def __init__(self, state=None):
        self.state = state or {}


def _multi_result_search_state():
    """State after a search that returned >1 result (so selected_product was
    never auto-set) and the customer is about to pick PRD00025 by code."""
    return {
        "last_search_products": [
            {
                "codigo_produto": "PRD00025",
                "descricao_completa": "CERV HEINEKEN LN 330ML (UN.)",
            },
            {
                "codigo_produto": "PRD00544",
                "descricao_completa": "CERV HEINEKEN LN 250ML (UN.)",
            },
        ],
        "last_search_product_codes": ["PRD00025", "PRD00544"],
    }


def _fake_availability_service():
    service = MagicMock()
    service.validate_stock_availability.return_value = {
        "codigo_produto": "PRD00025",
        "disponivel": True,
        "quantidade_disponivel": 302,
        "quantidade_solicitada": 6,
    }
    return service


def _patch_payment_side_effects():
    """Silence the DB-backed services payment writes go through."""
    return (
        patch("src.tools.payment_tools.PaymentRecordService"),
        patch("src.tools.payment_tools.SalesHistoryService"),
        patch("src.tools.payment_tools.InventoryService"),
    )


class TestAvailabilityPromotesSelection:
    def test_promotes_selected_product_with_name(self):
        ctx = FakeToolContext(_multi_result_search_state())
        service = _fake_availability_service()

        with patch(
            "src.tools.mongo_tools._get_inventory_service",
            return_value=service,
        ):
            result = check_product_availability(ctx, "PRD00025", 6)

        assert result["descricao_completa"] == "CERV HEINEKEN LN 330ML (UN.)"
        selected = ctx.state["selected_product"]
        assert selected["codigo_produto"] == "PRD00025"
        assert selected["descricao_completa"] == "CERV HEINEKEN LN 330ML (UN.)"


class TestPaymentNameResolution:
    def test_resolves_name_from_stock_check(self):
        # selected_product empty, but the stock check left code+name behind.
        ctx = FakeToolContext({
            "last_stock_check": {
                "codigo_produto": "PRD00025",
                "descricao_completa": "CERV HEINEKEN LN 330ML (UN.)",
            },
        })
        a, b, c = _patch_payment_side_effects()
        with a, b, c:
            result = processar_pagamento(
                ctx, valor=33.06, email="joao@teste.com",
                nome="João", sobrenome="Pereira", quantity=6,
            )

        assert result.get("error") is not True
        assert result["status"] == "approved"

    def test_resolves_name_from_search_results(self):
        # Only the code survives in last_stock_check; name comes from the cached
        # search results.
        ctx = FakeToolContext({
            **_multi_result_search_state(),
            "last_stock_check": {"codigo_produto": "PRD00025"},
        })
        a, b, c = _patch_payment_side_effects()
        with a, b, c:
            result = processar_pagamento(
                ctx, valor=33.06, email="joao@teste.com",
                nome="João", sobrenome="Pereira", quantity=6,
            )

        assert result["status"] == "approved"

    def test_falls_back_to_db_lookup_for_name(self):
        # Nowhere in state has the name — only a bare code.
        ctx = FakeToolContext({"selected_product_last": "PRD00025"})
        fake_inventory = MagicMock()
        fake_inventory.return_value.get_product_by_code.return_value = {
            "codigo_produto": "PRD00025",
            "descricao_completa": "CERV HEINEKEN LN 330ML (UN.)",
        }
        with patch("src.tools.payment_tools.PaymentRecordService"), \
                patch("src.tools.payment_tools.SalesHistoryService"), \
                patch("src.tools.payment_tools.InventoryService", fake_inventory):
            result = processar_pagamento(
                ctx, valor=33.06, email="joao@teste.com",
                nome="João", sobrenome="Pereira", quantity=6,
            )

        assert result["status"] == "approved"


class TestMultiResultFlowRegression:
    def test_full_flow_completes_payment_without_explicit_selection(self):
        """End-to-end reproduction of the original bug: multi-result search →
        availability by code → payment, with no get_product_by_code call."""
        ctx = FakeToolContext(_multi_result_search_state())
        service = _fake_availability_service()

        with patch(
            "src.tools.mongo_tools._get_inventory_service",
            return_value=service,
        ):
            check_product_availability(ctx, "PRD00025", 6)

        a, b, c = _patch_payment_side_effects()
        with a, b, c:
            result = processar_pagamento(
                ctx, valor=33.06, email="joao@teste.com",
                nome="João", sobrenome="Pereira", quantity=6,
            )

        assert result.get("error") is not True
        assert result["status"] == "approved"
