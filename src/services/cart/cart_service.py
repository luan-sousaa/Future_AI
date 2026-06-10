"""Carrinho de compras do agente varejista.

O carrinho vive em `tool_context.state["cart"]` — só as tools têm acesso ao
estado da sessão. Estas funções operam sobre o dict de estado puro (sem
ToolContext), o que as torna testáveis isoladamente. As tools em
`src/tools/cart_tools.py` envolvem isto com validação de estoque, e o
`processar_pagamento` lê/limpa o carrinho no checkout.

Cada item: {codigo_produto, descricao_completa, familia_produto,
            quantidade, preco_unitario}. O carrinho é chaveado por
codigo_produto — re-adicionar o mesmo produto ATUALIZA a quantidade
(a última quantidade vence), em vez de duplicar a linha.
"""
from __future__ import annotations

from typing import Any

CART_KEY = "cart"


def get_cart(state: dict[str, Any]) -> list[dict[str, Any]]:
    return state.get(CART_KEY, [])


def add_item(
    state: dict[str, Any],
    *,
    codigo_produto: str,
    descricao_completa: str,
    familia_produto: str | None,
    quantidade: int,
    preco_unitario: float,
) -> list[dict[str, Any]]:
    """Adiciona (ou atualiza a quantidade de) um item no carrinho."""
    cart = state.get(CART_KEY, [])

    for item in cart:
        if item["codigo_produto"] == codigo_produto:
            item["quantidade"] = quantidade
            item["preco_unitario"] = preco_unitario
            item["descricao_completa"] = descricao_completa
            item["familia_produto"] = familia_produto
            break
    else:
        cart.append(
            {
                "codigo_produto": codigo_produto,
                "descricao_completa": descricao_completa,
                "familia_produto": familia_produto,
                "quantidade": quantidade,
                "preco_unitario": preco_unitario,
            }
        )

    state[CART_KEY] = cart
    return cart


def remove_item(
    state: dict[str, Any],
    codigo_produto: str,
) -> list[dict[str, Any]]:
    cart = [
        item
        for item in state.get(CART_KEY, [])
        if item["codigo_produto"] != codigo_produto
    ]
    state[CART_KEY] = cart
    return cart


def clear_cart(state: dict[str, Any]) -> None:
    state[CART_KEY] = []


def item_total(item: dict[str, Any]) -> float:
    return round(
        (item.get("quantidade") or 0) * (item.get("preco_unitario") or 0.0),
        2,
    )


def cart_total(cart: list[dict[str, Any]]) -> float:
    return round(sum(item_total(item) for item in cart), 2)


def cart_summary(cart: list[dict[str, Any]]) -> dict[str, Any]:
    """Resumo amigável pro agente narrar."""
    return {
        "itens": [
            {
                "codigo_produto": item.get("codigo_produto"),
                "descricao_completa": item.get("descricao_completa"),
                "quantidade": item.get("quantidade"),
                "preco_unitario": item.get("preco_unitario"),
                "subtotal": item_total(item),
            }
            for item in cart
        ],
        "total": cart_total(cart),
        "quantidade_itens": len(cart),
    }
