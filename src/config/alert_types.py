from enum import Enum
from typing import Dict, List

class AlertTypeEnum(Enum):
    """Enumeração dos tipos de alertas"""
    CRITICAL = "critical"
    LOW_STOCK = "low_stock"
    ZERO_STOCK = "zero_stock"
    RUPTURE_RISK = "rupture_risk"
    NEGATIVE_STOCK = "negative_stock"
    OUT_OF_STOCK = "out_of_stock"
    INACTIVE = "inactive"
    OVERSTOCKED = "overstocked"
    HIGH_MOVEMENT = "high_movement"
    LOW_MOVEMENT = "low_movement"

# Configuração detalhada de cada tipo 
ALERT_TYPES: Dict[str, Dict] = {
    
    # ═══════════════════════════════════════════════════════════════
    # ALERTAS DE RUPTURA
    # ═══════════════════════════════════════════════════════════════
    
    "zero_stock": {
        "name": "Estoque Zerado",
        "description": "Produto com quantidade = 0",
        "severity": "CRITICO",
        "pt_br_explanation": "Produto fora de estoque - risco imediato de perda de vendas",
        "mongodb_query": {
            "$expr": {
                "$eq": ["$quantidade", 0]
            }
        },
        "prompt_reference": "Stock rupture means a product has zero available quantity",
        "action": "Reposição imediata recomendada",
    },
    
    "out_of_stock": {
        "name": "Fora de Estoque",
        "description": "Produto sem quantidade disponível",
        "severity": "CRITICO",
        "pt_br_explanation": "Produto completamente indisponível para venda",
        "mongodb_query": {
            "$expr": {
                "$lte": ["$quantidade", 0]
            }
        },
        "prompt_reference": "If the user asks which products are out of stock, use alert_type='out_of_stock'",
        "action": "Verificar disponibilidade e reposição urgente",
    },
    
    "rupture_risk": {
        "name": "Risco de Ruptura",
        "description": "Produto abaixo do estoque mínimo OU com tendência crítica de saída",
        "severity": "ALTO",
        "pt_br_explanation": "Produto que pode ficar sem estoque em breve - reposição prioritária",
        "mongodb_query": {
            "$expr": {
                "$and": [
                    {"$gt": ["$quantidade", 0]},
                    {
                        "$or": [
                            {"$lte": ["$quantidade", "$estoque_minimo"]},
                            {"$and": [
                                {"$gte": ["$movimento_recente", 10]},
                                {"$lte": ["$quantidade", {"$multiply": ["$estoque_minimo", 1.5]}]}
                            ]}
                        ]
                    }
                ]
            }
        },
        "prompt_reference": "Rupture risk means a product is below minimum stock, at zero stock, or showing critical recent outflow",
        "action": "Planejar reposição com antecedência",
    },
    
    # ═══════════════════════════════════════════════════════════════
    # ALERTAS DE ESTOQUE BAIXO
    # ═══════════════════════════════════════════════════════════════
    
    "critical": {
        "name": "Estoque Crítico",
        "description": "Estoque muito baixo (até 2 unidades acima do mínimo)",
        "severity": "ALTO",
        "pt_br_explanation": "Estoque em nível crítico - revisar reposição imediatamente",
        "mongodb_query": {
            "$expr": {
                "$and": [
                    {"$gt": ["$quantidade", 0]},
                    {"$lte": ["$quantidade", {"$add": ["$estoque_minimo", 2]}]},
                ]
            }
        },
        "prompt_reference": "Identify low-stock items using critical alert",
        "action": "Autorizar reposição de emergência se necessário",
    },
    
    "low_stock": {
        "name": "Estoque Baixo",
        "description": "Estoque abaixo do mínimo configurado",
        "severity": "MEDIO",
        "pt_br_explanation": "Produto com quantidade inferior ao mínimo - reposição recomendada",
        "mongodb_query": {
            "$expr": {
                "$and": [
                    {"$gt": ["$quantidade", 0]},
                    {"$lt": ["$quantidade", "$estoque_minimo"]},
                ]
            }
        },
        "prompt_reference": "If the user asks about critical stock or replenishment needs, use alert_type='low_stock'",
        "action": "Gerar ordem de reposição no próximo ciclo",
    },
    
    # ═══════════════════════════════════════════════════════════════
    # ALERTAS DE INCONSISTÊNCIA
    # ═══════════════════════════════════════════════════════════════
    
    "negative_stock": {
        "name": "Estoque Negativo",
        "description": "Quantidade negativa (inconsistência operacional)",
        "severity": "CRITICO",
        "pt_br_explanation": "Erro crítico - produto com quantidade negativa no sistema",
        "mongodb_query": {
            "$expr": {
                "$lt": ["$quantidade", 0]
            }
        },
        "prompt_reference": "Negative stock indicates an operational inconsistency that requires attention",
        "action": "Investigar imediatamente - revisar movimentação recente",
    },
    
    # ═══════════════════════════════════════════════════════════════
    # ALERTAS DE INATIVIDADE
    # ═══════════════════════════════════════════════════════════════  
    
    "inactive": {
        "name": "Produto Inativo",
        "description": "Produto sem movimento ou descontinuado",
        "severity": "MEDIO",
        "pt_br_explanation": "Produto com pouca/nenhuma movimentação - considerar descontinuar",
        "mongodb_query": {
            "$expr": {
                "$and": [
                    {"$gt": ["$quantidade", 0]},
                    {
                        "$or": [
                            {"$eq": ["$movimento_recente", 0]},
                            {"$lte": ["$movimento_recente", 1]},
                        ]
                    }
                ]
            }
        },
        "prompt_reference": "If the user asks about inactive catalog items, use get_inactive_products",
        "action": "Revisar capital investido em estoque parado",
    },
    
    "low_movement": {
        "name": "Movimento Baixo",
        "description": "Produto com pouca saída nos últimos períodos",
        "severity": "BAIXO",
        "pt_br_explanation": "Produto com baixa rotatividade - pode estar acumulando capital",
        "mongodb_query": {
            "$expr": {
                "$and": [
                    {"$gt": ["$quantidade", 0]},
                    {"$lt": ["$movimento_recente", 3]},
                ]
            }
        },
        "prompt_reference": "Low or no relevant movement may indicate idle stock",
        "action": "Considerar promoção ou desconto para aumentar giro",
    },
    
    # ═══════════════════════════════════════════════════════════════
    # ALERTAS DE EXCESSO
    # ═══════════════════════════════════════════════════════════════
    
    "overstocked": {
        "name": "Estoque Acumulado",
        "description": "Quantidade muito acima do mínimo sem movimento",
        "severity": "BAIXO",
        "pt_br_explanation": "Produto acumulado - pode indicar previsão incorreta",
        "mongodb_query": {
            "$expr": {
                "$and": [
                    {"$gt": ["$quantidade", {"$multiply": ["$estoque_minimo", 5]}]},
                    {"$lt": ["$movimento_recente", 2]},
                ]
            }
        },
        "prompt_reference": "High stock levels with low movement suggest capital tied up",
        "action": "Revisar demanda ou considerar promoção",
    },
    
    "high_movement": {
        "name": "Alta Movimentação",
        "description": "Produto com alta saída recente",
        "severity": "INFORMATIVO",
        "pt_br_explanation": "Produto com boa rotatividade - considerado em prioridade de reposição",
        "mongodb_query": {
            "$expr": {
                "$and": [
                    {"$gt": ["$quantidade", 0]},
                    {"$gte": ["$movimento_recente", 10]},
                ]
            }
        },
        "prompt_reference": "High stock outflow suggests stronger product movement and possible replenishment priority",
        "action": "Prioritizar reposição - produto com boa demanda",
    },
}

