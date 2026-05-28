from typing import Dict, List

ALERT_TYPES: Dict[str, Dict] = {

    # ═══════════════════════════════════════════════════════════════
    # RUPTURA
    # ═══════════════════════════════════════════════════════════════

    "zero_stock": {
        "name": "Estoque Zerado",
        "severity": "CRITICO",
        "description": "Produto com quantidade igual a zero.",
        "pt_br_explanation": (
            "Produto fora de estoque com risco imediato "
            "de perda de vendas."
        ),
        "action": "Reposição imediata recomendada.",
        "mongodb_query": {
            "$expr": {
                "$eq": ["$quantidade", 0]
            }
        },
    },

    "out_of_stock": {
        "name": "Fora de Estoque",
        "severity": "CRITICO",
        "description": "Produto sem disponibilidade.",
        "pt_br_explanation": (
            "Produto completamente indisponível "
            "para venda."
        ),
        "action": "Verificar reposição urgente.",
        "mongodb_query": {
            "$expr": {
                "$lte": ["$quantidade", 0]
            }
        },
    },

    "rupture_risk": {
        "name": "Risco de Ruptura",
        "severity": "ALTO",
        "description": (
            "Produto abaixo do estoque mínimo "
            "ou com tendência crítica de saída."
        ),
        "pt_br_explanation": (
            "Produto que pode ficar sem estoque "
            "em breve."
        ),
        "action": "Planejar reposição prioritária.",
        "mongodb_query": {
            "$expr": {
                "$and": [
                    {"$gt": ["$quantidade", 0]},
                    {
                        "$or": [
                            {
                                "$lte": [
                                    "$quantidade",
                                    "$estoque_minimo",
                                ]
                            },
                            {
                                "$and": [
                                    {
                                        "$gte": [
                                            "$movimento_recente",
                                            10,
                                        ]
                                    },
                                    {
                                        "$lte": [
                                            "$quantidade",
                                            {
                                                "$multiply": [
                                                    "$estoque_minimo",
                                                    1.5,
                                                ]
                                            },
                                        ]
                                    },
                                ]
                            },
                        ]
                    },
                ]
            }
        },
    },

    # ═══════════════════════════════════════════════════════════════
    # ESTOQUE BAIXO
    # ═══════════════════════════════════════════════════════════════

    "critical": {
        "name": "Estoque Crítico",
        "severity": "ALTO",
        "description": (
            "Quantidade muito próxima "
            "do estoque mínimo."
        ),
        "pt_br_explanation": (
            "Estoque em nível crítico."
        ),
        "action": (
            "Avaliar reposição emergencial."
        ),
        "mongodb_query": {
            "$expr": {
                "$and": [
                    {"$gt": ["$quantidade", 0]},
                    {
                        "$lte": [
                            "$quantidade",
                            {
                                "$add": [
                                    "$estoque_minimo",
                                    2,
                                ]
                            },
                        ]
                    },
                ]
            }
        },
    },

    "low_stock": {
        "name": "Estoque Baixo",
        "severity": "MEDIO",
        "description": (
            "Quantidade abaixo do estoque mínimo."
        ),
        "pt_br_explanation": (
            "Produto abaixo do nível ideal."
        ),
        "action": (
            "Gerar reposição no próximo ciclo."
        ),
        "mongodb_query": {
            "$expr": {
                "$and": [
                    {"$gt": ["$quantidade", 0]},
                    {
                        "$lt": [
                            "$quantidade",
                            "$estoque_minimo",
                        ]
                    },
                ]
            }
        },
    },

    # ═══════════════════════════════════════════════════════════════
    # INCONSISTÊNCIA
    # ═══════════════════════════════════════════════════════════════

    "negative_stock": {
        "name": "Estoque Negativo",
        "severity": "CRITICO",
        "description": (
            "Quantidade negativa registrada."
        ),
        "pt_br_explanation": (
            "Inconsistência operacional crítica."
        ),
        "action": (
            "Investigar movimentações recentes."
        ),
        "mongodb_query": {
            "$expr": {
                "$lt": ["$quantidade", 0]
            }
        },
    },

    # ═══════════════════════════════════════════════════════════════
    # MOVIMENTAÇÃO
    # ═══════════════════════════════════════════════════════════════

    "high_movement": {
        "name": "Alta Movimentação",
        "severity": "INFORMATIVO",
        "description": (
            "Produto com alta saída recente."
        ),
        "pt_br_explanation": (
            "Produto com forte demanda."
        ),
        "action": (
            "Priorizar reposição."
        ),
        "mongodb_query": {
            "$expr": {
                "$and": [
                    {"$gt": ["$quantidade", 0]},
                    {
                        "$gte": [
                            "$movimento_recente",
                            10,
                        ]
                    },
                ]
            }
        },
    },

    "low_movement": {
        "name": "Baixa Movimentação",
        "severity": "BAIXO",
        "description": (
            "Produto com pouca saída."
        ),
        "pt_br_explanation": (
            "Possível estoque parado."
        ),
        "action": (
            "Avaliar promoções ou revisão de demanda."
        ),
        "mongodb_query": {
            "$expr": {
                "$and": [
                    {"$gt": ["$quantidade", 0]},
                    {
                        "$lt": [
                            "$movimento_recente",
                            3,
                        ]
                    },
                ]
            }
        },
    },

    # ═══════════════════════════════════════════════════════════════
    # EXCESSO
    # ═══════════════════════════════════════════════════════════════

    "overstocked": {
        "name": "Estoque Acumulado",
        "severity": "BAIXO",
        "description": (
            "Quantidade muito acima do ideal."
        ),
        "pt_br_explanation": (
            "Capital parado em estoque."
        ),
        "action": (
            "Revisar previsão de demanda."
        ),
        "mongodb_query": {
            "$expr": {
                "$and": [
                    {
                        "$gt": [
                            "$quantidade",
                            {
                                "$multiply": [
                                    "$estoque_minimo",
                                    5,
                                ]
                            },
                        ]
                    },
                    {
                        "$lt": [
                            "$movimento_recente",
                            2,
                        ]
                    },
                ]
            }
        },
    },

    # ═══════════════════════════════════════════════════════════════
    # INATIVIDADE
    # ═══════════════════════════════════════════════════════════════

    "inactive": {
        "name": "Produto Inativo",
        "severity": "MEDIO",
        "description": (
            "Produto com pouca ou nenhuma movimentação."
        ),
        "pt_br_explanation": (
            "Produto potencialmente parado."
        ),
        "action": (
            "Avaliar descontinuação."
        ),
        "mongodb_query": {
            "$expr": {
                "$and": [
                    {"$gt": ["$quantidade", 0]},
                    {
                        "$or": [
                            {
                                "$eq": [
                                    "$movimento_recente",
                                    0,
                                ]
                            },
                            {
                                "$lte": [
                                    "$movimento_recente",
                                    1,
                                ]
                            },
                        ]
                    },
                ]
            }
        },
    },
}

VALID_ALERT_TYPES: List[str] = list(
    ALERT_TYPES.keys()
)

ALERTS_BY_SEVERITY = {
    "CRITICO": [
        key
        for key, value in ALERT_TYPES.items()
        if value["severity"] == "CRITICO"
    ],

    "ALTO": [
        key
        for key, value in ALERT_TYPES.items()
        if value["severity"] == "ALTO"
    ],

    "MEDIO": [
        key
        for key, value in ALERT_TYPES.items()
        if value["severity"] == "MEDIO"
    ],

    "BAIXO": [
        key
        for key, value in ALERT_TYPES.items()
        if value["severity"] == "BAIXO"
    ],

    "INFORMATIVO": [
        key
        for key, value in ALERT_TYPES.items()
        if value["severity"] == "INFORMATIVO"
    ],
}