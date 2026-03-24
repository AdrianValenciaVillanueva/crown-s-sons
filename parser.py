import lexer
from typing import List

class Parser:
    """Analizador Sintáctico Descendente Recursivo Completo."""
    def __init__(self, tokens):
        self.tokens = [t for t in tokens if t.type not in ('WHITESPACE', 'COMMENT')]
        self.pos = 0
        self.errors = []
        # Agregamos 'void' a los tipos válidos
        self.valid_types = ["int", "float", "double", "char", "bool", "string", "const", "void"]
        self.invalid_types = ["entero", "flotante", "booleano", "cadena"]
        self.error_lines = set()

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
                while self.pos < len(self.tokens) and self.peek().value not in (';', '}', '{'):
                    self.consume()
                if self.pos == start_pos or (self.peek() and self.peek().value in (';', '}')):
                    self.consume()
                    
        return self.errors

    def parse_statement(self):
        t = self.peek()
        if not t: return False

        if t.value == 'class':
            return self.parse_class_declaration()
        elif t.value == 'if':
            return self.parse_if()
        elif t.value == 'while':
            return self.parse_while()
        elif t.value == 'for':
            return self.parse_for()
        elif t.value == 'return':              
            return self.parse_return()
        elif t.value == '{':
            return self.parse_block()
        elif t.value in self.valid_types or t.value in self.invalid_types:
            return self.parse_declaration_or_method()
        elif t.type == 'IDENTIFIER':
            # Si hay un identificador seguido de otro, es una declaración de un objeto (ej. MiClase obj;)
            if self.pos + 1 < len(self.tokens):
                next_t = self.tokens[self.pos + 1]
                if next_t.type == 'IDENTIFIER':
                    return self.parse_declaration_or_method()
            return self.parse_assignment_or_expr()
        else:
            return self.parse_assignment_or_expr()

    # --- CLASES Y MÉTODOS ---
    def parse_return(self):
        t_ret = self.consume() # Consume 'return'
        
        # Si no es un punto y coma inmediato, debe haber una expresión
        if self.peek() and self.peek().value != ';':
            if not self.parse_logical_expr():
                return False
                
        if not self.peek() or self.peek().value != ';':
            self.add_error(f"Error Sintáctico: Se esperaba ';' después de 'return' en la línea {t_ret.line}.", t_ret.line)
            return False
            
        self.consume() # Consume ';'
        return True

    def parse_class_declaration(self):
        t_class = self.consume() # Consume 'class'
        
        t_id = self.peek()
        if not t_id or t_id.type != 'IDENTIFIER':
            self.add_error(f"Error Sintáctico: Se esperaba el nombre de la clase en la línea {t_class.line}.", t_class.line)
            return False
        self.consume()
        
        if not self.peek() or self.peek().value != '{':
            self.add_error(f"Error: Cuerpo de clase inválido en la declaración de 'class' en la línea {t_class.line}, columna {t_class.column}.", t_class.line)
            return False
        self.consume()
        
        # Cuerpo de la clase
        while self.peek() and self.peek().value != '}':
            success = self.parse_statement()
            if not success:
                while self.peek() and self.peek().value not in ('}', ';', '{'):
                    self.consume()
                if self.peek() and self.peek().value in (';', '{'):
                    self.consume()

        if not self.peek() or self.peek().value != '}':
            self.add_error(f"Error: Cuerpo de clase inválido en la declaración de 'class' en la línea {t_class.line}, columna {t_class.column}.", t_class.line)
            return False
        self.consume()
        return True

    def parse_declaration_or_method(self, require_semi=True):
        t_type = self.consume() # Consume el tipo de dato
        
        if t_type.value not in self.valid_types and t_type.type != 'IDENTIFIER':
            self.add_error(f"Error: Tipo de retorno inválido en la declaración de método en la línea {t_type.line}, columna {t_type.column}.", t_type.line)
            return False
            
        next_t = self.peek()
        if not next_t or next_t.type != 'IDENTIFIER':
            self.add_error(f"Error Sintáctico: Se esperaba un identificador en la línea {t_type.line}, columna {t_type.column}.", t_type.line)
            return False
        t_id = self.consume()
        
        # ¿Es método o variable?
        if self.peek() and self.peek().value == '(':
            self.consume() # Método: consume '('
            
            if not self.parse_parameters():
                return False
                
            if not self.peek() or self.peek().value != ')':
                self.add_error(f"Error Sintáctico: Paréntesis desbalanceados en la línea {t_id.line}.", t_id.line)
                return False
            self.consume() # Consume ')'
            
            # Un método exige su bloque de código { }
            if not self.peek() or self.peek().value != '{':
                self.add_error(f"Error Sintáctico: Se esperaba '{{' para el cuerpo del método en la línea {t_id.line}.", t_id.line)
                return False
                
            return self.parse_block()
            
        elif self.peek() and self.peek().value == '{':
            # Caso de error: olvidó los paréntesis en el método (ej. void miMetodo { )
            t_err = self.peek()
            self.add_error(f"Error Sintáctico: Faltan paréntesis '()' en el método en la línea {t_err.line}, columna {t_err.column}.", t_err.line)
            return False
            
        else:
            # Es una declaración de variable normal
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

    def parse_parameters(self):
        t = self.peek()
        if t and t.value == ')':
            return True # Sin parámetros

        while True:
            t_type = self.peek()
            if not t_type or (t_type.value not in self.valid_types and t_type.type != 'IDENTIFIER'):
                err_t = t_type if t_type else self.tokens[-1]
                self.add_error(f"Error: Parámetro inválido en la declaración de método en la línea {err_t.line}, columna {err_t.column}.", err_t.line)
                return False
            self.consume() # Consume tipo
            
            t_id = self.peek()
            if not t_id or t_id.type != 'IDENTIFIER':
                err_t = t_id if t_id else self.tokens[-1]
                self.add_error(f"Error: Parámetro inválido en la declaración de método en la línea {err_t.line}, columna {err_t.column}.", err_t.line)
                return False
            self.consume() # Consume ID
            
            t_comma = self.peek()
            if t_comma and t_comma.value == ',':
                self.consume()
            elif t_comma and t_comma.value != ')':
                # Si no hay coma, ni paréntesis de cierre, hay error de sintaxis (ej. int a float b)
                self.add_error(f"Error: Parámetro inválido en la declaración de método en la línea {t_comma.line}, columna {t_comma.column}.", t_comma.line)
                return False
            else:
                break
        return True

    # --- ESTRUCTURAS DE CONTROL (Se mantienen iguales, recortadas para ahorrar espacio en la lectura, pégalas de tu código original) ---
    def parse_if(self):
        t_if = self.consume()
        if not self.peek() or self.peek().value != '(':
            self.add_error(f"Error: Condición inválida en la estructura 'if' en la línea {t_if.line}, columna {t_if.column}.", t_if.line)
            return False
        self.consume()
        if not self.parse_logical_expr():
            self.add_error(f"Error: Condición inválida en la estructura 'if' en la línea {t_if.line}, columna {t_if.column}.", t_if.line)
            return False
        if not self.peek() or self.peek().value != ')':
            self.add_error(f"Error: Paréntesis desbalanceados en la estructura 'if' en la línea {t_if.line}, columna {t_if.column}.", t_if.line)
            return False
        self.consume()
        if not self.parse_block():
            self.add_error(f"Error: Bloque de sentencias faltante en la estructura 'if' en la línea {t_if.line}, columna {t_if.column}.", t_if.line)
            return False
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
        t = self.peek()
        if t and (t.value in self.valid_types or t.value in self.invalid_types):
            if not self.parse_declaration_or_method(require_semi=False):
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
        if not self.parse_logical_expr():
            self.add_error(f"Error: Componente inválido en la estructura 'for' en la línea {t_for.line}, columna {t_for.column}.", t_for.line)
            return False
        if not self.peek() or self.peek().value != ';':
            self.add_error(f"Error: Componente inválido en la estructura 'for' en la línea {t_for.line}, columna {t_for.column}.", t_for.line)
            return False
        self.consume()
        if not self.parse_assignment_or_expr(require_semi=False):
            self.add_error(f"Error: Componente inválido en la estructura 'for' en la línea {t_for.line}, columna {t_for.column}.", t_for.line)
            return False
        if not self.peek() or self.peek().value != ')':
            self.add_error(f"Error: Paréntesis faltantes en la estructura 'for' en la línea {t_for.line}, columna {t_for.column}.", t_for.line)
            return False
        self.consume()
        if not self.parse_block():
            self.add_error(f"Error: Bloque de sentencias faltante en la estructura 'for' en la línea {t_for.line}, columna {t_for.column}.", t_for.line)
            return False
        return True

    def parse_block(self):
        if not self.peek() or self.peek().value != '{':
            return False
        self.consume()
        while self.peek() and self.peek().value != '}':
            success = self.parse_statement()
            if not success:
                while self.peek() and self.peek().value not in (';', '}', '{'):
                    self.consume()
                if self.peek() and self.peek().value == ';':
                    self.consume()
        if not self.peek() or self.peek().value != '}':
            return False
        self.consume()
        return True

    def parse_assignment_or_expr(self, require_semi=True):
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
        
        if t.type == 'IDENTIFIER':
            self.consume()
            # Verificar si es una llamada a función ej. miMetodo(x, y)
            if self.peek() and self.peek().value == '(':
                self.consume() # Consume '('
                while self.peek() and self.peek().value != ')':
                    self.parse_logical_expr()
                    if self.peek() and self.peek().value == ',':
                        self.consume()
                if self.peek() and self.peek().value == ')':
                    self.consume()
                else:
                    self.add_error(f"Error Sintáctico: Falta ')' en la llamada al método en la línea {t.line}.", t.line)
            return True
        elif t.type in ('NUMBER', 'STRING', 'CHAR_LITERAL'): 
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
                self.add_error(f"Error: Paréntesis desbalanceados en la línea {open_paren.line}.", open_paren.line)
                return False
        return False

# --- FUNCIÓN DE ENTRADA ---
def parse(tokens: List[lexer.Token]) -> List[str]:
    parser = Parser(tokens)
    return parser.parse()