import pytest
from src.repositories.product_model import Produto, PrecoProduto, Categoria


def make_produto(**kwargs):
    defaults = {
        "id": "prod_001",
        "nome": "Produto Teste",
        "especificacao": None,
        "unidade_medida": "un",
        "precos": {},
    }
    defaults.update(kwargs)
    return Produto(**defaults)


class TestPrecosValidos:
    def test_all_valid(self):
        p = make_produto(precos={"Loja A": 10.0, "Loja B": 15.0})
        assert p.precos_validos() == {"Loja A": 10.0, "Loja B": 15.0}

    def test_filters_none_prices(self):
        p = make_produto(precos={"Loja A": 10.0, "Loja B": None})
        assert p.precos_validos() == {"Loja A": 10.0}

    def test_all_none_returns_empty(self):
        p = make_produto(precos={"Loja A": None})
        assert p.precos_validos() == {}

    def test_empty_precos(self):
        p = make_produto(precos={})
        assert p.precos_validos() == {}


class TestMenorPreco:
    def test_returns_cheapest(self):
        p = make_produto(precos={"A": 5.0, "B": 3.0, "C": 7.0})
        result = p.menor_preco()
        assert result is not None
        assert result.mercado == "B"
        assert result.preco == 3.0

    def test_returns_none_when_no_prices(self):
        p = make_produto(precos={})
        assert p.menor_preco() is None

    def test_ignores_none_prices(self):
        p = make_produto(precos={"A": None, "B": 5.0})
        result = p.menor_preco()
        assert result is not None
        assert result.mercado == "B"

    def test_single_price(self):
        p = make_produto(precos={"A": 9.99})
        result = p.menor_preco()
        assert result.preco == 9.99


class TestMaiorPreco:
    def test_returns_most_expensive(self):
        p = make_produto(precos={"A": 5.0, "B": 3.0, "C": 7.0})
        result = p.maior_preco()
        assert result is not None
        assert result.mercado == "C"
        assert result.preco == 7.0

    def test_returns_none_when_no_prices(self):
        p = make_produto(precos={})
        assert p.maior_preco() is None

    def test_ignores_none_prices(self):
        p = make_produto(precos={"A": None, "B": 5.0})
        result = p.maior_preco()
        assert result is not None
        assert result.preco == 5.0


class TestPrecosOrdenados:
    def test_sorted_ascending(self):
        p = make_produto(precos={"A": 10.0, "B": 5.0, "C": 7.0})
        result = p.precos_ordenados()
        assert [r.preco for r in result] == [5.0, 7.0, 10.0]

    def test_excludes_none_prices(self):
        p = make_produto(precos={"A": 10.0, "B": None})
        result = p.precos_ordenados()
        assert len(result) == 1
        assert result[0].preco == 10.0

    def test_empty_precos(self):
        p = make_produto(precos={})
        assert p.precos_ordenados() == []

    def test_returns_preco_produto_instances(self):
        p = make_produto(precos={"A": 5.0})
        result = p.precos_ordenados()
        assert isinstance(result[0], PrecoProduto)


class TestCategoria:
    def test_with_products(self):
        p1 = make_produto(id="p1", nome="Produto 1")
        p2 = make_produto(id="p2", nome="Produto 2")
        cat = Categoria(id="cat_01", nome="Categoria Teste", produtos=[p1, p2])
        assert len(cat.produtos) == 2
        assert cat.id == "cat_01"

    def test_default_empty_products(self):
        cat = Categoria(id="cat_01", nome="Vazia")
        assert cat.produtos == []
