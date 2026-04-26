from unittest.mock import patch

import pandas as pd
import pytest

from src.tools.db_tools_excel import (
    search_product_by_name,
    get_product_by_code,
    get_product_stock_and_price_summary,
    get_low_stock_products,
    get_inactive_products,
)

SAMPLE_DATA = {
    "descricao_completa": ["Arroz Tipo 1 5kg", "Feijão Preto 1kg", "Tabaco Importado 50g"],
    "familia_produto": ["Arroz", "Feijão", "Tabaco"],
    "codigo_produto": ["PRD001", "PRD002", "PRD003"],
    "codigo_ean_gtin": ["789001", "789002", "789003"],
    "produto_inativo": ["Não", "Não", "Sim"],
    "unidade": ["CX", "PC", "UN"],
    "quantidade": [100.0, 5.0, 50.0],
    "estoque_minimo": [10.0, 10.0, 30.0],
    "preco_sintetico": [25.90, 8.50, 45.00],
}


@pytest.fixture
def mock_df():
    return pd.DataFrame(SAMPLE_DATA)


class TestSearchProductByName:
    def test_finds_by_partial_name(self, mock_df):
        with patch("src.tools.db_tools_excel.load_excel_data", return_value=mock_df):
            result = search_product_by_name("arroz")
        assert len(result) == 1
        assert result[0]["codigo_produto"] == "PRD001"

    def test_case_insensitive(self, mock_df):
        with patch("src.tools.db_tools_excel.load_excel_data", return_value=mock_df):
            result = search_product_by_name("TABACO")
        assert len(result) == 1
        assert result[0]["codigo_produto"] == "PRD003"

    def test_empty_term_returns_empty(self):
        result = search_product_by_name("")
        assert result == []

    def test_whitespace_term_returns_empty(self):
        result = search_product_by_name("   ")
        assert result == []

    def test_no_match_returns_empty(self, mock_df):
        with patch("src.tools.db_tools_excel.load_excel_data", return_value=mock_df):
            result = search_product_by_name("produto_inexistente_xyz")
        assert result == []

    def test_respects_limit(self, mock_df):
        with patch("src.tools.db_tools_excel.load_excel_data", return_value=mock_df):
            result = search_product_by_name("a", limit=1)
        assert len(result) <= 1

    def test_returns_empty_when_data_unavailable(self):
        with patch("src.tools.db_tools_excel.load_excel_data", return_value=None):
            result = search_product_by_name("arroz")
        assert result == []

    def test_result_contains_expected_fields(self, mock_df):
        with patch("src.tools.db_tools_excel.load_excel_data", return_value=mock_df):
            result = search_product_by_name("feijão")
        assert "codigo_produto" in result[0]
        assert "descricao_completa" in result[0]
        assert "preco_sintetico" in result[0]


class TestGetProductByCode:
    def test_finds_existing_product(self, mock_df):
        with patch("src.tools.db_tools_excel.load_excel_data", return_value=mock_df):
            result = get_product_by_code("PRD001")
        assert result is not None
        assert result["descricao_completa"] == "Arroz Tipo 1 5kg"
        assert result["preco_sintetico"] == pytest.approx(25.90)

    def test_returns_none_for_unknown_code(self, mock_df):
        with patch("src.tools.db_tools_excel.load_excel_data", return_value=mock_df):
            result = get_product_by_code("INEXISTENTE")
        assert result is None

    def test_empty_code_returns_none(self):
        result = get_product_by_code("")
        assert result is None

    def test_returns_none_when_data_unavailable(self):
        with patch("src.tools.db_tools_excel.load_excel_data", return_value=None):
            result = get_product_by_code("PRD001")
        assert result is None

    def test_result_contains_all_fields(self, mock_df):
        with patch("src.tools.db_tools_excel.load_excel_data", return_value=mock_df):
            result = get_product_by_code("PRD002")
        expected_fields = [
            "codigo_produto", "descricao_completa", "familia_produto",
            "codigo_ean_gtin", "produto_inativo", "unidade",
            "quantidade", "estoque_minimo", "preco_sintetico",
        ]
        for field in expected_fields:
            assert field in result


class TestGetProductStockAndPriceSummary:
    def test_returns_summary(self, mock_df):
        with patch("src.tools.db_tools_excel.load_excel_data", return_value=mock_df):
            result = get_product_stock_and_price_summary("PRD002")
        assert result is not None
        assert result["quantidade_em_estoque"] == pytest.approx(5.0)
        assert result["preco_sintetico"] == pytest.approx(8.50)

    def test_returns_none_for_unknown_code(self, mock_df):
        with patch("src.tools.db_tools_excel.load_excel_data", return_value=mock_df):
            result = get_product_stock_and_price_summary("NOPE")
        assert result is None

    def test_summary_has_stock_fields(self, mock_df):
        with patch("src.tools.db_tools_excel.load_excel_data", return_value=mock_df):
            result = get_product_stock_and_price_summary("PRD001")
        assert "quantidade_em_estoque" in result
        assert "estoque_minimo" in result
        assert "preco_sintetico" in result


class TestGetLowStockProducts:
    def test_returns_below_minimum_stock(self, mock_df):
        with patch("src.tools.db_tools_excel.load_excel_data", return_value=mock_df):
            result = get_low_stock_products()
        codes = [r["codigo_produto"] for r in result]
        assert "PRD002" in codes  # quantidade=5 < estoque_minimo=10
        assert "PRD001" not in codes  # quantidade=100 > estoque_minimo=10

    def test_respects_limit(self, mock_df):
        with patch("src.tools.db_tools_excel.load_excel_data", return_value=mock_df):
            result = get_low_stock_products(limit=1)
        assert len(result) <= 1

    def test_returns_empty_when_data_unavailable(self):
        with patch("src.tools.db_tools_excel.load_excel_data", return_value=None):
            result = get_low_stock_products()
        assert result == []


class TestGetInactiveProducts:
    def test_returns_inactive_only(self, mock_df):
        with patch("src.tools.db_tools_excel.load_excel_data", return_value=mock_df):
            result = get_inactive_products()
        codes = [r["codigo_produto"] for r in result]
        assert "PRD003" in codes
        assert "PRD001" not in codes
        assert "PRD002" not in codes

    def test_respects_limit(self, mock_df):
        with patch("src.tools.db_tools_excel.load_excel_data", return_value=mock_df):
            result = get_inactive_products(limit=1)
        assert len(result) <= 1

    def test_returns_empty_when_data_unavailable(self):
        with patch("src.tools.db_tools_excel.load_excel_data", return_value=None):
            result = get_inactive_products()
        assert result == []
