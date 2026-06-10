from unittest.mock import MagicMock, patch

from src.services.cart import cart_service
from src.tools.cart_tools import add_to_cart, remove_from_cart, view_cart
from src.tools.payment_tools import processar_pagamento


class FakeToolContext:
    def __init__(self, state=None):
        self.state = state or {}


# --------------------------------------------------------------------------
# cart_service (funções puras)
# --------------------------------------------------------------------------
class TestCartService:
    def test_add_and_total(self):
        state: dict = {}
        cart_service.add_item(
            state,
            codigo_produto="PRD1",
            descricao_completa="Cerveja",
            familia_produto="CERVEJA",
            quantidade=3,
            preco_unitario=10.58,
        )
        cart_service.add_item(
            state,
            codigo_produto="PRD2",
            descricao_completa="Torcida",
            familia_produto="PEPSICO_SALGADOS",
            quantidade=1,
            preco_unitario=3.99,
        )
        assert len(cart_service.get_cart(state)) == 2
        assert cart_service.cart_total(cart_service.get_cart(state)) == 35.73

    def test_readding_same_product_updates_quantity(self):
        state: dict = {}
        for qty in (2, 5):
            cart_service.add_item(
                state,
                codigo_produto="PRD1",
                descricao_completa="Cerveja",
                familia_produto="CERVEJA",
                quantidade=qty,
                preco_unitario=10.0,
            )
        cart = cart_service.get_cart(state)
        assert len(cart) == 1
        assert cart[0]["quantidade"] == 5

    def test_remove_and_clear(self):
        state: dict = {}
        cart_service.add_item(
            state, codigo_produto="PRD1", descricao_completa="x",
            familia_produto="CERVEJA", quantidade=1, preco_unitario=10.0,
        )
        cart_service.remove_item(state, "PRD1")
        assert cart_service.get_cart(state) == []


# --------------------------------------------------------------------------
# add_to_cart tool
# --------------------------------------------------------------------------
class TestAddToCartTool:
    def test_adds_selected_product_with_stock(self):
        ctx = FakeToolContext({
            "selected_product": {
                "codigo_produto": "PRD00025",
                "descricao_completa": "CERV HEINEKEN LN 330ML (UN.)",
                "familia_produto": "CERVEJA",
                "preco_sintetico": 5.51,
            },
            "selected_product_last": "PRD00025",
        })
        service = MagicMock()
        service.validate_stock_availability.return_value = {"disponivel": True}

        with patch(
            "src.tools.cart_tools._get_inventory_service",
            return_value=service,
        ):
            result = add_to_cart(ctx, 6)

        assert result.get("error") is not True
        assert result["quantidade_itens"] == 1
        assert result["total"] == round(6 * 5.51, 2)

    def test_blocks_when_insufficient_stock(self):
        ctx = FakeToolContext({"selected_product_last": "PRD00025"})
        service = MagicMock()
        service.validate_stock_availability.return_value = {
            "disponivel": False, "quantidade_disponivel": 2,
        }
        with patch(
            "src.tools.cart_tools._get_inventory_service",
            return_value=service,
        ):
            result = add_to_cart(ctx, 999)

        assert result["error"] is True
        assert cart_service.get_cart(ctx.state) == []


# --------------------------------------------------------------------------
# processar_pagamento — checkout itemizado do carrinho
# --------------------------------------------------------------------------
class TestCartCheckout:
    def test_charges_whole_cart_with_shared_order_id(self):
        ctx = FakeToolContext({
            "cart": [
                {
                    "codigo_produto": "PRD00025",
                    "descricao_completa": "Cerveja",
                    "familia_produto": "CERVEJA",
                    "quantidade": 3,
                    "preco_unitario": 10.58,
                },
                {
                    "codigo_produto": "PRD00537",
                    "descricao_completa": "Torcida",
                    "familia_produto": "PEPSICO_SALGADOS",
                    "quantidade": 1,
                    "preco_unitario": 3.99,
                },
            ],
        })

        payment_cls = MagicMock()
        sales_cls = MagicMock()
        inventory_cls = MagicMock()

        with patch("src.tools.payment_tools.PaymentRecordService", payment_cls), \
                patch("src.tools.payment_tools.SalesHistoryService", sales_cls), \
                patch("src.tools.payment_tools.InventoryService", inventory_cls):
            result = processar_pagamento(
                ctx, email="joao@teste.com", nome="João", sobrenome="Pereira",
            )

        assert result["status"] == "approved"

        # pagamento único com o total do carrinho (3*10.58 + 1*3.99 = 35.73)
        _, payment_kwargs = payment_cls.return_value.save_payment_record.call_args
        assert payment_kwargs["value"] == 35.73

        # uma venda por item, todas com o MESMO order_id
        sale_calls = sales_cls.return_value.save_sale_record.call_args_list
        assert len(sale_calls) == 2
        order_ids = {c.kwargs["order_id"] for c in sale_calls}
        assert len(order_ids) == 1

        # baixa de estoque por item
        assert inventory_cls.return_value.decrease_stock_after_sale.call_count == 2

        # carrinho esvaziado após o checkout
        assert cart_service.get_cart(ctx.state) == []

    def test_empty_cart_falls_back_to_single_item(self):
        # Sem carrinho -> caminho legado, exige valor e produto selecionado.
        ctx = FakeToolContext({
            "selected_product": {
                "codigo_produto": "PRD00025",
                "descricao_completa": "Cerveja",
                "familia_produto": "CERVEJA",
            },
        })
        with patch("src.tools.payment_tools.PaymentRecordService"), \
                patch("src.tools.payment_tools.SalesHistoryService"), \
                patch("src.tools.payment_tools.InventoryService"):
            result = processar_pagamento(
                ctx, valor=31.74, email="joao@teste.com",
                nome="João", sobrenome="Pereira", quantity=3,
            )
        assert result["status"] == "approved"
