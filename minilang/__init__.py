"""MiniLang: lexer, parser e analisador semântico."""

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
from minilang.diagnostics import Diagnostico
from minilang.lexer import Lexer, tokenizar
from minilang.parser import Parser, parsear
from minilang.semantic import (
    AnalisadorSemantico,
    DiagnosticoSemantico,
    Simbolo,
    TabelaSimbolos,
    Tipo,
)
from minilang.tokens import PALAVRAS_RESERVADAS, Token, TokenType

__all__ = [
    "AnalisadorSemantico",
    "Atribuicao",
    "Binaria",
    "Bloco",
    "Booleano",
    "Declaracao",
    "Diagnostico",
    "DiagnosticoSemantico",
    "Enquanto",
    "Inteiro",
    "Lexer",
    "PALAVRAS_RESERVADAS",
    "Parser",
    "Programa",
    "Saida",
    "Se",
    "Simbolo",
    "TabelaSimbolos",
    "Tipo",
    "Token",
    "TokenType",
    "Variavel",
    "parsear",
    "tokenizar",
]