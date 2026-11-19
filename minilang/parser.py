"""Parser descendente recursivo da MiniLang."""

from __future__ import annotations
from typing import Any

from minilang.lexer import Lexer
from minilang.tokens import Token, TokenType
from .ast import (
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


class ParseError(Exception):
    """Erro sintático detectado durante a análise."""

    def __init__(self, mensagem: str, token: Token):
        super().__init__(
            f"Erro sintático na linha {token.linha}, coluna {token.coluna} "
            f"no token '{token.lexema}': {mensagem}"
        )
        self.token = token


class Parser:
    """Analisa uma sequência de tokens e produz uma AST."""

    def __init__(self, tokens: list[Token]) -> None:
        self.tokens = tokens
        self.index = 0

    def programa(self) -> Programa:
        """Nó raiz do programa."""
        return Programa(self.lista_itens())

    def lista_itens(self, parar_em: TokenType | None = None) -> list[Any]:
        """Consome uma sequência de itens até o fim do arquivo ou delimitador."""
        instrucoes = []
        while not self.at_end():
            if parar_em is not None and self.check(parar_em):
                break
            instrucoes.append(self.item())
        return instrucoes

    def item(self) -> Any:
        """Roteia para declaração, saída, bloco, condicional, laço ou atribuição."""
        if self.match(TokenType.KW_INT, TokenType.KW_BOOL):
            return self.declaracao(self.previous())
        if self.match(TokenType.KW_PRINT):
            return self.saida(self.previous())
        if self.match(TokenType.LBRACE):
            return self.bloco(self.previous())
        if self.match(TokenType.KW_IF):
            return self.comando_se(self.previous())
        if self.match(TokenType.KW_WHILE):
            return self.comando_enquanto(self.previous())

        return self.atribuicao()

    def bloco(self, token_abertura: Token) -> Bloco:
        """Reconhece: { lista_itens }"""
        instrucoes = self.lista_itens(parar_em=TokenType.RBRACE)
        self.expect(TokenType.RBRACE, "esperado '}' para fechar o bloco")
        return Bloco(instrucoes, linha=token_abertura.linha, coluna=token_abertura.coluna)

    def comando_se(self, token_if: Token) -> Se:
        """Reconhece: if ( expressao ) instrucao [else instrucao]"""
        self.expect(TokenType.LPAREN, "esperado '(' após 'if'")
        condicao = self.expressao()
        self.expect(TokenType.RPAREN, "esperado ')' após condição do 'if'")
        entao = self.item()
        senao = None
        if self.match(TokenType.KW_ELSE):
            senao = self.item()
        return Se(condicao, entao, senao, linha=token_if.linha, coluna=token_if.coluna)

    def comando_enquanto(self, token_while: Token) -> Enquanto:
        """Reconhece: while ( expressao ) instrucao"""
        self.expect(TokenType.LPAREN, "esperado '(' após 'while'")
        condicao = self.expressao()
        self.expect(TokenType.RPAREN, "esperado ')' após condição do 'while'")
        corpo = self.item()
        return Enquanto(condicao, corpo, linha=token_while.linha, coluna=token_while.coluna)

    def atribuicao(self) -> Atribuicao:
        """Reconhece: ident = expressao ;"""
        nome_token = self.expect(TokenType.IDENT, "esperado identificador para atribuição")
        self.expect(TokenType.ASSIGN, "esperado '=' após o identificador")
        valor = self.expressao()
        self.expect(TokenType.SEMICOLON, "esperado ';' após atribuição")
        return Atribuicao(
            nome_token.lexema,
            valor,
            linha=nome_token.linha,
            coluna=nome_token.coluna,
        )

    def declaracao(self, token_tipo: Token) -> Declaracao:
        """Reconhece: (int | bool) ident ;"""
        nome_token = self.expect(
            TokenType.IDENT, f"esperado identificador após '{token_tipo.lexema}'"
        )
        self.expect(TokenType.SEMICOLON, "esperado ';' após declaração")
        return Declaracao(
            nome=nome_token.lexema,
            tipo=token_tipo.lexema,
            linha=nome_token.linha,
            coluna=nome_token.coluna,
        )

    def saida(self, token_print: Token) -> Saida:
        """Reconhece: print ( expressao ) ;"""
        self.expect(TokenType.LPAREN, "esperado '(' após 'print'")
        expr = self.expressao()
        self.expect(TokenType.RPAREN, "esperado ')' após expressão")
        self.expect(TokenType.SEMICOLON, "esperado ';' após print")
        return Saida(expr, linha=token_print.linha, coluna=token_print.coluna)

    # ==========================================
    # Hierarquia de Expressões (Menor -> Maior precedência)
    # ==========================================
    def expressao(self) -> Any:
        """Ponto de entrada para expressões."""
        return self.expressao_ou()

    def expressao_ou(self) -> Any:
        """Reconhece operador lógico OR."""
        expr = self.expressao_e()
        while self.check(TokenType.KW_OR):
            op = self.advance()
            direita = self.expressao_e()
            expr = Binaria(op.lexema, expr, direita, linha=op.linha, coluna=op.coluna)
        return expr

    def expressao_e(self) -> Any:
        """Reconhece operador lógico AND."""
        expr = self.igualdade()
        while self.check(TokenType.KW_AND):
            op = self.advance()
            direita = self.igualdade()
            expr = Binaria(op.lexema, expr, direita, linha=op.linha, coluna=op.coluna)
        return expr

    def igualdade(self) -> Any:
        """Reconhece operadores == e !=."""
        expr = self.comparacao()
        while self.check_any(TokenType.EQUAL_EQUAL, TokenType.BANG_EQUAL):
            op = self.advance()
            direita = self.comparacao()
            expr = Binaria(op.lexema, expr, direita, linha=op.linha, coluna=op.coluna)
        return expr

    def comparacao(self) -> Any:
        """Reconhece operadores <, <=, >, >=."""
        expr = self.soma()
        while self.check_any(
            TokenType.LESS,
            TokenType.LESS_EQUAL,
            TokenType.GREATER,
            TokenType.GREATER_EQUAL,
        ):
            op = self.advance()
            direita = self.soma()
            expr = Binaria(op.lexema, expr, direita, linha=op.linha, coluna=op.coluna)
        return expr

    def soma(self) -> Any:
        """Reconhece operadores aditivos (+, -)."""
        expr = self.termo()
        while self.check_any(TokenType.PLUS, TokenType.MINUS):
            op = self.advance()
            direita = self.termo()
            expr = Binaria(op.lexema, expr, direita, linha=op.linha, coluna=op.coluna)
        return expr

    def termo(self) -> Any:
        """Reconhece operadores multiplicativos (*, /)."""
        expr = self.fator()
        while self.check_any(TokenType.STAR, TokenType.SLASH):
            op = self.advance()
            direita = self.fator()
            expr = Binaria(op.lexema, expr, direita, linha=op.linha, coluna=op.coluna)
        return expr

    def fator(self) -> Any:
        """Reconhece literais, variáveis ou expressões entre parênteses."""
        if self.match(TokenType.INT_LITERAL):
            tok = self.previous()
            return Inteiro(int(tok.lexema), linha=tok.linha, coluna=tok.coluna)
        if self.match(TokenType.KW_TRUE):
            tok = self.previous()
            return Booleano(True, linha=tok.linha, coluna=tok.coluna)
        if self.match(TokenType.KW_FALSE):
            tok = self.previous()
            return Booleano(False, linha=tok.linha, coluna=tok.coluna)
        if self.match(TokenType.IDENT):
            tok = self.previous()
            return Variavel(tok.lexema, linha=tok.linha, coluna=tok.coluna)
        if self.match(TokenType.LPAREN):
            expr = self.expressao()
            self.expect(TokenType.RPAREN, "esperado ')' após expressão")
            return expr

        raise ParseError("expressão inválida", self.peek())

    # ==========================================
    # Funções Auxiliares
    # ==========================================
    def match(self, *tipos: TokenType) -> bool:
        if self.check_any(*tipos):
            self.advance()
            return True
        return False

    def check_any(self, *tipos: TokenType) -> bool:
        if self.at_end():
            return False
        return self.peek().tipo in tipos

    def check(self, tipo: TokenType) -> bool:
        if self.at_end():
            return False
        return self.peek().tipo is tipo

    def expect(self, tipo: TokenType, mensagem: str) -> Token:
        if self.check(tipo):
            return self.advance()
        raise ParseError(mensagem, self.peek())

    def advance(self) -> Token:
        if not self.at_end():
            token = self.tokens[self.index]
            self.index += 1
            return token
        return self.tokens[-1]

    def previous(self) -> Token:
        return self.tokens[self.index - 1]

    def at_end(self) -> bool:
        return self.peek().tipo is TokenType.EOF

    def peek(self) -> Token:
        return self.tokens[self.index]


def parsear(fonte: str) -> Programa:
    """Analisa uma entrada textual da MiniLang e devolve a AST."""
    tokens, diagnosticos = Lexer(fonte).scan_tokens()
    if diagnosticos:
        raise ValueError(f"Erros léxicos encontrados: {diagnosticos}")

    return Parser(tokens).programa()