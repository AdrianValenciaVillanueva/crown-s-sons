import re, sys
from dataclasses import dataclass
from typing import List, Tuple

#Clase para representar un token con su tipo, valor y posición en el texto
@dataclass
class Token:
    type: str
    value: str
    span: Tuple[int, int]

#Lista de Keywords de C++ para reconocer en el lexer
KEYWORDS = [
    "if", "else", "while", "for", "class", "int", "float", "double",
    "return", "break", "continue", "char", "bool", "void", "public",
    "private", "protected", "virtual", "static", "const", "new", "delete",
    "using", "namespace", "std", "cout", "endl", "cin" 
]

# Diccionario para mapear los grupos del Regex a los nombres de Tokens finales
TOKEN_TYPE_MAP = {
    'BLOCK_COMMENT': 'COMMENT',
    'LINE_COMMENT':  'COMMENT',
    'INT':           'NUMBER',
    'FLOAT':         'NUMBER',
    'STRING':        'STRING',
    'KEYWORD':       'KEYWORD',
    'IDENTIFIER':    'IDENTIFIER',
    'LOGICAL':       'OPERATOR',
    'SHIFT_OP':      'OPERATOR',
    'RELATIONAL':    'OPERATOR',
    'ASSIGN':        'OPERATOR',  
    'ARITH':         'OPERATOR',
    'SCOPE':         'OPERATOR',
    'SYMBOL':        'SYMBOL',
    'OTHER':         'OTHER'
}

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
    r'(?P<ASSIGN>=)|'                     
    r'(?P<ARITH>\+|\-|\*|/|%)|'          
    r'(?P<SYMBOL>[\(\)\[\]\{\},;\.#])|'  
    r'(?P<WHITESPACE>\s+)|'
    r'(?P<OTHER>.)'
)

_COMPILED = re.compile(TOKEN_REGEX)

def tokenize(text: str) -> List[Token]:
    tokens: List[Token] = []
    
    for m in _COMPILED.finditer(text):
        kind = m.lastgroup
        value = m.group(kind)
        start, end = m.span()
        
        if kind == 'WHITESPACE':
            continue
            
        #Se obtiene el nombre final del token usando el diccionario
        #Si no está en el diccionario, usamos el nombre del grupo original
        final_type = TOKEN_TYPE_MAP.get(kind, kind)
        
        tokens.append(Token(final_type, value, (start, end)))
        
    return tokens
