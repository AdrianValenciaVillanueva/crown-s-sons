import lexer
from typing import List

class ExprParser:
    """Analizador de expresiones aritméticas y lógicas usando Descenso Recursivo."""
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0
        self.errors = []

    def add_error(self, msg):
        """Solo guardamos el primer error de la línea para evitar la 'cascada'."""
        if not self.errors:
            self.errors.append(msg)

    def peek(self):
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def consume(self):
        t = self.peek()
        if t: self.pos += 1
        return t

    def parse(self):
        if not self.tokens: return self.errors
        
        success = self.parse_logical_expr()
        
        # Si terminó de analizar pero sobraron símbolos (ej. "x + y 5")
        if success and self.pos < len(self.tokens):
            extra_t = self.peek()
            self.add_error(f"Error: Elemento inesperado '{extra_t.value}' en la línea {extra_t.line}, columna {extra_t.column}.")
            
        return self.errors

    def parse_logical_expr(self):
        if not self.parse_logical_term(): return False
        while self.peek() and self.peek().value in ('&&', '||'):
            op = self.consume()
            if not self.parse_logical_term():
                self.add_error(f"Error: Operador lógico sin término en la línea {op.line}, columna {op.column}.")
                return False
        return True

    def parse_logical_term(self):
        if not self.parse_arith_expr(): return False
        rel_ops = ('==', '!=', '>', '<', '>=', '<=')
        t = self.peek()
        if t and t.value in rel_ops:
            op = self.consume()
            if not self.parse_arith_expr():
                self.add_error(f"Error: Comparación inválida en la línea {op.line}, columna {op.column}.")
                return False
        return True

    def parse_arith_expr(self):
        if not self.parse_term(): return False
        while self.peek() and self.peek().value in ('+', '-'):
            op = self.consume()
            if not self.parse_term():
                self.add_error(f"Error: Operador sin término en la línea {op.line}, columna {op.column}.")
                return False
        return True

    def parse_term(self):
        if not self.parse_factor(): return False
        while self.peek() and self.peek().value in ('*', '/'):
            op = self.consume()
            if not self.parse_factor():
                self.add_error(f"Error: Operador sin término en la línea {op.line}, columna {op.column}.")
                return False
        return True

    def parse_factor(self):
        t = self.peek()
        if not t: return False
        
        # El lexer marca variables/números como IDENTIFIER o NUMBER
        if t.type in ('IDENTIFIER', 'NUMBER'):
            self.consume()
            return True
        elif t.value == '(':
            open_paren = self.consume()
            res = self.parse_arith_expr()
            
            t_close = self.peek()
            if t_close and t_close.value == ')':
                self.consume()
                return res
            else:
                self.add_error(f"Error: Paréntesis desbalanceados en la línea {open_paren.line}, columna {open_paren.column}.")
                return False
        return False

def parse_declaration(tokens: List[lexer.Token], valid_types, invalid_types) -> List[str]:
    """Valida la declaración de variables (Práctica anterior)."""
    errors = []
    if not tokens: return errors
    t = tokens[0]
    
    if t.value in invalid_types:
        errors.append(f"Error Sintáctico: Tipo no válido '{t.value}' en línea {t.line}, columna {t.column}. Los tipos válidos son: {', '.join(valid_types)}.")
    
    if len(tokens) < 2:
        errors.append(f"Error Sintáctico: Declaración incompleta en línea {t.line}.")
        return errors
        
    next_t = tokens[1]
    if next_t.type == 'ERROR' and next_t.value[0].isdigit():
        errors.append(f"Error Sintáctico: Identificador inválido '{next_t.value}' en línea {next_t.line}, columna {next_t.column}. Un identificador debe comenzar con letra o guion bajo.")
    elif next_t.type != 'IDENTIFIER' and next_t.type != 'ERROR':
        errors.append(f"Error Sintáctico: Se esperaba un identificador en línea {next_t.line}, columna {next_t.column}. Se encontró '{next_t.value}'.")
        
    # Verificar punto y coma al final
    has_semi = any(tok.value == ';' for tok in tokens)
    if not has_semi:
        last_t = tokens[-1]
        col = last_t.column + len(last_t.value)
        errors.append(f"Error Sintáctico: Se esperaba ';' al final de la declaración en la línea {last_t.line}, columna {col}.")
        
    return errors

def parse(tokens: List[lexer.Token]) -> List[str]:
    """Función principal que recibe los tokens del editor."""
    errors = []
    filtered_tokens = [t for t in tokens if t.type not in ('WHITESPACE', 'COMMENT')]
    
    # Agrupamos los tokens por línea
    lines = {}
    for t in filtered_tokens:
        if t.line not in lines:
            lines[t.line] = []
        lines[t.line].append(t)
        
    valid_types = ["int", "float", "double", "char", "bool", "string", "const"]
    invalid_types = ["entero", "flotante", "booleano", "cadena"]
    
    for line_num, line_tokens in lines.items():
        first_t = line_tokens[0]
        # Validar declaraciones
        if first_t.value in valid_types or first_t.value in invalid_types:
            errors.extend(parse_declaration(line_tokens, valid_types, invalid_types))
        else:
            # Validar Expresiones Matemáticas/Lógicas
            expr_parser = ExprParser(line_tokens)
            expr_errors = expr_parser.parse()
            errors.extend(expr_errors)
            
    return errors