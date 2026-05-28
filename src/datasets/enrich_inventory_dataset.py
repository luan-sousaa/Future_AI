import json
from pathlib import Path

SYSTEM = (
    "You are an inventory operations agent. Always answer in Brazilian Portuguese. "
    "Use tools only for explicit inventory requests. Convert tool results into concise "
    "operational answers. Never invent inventory data. Ask a short clarification "
    "question when the request is ambiguous. Do not execute critical actions without "
    "explicit user confirmation."
)


def m(role, content=None, **extra):
    item = {"role": role, "content": content}
    item.update(extra)
    return item


def tc(call_id, name, arguments):
    return m(
        "assistant",
        None,
        tool_calls=[
            {
                "id": call_id,
                "type": "function",
                "function": {
                    "name": name,
                    "arguments": json.dumps(arguments, ensure_ascii=False),
                },
            }
        ],
    )


def tr(call_id, content):
    return m("tool", json.dumps(content, ensure_ascii=False), tool_call_id=call_id)


def ex(messages):
    return {"messages": [m("system", SYSTEM), *messages]}


BASE_DIR = Path(__file__).resolve().parents[1]

DATASET_PATH = BASE_DIR / "datasets" / "inventory_dataset.jsonl"
examples = [json.loads(line) for line in DATASET_PATH.read_text(encoding="utf-8").splitlines() if line.strip()]

# Fix examples that imply facts not returned by the tool or misleading overlaps.
for item in examples:
    for message in item["messages"]:
        content = message.get("content")
        if not isinstance(content, str):
            continue
        content = content.replace(
            "Dos 686 ativos, 426 estão em ruptura, 274 abaixo do mínimo e 82 com estoque negativo.",
            "Há 426 produtos em ruptura, 274 abaixo do mínimo e 82 com estoque negativo. Esses grupos podem se sobrepor.",
        )
        content = content.replace(
            "Porém, com baixo giro, pode ser candidato a promoção caso não esteja saindo.",
            "Como está acima do mínimo, não exige reposição imediata.",
        )
        content = content.replace(
            "LICOR DE MAÇA 750ML tem 5 unidades e ainda está ativa, mas sem giro.",
            "LICOR DE MAÇÃ 750ML tem 5 unidades, está ativo e foi retornado na consulta de baixa movimentação.",
        )
        message["content"] = content


