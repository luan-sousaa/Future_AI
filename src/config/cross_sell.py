"""Mapa estático de cross-sell ("leva-junto") por família de produto.

Cada chave é a família-âncora (o que o cliente está levando) e o valor é a
lista de famílias complementares que costumam casar com ela. É o sinal de
*cold start*: funciona desde o dia zero, sem depender de histórico de vendas.

Quando o grafo de co-ocorrência (aprendido do `sales_history`) tiver dado
suficiente, ele tem prioridade; este mapa entra como fallback. Ver
`InventoryService.get_complementary_products`.

Famílias propositalmente fora do mapa (CONVENIENCIA, AGUA E ISOTONICO, etc.)
não disparam sugestão — em geral são complementos de outras, não âncoras.
Nomes precisam casar exatamente com `familia_produto` no MongoDB.
"""

COMPLEMENTARY_FAMILIES: dict[str, list[str]] = {
    "CERVEJA": [
        "PEPSICO_SALGADOS",
        "SNACK E BOMBONIERE",
        "QUADRADO_BBQ",
        "TABACARIA",
    ],
    "CERVEJA ARTESANAL": [
        "PEPSICO_SALGADOS",
        "SNACK E BOMBONIERE",
        "QUADRADO_BBQ",
    ],
    "DESTILADOS": [
        "ENERGETICO E ICE",
        "REFRIGERANTE",
        "AGUA E ISOTONICO",
        "EMBALAGENS DESCARTAVEIS E AFINS",
    ],
    "DOSES": [
        "ENERGETICO E ICE",
        "REFRIGERANTE",
    ],
    "LICOR": [
        "ENERGETICO E ICE",
        "REFRIGERANTE",
    ],
    "DRINK/COPAO": [
        "ENERGETICO E ICE",
        "DESTILADOS",
    ],
    "VINHO E ESPUMANTE": [
        "SNACK E BOMBONIERE",
        "QUADRADO_BBQ",
        "COMIDA VENDAS",
    ],
    "ENERGETICO E ICE": [
        "DESTILADOS",
        "DOSES",
    ],
    "REFRIGERANTE": [
        "PEPSICO_SALGADOS",
        "SNACK E BOMBONIERE",
        "COMIDA VENDAS",
    ],
    "PEPSICO_SALGADOS": [
        "CERVEJA",
        "REFRIGERANTE",
        "ENERGETICO E ICE",
    ],
    "SNACK E BOMBONIERE": [
        "CERVEJA",
        "REFRIGERANTE",
        "CERVEJA ARTESANAL",
    ],
    "QUADRADO_BBQ": [
        "CERVEJA",
        "CERVEJA ARTESANAL",
        "EMBALAGENS DESCARTAVEIS E AFINS",
        "MATERIAL LIMPEZA E AFINS",
    ],
    "COMIDA VENDAS": [
        "REFRIGERANTE",
        "CERVEJA",
        "AGUA E ISOTONICO",
    ],
    "TABACARIA": [
        "ENERGETICO E ICE",
        "CONVENIENCIA",
        "SNACK E BOMBONIERE",
    ],
    "SORVETE": [
        "SNACK E BOMBONIERE",
    ],
}


def complementary_families(familia: str | None) -> list[str]:
    """Famílias complementares de uma âncora; lista vazia se não mapeada."""
    if not familia:
        return []
    return COMPLEMENTARY_FAMILIES.get(familia, [])
