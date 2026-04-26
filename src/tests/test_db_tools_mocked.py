from src.tools.db_tools_mocked import (
    load_categorias,
    list_all_products,
    search_for_product_name,
    get_product_by_id,
    get_product_details,
    get_prices_summary,
)


class TestLoadCategorias:
    def test_returns_non_empty_list(self):
        result = load_categorias()
        assert isinstance(result, list)
        assert len(result) > 0

    def test_categories_have_required_fields(self):
        result = load_categorias()
        for cat in result:
            assert cat.id
            assert cat.nome
            assert isinstance(cat.produtos, list)


class TestListAllProducts:
    def test_returns_products(self):
        result = list_all_products()
        assert len(result) > 0

    def test_products_have_required_fields(self):
        result = list_all_products()
        for p in result:
            assert p.id
            assert p.nome
            assert isinstance(p.precos, dict)


class TestSearchForProductName:
    def test_finds_by_partial_name(self):
        result = search_for_product_name("achocolatado")
        assert len(result) > 0

    def test_case_insensitive(self):
        lower = search_for_product_name("achocolatado")
        upper = search_for_product_name("ACHOCOLATADO")
        assert len(lower) == len(upper)

    def test_empty_term_returns_empty(self):
        result = search_for_product_name("")
        assert result == []

    def test_whitespace_returns_empty(self):
        result = search_for_product_name("   ")
        assert result == []

    def test_no_match_returns_empty(self):
        result = search_for_product_name("xyz_produto_inexistente_9999")
        assert result == []

    def test_result_has_expected_fields(self):
        result = search_for_product_name("achocolatado")
        assert len(result) > 0
        for item in result:
            assert "id" in item
            assert "nome" in item
            assert "categoria" in item


class TestGetProductById:
    def test_finds_known_product(self):
        result = get_product_by_id("achocolatado_nescau_400g")
        assert result is not None
        assert result.nome == "Achocolatado Nescau"

    def test_empty_id_returns_none(self):
        result = get_product_by_id("")
        assert result is None

    def test_unknown_id_returns_none(self):
        result = get_product_by_id("produto_que_nao_existe_9999")
        assert result is None

    def test_case_insensitive_lookup(self):
        result = get_product_by_id("ACHOCOLATADO_NESCAU_400G")
        assert result is not None


class TestGetProductDetails:
    def test_returns_dict_with_fields(self):
        result = get_product_details("achocolatado_nescau_400g")
        assert result is not None
        for field in ("id", "nome", "unidade_medida", "categoria"):
            assert field in result

    def test_unknown_returns_none(self):
        result = get_product_details("nao_existe")
        assert result is None


class TestGetPricesSummary:
    def test_returns_complete_summary(self):
        result = get_prices_summary("achocolatado_nescau_400g")
        assert result is not None
        for field in ("menor_preco", "maior_preco", "precos", "quantidade_de_mercados"):
            assert field in result

    def test_menor_less_than_or_equal_maior(self):
        result = get_prices_summary("achocolatado_nescau_400g")
        assert result["menor_preco"]["preco"] <= result["maior_preco"]["preco"]

    def test_precos_is_list(self):
        result = get_prices_summary("achocolatado_nescau_400g")
        assert isinstance(result["precos"], list)

    def test_unknown_returns_none(self):
        result = get_prices_summary("nao_existe")
        assert result is None
