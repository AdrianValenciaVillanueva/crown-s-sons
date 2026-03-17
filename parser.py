import lexer
from typing import List

class SymbolTable:
    """Estructura de datos para la Tabla de Símbolos con manejo de Ámbitos (Scope)."""
    def __init__(self):
        # Usamos una lista de diccionarios. El índice 0 es el ámbito GLOBAL.
        self.scopes = [{}]

    def enter_scope(self):
        """Crea un nuevo ámbito local."""
        self.scopes.append({})

    def exit_scope(self):
        """Destruye el ámbito local actual al salir de un bloque."""
        if len(self.scopes) > 1:
            self.scopes.pop()

    def insert(self, name, datatype):
        """Inserta un símbolo en el ámbito actual. Retorna False si ya existe."""
        current_scope = self.scopes[-1]
        if name in current_scope:
            return False
        
        current_scope[name] = {
            'type': datatype,
            'scope': 'global' if len(self.scopes) == 1 else 'local'
        }
        return True

    def lookup(self, name):
        """Busca un símbolo desde el ámbito local actual hasta el global (Top-Down)."""
        for scope in reversed(self.scopes):
            if name in scope:
                return scope[name]
        return None


class Parser:
    """Analizador Sintáctico y Semántico Descendente Recursivo."""
    def __init__(self, tokens):
        self.tokens = [t for t in tokens if t.type not in ('WHITESPACE', 'COMMENT')]
        self.pos = 0
        
        self.errors = []
        self.semantic_errors = []
        self.error_lines = set()
        self.semantic_error_lines = set()
        
        self.sym_tab = SymbolTable()
        
        self.valid_types = ["int", "float", "double", "char", "bool", "string", "const", "void"]
        self.invalid_types = ["entero", "flotante", "booleano", "cadena"]

    def add_error(self, msg, line):
        if line not in self.error_lines:
            self.errors.append(msg)
            self.error_lines.add(line)

    def add_semantic_error(self, msg, line):
        if line not in self.semantic_error_lines:
            self.semantic_errors.append(msg)
            self.semantic_error_lines.add(line)

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
                    
        return self.errors, self.semantic_errors

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
        elif t.value == '{':
            return self.parse_block()
        elif t.value in self.valid_types or t.value in self.invalid_types:
            return self.parse_declaration_or_method()
        elif t.type == 'IDENTIFIER':
            if self.pos + 1 < len(self.tokens):
                next_t = self.tokens[self.pos + 1]
                if next_t.type == 'IDENTIFIER':
                    return self.parse_declaration_or_method()
            return self.parse_assignment_or_expr()
        else:
            return self.parse_assignment_or_expr()

    def parse_class_declaration(self):
        t_class = self.consume()
        t_id = self.peek()
        if not t_id or t_id.type != 'IDENTIFIER':
            self.add_error(f"Error Sintáctico: Se esperaba el nombre de la clase en la línea {t_class.line}.", t_class.line)
            return False
        self.consume()
        
        if not self.peek() or self.peek().value != '{':
            self.add_error(f"Error: Cuerpo de clase inválido en la declaración de 'class' en la línea {t_class.line}, columna {t_class.column}.", t_class.line)
            return False
        self.consume()
        
        self.sym_tab.enter_scope() 
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
        self.sym_tab.exit_scope()
        return True

    def parse_declaration_or_method(self, require_semi=True):
        t_type = self.consume()
        if t_type.value not in self.valid_types and t_type.type != 'IDENTIFIER':
            self.add_error(f"Error: Tipo de retorno inválido en la línea {t_type.line}, columna {t_type.column}.", t_type.line)
            return False
            
        next_t = self.peek()
        if not next_t or next_t.type != 'IDENTIFIER':
            self.add_error(f"Error Sintáctico: Se esperaba un identificador en la línea {t_type.line}, columna {t_type.column}.", t_type.line)
            return False
        t_id = self.consume()
        
        if self.peek() and self.peek().value == '(':
            if not self.sym_tab.insert(t_id.value, t_type.value):
                self.add_semantic_error(f"Error Semántico: Método '{t_id.value}' ya declarado en la línea {t_id.line}.", t_id.line)
            
            self.consume() 
            self.sym_tab.enter_scope() 
            
            if not self.parse_parameters(): return False
                
            if not self.peek() or self.peek().value != ')':
                self.add_error(f"Error Sintáctico: Paréntesis desbalanceados en la línea {t_id.line}.", t_id.line)
                return False
            self.consume() 
            
            if not self.peek() or self.peek().value != '{':
                self.add_error(f"Error Sintáctico: Se esperaba '{{' en la línea {t_id.line}.", t_id.line)
                return False
                
            res = self.parse_block(new_scope=False) 
            self.sym_tab.exit_scope()
            return res
            
        elif self.peek() and self.peek().value == '{':
            t_err = self.peek()
            self.add_error(f"Error Sintáctico: Faltan paréntesis '()' en el método en la línea {t_err.line}, columna {t_err.column}.", t_err.line)
            return False
            
        else:
            if not self.sym_tab.insert(t_id.value, t_type.value):
                self.add_semantic_error(f"Error Semántico: Identificador '{t_id.value}' ya declarado en la línea {t_id.line}, columna {t_id.column}.", t_id.line)
            
            if self.peek() and self.peek().value == '=':
                op = self.consume()
                success, rhs_type = self.parse_logical_expr()
                if not success: return False
                
                if t_type.value == 'int' and rhs_type == 'float':
                    self.add_semantic_error(f"Error Semántico: Tipo de dato incompatible en la asignación a '{t_id.value}' en la línea {op.line}, columna {op.column}. (No se puede asignar float a int)", op.line)
                elif t_type.value != rhs_type and rhs_type != 'unknown':
                    self.add_semantic_error(f"Error Semántico: Tipo de dato incompatible en la asignación a '{t_id.value}' en la línea {op.line}, columna {op.column}. Esperado '{t_type.value}', recibido '{rhs_type}'.", op.line)
                    
            if require_semi:
                if not self.peek() or self.peek().value != ';':
                    t_prev = self.tokens[self.pos - 1]
                    self.add_error(f"Error Sintáctico: Se esperaba ';' en la línea {t_prev.line}.", t_prev.line)
                    return False
                self.consume()
            return True

    def parse_parameters(self):
        t = self.peek()
        if t and t.value == ')': return True

        while True:
            t_type = self.peek()
            if not t_type or (t_type.value not in self.valid_types and t_type.type != 'IDENTIFIER'):
                err_t = t_type if t_type else self.tokens[-1]
                self.add_error(f"Error: Parámetro inválido en la línea {err_t.line}.", err_t.line)
                return False
            self.consume() 
            
            t_id = self.peek()
            if not t_id or t_id.type != 'IDENTIFIER':
                err_t = t_id if t_id else self.tokens[-1]
                self.add_error(f"Error: Parámetro inválido en la línea {err_t.line}.", err_t.line)
                return False
            self.consume() 
            
            if not self.sym_tab.insert(t_id.value, t_type.value):
                self.add_semantic_error(f"Error Semántico: Parámetro '{t_id.value}' ya declarado en la línea {t_id.line}.", t_id.line)
            
            t_comma = self.peek()
            if t_comma and t_comma.value == ',':
                self.consume()
            elif t_comma and t_comma.value != ')':
                self.add_error(f"Error: Parámetro inválido en la línea {t_comma.line}.", t_comma.line)
                return False
            else:
                break
        return True

    def parse_if(self):
        t_if = self.consume()
        if not self.peek() or self.peek().value != '(':
            self.add_error(f"Error: Condición inválida en la línea {t_if.line}.", t_if.line)
            return False
        self.consume()
        
        success, _ = self.parse_logical_expr()
        if not success: return False
            
        if not self.peek() or self.peek().value != ')':
            self.add_error(f"Error: Paréntesis desbalanceados en la línea {t_if.line}.", t_if.line)
            return False
        self.consume()
        if not self.parse_block(): return False
        
        t_else = self.peek()
        if t_else and t_else.value == 'else':
            t_else_tok = self.consume()
            if not self.parse_block(): return False
        return True

    def parse_while(self):
        t_while = self.consume()
        if not self.peek() or self.peek().value != '(':
            self.add_error(f"Error: Paréntesis faltantes en la línea {t_while.line}.", t_while.line)
            return False
        self.consume()
        
        success, _ = self.parse_logical_expr()
        if not success: return False
            
        if not self.peek() or self.peek().value != ')':
            self.add_error(f"Error: Paréntesis faltantes en la línea {t_while.line}.", t_while.line)
            return False
        self.consume()
        if not self.parse_block(): return False
        return True

    def parse_for(self):
        t_for = self.consume()
        if not self.peek() or self.peek().value != '(': return False
        self.consume()
        
        self.sym_tab.enter_scope()
        
        t = self.peek()
        if t and (t.value in self.valid_types or t.value in self.invalid_types):
            if not self.parse_declaration_or_method(require_semi=False): return False
        else:
            if not self.parse_assignment_or_expr(require_semi=False): return False
            
        if not self.peek() or self.peek().value != ';': return False
        self.consume()
        
        success, _ = self.parse_logical_expr()
        if not success: return False
            
        if not self.peek() or self.peek().value != ';': return False
        self.consume()
        
        if not self.parse_assignment_or_expr(require_semi=False): return False
            
        if not self.peek() or self.peek().value != ')': return False
        self.consume()
        
        if not self.parse_block(new_scope=False): return False 
        
        self.sym_tab.exit_scope()
        return True

    def parse_block(self, new_scope=True):
        if not self.peek() or self.peek().value != '{':
            return False
        self.consume()
        
        if new_scope: self.sym_tab.enter_scope()
            
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
        
        if new_scope: self.sym_tab.exit_scope()
        return True

    def parse_assignment_or_expr(self, require_semi=True):
        success, lhs_type = self.parse_logical_expr()
        if not success: return False
        
        if self.peek() and self.peek().value == '=':
            op = self.consume()
            
            id_name = "variable"
            prev_t = self.tokens[self.pos - 2]
            if prev_t.type == 'IDENTIFIER': id_name = f"'{prev_t.value}'"
            
            success2, rhs_type = self.parse_logical_expr()
            if not success2: return False
            
            if lhs_type != rhs_type and lhs_type != 'unknown' and rhs_type != 'unknown':
                
                # --- PARCHE DE COMPATIBILIDAD FLOAT / DOUBLE ---
                if lhs_type in ('float', 'double') and rhs_type in ('float', 'double'):
                    pass
                elif lhs_type == 'int' and rhs_type == 'float':
                    self.add_semantic_error(f"Error Semántico: Tipo de dato incompatible en la asignación a {id_name} en la línea {op.line}. (No se puede asignar float a int)", op.line)
                else:
                    self.add_semantic_error(f"Error Semántico: Tipo de dato incompatible en la asignación a {id_name} en la línea {op.line}. Esperado '{lhs_type}', recibido '{rhs_type}'.", op.line)

        if require_semi:
            if not self.peek() or self.peek().value != ';':
                t_prev = self.tokens[self.pos - 1]
                self.add_error(f"Error Sintáctico: Se esperaba ';' en la línea {t_prev.line}.", t_prev.line)
                return False
            self.consume()
        return True

    def parse_logical_expr(self):
        success, t_type = self.parse_logical_term()
        if not success: return False, 'unknown'
        while self.peek() and self.peek().value in ('&&', '||'):
            op = self.consume()
            success2, _ = self.parse_logical_term()
            if not success2:
                self.add_error(f"Error: Operador lógico sin término en la línea {op.line}, columna {op.column}.", op.line)
                return False, 'unknown'
            t_type = 'bool'
        return True, t_type

    def parse_logical_term(self):
        success, t_type = self.parse_arith_expr()
        if not success: return False, 'unknown'
        rel_ops = ('==', '!=', '>', '<', '>=', '<=')
        t = self.peek()
        if t and t.value in rel_ops:
            op = self.consume()
            success2, _ = self.parse_arith_expr()
            if not success2:
                self.add_error(f"Error: Comparación inválida en la línea {op.line}.", op.line)
                return False, 'unknown'
            t_type = 'bool'
        return True, t_type

    def parse_arith_expr(self):
        success, t_type = self.parse_term()
        if not success: return False, 'unknown'
        while self.peek() and self.peek().value in ('+', '-'):
            op = self.consume()
            success2, t_type2 = self.parse_term()
            if not success2:
                self.add_error(f"Error: Operador sin término en la línea {op.line}.", op.line)
                return False, 'unknown'
            if t_type == 'float' or t_type2 == 'float': t_type = 'float'
        return True, t_type

    def parse_term(self):
        success, t_type = self.parse_factor()
        if not success: return False, 'unknown'
        while self.peek() and self.peek().value in ('*', '/'):
            op = self.consume()
            success2, t_type2 = self.parse_factor()
            if not success2:
                self.add_error(f"Error: Operador sin término en la línea {op.line}.", op.line)
                return False, 'unknown'
            if t_type == 'float' or t_type2 == 'float': t_type = 'float'
        return True, t_type

    def parse_factor(self):
        t = self.peek()
        if not t: return False, 'unknown'
        
        if t.type == 'IDENTIFIER':
            # --- PARCHE: BOOLEANOS TRUE / FALSE ---
            if t.value in ('true', 'false'):
                self.consume()
                return True, 'bool'
                
            sym = self.sym_tab.lookup(t.value)
            if not sym:
                self.add_semantic_error(f"Error Semántico: Identificador '{t.value}' no declarado en la línea {t.line}, columna {t.column}.", t.line)
                self.consume()
                return True, 'unknown'
            self.consume()
            return True, sym['type']
            
        elif t.type == 'NUMBER':
            val = self.consume().value
            return True, 'float' if '.' in val else 'int'
            
        elif t.type == 'STRING':
            self.consume()
            return True, 'string'
            
        # --- PARCHE: LECTURA DE CHAR ---
        elif t.type == 'CHAR_LITERAL':
            self.consume()
            return True, 'char'
            
        elif t.value == '(':
            open_paren = self.consume()
            success, t_type = self.parse_logical_expr()
            t_close = self.peek()
            if t_close and t_close.value == ')':
                self.consume()
                return success, t_type
            else:
                self.add_error(f"Error Sintáctico: Paréntesis desbalanceados en la línea {open_paren.line}.", open_paren.line)
                return False, 'unknown'
        return False, 'unknown'

def parse(tokens: List[lexer.Token]):
    parser = Parser(tokens)
    return parser.parse()