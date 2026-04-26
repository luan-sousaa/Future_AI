from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class PrecoProduto:
    mercado: str
    preco: float


@dataclass
class Produto:
    id: str
    nome: str
    especificacao: str | None
    unidade_medida: str
    precos: dict[str, float | None] = field(default_factory=dict)

    def precos_validos(self) -> dict[str, float]:
        return {
            mercado: preco
            for mercado, preco in self.precos.items()
            if preco is not None
        }

    def menor_preco(self) -> PrecoProduto | None:
        validos = self.precos_validos()
        if not validos:
            return None

        mercado, preco = min(validos.items(), key=lambda item: item[1])
        return PrecoProduto(mercado=mercado, preco=preco)

    def maior_preco(self) -> PrecoProduto | None:
        validos = self.precos_validos()
        if not validos:
            return None

        mercado, preco = max(validos.items(), key=lambda item: item[1])
        return PrecoProduto(mercado=mercado, preco=preco)

    def precos_ordenados(self) -> list[PrecoProduto]:
        validos = self.precos_validos()

        return [
            PrecoProduto(mercado=mercado, preco=preco)
            for mercado, preco in sorted(validos.items(), key=lambda item: item[1])
        ]


@dataclass
class Categoria:
    id: str
    nome: str
    produtos: list[Produto] = field(default_factory=list)
