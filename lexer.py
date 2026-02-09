# lexer.py
# Lexer simple para C++ usando expresiones regulares
# Devuelto: lista de tokens con tipo, valor y span (start,end)

import re
from dataclasses import dataclass
from typing import List, Tuple

@dataclass
class Token:
    type: str
    value: str
    span: Tuple[int, int]

# Lista de palabras clave (pueden ampliarse)
KEYWORDS = [
    "if", "else", "while", "for", "class", "int", "float", "double",
    "return", "break", "continue", "char", "bool", "void", "public",
    "private", "protected", "virtual", "static", "const", "new", "delete"
]

# Construir el patrón combinado con grupos con nombre. El orden importa.
TOKEN_REGEX = (
    r'(?P<BLOCK_COMMENT>/\*[\s\S]*?\*/)|'
    r'(?P<LINE_COMMENT>//.*)|'
    r'(?P<STRING>"([^"\\]|\\.)*")|'
    r'(?P<FLOAT>\b\d+\.\d+\b)|'
    r'(?P<INT>\b\d+\b)|'
    r'(?P<KEYWORD>\b(?:' + '|'.join(re.escape(k) for k in KEYWORDS) + r')\b)|'
    r'(?P<IDENTIFIER>\b[a-zA-Z_][a-zA-Z0-9_]*\b)|'
    r'(?P<LOGICAL>&&|\|\||!)|'
    r'(?P<SCOPE>::)|'
    r'(?P<SHIFT_OP><<|>>)|'
    r'(?P<RELATIONAL><=|>=|==|!=|<|>)|'
    r'(?P<ARITH>\+|\-|\*|/)|'
    r'(?P<SYMBOL>[\(\)\[\]\{\},;\.])|'
    r'(?P<WHITESPACE>\s+)|'
    r'(?P<OTHER>.)'
)

_COMPILED = re.compile(TOKEN_REGEX)


def tokenize(text: str) -> List[Token]:
    """Tokeniza el texto y devuelve lista de Token(type, value, (start,end)).
    Los tokens incluyen comentarios, cadenas, números, palabras clave, identificadores,
    operadores y símbolos.
    """
    tokens: List[Token] = []
    for m in _COMPILED.finditer(text):
        t = m.lastgroup
        v = m.group(t)
        start = m.start()
        end = m.end()
        if t == 'WHITESPACE':
            continue
        if t == 'OTHER':
            # Ignorar, o clasificar como OTHER
            tokens.append(Token('OTHER', v, (start, end)))
        else:
            # Normalizar los tipos para usarlos en el resaltador
            typ = t
            if typ == 'KEYWORD':
                typ = 'KEYWORD'
            elif typ in ('INT', 'FLOAT'):
                typ = 'NUMBER'
            elif typ == 'ARITH':
                typ = 'OPERATOR'
            elif typ == 'RELATIONAL':
                typ = 'OPERATOR'
            elif typ == 'LOGICAL':
                typ = 'OPERATOR'
            elif typ in ('SHIFT_OP', 'SCOPE'):
                typ = 'OPERATOR'
            elif typ in ('LINE_COMMENT', 'BLOCK_COMMENT'):
                typ = 'COMMENT'
            elif typ == 'STRING':
                typ = 'STRING'
            elif typ == 'IDENTIFIER':
                typ = 'IDENTIFIER'
            elif typ == 'SYMBOL':
                typ = 'SYMBOL'
            else:
                typ = typ
            tokens.append(Token(typ, v, (start, end)))
    return tokens
