"""Ponto de entrada do compilador da MiniLang (Léxico, Sintático e Semântico).

Uso:
    python main.py examples/programa.min
"""

import sys
from minilang import AnalisadorSemantico, Lexer
from minilang.parser import ParseError, parsear

CODIGO_SUCESSO = 0
CODIGO_COM_DIAGNOSTICOS = 1
CODIGO_ERRO_DE_USO = 2


def imprimir_tabelas_simbolos(analisador: AnalisadorSemantico) -> None:
    """Exibe as tabelas de símbolos de todos os escopos (global e blocos)."""
    print("=" * 60)
    print("1. TABELAS DE SÍMBOLOS POR ESCOPO")
    print("=" * 60)
    for tabela in analisador.todas_tabelas:
        print(f"\n[Escopo {tabela.nome_escopo}]")
        if not tabela.simbolos:
            print("  (vazio)")
            continue
        print(f"  {'Símbolo':<8} | {'Nome':<15} | {'Tipo':<6} | {'Origem'}")
        print(f"  {'-'*8}-+-{'-'*15}-+-{'-'*6}-+-{'-'*8}")
        for simb in tabela.simbolos.values():
            print(f"  {simb.id:<8} | {simb.nome:<15} | {simb.tipo.value:<6} | {simb.origem}")


def imprimir_ast_anotada(no, analisador: AnalisadorSemantico, prefixo="", eh_ultimo=True) -> None:
    """Imprime a AST anotada com vínculos de símbolos e tipos sintetizados."""
    nome_classe = no.__class__.__name__
    marcador = "└── " if eh_ultimo else "├── "
    prefixo_filhos = prefixo + ("    " if eh_ultimo else "│   ")

    simb = analisador.vinculos.get(id(no))
    tipo = analisador.tipos.get(id(no))
    anotacao_tipo = f": {tipo.value}" if tipo else ""

    if nome_classe == "Programa":
        print("\n" + "=" * 60)
        print("2. AST ANOTADA")
        print("=" * 60)
        print("Programa")
        for i, decl in enumerate(no.declaracoes):
            imprimir_ast_anotada(decl, analisador, "", i == len(no.declaracoes) - 1)

    elif nome_classe == "Declaracao":
        vinculo = simb.id if simb else "ERRO"
        print(f"{prefixo}{marcador}Decl({no.nome}) -> {vinculo}{anotacao_tipo}")

    elif nome_classe == "Atribuicao":
        vinculo = f"{simb.id} ({simb.tipo.value})" if simb else "ERRO"
        print(f"{prefixo}{marcador}Atrib({no.nome}) -> {vinculo} [expr{anotacao_tipo}]")
        imprimir_ast_anotada(no.valor, analisador, prefixo_filhos, True)

    elif nome_classe == "Saida":
        print(f"{prefixo}{marcador}Saida")
        imprimir_ast_anotada(no.expressao, analisador, prefixo_filhos, True)

    elif nome_classe == "Bloco":
        print(f"{prefixo}{marcador}Bloco")
        for i, instr in enumerate(no.instrucoes):
            imprimir_ast_anotada(instr, analisador, prefixo_filhos, i == len(no.instrucoes) - 1)

    elif nome_classe == "Se":
        print(f"{prefixo}{marcador}Se")
        imprimir_ast_anotada(no.condicao, analisador, prefixo_filhos, False)
        imprimir_ast_anotada(no.entao, analisador, prefixo_filhos, no.senao is None)
        if no.senao is not None:
            imprimir_ast_anotada(no.senao, analisador, prefixo_filhos, True)

    elif nome_classe == "Enquanto":
        print(f"{prefixo}{marcador}Enquanto")
        imprimir_ast_anotada(no.condicao, analisador, prefixo_filhos, False)
        imprimir_ast_anotada(no.corpo, analisador, prefixo_filhos, True)

    elif nome_classe == "Binaria":
        print(f"{prefixo}{marcador}Binaria({no.operador}){anotacao_tipo}")
        imprimir_ast_anotada(no.esquerda, analisador, prefixo_filhos, False)
        imprimir_ast_anotada(no.direita, analisador, prefixo_filhos, True)

    elif nome_classe == "Inteiro":
        print(f"{prefixo}{marcador}Inteiro({no.valor}){anotacao_tipo}")

    elif nome_classe == "Booleano":
        print(f"{prefixo}{marcador}Booleano({no.valor}){anotacao_tipo}")

    elif nome_classe == "Variavel":
        vinculo = simb.id if simb else "ERRO"
        print(f"{prefixo}{marcador}Variavel({no.nome}) -> {vinculo}{anotacao_tipo}")


def imprimir_diagnosticos(analisador: AnalisadorSemantico) -> None:
    """Exibe os diagnósticos semânticos encontrados."""
    print("\n" + "=" * 60)
    print("3. DIAGNÓSTICOS SEMÂNTICOS")
    print("=" * 60)
    if not analisador.diagnosticos:
        print("Nenhum erro semântico encontrado.")
    else:
        for diag in analisador.diagnosticos:
            print(f"  {diag}")


def main(argv: list[str]) -> int:
    """Lê o arquivo, executa análise léxica, sintática e semântica."""
    if len(argv) != 2:
        print("uso: python main.py <arquivo.min>", file=sys.stderr)
        return CODIGO_ERRO_DE_USO

    caminho = argv[1]

    try:
        with open(caminho, "r", encoding="utf-8-sig") as arquivo:
            fonte = arquivo.read()
    except OSError as erro:
        print(f"não foi possível ler {caminho}: {erro}", file=sys.stderr)
        return CODIGO_ERRO_DE_USO

    # 1. Verifica erros léxicos primeiro
    _, diagnosticos_lexicos = Lexer(fonte).scan_tokens()
    if diagnosticos_lexicos:
        print("DIAGNÓSTICOS LÉXICOS ENCONTRADOS:\n")
        for d in diagnosticos_lexicos:
            print(f"{d.linha}:{d.coluna} erro léxico: {d.mensagem}")
        return CODIGO_COM_DIAGNOSTICOS

    # 2. Executa o parser e captura erros sintáticos
    try:
        ast = parsear(fonte)
    except ParseError as erro:
        print("ERRO SINTÁTICO:\n")
        print(erro)
        return CODIGO_COM_DIAGNOSTICOS
    except Exception as e:
        print(f"ERRO INTERNO: {e}")
        return CODIGO_COM_DIAGNOSTICOS

    # 3. Executa a análise semântica e exibe os relatórios
    analisador = AnalisadorSemantico()
    analisador.analisar(ast)

    imprimir_tabelas_simbolos(analisador)
    imprimir_ast_anotada(ast, analisador)
    imprimir_diagnosticos(analisador)

    return CODIGO_COM_DIAGNOSTICOS if analisador.diagnosticos else CODIGO_SUCESSO


if __name__ == "__main__":
    sys.exit(main(sys.argv))