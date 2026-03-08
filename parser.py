import lexer
from typing import List

class Parser:
    """Analizador Sintáctico Descendente Recursivo Completo."""
    def __init__(self, tokens):
        # Ignoramos espacios y comentarios globalmente
        self.tokens = [t for t in tokens if t.type not in ('WHITESPACE', 'COMMENT')]
        self.pos = 0
        self.errors = []
        self.valid_types = ["int", "float", "double", "char", "bool", "string", "const"]
        self.invalid_types = ["entero", "flotante", "booleano", "cadena"]
        self.error_lines = set() # Filtro anti-cascada por línea

    def add_error(self, msg, line):
        if line not in self.error_lines:
            self.errors.append(msg)
            self.error_lines.add(line)

    def peek(self):
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def consume(self):
        t = self.peek()
        if t: self.pos += 1
        return t

    def parse(self):
        while self.pos < len(self.tokens):
            start_pos = self.pos
            success = self.parse_statement()
            
            if not success:
                # Sincronización (Recovery): Avanzamos hasta el próximo ';' o '}' para no trabarnos en un bucle infinito
                while self.pos < len(self.tokens) and self.peek().value not in (';', '}', '{'):
                    self.consume()
                if self.pos == start_pos or (self.peek() and self.peek().value in (';', '}')):
                    self.consume()
                    
        return self.errors

    def parse_statement(self):
        t = self.peek()
        if not t: return False

        if t.value == 'if':
            return self.parse_if()
        elif t.value == 'while':
            return self.parse_while()
        elif t.value == 'for':
            return self.parse_for()
        elif t.value == '{':
            return self.parse_block()
        elif t.value in self.valid_types or t.value in self.invalid_types:
            return self.parse_declaration()
        else:
            return self.parse_assignment_or_expr()

    # --- ESTRUCTURAS DE CONTROL ---
    def parse_if(self):
        t_if = self.consume() # consume 'if'
        
        if not self.peek() or self.peek().value != '(':
            self.add_error(f"Error: Condición inválida en la estructura 'if' en la línea {t_if.line}, columna {t_if.column}.", t_if.line)
            return False
        self.consume()
        
        # Validar condición
        if not self.parse_logical_expr():
            self.add_error(f"Error: Condición inválida en la estructura 'if' en la línea {t_if.line}, columna {t_if.column}.", t_if.line)
            return False
            
        if not self.peek() or self.peek().value != ')':
            self.add_error(f"Error: Paréntesis desbalanceados en la estructura 'if' en la línea {t_if.line}, columna {t_if.column}.", t_if.line)
            return False
        self.consume()
        
        # Validar bloque { }
        if not self.parse_block():
            self.add_error(f"Error: Bloque de sentencias faltante en la estructura 'if' en la línea {t_if.line}, columna {t_if.column}.", t_if.line)
            return False
            
        # Validar Else opcional
        t_else = self.peek()
        if t_else and t_else.value == 'else':
            t_else_tok = self.consume()
            if not self.parse_block():
                self.add_error(f"Error: Bloque de sentencias faltante en la estructura 'else' en la línea {t_else_tok.line}, columna {t_else_tok.column}.", t_else_tok.line)
                return False
        return True

    def parse_while(self):
        t_while = self.consume()
        
        if not self.peek() or self.peek().value != '(':
            self.add_error(f"Error: Paréntesis faltantes en la estructura 'while' en la línea {t_while.line}, columna {t_while.column}.", t_while.line)
            return False
        self.consume()
        
        if not self.parse_logical_expr():
            self.add_error(f"Error: Condición inválida en la estructura 'while' en la línea {t_while.line}, columna {t_while.column}.", t_while.line)
            return False
            
        if not self.peek() or self.peek().value != ')':
            self.add_error(f"Error: Paréntesis faltantes en la estructura 'while' en la línea {t_while.line}, columna {t_while.column}.", t_while.line)
            return False
        self.consume()
        
        if not self.parse_block():
            self.add_error(f"Error: Bloque de sentencias faltante en la estructura 'while' en la línea {t_while.line}, columna {t_while.column}.", t_while.line)
            return False
        return True

    def parse_for(self):
        t_for = self.consume()
        
        if not self.peek() or self.peek().value != '(':
            self.add_error(f"Error: Paréntesis faltantes en la estructura 'for' en la línea {t_for.line}, columna {t_for.column}.", t_for.line)
            return False
        self.consume()
        
        # 1. Inicialización
        t = self.peek()
        if t and (t.value in self.valid_types or t.value in self.invalid_types):
            if not self.parse_declaration(require_semi=False):
                self.add_error(f"Error: Componente inválido en la estructura 'for' en la línea {t_for.line}, columna {t_for.column}.", t_for.line)
                return False
        else:
            if not self.parse_assignment_or_expr(require_semi=False):
                self.add_error(f"Error: Componente inválido en la estructura 'for' en la línea {t_for.line}, columna {t_for.column}.", t_for.line)
                return False
        
        if not self.peek() or self.peek().value != ';':
            self.add_error(f"Error: Componente inválido en la estructura 'for' en la línea {t_for.line}, columna {t_for.column}.", t_for.line)
            return False
        self.consume()
        
        # 2. Condición
        if not self.parse_logical_expr():
            self.add_error(f"Error: Componente inválido en la estructura 'for' en la línea {t_for.line}, columna {t_for.column}.", t_for.line)
            return False
        if not self.peek() or self.peek().value != ';':
            self.add_error(f"Error: Componente inválido en la estructura 'for' en la línea {t_for.line}, columna {t_for.column}.", t_for.line)
            return False
        self.consume()
        
        # 3. Actualización
        if not self.parse_assignment_or_expr(require_semi=False):
            self.add_error(f"Error: Componente inválido en la estructura 'for' en la línea {t_for.line}, columna {t_for.column}.", t_for.line)
            return False
            
        if not self.peek() or self.peek().value != ')':
            self.add_error(f"Error: Paréntesis faltantes en la estructura 'for' en la línea {t_for.line}, columna {t_for.column}.", t_for.line)
            return False
        self.consume()
        
        # 4. Bloque
        if not self.parse_block():
            self.add_error(f"Error: Bloque de sentencias faltante en la estructura 'for' en la línea {t_for.line}, columna {t_for.column}.", t_for.line)
            return False
        return True

    def parse_block(self):
        """Analiza todo lo que esté entre llaves { }."""
        if not self.peek() or self.peek().value != '{':
            return False
        self.consume()
        
        while self.peek() and self.peek().value != '}':
            success = self.parse_statement()
            if not success:
                # Sincronización interna del bloque
                while self.peek() and self.peek().value not in (';', '}'):
                    self.consume()
                if self.peek() and self.peek().value == ';':
                    self.consume()
                    
        if not self.peek() or self.peek().value != '}':
            return False
        self.consume()
        return True

    # --- DECLARACIONES Y ASIGNACIONES ---
    def parse_declaration(self, require_semi=True):
        t = self.consume()
        if t.value in self.invalid_types:
            self.add_error(f"Error Sintáctico: Tipo no válido '{t.value}' en línea {t.line}, columna {t.column}.", t.line)
            
        next_t = self.peek()
        if not next_t:
            self.add_error(f"Error Sintáctico: Declaración incompleta en línea {t.line}.", t.line)
            return False
            
        if next_t.type == 'ERROR' and next_t.value[0].isdigit():
            self.add_error(f"Error Sintáctico: Identificador inválido '{next_t.value}' en línea {next_t.line}.", next_t.line)
            self.consume()
        elif next_t.type != 'IDENTIFIER':
            self.add_error(f"Error Sintáctico: Se esperaba un identificador en línea {next_t.line}, columna {next_t.column}.", next_t.line)
            return False
        else:
            self.consume()
            
        if self.peek() and self.peek().value == '=':
            self.consume()
            if not self.parse_logical_expr():
                return False
                
        if require_semi:
            if not self.peek() or self.peek().value != ';':
                t_prev = self.tokens[self.pos - 1]
                self.add_error(f"Error Sintáctico: Se esperaba ';' en la línea {t_prev.line}.", t_prev.line)
                return False
            self.consume()
        return True

    def parse_assignment_or_expr(self, require_semi=True):
        """Detecta cosas como 'x = x + 1;' o simplemente '5 + 5;'"""
        if not self.parse_logical_expr():
            return False
            
        if self.peek() and self.peek().value == '=':
            self.consume()
            if not self.parse_logical_expr():
                return False
                
        if require_semi:
            if not self.peek() or self.peek().value != ';':
                t_prev = self.tokens[self.pos - 1]
                self.add_error(f"Error Sintáctico: Se esperaba ';' en la línea {t_prev.line}.", t_prev.line)
                return False
            self.consume()
        return True

    # --- EXPRESIONES LOGICAS Y MATEMÁTICAS ---
    def parse_logical_expr(self):
        if not self.parse_logical_term(): return False
        while self.peek() and self.peek().value in ('&&', '||'):
            op = self.consume()
            if not self.parse_logical_term():
                self.add_error(f"Error: Operador lógico sin término en la línea {op.line}, columna {op.column}.", op.line)
                return False
        return True

    def parse_logical_term(self):
        if not self.parse_arith_expr(): return False
        rel_ops = ('==', '!=', '>', '<', '>=', '<=')
        t = self.peek()
        if t and t.value in rel_ops:
            op = self.consume()
            if not self.parse_arith_expr():
                self.add_error(f"Error: Comparación inválida en la línea {op.line}, columna {op.column}.", op.line)
                return False
        return True

    def parse_arith_expr(self):
        if not self.parse_term(): return False
        while self.peek() and self.peek().value in ('+', '-'):
            op = self.consume()
            if not self.parse_term():
                self.add_error(f"Error: Operador sin término en la línea {op.line}, columna {op.column}.", op.line)
                return False
        return True

    def parse_term(self):
        if not self.parse_factor(): return False
        while self.peek() and self.peek().value in ('*', '/'):
            op = self.consume()
            if not self.parse_factor():
                self.add_error(f"Error: Operador sin término en la línea {op.line}, columna {op.column}.", op.line)
                return False
        return True

    def parse_factor(self):
        t = self.peek()
        if not t: return False
        if t.type in ('IDENTIFIER', 'NUMBER'):
            self.consume()
            return True
        elif t.value == '(':
            open_paren = self.consume()
            res = self.parse_logical_expr()
            t_close = self.peek()
            if t_close and t_close.value == ')':
                self.consume()
                return res
            else:
                self.add_error(f"Error: Paréntesis desbalanceados en la línea {open_paren.line}, columna {open_paren.column}.", open_paren.line)
                return False
        return False

# --- FUNCIÓN DE ENTRADA ---
def parse(tokens: List[lexer.Token]) -> List[str]:
    parser = Parser(tokens)
    return parser.parse()