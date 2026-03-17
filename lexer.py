import re
from dataclasses import dataclass
from typing import List, Tuple

@dataclass
class Token:
    type: str
    value: str
    span: Tuple[int, int]
    line: int       # Número de línea
    column: int     # Número de columna
    error: str = None # Si hay error, aquí va la descripción

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
    'CHAR_LITERAL':  'CHAR_LITERAL',
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

# Se agregaron errores lexicos al regex
TOKEN_REGEX = (
    r'(?P<BLOCK_COMMENT>/\*[\s\S]*?\*/)|'
    r'(?P<LINE_COMMENT>//.*)|'
    
    # 1. Cadenas mal formadas (no cierran comillas antes de nueva línea o fin de archivo)
    r'(?P<ERR_STRING_OPEN>"[^"]*(\n|$))|' 
    r'(?P<STRING>"([^"\\]|\\.)*")|'

    # --- Atrapamos TODO lo que esté entre comillas simples ---
    r"(?P<CHAR_LITERAL>'[^']*')|"
    
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
        line = text.count('\n', 0, start) + 1
        last_newline = text.rfind('\n', 0, start)
        column = start - last_newline

        if kind == 'WHITESPACE':
            continue
            
        # --- MANEJO DE ERRORES LÉXICOS ---
        if kind == 'ERR_STRING_OPEN':
            tokens.append(Token('ERROR', value, (start, end), line, column, "Cadena no cerrada (Falta comilla de cierre)"))
        elif kind == 'ERR_FLOAT_BAD':
            tokens.append(Token('ERROR', value, (start, end), line, column, "Literal numérico mal formado (múltiples puntos)"))
        elif kind == 'ERR_ID_BAD':
            tokens.append(Token('ERROR', value, (start, end), line, column, "Identificador inválido (no puede iniciar con número)"))
        elif kind == 'ERR_UNKNOWN':
             tokens.append(Token('ERROR', value, (start, end), line, column, "Carácter no reconocido"))
        else:
            # --- VALIDACIÓN MANUAL DE CHAR ---
            if kind == 'CHAR_LITERAL':
                # Validamos la longitud: un char normal son 3 caracteres (ej: 'z')
                # Un salto de línea o escape son 4 caracteres (ej: '\n')
                if len(value) > 4 or len(value) < 3:
                    tokens.append(Token('ERROR', value, (start, end), line, column, "Literal de carácter mal formado (debe ser exactamente un carácter)"))
                    continue  # Brincamos la creación del token válido
            
            # Token Válido
            final_type = TOKEN_TYPE_MAP.get(kind, kind)
            tokens.append(Token(final_type, value, (start, end), line, column))
        
    return tokens