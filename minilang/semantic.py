"""Analisador Semântico da MiniLang: escopos, resolução de nomes e tipos."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from minilang.ast import (
    Atribuicao,
    Binaria,
    Bloco,
    Booleano,
    Declaracao,
    Enquanto,
    Inteiro,
    Programa,
    Saida,
    Se,
    Variavel,
)


class Tipo(Enum):
    INT = "int"
    BOOL = "bool"
    ERRO = "ERRO"


@dataclass(frozen=True)
class Simbolo:
    """Representa uma declaração válida registrada na tabela de símbolos."""

    id: str
    nome: str
    tipo: Tipo
    escopo: str
    linha: int
    coluna: int

    @property
    def origem(self) -> str:
        return f"{self.linha}:{self.coluna}"


@dataclass(frozen=True)
class DiagnosticoSemantico:
    """Erro semântico detectado durante a análise."""

    linha: int
    coluna: int
    causa: str

    def __str__(self) -> str:
        return f"{self.linha}:{self.coluna}: {self.causa}"


@dataclass
class TabelaSimbolos:
    """Tabela de símbolos de um único escopo."""

    id_escopo: int
    nome_escopo: str
    pai: TabelaSimbolos | None = None
    simbolos: dict[str, Simbolo] = field(default_factory=dict)

    def declarar(self, simbolo: Simbolo) -> bool:
        """Tenta inserir o símbolo apenas no escopo atual. Retorna False se duplicado."""
        if simbolo.nome in self.simbolos:
            return False
        self.simbolos[simbolo.nome] = simbolo
        return True

    def buscar_local(self, nome: str) -> Simbolo | None:
        return self.simbolos.get(nome)

    def resolver(self, nome: str) -> Simbolo | None:
        """Procura do escopo atual para fora (até o global)."""
        atual: TabelaSimbolos | None = self
        while atual is not None:
            encontrado = atual.simbolos.get(nome)
            if encontrado is not None:
                return encontrado
            atual = atual.pai
        return None


class AnalisadorSemantico:
    """Percorre a AST em uma passagem anotando vínculos, tipos e diagnósticos."""

    def __init__(self) -> None:
        self.contador_simbolos = 0
        self.contador_escopos = 0

        self.escopo_global = TabelaSimbolos(id_escopo=0, nome_escopo="0. global", pai=None)
        self.escopo_atual = self.escopo_global
        self.todas_tabelas: list[TabelaSimbolos] = [self.escopo_global]

        # Anotações indexadas por id(no) já que os nós da AST são frozen=True
        self.vinculos: dict[int, Simbolo | None] = {}
        self.tipos: dict[int, Tipo] = {}
        self.diagnosticos: list[DiagnosticoSemantico] = []

    def analisar(self, programa: Programa) -> None:
        """Executa a análise semântica completa a partir do nó raiz."""
        for item in programa.declaracoes:
            self._visitar(item)

    # ------------------------------------------------------------------
    # Helpers internos
    # ------------------------------------------------------------------
    def _novo_simbolo(self, nome: str, tipo: Tipo, linha: int, coluna: int) -> Simbolo:
        simbolo = Simbolo(
            id=f"s{self.contador_simbolos}",
            nome=nome,
            tipo=tipo,
            escopo=self.escopo_atual.nome_escopo,
            linha=linha,
            coluna=coluna,
        )
        self.contador_simbolos += 1
        return simbolo

    def _entrar_escopo(self) -> None:
        self.contador_escopos += 1
        nova_tabela = TabelaSimbolos(
            id_escopo=self.contador_escopos,
            nome_escopo=f"{self.contador_escopos}. bloco",
            pai=self.escopo_atual,
        )
        self.escopo_atual = nova_tabela
        self.todas_tabelas.append(nova_tabela)

    def _sair_escopo(self) -> None:
        if self.escopo_atual.pai is not None:
            self.escopo_atual = self.escopo_atual.pai

    def _erro(self, linha: int, coluna: int, causa: str) -> None:
        self.diagnosticos.append(DiagnosticoSemantico(linha, coluna, causa))

    def _converter_tipo(self, nome_tipo: str) -> Tipo:
        if nome_tipo == "int":
            return Tipo.INT
        if nome_tipo == "bool":
            return Tipo.BOOL
        return Tipo.ERRO

    # ------------------------------------------------------------------
    # Visitas na AST
    # ------------------------------------------------------------------
    def _visitar(self, no: Any) -> Tipo:
        if isinstance(no, Declaracao):
            return self._visitar_declaracao(no)
        if isinstance(no, Atribuicao):
            return self._visitar_atribuicao(no)
        if isinstance(no, Saida):
            return self._visitar_saida(no)
        if isinstance(no, Bloco):
            return self._visitar_bloco(no)
        if isinstance(no, Se):
            return self._visitar_se(no)
        if isinstance(no, Enquanto):
            return self._visitar_enquanto(no)
        if isinstance(no, Binaria):
            return self._visitar_binaria(no)
        if isinstance(no, Variavel):
            return self._visitar_variavel(no)
        if isinstance(no, Inteiro):
            self.tipos[id(no)] = Tipo.INT
            return Tipo.INT
        if isinstance(no, Booleano):
            self.tipos[id(no)] = Tipo.BOOL
            return Tipo.BOOL

        return Tipo.ERRO

    def _visitar_declaracao(self, no: Declaracao) -> Tipo:
        tipo_decl = self._converter_tipo(no.tipo)
        existente = self.escopo_atual.buscar_local(no.nome)

        if existente is not None:
            self._erro(
                no.linha,
                no.coluna,
                f"redeclaração de '{no.nome}' neste escopo (já declarado em {existente.origem}).",
            )
            self.vinculos[id(no)] = None
            self.tipos[id(no)] = Tipo.ERRO
            return Tipo.ERRO

        simbolo = self._novo_simbolo(no.nome, tipo_decl, no.linha, no.coluna)
        self.escopo_atual.declarar(simbolo)
        self.vinculos[id(no)] = simbolo
        self.tipos[id(no)] = tipo_decl
        return tipo_decl

    def _visitar_atribuicao(self, no: Atribuicao) -> Tipo:
        simbolo = self.escopo_atual.resolver(no.nome)
        self.vinculos[id(no)] = simbolo

        if simbolo is None:
            self._erro(no.linha, no.coluna, f"identificador '{no.nome}' não declarado neste ponto.")

        # Visita a expressão independentemente do destino para capturar erros separados
        tipo_expr = self._visitar(no.valor)

        if simbolo is None or tipo_expr == Tipo.ERRO:
            self.tipos[id(no)] = Tipo.ERRO
            return Tipo.ERRO

        if simbolo.tipo != tipo_expr:
            self._erro(
                no.linha,
                no.coluna,
                f"atribuição incompatível para '{no.nome}': esperado '{simbolo.tipo.value}', encontrado '{tipo_expr.value}'.",
            )
            self.tipos[id(no)] = Tipo.ERRO
            return Tipo.ERRO

        self.tipos[id(no)] = simbolo.tipo
        return simbolo.tipo

    def _visitar_saida(self, no: Saida) -> Tipo:
        tipo_expr = self._visitar(no.expressao)
        if tipo_expr == Tipo.ERRO:
            self.tipos[id(no)] = Tipo.ERRO
            return Tipo.ERRO

        if tipo_expr not in (Tipo.INT, Tipo.BOOL):
            self._erro(
                no.linha,
                no.coluna,
                f"comando 'print' não aceita expressão do tipo '{tipo_expr.value}'.",
            )
            self.tipos[id(no)] = Tipo.ERRO
            return Tipo.ERRO

        self.tipos[id(no)] = tipo_expr
        return tipo_expr

    def _visitar_bloco(self, no: Bloco) -> Tipo:
        self._entrar_escopo()
        for instrucao in no.instrucoes:
            self._visitar(instrucao)
        self._sair_escopo()
        return Tipo.INT

    def _visitar_se(self, no: Se) -> Tipo:
        tipo_cond = self._visitar(no.condicao)
        if tipo_cond != Tipo.ERRO and tipo_cond != Tipo.BOOL:
            self._erro(
                no.linha,
                no.coluna,
                f"condição do 'if' deve ser 'bool', mas foi encontrado '{tipo_cond.value}'.",
            )

        self._visitar(no.entao)
        if no.senao is not None:
            self._visitar(no.senao)
        return Tipo.BOOL

    def _visitar_enquanto(self, no: Enquanto) -> Tipo:
        tipo_cond = self._visitar(no.condicao)
        if tipo_cond != Tipo.ERRO and tipo_cond != Tipo.BOOL:
            self._erro(
                no.linha,
                no.coluna,
                f"condição do 'while' deve ser 'bool', mas foi encontrado '{tipo_cond.value}'.",
            )

        self._visitar(no.corpo)
        return Tipo.BOOL

    def _visitar_variavel(self, no: Variavel) -> Tipo:
        simbolo = self.escopo_atual.resolver(no.nome)
        self.vinculos[id(no)] = simbolo

        if simbolo is None:
            self._erro(no.linha, no.coluna, f"identificador '{no.nome}' não declarado neste ponto.")
            self.tipos[id(no)] = Tipo.ERRO
            return Tipo.ERRO

        self.tipos[id(no)] = simbolo.tipo
        return simbolo.tipo

    def _visitar_binaria(self, no: Binaria) -> Tipo:
        tipo_esq = self._visitar(no.esquerda)
        tipo_dir = self._visitar(no.direita)

        # Propaga ERRO sem emitir diagnóstico duplicado
        if tipo_esq == Tipo.ERRO or tipo_dir == Tipo.ERRO:
            self.tipos[id(no)] = Tipo.ERRO
            return Tipo.ERRO

        op = no.operador

        # Aritméticos: int x int -> int
        if op in ("+", "-", "*", "/"):
            if tipo_esq == Tipo.INT and tipo_dir == Tipo.INT:
                self.tipos[id(no)] = Tipo.INT
                return Tipo.INT
            self._erro(
                no.linha,
                no.coluna,
                f"operandos incompatíveis para '{op}': esperado 'int' e 'int', encontrado '{tipo_esq.value}' e '{tipo_dir.value}'.",
            )
            self.tipos[id(no)] = Tipo.ERRO
            return Tipo.ERRO

        # Comparação de ordem: int x int -> bool
        if op in ("<", "<=", ">", ">="):
            if tipo_esq == Tipo.INT and tipo_dir == Tipo.INT:
                self.tipos[id(no)] = Tipo.BOOL
                return Tipo.BOOL
            self._erro(
                no.linha,
                no.coluna,
                f"operandos incompatíveis para '{op}': esperado 'int' e 'int', encontrado '{tipo_esq.value}' e '{tipo_dir.value}'.",
            )
            self.tipos[id(no)] = Tipo.ERRO
            return Tipo.ERRO

        # Igualdade: tipos iguais (int==int ou bool==bool) -> bool
        if op in ("==", "!="):
            if tipo_esq == tipo_dir:
                self.tipos[id(no)] = Tipo.BOOL
                return Tipo.BOOL
            self._erro(
                no.linha,
                no.coluna,
                f"operandos incompatíveis para '{op}': tipos devem ser iguais, encontrado '{tipo_esq.value}' e '{tipo_dir.value}'.",
            )
            self.tipos[id(no)] = Tipo.ERRO
            return Tipo.ERRO

        # Lógicos: bool x bool -> bool
        if op in ("AND", "and", "OR", "or"):
            if tipo_esq == Tipo.BOOL and tipo_dir == Tipo.BOOL:
                self.tipos[id(no)] = Tipo.BOOL
                return Tipo.BOOL
            self._erro(
                no.linha,
                no.coluna,
                f"operandos incompatíveis para '{op}': esperado 'bool' e 'bool', encontrado '{tipo_esq.value}' e '{tipo_dir.value}'.",
            )
            self.tipos[id(no)] = Tipo.ERRO
            return Tipo.ERRO

        self.tipos[id(no)] = Tipo.ERRO
        return Tipo.ERRO