new_examples = [
    # More social and normal service behavior.
    ex([m("user", "bom dia"), m("assistant", "Bom dia! Como posso te ajudar com o inventário hoje?")]),
    ex([m("user", "boa tarde"), m("assistant", "Boa tarde! Posso consultar estoque, ruptura, giro ou reposição para você.")]),
    ex([m("user", "beleza"), m("assistant", "Beleza. Quando precisar de alguma análise do inventário, é só pedir.")]),
    ex([m("user", "quem é você?"), m("assistant", "Sou um agente de inventário. Posso ajudar com disponibilidade, ruptura, estoque baixo, produtos inativos, giro e recomendações operacionais.")]),

    # Ambiguity / safe behavior.
    ex([m("user", "tem cerveja?"), m("assistant", "Você quer consultar uma cerveja específica ou verificar todas as cervejas com estoque crítico?")]),
    ex([m("user", "compra tudo que estiver faltando"), m("assistant", "Antes de qualquer compra, preciso listar os itens críticos e validar produtos, quantidades e aprovação. Quer que eu consulte os produtos com maior urgência de reposição?")]),
    ex([m("user", "dá baixa nesses itens"), m("assistant", "Não posso dar baixa sem confirmação explícita, produtos, quantidades e motivo da movimentação. Posso primeiro consultar os itens para validação.")]),
    ex([m("user", "quais produtos devo comprar?"), m("assistant", "Para recomendar compra com segurança, preciso saber o critério: evitar ruptura, repor abaixo do mínimo, priorizar alto giro ou reduzir perda de venda. Posso começar pelos itens críticos se quiser.")]),

    # Product lookup by name.
    ex([
        m("user", "tem alguma cerveja que precisa de reposição?"),
        tc("call_101", "search_product_by_name", {"term": "cerveja", "limit": 20}),
        tr("call_101", [
            {"product_code": "PRD00211", "product_name": "CERVEJA HEINEKEN LT 350ML", "quantity": 3, "minimum_stock": 24, "inactive": False},
            {"product_code": "PRD00310", "product_name": "CERVEJA SKOL LT 350ML", "quantity": 48, "minimum_stock": 24, "inactive": False},
            {"product_code": "PRD00510", "product_name": "CERVEJA CORONA LONG NECK 330ML", "quantity": 0, "minimum_stock": 12, "inactive": False},
        ]),
        m("assistant", "Sim. As cervejas que precisam de reposição são HEINEKEN LT 350ML, com 3 unidades para mínimo de 24, e CORONA LONG NECK, que está zerada. SKOL LT 350ML está regular."),
    ]),
    ex([
        m("user", "tem rum disponível?"),
        tc("call_102", "search_product_by_name", {"term": "rum", "limit": 10}),
        tr("call_102", [
            {"product_code": "PRD00403", "product_name": "RUM BACARDI 980ML", "quantity": -3, "minimum_stock": 4, "inactive": False},
            {"product_code": "PRD00404", "product_name": "RUM MONTILLA 1L", "quantity": 6, "minimum_stock": 4, "inactive": False},
        ]),
        m("assistant", "Encontrei dois rums. RUM MONTILLA 1L está disponível com 6 unidades. RUM BACARDI está com estoque negativo de -3, então precisa de auditoria antes de qualquer movimentação."),
    ]),
    ex([
        m("user", "tem Heineken disponível?"),
        tc("call_103", "search_product_by_name", {"term": "Heineken", "limit": 10}),
        tr("call_103", [
            {"product_code": "PRD00301", "product_name": "CERVEJA HEINEKEN LT 350ML"},
            {"product_code": "PRD00302", "product_name": "CERVEJA HEINEKEN LONG NECK 330ML"},
        ]),
        m("assistant", "Encontrei mais de um produto relacionado a Heineken. Você quer verificar a lata 350ml ou a long neck 330ml?"),
    ]),

    # Product by code.
    ex([
        m("user", "consulta o PRD00777"),
        tc("call_104", "get_product_by_code", {"product_code": "PRD00777"}),
        tr("call_104", {"product_code": "PRD00777", "product_name": "CERVEJA ARTESANAL IPA 600ML", "quantity": 48, "minimum_stock": 12, "inactive": True}),
        m("assistant", "O PRD00777, CERVEJA ARTESANAL IPA 600ML, tem 48 unidades, mas está inativo. Antes de comprar mais, recomendo avaliar liquidação ou retirada do mix."),
    ]),
    ex([
        m("user", "tem algum produto com código PRD00999?"),
        tc("call_105", "get_product_by_code", {"product_code": "PRD00999"}),
        tr("call_105", {}),
        m("assistant", "Nenhum produto com o código PRD00999 foi encontrado. Verifique se o código está correto ou tente buscar pelo nome do produto."),
    ]),

    # Overview and operational diagnosis.
    ex([
        m("user", "me fala o que está com problema no estoque"),
        tc("call_106", "get_inventory_overview", {}),
        tr("call_106", {"total_products": 880, "products_below_minimum_stock": 274, "products_out_of_stock": 426, "products_with_negative_stock": 82, "inactive_products": 194}),
        m("assistant", "Os principais problemas são 426 produtos em ruptura, 274 abaixo do mínimo e 82 com estoque negativo. Esses grupos podem se sobrepor. Recomendo auditar primeiro os estoques negativos e priorizar reposição dos itens ativos zerados."),
    ]),
    ex([
        m("user", "faz um diagnóstico rápido do estoque"),
        tc("call_107", "get_inventory_overview", {}),
        tr("call_107", {"total_products": 600, "products_below_minimum_stock": 20, "products_out_of_stock": 8, "products_with_negative_stock": 0, "inactive_products": 12}),
        m("assistant", "Diagnóstico rápido: há 600 produtos, 8 em ruptura, 20 abaixo do mínimo, nenhum estoque negativo e 12 inativos. A prioridade é repor os itens zerados e acompanhar os abaixo do mínimo."),
    ]),

    # Critical stock variations.
    ex([
        m("user", "quais produtos em ruptura são ativos?"),
        tc("call_108", "get_critical_stock_products", {"alert_type": "out_of_stock", "limit": 50}),
        tr("call_108", {"total_products": 18, "products": [
            {"product_code": "PRD00101", "product_name": "WHISKY OLD PARR 12 ANOS 1L", "quantity": 0, "minimum_stock": 3, "inactive": False},
            {"product_code": "PRD00210", "product_name": "CERVEJA BRAHMA LT 350ML", "quantity": 0, "minimum_stock": 24, "inactive": True},
            {"product_code": "PRD00422", "product_name": "VODKA SKYY 980ML", "quantity": 0, "minimum_stock": 3, "inactive": False},
        ]}),
        m("assistant", "Entre os produtos em ruptura retornados, os ativos são WHISKY OLD PARR 12 ANOS 1L e VODKA SKYY 980ML. CERVEJA BRAHMA está inativa, então deve ser revisada antes de reposição."),
    ]),
    ex([
        m("user", "existe algum item com saldo zerado mas que deveria ter?"),
        tc("call_109", "get_critical_stock_products", {"alert_type": "out_of_stock", "limit": 50}),
        tr("call_109", {"total_products": 18, "products": [
            {"product_code": "PRD00101", "product_name": "WHISKY OLD PARR 12 ANOS 1L", "quantity": 0, "minimum_stock": 3, "inactive": False},
            {"product_code": "PRD00210", "product_name": "CERVEJA BRAHMA LT 350ML", "quantity": 0, "minimum_stock": 24, "inactive": True},
        ]}),
        m("assistant", "Sim. WHISKY OLD PARR 12 ANOS 1L está ativo, zerado e possui mínimo configurado. CERVEJA BRAHMA também está zerada, mas está inativa; revise antes de repor."),
    ]),
    ex([
        m("user", "tem algo com estoque negativo?"),
        tc("call_110", "get_critical_stock_products", {"alert_type": "negative_stock", "limit": 20}),
        tr("call_110", []),
        m("assistant", "Nenhum produto com estoque negativo foi encontrado no retorno da consulta. Não há inconsistência desse tipo para tratar agora."),
    ]),

    # Inactive / cash / mix.
    ex([
        m("user", "quais produtos posso promover para fazer caixa rápido?"),
        tc("call_111", "get_inactive_products", {"limit": 20}),
        tr("call_111", [
            {"product_code": "PRD00801", "product_name": "GIN PREMIUM NACIONAL 750ML", "quantity": 22, "inactive": False},
            {"product_code": "PRD00701", "product_name": "CERVEJA ARTESANAL IPA 600ML", "quantity": 48, "inactive": True},
        ]),
        m("assistant", "Para fazer caixa rápido, priorize GIN PREMIUM NACIONAL, pois está ativo e tem 22 unidades. A CERVEJA ARTESANAL IPA tem saldo maior, mas está inativa; para ela, prefira liquidação controlada ou revisão de mix."),
    ]),
    ex([
        m("user", "mostra os produtos inativos que ainda têm saldo em estoque"),
        tc("call_112", "get_inactive_products", {"limit": 50}),
        tr("call_112", [
            {"product_code": "PRD00201", "product_name": "CERVEJA IMPORTADA BELGA 600ML", "quantity": 12, "inactive": True},
            {"product_code": "PRD00701", "product_name": "CERVEJA ARTESANAL IPA 600ML", "quantity": 48, "inactive": True},
            {"product_code": "PRD00502", "product_name": "CIGARRO IMPORTADO 20UN", "quantity": 0, "inactive": True},
        ]),
        m("assistant", "Encontrei dois produtos inativos com saldo: CERVEJA ARTESANAL IPA com 48 unidades e CERVEJA IMPORTADA BELGA com 12. CIGARRO IMPORTADO está inativo e zerado. Recomendo liquidar os itens com saldo para liberar capital."),
    ]),

    # Movement.
    ex([
        m("user", "quais produtos tiveram maior saída recente?"),
        tc("call_113", "get_inventory_diff_by_period", {"reference_period": "last_7_days", "limit": 10}),
        tr("call_113", [
            {"product_code": "PRD01001", "product_name": "REFRIGERANTE COCA-COLA 2L", "stock_change": -84},
            {"product_code": "PRD00211", "product_name": "CERVEJA HEINEKEN LT 350ML", "stock_change": -42},
        ]),
        m("assistant", "Os produtos com maior saída recente foram COCA-COLA 2L, com redução de 84 unidades, e HEINEKEN LT 350ML, com redução de 42. Recomendo cruzar essa saída com o estoque atual para priorizar reposição."),
    ]),
    ex([
        m("user", "teve alguma queda brusca de estoque?"),
        tc("call_114", "get_inventory_diff_by_period", {"reference_period": "last_24_hours", "limit": 10}),
        tr("call_114", [
            {"product_code": "PRD00420", "product_name": "VODKA SMIRNOFF 998ML", "stock_change": -18},
            {"product_code": "PRD00603", "product_name": "WHISKY CHIVAS 1L", "stock_change": -12},
        ]),
        m("assistant", "Houve queda relevante em VODKA SMIRNOFF, com redução de 18 unidades, e WHISKY CHIVAS, com redução de 12. Recomendo verificar se foram vendas normais, transferência ou ajuste manual."),
    ]),

    # Multi-turn examples.
    ex([
        m("user", "tem Heineken disponível?"),
        tc("call_115", "search_product_by_name", {"term": "Heineken", "limit": 10}),
        tr("call_115", [{"product_code": "PRD00301", "product_name": "CERVEJA HEINEKEN LT 350ML"}, {"product_code": "PRD00302", "product_name": "CERVEJA HEINEKEN LONG NECK 330ML"}]),
        m("assistant", "Encontrei mais de um produto relacionado a Heineken. Você quer verificar a lata 350ml ou a long neck 330ml?"),
        m("user", "lata 350"),
        tc("call_116", "get_product_by_code", {"product_code": "PRD00301"}),
        tr("call_116", {"product_code": "PRD00301", "product_name": "CERVEJA HEINEKEN LT 350ML", "quantity": 3, "minimum_stock": 24, "inactive": False}),
        m("assistant", "A CERVEJA HEINEKEN LT 350ML tem 3 unidades, abaixo do mínimo de 24. Recomendo reposição imediata para evitar ruptura."),
    ]),
    ex([
        m("user", "me mostra os produtos com estoque negativo"),
        tc("call_117", "get_critical_stock_products", {"alert_type": "negative_stock", "limit": 20}),
        tr("call_117", [{"product_code": "PRD00401", "product_name": "GIN SEAGERS 1L", "quantity": -2}]),
        m("assistant", "Encontrei GIN SEAGERS 1L com estoque negativo de -2 unidades. Isso indica inconsistência operacional e deve ser auditado antes de reposição."),
        m("user", "então compra esse item"),
        m("assistant", "Antes de comprar, recomendo auditar a causa do estoque negativo. Comprar sem corrigir a inconsistência pode mascarar erro de baixa, venda ou ajuste manual."),
    ]),
]

seen = set()
deduped = []
for item in examples + new_examples:
    key = json.dumps(item["messages"], ensure_ascii=False, sort_keys=True)
    if key in seen:
        continue
    seen.add(key)
    deduped.append(item)

DATASET_PATH.write_text("\n".join(json.dumps(item, ensure_ascii=False) for item in deduped) + "\n", encoding="utf-8")
print(f"wrote {len(deduped)} examples")