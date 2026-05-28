"""
Dataset de exemplos para fine-tuning do agente de inventário.
Baseado nas tools reais: search_product_by_name, get_product_by_code, etc.
"""

SYSTEM_PROMPT = "You are an inventory operations agent. Always answer in Brazilian Portuguese. Use tools only for explicit inventory requests. Convert tool results into concise operational answers. Never invent inventory data."

INVENTORY_FINETUNE_EXAMPLES = [
    {
        "category": "saudacao",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": "oi"},
            {"role": "assistant", "content": "Olá! Estou aqui para ajudar com o inventário. Pode perguntar sobre estoque, rupturas, movimentações ou reposição."}
        ]
    },
    {
        "category": "saudacao",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": "tudo bem?"},
            {"role": "assistant", "content": "Tudo certo! Pronto para consultar o inventário sempre que precisar."}
        ]
    },
    {
        "category": "saudacao",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": "obrigado"},
            {"role": "assistant", "content": "De nada! Se precisar de mais alguma consulta de estoque ou reposição, é só falar."}
        ]
    },
    {
        "category": "saudacao",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": "ok, até mais"},
            {"role": "assistant", "content": "Até mais! Qualquer dúvida sobre o inventário, estou à disposição."}
        ]
    },
    {
        "category": "busca_produto",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": "Tem Red Bull disponível?"},
            {"role": "assistant", "tool_calls": [{"id": "call_010", "type": "function", "function": {"name": "search_product_by_name", "arguments": "{\"term\":\"Red Bull\",\"limit\":10}"}}]},
            {"role": "tool", "tool_call_id": "call_010", "content": "[{\"product_code\":\"PRD00213\",\"product_name\":\"ENERGÉTICO RED BULL LT 250ML\",\"quantity\":3,\"minimum_stock\":4},{\"product_code\":\"PRD00214\",\"product_name\":\"ENERGÉTICO RED BULL LT 355ML\",\"quantity\":0,\"minimum_stock\":6}]"},
            {"role": "assistant", "content": "Encontrei dois produtos Red Bull. O ENERGÉTICO RED BULL LT 250ML tem 3 unidades, mas está abaixo do mínimo de 4. O RED BULL LT 355ML está zerado. Recomendo reposição imediata de ambos."}
        ]
    },
    {
        "category": "busca_produto",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": "Busca Skol no sistema"},
            {"role": "assistant", "tool_calls": [{"id": "call_011", "type": "function", "function": {"name": "search_product_by_name", "arguments": "{\"term\":\"Skol\",\"limit\":10}"}}]},
            {"role": "tool", "tool_call_id": "call_011", "content": "[{\"product_code\":\"PRD00310\",\"product_name\":\"CERVEJA SKOL LT 350ML\",\"quantity\":48,\"minimum_stock\":24},{\"product_code\":\"PRD00311\",\"product_name\":\"CERVEJA SKOL LONG NECK 330ML\",\"quantity\":12,\"minimum_stock\":12}]"},
            {"role": "assistant", "content": "Encontrei dois produtos Skol. A CERVEJA SKOL LT 350ML tem 48 unidades — acima do mínimo de 24. A SKOL LONG NECK 330ML tem 12 unidades, exatamente no limite mínimo configurado. Monitore esse segundo item para evitar ruptura."}
        ]
    },
    {
        "category": "busca_produto",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": "Procura vodka no catálogo"},
            {"role": "assistant", "tool_calls": [{"id": "call_012", "type": "function", "function": {"name": "search_product_by_name", "arguments": "{\"term\":\"vodka\",\"limit\":10}"}}]},
            {"role": "tool", "tool_call_id": "call_012", "content": "[{\"product_code\":\"PRD00420\",\"product_name\":\"VODKA SMIRNOFF 998ML\",\"quantity\":7,\"minimum_stock\":6},{\"product_code\":\"PRD00421\",\"product_name\":\"VODKA ABSOLUT 750ML\",\"quantity\":2,\"minimum_stock\":4},{\"product_code\":\"PRD00422\",\"product_name\":\"VODKA SKYY 980ML\",\"quantity\":0,\"minimum_stock\":3}]"},
            {"role": "assistant", "content": "Encontrei 3 vodkas no catálogo. A SMIRNOFF 998ML está regular com 7 unidades. A ABSOLUT 750ML tem 2 unidades, abaixo do mínimo de 4. A VODKA SKYY 980ML está zerada. Recomendo reposição de Absolut e Skyy com urgência."}
        ]
    },
    {
        "category": "consulta_codigo",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": "qual o estoque do PRD00211?"},
            {"role": "assistant", "tool_calls": [{"id": "call_013", "type": "function", "function": {"name": "get_product_by_code", "arguments": "{\"product_code\":\"PRD00211\"}"}}]},
            {"role": "tool", "tool_call_id": "call_013", "content": "{\"product_code\":\"PRD00211\",\"product_name\":\"CERVEJA HEINEKEN LT 350ML\",\"quantity\":3,\"minimum_stock\":24,\"inactive\":false}"},
            {"role": "assistant", "content": "O produto PRD00211 — CERVEJA HEINEKEN LT 350ML — tem apenas 3 unidades, muito abaixo do mínimo de 24. Situação crítica: reposição imediata recomendada."}
        ]
    },
    {
        "category": "consulta_codigo",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": "Me dá o detalhe do produto PRD00401"},
            {"role": "assistant", "tool_calls": [{"id": "call_014", "type": "function", "function": {"name": "get_product_by_code", "arguments": "{\"product_code\":\"PRD00401\"}"}}]},
            {"role": "tool", "tool_call_id": "call_014", "content": "{\"product_code\":\"PRD00401\",\"product_name\":\"GIN SEAGERS 1L\",\"quantity\":-2,\"minimum_stock\":6,\"inactive\":false}"},
            {"role": "assistant", "content": "O produto PRD00401 — GIN SEAGERS 1L — está com estoque negativo de -2 unidades. Isso indica inconsistência operacional: pode ser venda sem baixa, ajuste incorreto ou divergência de inventário. Recomendo auditoria das movimentações antes de qualquer reposição."}
        ]
    },
    {
        "category": "consulta_codigo",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": "verifica o código PRD00101"},
            {"role": "assistant", "tool_calls": [{"id": "call_015", "type": "function", "function": {"name": "get_product_by_code", "arguments": "{\"product_code\":\"PRD00101\"}"}}]},
            {"role": "tool", "tool_call_id": "call_015", "content": "{\"product_code\":\"PRD00101\",\"product_name\":\"WHISKY OLD PARR 12 ANOS 1L\",\"quantity\":0,\"minimum_stock\":3,\"inactive\":false}"},
            {"role": "assistant", "content": "O produto PRD00101 — WHISKY OLD PARR 12 ANOS 1L — está zerado, com mínimo configurado de 3 unidades. Produto ativo em ruptura. Recomendo acionar reposição com o fornecedor."}
        ]
    },
    {
        "category": "panorama_geral",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": "quero ver o panorama geral do estoque"},
            {"role": "assistant", "tool_calls": [{"id": "call_016", "type": "function", "function": {"name": "get_inventory_overview", "arguments": "{}"}}]},
            {"role": "tool", "tool_call_id": "call_016", "content": "{\"total_products\":1240,\"products_below_minimum_stock\":89,\"products_out_of_stock\":35,\"products_with_negative_stock\":12,\"inactive_products\":23}"},
            {"role": "assistant", "content": "O inventário tem 1.240 produtos cadastrados. Desses, 35 estão zerados, 89 abaixo do mínimo e 12 com estoque negativo — esses últimos exigem auditoria imediata. Há ainda 23 produtos inativos. A situação pede ação prioritária nos itens negativos e zerados para evitar perda de vendas."}
        ]
    },
    {
        "category": "panorama_geral",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": "qual a saúde geral do inventário?"},
            {"role": "assistant", "tool_calls": [{"id": "call_017", "type": "function", "function": {"name": "get_inventory_overview", "arguments": "{}"}}]},
            {"role": "tool", "tool_call_id": "call_017", "content": "{\"total_products\":880,\"products_below_minimum_stock\":274,\"products_out_of_stock\":426,\"products_with_negative_stock\":82,\"inactive_products\":194}"},
            {"role": "assistant", "content": "O inventário está em situação crítica: 426 produtos zerados, 274 abaixo do mínimo e 82 com estoque negativo. Quase 59% do catálogo tem algum tipo de alerta. Recomendo priorizar estoque negativo e rupturas primeiro, depois tratar os abaixo do mínimo por ordem de giro."}
        ]
    },
    {
        "category": "panorama_geral",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": "resumo do inventário hoje"},
            {"role": "assistant", "tool_calls": [{"id": "call_018", "type": "function", "function": {"name": "get_inventory_overview", "arguments": "{}"}}]},
            {"role": "tool", "tool_call_id": "call_018", "content": "{\"total_products\":950,\"products_below_minimum_stock\":45,\"products_out_of_stock\":18,\"products_with_negative_stock\":5,\"inactive_products\":31}"},
            {"role": "assistant", "content": "Resumo do inventário: 950 produtos no total, com 18 em ruptura, 45 abaixo do mínimo e 5 com estoque negativo. Os 31 produtos inativos representam capital parado e devem ser revisados. No geral, a situação está controlada, mas os 5 itens negativos precisam de correção imediata."}
        ]
    },
    {
        "category": "estoque_critico",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": "quais produtos estão em ruptura agora?"},
            {"role": "assistant", "tool_calls": [{"id": "call_019", "type": "function", "function": {"name": "get_critical_stock_products", "arguments": "{\"alert_type\":\"out_of_stock\",\"limit\":20}"}}]},
            {"role": "tool", "tool_call_id": "call_019", "content": "{\"total_products\":18,\"products\":[{\"product_code\":\"PRD00101\",\"product_name\":\"WHISKY OLD PARR 12 ANOS 1L\",\"quantity\":0,\"minimum_stock\":3,\"inactive\":false},{\"product_code\":\"PRD00422\",\"product_name\":\"VODKA SKYY 980ML\",\"quantity\":0,\"minimum_stock\":3,\"inactive\":false},{\"product_code\":\"PRD00510\",\"product_name\":\"CERVEJA CORONA LONG NECK 330ML\",\"quantity\":0,\"minimum_stock\":12,\"inactive\":false}]}"},
            {"role": "assistant", "content": "Há 18 produtos em ruptura total. Os mais relevantes são WHISKY OLD PARR 12 ANOS 1L, VODKA SKYY 980ML e CERVEJA CORONA LONG NECK 330ML — todos ativos e zerados. Recomendo acionar reposição imediata para esses itens para evitar perda de venda."}
        ]
    },
    {
        "category": "estoque_critico",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": "mostra os produtos com estoque crítico"},
            {"role": "assistant", "tool_calls": [{"id": "call_020", "type": "function", "function": {"name": "get_critical_stock_products", "arguments": "{\"alert_type\":\"low_stock\",\"limit\":20}"}}]},
            {"role": "tool", "tool_call_id": "call_020", "content": "{\"total_products\":45,\"products\":[{\"product_code\":\"PRD00211\",\"product_name\":\"CERVEJA HEINEKEN LT 350ML\",\"quantity\":3,\"minimum_stock\":24},{\"product_code\":\"PRD00421\",\"product_name\":\"VODKA ABSOLUT 750ML\",\"quantity\":2,\"minimum_stock\":4},{\"product_code\":\"PRD00601\",\"product_name\":\"WHISKY JACK DANIELS 1L\",\"quantity\":1,\"minimum_stock\":3}]}"},
            {"role": "assistant", "content": "Há 45 produtos com estoque crítico. Os mais urgentes são CERVEJA HEINEKEN LT 350ML com 3 unidades (mínimo 24), VODKA ABSOLUT 750ML com 2 unidades (mínimo 4) e WHISKY JACK DANIELS 1L com apenas 1 unidade (mínimo 3). Esses três precisam de reposição prioritária."}
        ]
    },
    {
        "category": "estoque_critico",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": "lista os itens abaixo do estoque mínimo"},
            {"role": "assistant", "tool_calls": [{"id": "call_021", "type": "function", "function": {"name": "get_critical_stock_products", "arguments": "{\"alert_type\":\"low_stock\",\"limit\":50}"}}]},
            {"role": "tool", "tool_call_id": "call_021", "content": "{\"total_products\":89,\"products\":[{\"product_code\":\"PRD00311\",\"product_name\":\"CERVEJA SKOL LONG NECK 330ML\",\"quantity\":12,\"minimum_stock\":12},{\"product_code\":\"PRD00502\",\"product_name\":\"ENERGÉTICO MONSTER 473ML\",\"quantity\":5,\"minimum_stock\":8},{\"product_code\":\"PRD00703\",\"product_name\":\"SUCO NATURAL LARANJA 1L\",\"quantity\":4,\"minimum_stock\":10}]}"},
            {"role": "assistant", "content": "São 89 produtos abaixo do mínimo. Destaques: CERVEJA SKOL LONG NECK 330ML está exatamente no limite (12 unidades), ENERGÉTICO MONSTER 473ML tem 5 contra mínimo de 8 e SUCO NATURAL LARANJA 1L tem 4 contra mínimo de 10. Recomendo tratar primeiro os de maior déficit relativo."}
        ]
    },
    {
        "category": "estoque_critico",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": "quais itens estão com estoque negativo?"},
            {"role": "assistant", "tool_calls": [{"id": "call_022", "type": "function", "function": {"name": "get_critical_stock_products", "arguments": "{\"alert_type\":\"negative_stock\",\"limit\":20}"}}]},
            {"role": "tool", "tool_call_id": "call_022", "content": "[{\"product_code\":\"PRD00401\",\"product_name\":\"GIN SEAGERS 1L\",\"quantity\":-2},{\"product_code\":\"PRD00402\",\"product_name\":\"WHISKY BLACK LABEL 1L\",\"quantity\":-1},{\"product_code\":\"PRD00403\",\"product_name\":\"RUM BACARDI 980ML\",\"quantity\":-3}]"},
            {"role": "assistant", "content": "Há 3 produtos com estoque negativo: GIN SEAGERS 1L com -2 unidades, WHISKY BLACK LABEL 1L com -1 e RUM BACARDI 980ML com -3. Essas inconsistências precisam ser auditadas antes de qualquer reposição — verifique movimentações, baixas de venda e ajustes manuais."}
        ]
    },
    {
        "category": "estoque_critico",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": "tem algum produto com saldo negativo?"},
            {"role": "assistant", "tool_calls": [{"id": "call_023", "type": "function", "function": {"name": "get_critical_stock_products", "arguments": "{\"alert_type\":\"negative_stock\",\"limit\":20}"}}]},
            {"role": "tool", "tool_call_id": "call_023", "content": "[]"},
            {"role": "assistant", "content": "Nenhum produto com estoque negativo foi encontrado no momento. O inventário está sem inconsistências desse tipo."}
        ]
    },
    {
        "category": "produtos_inativos",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": "quais produtos não estão movimentando há muito tempo?"},
            {"role": "assistant", "tool_calls": [{"id": "call_024", "type": "function", "function": {"name": "get_inactive_products", "arguments": "{\"limit\":20}"}}]},
            {"role": "tool", "tool_call_id": "call_024", "content": "[{\"product_code\":\"PRD00201\",\"product_name\":\"CERVEJA IMPORTADA BELGA 600ML\",\"quantity\":12,\"inactive\":true},{\"product_code\":\"PRD00202\",\"product_name\":\"LICOR DE MAÇA 750ML\",\"quantity\":5,\"inactive\":false},{\"product_code\":\"PRD00203\",\"product_name\":\"SAQUÊ TRADICIONAL 750ML\",\"quantity\":8,\"inactive\":true}]"},
            {"role": "assistant", "content": "Encontrei produtos sem movimentação recente. CERVEJA IMPORTADA BELGA 600ML tem 12 unidades e está inativa. LICOR DE MAÇÃ 750ML tem 5 unidades e ainda está ativo, mas sem giro. SAQUÊ TRADICIONAL 750ML tem 8 unidades e está inativo. Recomendo promoção para os ativos e revisão dos inativos antes de novas compras."}
        ]
    },
    {
        "category": "produtos_inativos",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": "mostra os produtos inativos do sistema"},
            {"role": "assistant", "tool_calls": [{"id": "call_025", "type": "function", "function": {"name": "get_inactive_products", "arguments": "{\"limit\":30}"}}]},
            {"role": "tool", "tool_call_id": "call_025", "content": "[{\"product_code\":\"PRD00501\",\"product_name\":\"TABACO ESPECIAL 25G\",\"quantity\":2,\"inactive\":true},{\"product_code\":\"PRD00502\",\"product_name\":\"CIGARRO IMPORTADO 20UN\",\"quantity\":0,\"inactive\":true},{\"product_code\":\"PRD00503\",\"product_name\":\"ENERGÉTICO IMPORTADO 250ML\",\"quantity\":15,\"inactive\":true}]"},
            {"role": "assistant", "content": "Encontrei produtos inativos no sistema. TABACO ESPECIAL 25G tem 2 unidades em estoque. CIGARRO IMPORTADO 20UN está zerado. ENERGÉTICO IMPORTADO 250ML tem 15 unidades paradas. Recomendo avaliar descontinuação, liquidação ou devolução ao fornecedor para liberar capital e espaço."}
        ]
    },
    {
        "category": "produtos_inativos",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": "quais itens deveria tirar do mix?"},
            {"role": "assistant", "tool_calls": [{"id": "call_026", "type": "function", "function": {"name": "get_inactive_products", "arguments": "{\"limit\":20}"}}]},
            {"role": "tool", "tool_call_id": "call_026", "content": "[{\"product_code\":\"PRD00601\",\"product_name\":\"VINHO DE MESA TINTO 750ML\",\"quantity\":24,\"inactive\":true},{\"product_code\":\"PRD00602\",\"product_name\":\"APERITIVO IMPORTADO 700ML\",\"quantity\":3,\"inactive\":false}]"},
            {"role": "assistant", "content": "Candidatos para retirada do mix: VINHO DE MESA TINTO 750ML tem 24 unidades paradas e está inativo — ideal para liquidação antes de descontinuar. APERITIVO IMPORTADO 700ML ainda está ativo mas com baixo giro e apenas 3 unidades. Recomendo revisar a rentabilidade de ambos antes de qualquer decisão."}
        ]
    },
    {
        "category": "produtos_inativos",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": "o que está parado e ocupando espaço?"},
            {"role": "assistant", "tool_calls": [{"id": "call_027", "type": "function", "function": {"name": "get_inactive_products", "arguments": "{\"limit\":20}"}}]},
            {"role": "tool", "tool_call_id": "call_027", "content": "[{\"product_code\":\"PRD00701\",\"product_name\":\"CERVEJA ARTESANAL IPA 600ML\",\"quantity\":48,\"inactive\":true},{\"product_code\":\"PRD00702\",\"product_name\":\"VINAGRE BALSÂMICO 500ML\",\"quantity\":30,\"inactive\":true},{\"product_code\":\"PRD00703\",\"product_name\":\"SUCO DETOX 300ML\",\"quantity\":18,\"inactive\":false}]"},
            {"role": "assistant", "content": "Os produtos que mais ocupam espaço sem girar são CERVEJA ARTESANAL IPA 600ML com 48 unidades inativas e VINAGRE BALSÂMICO 500ML com 30 unidades inativas. SUCO DETOX 300ML tem 18 unidades e ainda está ativo, mas sem movimentação. Recomendo promoção ou liquidação para liberar espaço rapidamente."}
        ]
    },
    {
        "category": "produtos_inativos",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": "quais produtos posso promover para fazer caixa rápido?"},
            {"role": "assistant", "tool_calls": [{"id": "call_028", "type": "function", "function": {"name": "get_inactive_products", "arguments": "{\"limit\":20}"}}]},
            {"role": "tool", "call_id": "call_028", "content": "[{\"product_code\":\"PRD00701\",\"product_name\":\"CERVEJA ARTESANAL IPA 600ML\",\"quantity\":48,\"inactive\":true},{\"product_code\":\"PRD00801\",\"product_name\":\"GIN PREMIUM NACIONAL 750ML\",\"quantity\":22,\"inactive\":false},{\"product_code\":\"PRD00802\",\"product_name\":\"LICOR AMARETTO 700ML\",\"quantity\":10,\"inactive\":false}]"},
            {"role": "assistant", "content": "Para gerar caixa rapidamente, os melhores candidatos são GIN PREMIUM NACIONAL 750ML com 22 unidades ativas e LICOR AMARETTO 700ML com 10 unidades ativas — ambos com baixo giro e estoque relevante para promoção. A CERVEJA ARTESANAL IPA 600ML tem 48 unidades, mas está inativa: recomenda-se liquidação antes de descontinuar."}
        ]
    },
    {
        "category": "busca_produto",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": "tem whisky disponível?"},
            {"role": "assistant", "tool_calls": [{"id": "call_029", "type": "function", "function": {"name": "search_product_by_name", "arguments": "{\"term\":\"whisky\",\"limit\":10}"}}]},
            {"role": "tool", "tool_call_id": "call_029", "content": "[{\"product_code\":\"PRD00601\",\"product_name\":\"WHISKY JACK DANIELS 1L\",\"quantity\":1,\"minimum_stock\":3},{\"product_code\":\"PRD00602\",\"product_name\":\"WHISKY BLACK LABEL 1L\",\"quantity\":-1,\"minimum_stock\":3},{\"product_code\":\"PRD00603\",\"product_name\":\"WHISKY CHIVAS REGAL 12 ANOS 1L\",\"quantity\":8,\"minimum_stock\":4}]"},
            {"role": "assistant", "content": "Encontrei 3 whiskies. JACK DANIELS 1L tem 1 unidade, abaixo do mínimo de 3. BLACK LABEL 1L está com estoque negativo de -1, o que indica inconsistência. Só CHIVAS REGAL 12 ANOS 1L está regular com 8 unidades. Recomendo auditoria no Black Label e reposição do Jack Daniels."}
        ]
    },
    {
        "category": "busca_produto",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": "pesquisa energético"},
            {"role": "assistant", "tool_calls": [{"id": "call_030", "type": "function", "function": {"name": "search_product_by_name", "arguments": "{\"term\":\"energético\",\"limit\":10}"}}]},
            {"role": "tool", "tool_call_id": "call_030", "content": "[{\"product_code\":\"PRD00213\",\"product_name\":\"ENERGÉTICO RED BULL LT 250ML\",\"quantity\":3,\"minimum_stock\":4},{\"product_code\":\"PRD00502\",\"product_name\":\"ENERGÉTICO MONSTER 473ML\",\"quantity\":5,\"minimum_stock\":8},{\"product_code\":\"PRD00503\",\"product_name\":\"ENERGÉTICO TNT 350ML\",\"quantity\":22,\"minimum_stock\":12}]"},
            {"role": "assistant", "content": "Encontrei 3 energéticos. RED BULL LT 250ML tem 3 unidades, abaixo do mínimo de 4. MONSTER 473ML tem 5 unidades para mínimo de 8. TNT 350ML está regular com 22 unidades. Recomendo reposição de Red Bull e Monster para evitar ruptura."}
        ]
    },
    {
        "category": "busca_produto",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": "busca refrigerante"},
            {"role": "assistant", "tool_calls": [{"id": "call_031", "type": "function", "function": {"name": "search_product_by_name", "arguments": "{\"term\":\"refrigerante\",\"limit\":10}"}}]},
            {"role": "tool", "tool_call_id": "call_031", "content": "[{\"product_code\":\"PRD01001\",\"product_name\":\"REFRIGERANTE COCA-COLA 2L\",\"quantity\":84,\"minimum_stock\":24},{\"product_code\":\"PRD01002\",\"product_name\":\"REFRIGERANTE GUARANÁ ANTARCTICA 2L\",\"quantity\":36,\"minimum_stock\":24},{\"product_code\":\"PRD01003\",\"product_name\":\"REFRIGERANTE FANTA LARANJA 2L\",\"quantity\":0,\"minimum_stock\":12}]"},
            {"role": "assistant", "content": "Encontrei 3 refrigerantes. COCA-COLA 2L tem 84 unidades, bem acima do mínimo. GUARANÁ ANTARCTICA 2L tem 36 unidades, dentro do esperado. FANTA LARANJA 2L está zerada, abaixo do mínimo de 12. Recomendo reposição imediata da Fanta."}
        ]
    },
    {
        "category": "busca_produto",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": "tem gin no estoque?"},
            {"role": "assistant", "tool_calls": [{"id": "call_032", "type": "function", "function": {"name": "search_product_by_name", "arguments": "{\"term\":\"gin\",\"limit\":10}"}}]},
            {"role": "tool", "tool_call_id": "call_032", "content": "[{\"product_code\":\"PRD00401\",\"product_name\":\"GIN SEAGERS 1L\",\"quantity\":-2,\"minimum_stock\":6},{\"product_code\":\"PRD00801\",\"product_name\":\"GIN PREMIUM NACIONAL 750ML\",\"quantity\":22,\"minimum_stock\":6},{\"product_code\":\"PRD00802\",\"product_name\":\"GIN TANQUERAY 750ML\",\"quantity\":4,\"minimum_stock\":4}]"},
            {"role": "assistant", "content": "Encontrei 3 gins. GIN SEAGERS 1L está com estoque negativo de -2, indicando inconsistência que precisa ser auditada. GIN PREMIUM NACIONAL 750ML está em dia com 22 unidades. GIN TANQUERAY 750ML tem 4 unidades, exatamente no limite mínimo — monitore de perto."}
        ]
    },
    {
        "category": "estoque_critico",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": "Preciso dos produtos mais urgentes para repor"},
            {"role": "assistant", "tool_calls": [{"id": "call_033", "type": "function", "function": {"name": "get_critical_stock_products", "arguments": "{\"alert_type\":\"low_stock\",\"limit\":10}"}}]},
            {"role": "tool", "tool_call_id": "call_033", "content": "{\"total_products\":45,\"products\":[{\"product_code\":\"PRD00211\",\"product_name\":\"CERVEJA HEINEKEN LT 350ML\",\"quantity\":3,\"minimum_stock\":24},{\"product_code\":\"PRD00601\",\"product_name\":\"WHISKY JACK DANIELS 1L\",\"quantity\":1,\"minimum_stock\":3},{\"product_code\":\"PRD00421\",\"product_name\":\"VODKA ABSOLUT 750ML\",\"quantity\":2,\"minimum_stock\":4}]}"},
            {"role": "assistant", "content": "Os 3 itens mais urgentes para reposição são CERVEJA HEINEKEN LT 350ML com apenas 3 unidades para mínimo de 24, VODKA ABSOLUT 750ML com 2 para mínimo de 4 e WHISKY JACK DANIELS 1L com apenas 1 unidade. Esses devem ser priorizados no próximo pedido de compra."}
        ]
    },
    {
        "category": "estoque_critico",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": "quais os produtos em ruptura total que são ativos?"},
            {"role": "assistant", "tool_calls": [{"id": "call_034", "type": "function", "function": {"name": "get_critical_stock_products", "arguments": "{\"alert_type\":\"out_of_stock\",\"limit\":50}"}}]},
            {"role": "tool", "tool_call_id": "call_034", "content": "{\"total_products\":18,\"products\":[{\"product_code\":\"PRD00101\",\"product_name\":\"WHISKY OLD PARR 12 ANOS 1L\",\"quantity\":0,\"minimum_stock\":3,\"inactive\":false},{\"product_code\":\"PRD00422\",\"product_name\":\"VODKA SKYY 980ML\",\"quantity\":0,\"minimum_stock\":3,\"inactive\":false},{\"product_code\":\"PRD00510\",\"product_name\":\"CERVEJA CORONA LONG NECK 330ML\",\"quantity\":0,\"minimum_stock\":12,\"inactive\":false},{\"product_code\":\"PRD00210\",\"product_name\":\"CERVEJA BRAHMA LT 350ML\",\"quantity\":0,\"minimum_stock\":24,\"inactive\":true}]}"},
            {"role": "assistant", "content": "Identifiquei 18 produtos em ruptura total. Filtrando os que estão ativos, os principais destaques são o WHISKY OLD PARR 12 ANOS 1L, a VODKA SKYY 980ML e a CERVEJA CORONA LONG NECK 330ML. A Cerveja Brahma LT 350ml também está zerada, porém consta como inativa no sistema. Recomendo focar o pedido de compras nos três primeiros itens para reestabelecer o estoque."}
        ]
    }
]

RECOMMENDED_QUANTITIES = {
    "busca_produto": {"min": 200, "ideal": 400},
    "consulta_estoque": {"min": 300, "ideal": 600},
    "verificacao_disponibilidade": {"min": 200, "ideal": 400},
    "alerta_estoque_critico": {"min": 200, "ideal": 400},
    "resumo_estoque": {"min": 150, "ideal": 300},
    "produtos_inativos": {"min": 100, "ideal": 200},
    "analise_movimentacao": {"min": 150, "ideal": 300},
    "ambiguidade": {"min": 100, "ideal": 200},
    "multi_turno": {"min": 100, "ideal": 200},
}