# Lista de tipos válidos (para validação rápida)
VALID_ALERT_TYPES: List[str] = list(ALERT_TYPES.keys())

ALERTS_BY_SEVERITY = {
    "CRITICO": [k for k, v in ALERT_TYPES.items() if v["severity"] == "CRITICO"],
    "ALTO": [k for k, v in ALERT_TYPES.items() if v["severity"] == "ALTO"],
    "MEDIO": [k for k, v in ALERT_TYPES.items() if v["severity"] == "MEDIO"],
    "BAIXO": [k for k, v in ALERT_TYPES.items() if v["severity"] == "BAIXO"],
    "INFORMATIVO": [k for k, v in ALERT_TYPES.items() if v["severity"] == "INFORMATIVO"],
}

class AlertTypeManager:
    """
    Gerenciador de tipos de alerta
    """
    @staticmethod
    def normalize(alert_type) -> str:
        """
        Normalize alert type input.
        """

        if isinstance(alert_type, Enum):
            return alert_type.value

        return str(alert_type).strip().lower()

    @staticmethod
    def is_valid(alert_type: str) -> bool:
        """Verifica se o tipo de alerta é válido"""
        return alert_type in VALID_ALERT_TYPES
    
    @staticmethod
    def get_all() -> List[str]:
        """Retorna todos os tipos válidos"""
        return VALID_ALERT_TYPES
    
    @staticmethod
    def get_by_severity(severity: str) -> List[str]:
        """Retorna tipos por severidade"""
        return ALERTS_BY_SEVERITY.get(severity, [])
    
    @staticmethod
    def get_config(alert_type: str) -> Dict:
        """Retorna configuração completa do tipo de alerta"""
        if not AlertTypeManager.is_valid(alert_type):
            raise ValueError(f"Alert type '{alert_type}' is not valid")
        return ALERT_TYPES[alert_type]
    
    @staticmethod
    def get_mongodb_query(alert_type: str) -> Dict:
        """Retorna query MongoDB para o tipo de alerta"""
        config = AlertTypeManager.get_config(alert_type)
        return config.get("mongodb_query", {})
    
    @staticmethod
    def get_description(alert_type: str) -> str:
        """Retorna descrição amigável do tipo de alerta"""
        config = AlertTypeManager.get_config(alert_type)
        return f"{config['name']}: {config['pt_br_explanation']}"