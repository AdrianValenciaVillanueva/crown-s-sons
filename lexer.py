import re
from dataclasses import dataclass
from typing import List, Tuple

@dataclass
class Token:
    type: str
    value: str
    span: Tuple[int, int]
    line: int       # Nueva: Número de línea
    column: int     # Nueva: Número de columna
    error: str = None # Nueva: Si hay error, aquí va la descripción

KEYWORDS = [
    "if", "else", "while", "for", "class", "int", "float", "double",
    "return", "break", "continue", "char", "bool", "void", "public",
    "private", "protected", "virtual", "static", "const", "new", "delete",
    "using", "namespace", "std", "cout", "endl", "cin" 
]

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
    'WHITESPACE':    'WHITESPACE'
}

# ERRORES LÉXICOS (Agregados para la práctica)
# Nota: El orden importa. Ponemos las reglas de error antes o en lugares estratégicos.
TOKEN_REGEX = (
    r'(?P<BLOCK_COMMENT>/\*[\s\S]*?\*/)|'
    r'(?P<LINE_COMMENT>//.*)|'
    
    # 1. Cadenas mal formadas (no cierran comillas antes de nueva línea o fin de archivo)
    r'(?P<ERR_STRING_OPEN>"[^"]*(\n|$))|' 
    r'(?P<STRING>"([^"\\]|\\.)*")|'
    
    # 2. Literales numéricos incorrectos (ej: 12.34.56)
    r'(?P<ERR_FLOAT_BAD>\d+\.\d+\.\d+)|' 
    r'(?P<FLOAT>\b\d+\.\d+\b)|'
    
    # 3. Identificadores mal formados (empiezan con número, ej: 1var)
    r'(?P<ERR_ID_BAD>\d+[a-zA-Z_]\w*)|' 
    
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
    
    # 4. Caracteres no reconocidos (Cualquier cosa que sobró)
    r'(?P<ERR_UNKNOWN>.)' 
)

_COMPILED = re.compile(TOKEN_REGEX)

def tokenize(text: str) -> List[Token]:
    tokens: List[Token] = []
    
    # Iteramos sobre todas las coincidencias
    for m in _COMPILED.finditer(text):
        kind = m.lastgroup
        value = m.group(kind)
        start, end = m.span()
        
        # Calcular Línea y Columna
        # line: cuenta los saltos de línea hasta el inicio del token (+1 porque empezamos en 1)
        line = text.count('\n', 0, start) + 1
        # col: posición actual menos la posición del último salto de línea
        last_newline = text.rfind('\n', 0, start)
        column = start - last_newline # (Si es -1, se vuelve start + 1)

        if kind == 'WHITESPACE':
            continue
            
        # --- MANEJO DE ERRORES ---
        if kind == 'ERR_STRING_OPEN':
            tokens.append(Token('ERROR', value, (start, end), line, column, "Cadena no cerrada (Falta comilla de cierre)"))
        elif kind == 'ERR_FLOAT_BAD':
            tokens.append(Token('ERROR', value, (start, end), line, column, "Literal numérico mal formado (múltiples puntos)"))
        elif kind == 'ERR_ID_BAD':
            tokens.append(Token('ERROR', value, (start, end), line, column, "Identificador inválido (no puede iniciar con número)"))
        elif kind == 'ERR_UNKNOWN':
             tokens.append(Token('ERROR', value, (start, end), line, column, "Carácter no reconocido"))
        else:
            # Token Válido
            final_type = TOKEN_TYPE_MAP.get(kind, kind)
            tokens.append(Token(final_type, value, (start, end), line, column))
        
    return tokens