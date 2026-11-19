"""Árvores sintáticas abstratas da MiniLang."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Programa:
    declaracoes: list[Any] = field(default_factory=list)


@dataclass(frozen=True)
class Declaracao:
    nome: str
    tipo: str = "int"
    linha: int = 0
    coluna: int = 0


@dataclass(frozen=True)
class Atribuicao:
    nome: str
    valor: Any
    linha: int = 0
    coluna: int = 0


@dataclass(frozen=True)
class Saida:
    expressao: Any
    linha: int = 0
    coluna: int = 0


@dataclass(frozen=True)
class Variavel:
    nome: str
    linha: int = 0
    coluna: int = 0


@dataclass(frozen=True)
class Inteiro:
    valor: int
    linha: int = 0
    coluna: int = 0


@dataclass(frozen=True)
class Booleano:
    valor: bool
    linha: int = 0
    coluna: int = 0


@dataclass(frozen=True)
class Binaria:
    operador: str
    esquerda: Any
    direita: Any
    linha: int = 0
    coluna: int = 0


@dataclass(frozen=True)
class Bloco:
    instrucoes: list[Any] = field(default_factory=list)
    linha: int = 0
    coluna: int = 0


@dataclass(frozen=True)
class Se:
    condicao: Any
    entao: Any
    senao: Any | None = None
    linha: int = 0
    coluna: int = 0


@dataclass(frozen=True)
class Enquanto:
    condicao: Any
    corpo: Any
    linha: int = 0
    coluna: int = 0