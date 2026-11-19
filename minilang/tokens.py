"""Tipos de token e tabela de palavras reservadas da MiniLang."""

from dataclasses import dataclass
from enum import Enum


class TokenType(Enum):
    """Categorias de token produzidas pelo lexer."""

    # KEYWORD_CORE
    KW_INT = "KW_INT"
    KW_BOOL = "KW_BOOL"
    KW_PRINT = "KW_PRINT"

    # KEYWORD_EXT
    KW_IF = "KW_IF"
    KW_ELSE = "KW_ELSE"
    KW_WHILE = "KW_WHILE"

    # BOOLEANOS E LÓGICOS
    KW_TRUE = "KW_TRUE"
    KW_FALSE = "KW_FALSE"
    KW_AND = "KW_AND"
    KW_OR = "KW_OR"

    # IDENT_BASE e INT_LITERAL
    IDENT = "IDENT"
    INT_LITERAL = "INT_LITERAL"

    # ASSIGN
    ASSIGN = "ASSIGN"

    # ARITH_OP
    PLUS = "PLUS"
    MINUS = "MINUS"
    STAR = "STAR"
    SLASH = "SLASH"

    # REL_OP
    EQUAL_EQUAL = "EQUAL_EQUAL"
    BANG_EQUAL = "BANG_EQUAL"
    LESS = "LESS"
    LESS_EQUAL = "LESS_EQUAL"
    GREATER = "GREATER"
    GREATER_EQUAL = "GREATER_EQUAL"

    # DELIMITER_CORE
    LPAREN = "LPAREN"
    RPAREN = "RPAREN"
    SEMICOLON = "SEMICOLON"

    # BLOCK_DELIMITER
    LBRACE = "LBRACE"
    RBRACE = "RBRACE"

    # Fim da entrada
    EOF = "EOF"


PALAVRAS_RESERVADAS = {
    "int": TokenType.KW_INT,
    "bool": TokenType.KW_BOOL,
    "print": TokenType.KW_PRINT,
    "if": TokenType.KW_IF,
    "else": TokenType.KW_ELSE,
    "while": TokenType.KW_WHILE,
    "True": TokenType.KW_TRUE,
    "true": TokenType.KW_TRUE,
    "False": TokenType.KW_FALSE,
    "false": TokenType.KW_FALSE,
    "AND": TokenType.KW_AND,
    "and": TokenType.KW_AND,
    "OR": TokenType.KW_OR,
    "or": TokenType.KW_OR,
}


@dataclass(frozen=True)
class Token:
    """Unidade léxica reconhecida, com a posição do seu primeiro símbolo."""

    tipo: TokenType
    lexema: str
    linha: int
    coluna: int

    def __str__(self) -> str:
        return f"{self.linha}:{self.coluna} {self.tipo.value} {self.lexema!r}"