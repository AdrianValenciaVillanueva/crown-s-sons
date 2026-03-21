class SymbolTable:
    def __init__(self):
        # Lista de diccionarios. Cada diccionario es un ámbito (scope).
        # El índice 0 siempre es el ámbito GLOBAL.
        self.scopes = [{}]
        # Guardaremos todos los símbolos descubiertos para poder mostrarlos al final
        self.all_symbols = {} 

    def push_scope(self):
        """Entra a un nuevo ámbito (ej. al leer '{')"""
        self.scopes.append({})

    def pop_scope(self):
        """Sale del ámbito actual (ej. al leer '}')"""
        if len(self.scopes) > 1:
            self.scopes.pop()

    def insert(self, name, symbol_type):
        """Inserta un símbolo en el ámbito actual."""
        current_scope = self.scopes[-1]
        if name in current_scope:
            return False # Error: Ya fue declarado en este mismo ámbito
        
        alcance = 'global' if len(self.scopes) == 1 else 'local'
        simbolo_info = {'tipo': symbol_type, 'alcance': alcance}
        
        current_scope[name] = simbolo_info
        self.all_symbols[name] = simbolo_info # Guardar copia para la consola
        return True

    def lookup(self, name):
        """Busca un símbolo desde el ámbito más interno (local) hacia el externo (global)."""
        for scope in reversed(self.scopes):
            if name in scope:
                return scope[name]
        return None


class SemanticAnalyzer:
    def __init__(self, tokens):
        # Filtramos espacios y comentarios para facilitar el análisis
        self.tokens = [t for t in tokens if t.type not in ('WHITESPACE', 'COMMENT')]
        self.pos = 0
        self.errors = []
        self.sym_table = SymbolTable()
        self.valid_types = ["int", "float", "double", "char", "bool", "string"]

    def peek(self, offset=0):
        if self.pos + offset < len(self.tokens):
            return self.tokens[self.pos + offset]
        return None

    def analyze(self):
        while self.pos < len(self.tokens):
            t = self.tokens[self.pos]

            # 1. GESTIÓN DE ÁMBITO (Scope)
            if t.value == '{':
                self.sym_table.push_scope()
                self.pos += 1
                continue
            if t.value == '}':
                self.sym_table.pop_scope()
                self.pos += 1
                continue

            # 2. DECLARACIÓN DE VARIABLES (Ej: int x;)
            if t.value in self.valid_types:
                next_t = self.peek(1)
                if next_t and next_t.type == 'IDENTIFIER':
                    var_type = t.value
                    var_name = next_t.value
                    
                    # Insertar en tabla de símbolos
                    if not self.sym_table.insert(var_name, var_type):
                        self.errors.append(f"Error Semántico: El identificador '{var_name}' ya fue declarado. (Línea {next_t.line}, Col {next_t.column})")

                    # Checar si además hay asignación directa (Ej: int x = 5;)
                    if self.peek(2) and self.peek(2).value == '=':
                        self.pos += 2 # Saltar a la variable
                        self.check_assignment(var_name, var_type, next_t.line, next_t.column)
                        continue
            
            # 3. USO Y ASIGNACIÓN DE VARIABLES (Ej: x = y;)
            if t.type == 'IDENTIFIER':
                var_name = t.value
                symbol = self.sym_table.lookup(var_name)
                
                # Validar que exista en la tabla de símbolos
                if not symbol:
                    # Ignorar si es nombre de clase o función seguida de ')' o '{'
                    next_t = self.peek(1)
                    if not (next_t and next_t.value in ('(', '{')):
                        self.errors.append(f"Error Semántico: Identificador '{var_name}' no declarado. (Línea {t.line}, Col {t.column})")
                else:
                    var_type = symbol['tipo']
                    next_t = self.peek(1)
                    if next_t and next_t.value == '=':
                        self.pos += 1 # Saltar a la variable
                        self.check_assignment(var_name, var_type, t.line, t.column)
                        continue

            self.pos += 1

        return self.errors, self.sym_table

    def check_assignment(self, var_name, var_type, line, col):
        """Evalúa el lado derecho de una asignación para verificar el tipo de dato."""
        self.pos += 1 # Consumir el '='
        expr_tokens = []
        
        # Leer todo hasta el punto y coma o coma
        while self.pos < len(self.tokens) and self.tokens[self.pos].value not in (';', ','):
            expr_tokens.append(self.tokens[self.pos])
            self.pos += 1
            
        if not expr_tokens: 
            return

        # Mandamos a inferir el tipo y validar la expresión matemática/lógica
        expr_type = self.infer_expression_type(expr_tokens, line, col)

        if expr_type and not self.types_are_compatible(var_type, expr_type):
            self.errors.append(f"Error Semántico: Tipo de dato incompatible. Se intentó asignar '{expr_type}' a '{var_name}' de tipo '{var_type}'. (Línea {line}, Col {col})")

    def infer_expression_type(self, tokens, line, col):
        """Infiere el tipo de una expresión y valida que las operaciones sean legales."""
        types_in_expr = set()
        
        # Categorías de operadores
        math_ops = {'+', '-', '*', '/', '%'}
        rel_ops = {'==', '!=', '<', '>', '<=', '>='}
        log_ops = {'&&', '||'}
        
        found_math = False
        found_rel = False
        found_log = False
        
        for i, t in enumerate(tokens):
            if t.value in math_ops: found_math = True
            if t.value in rel_ops: found_rel = True
            if t.value in log_ops: found_log = True
            
            # 🚨 1. Validación: División por cero
            if t.value == '/' and i + 1 < len(tokens):
                if tokens[i+1].value == '0':
                    self.errors.append(f"Error Semántico: División por cero no permitida. (Línea {t.line}, Col {t.column})")

            # Analizar el tipo de cada token en la expresión
            t_type = None
            if t.type == 'STRING': t_type = 'string'
            elif t.type == 'CHAR_LITERAL': t_type = 'char'
            elif t.value in ('true', 'false'): t_type = 'bool'
            elif t.type == 'NUMBER':
                t_type = 'float' if '.' in t.value else 'int'
            elif t.type == 'IDENTIFIER':
                sym = self.sym_table.lookup(t.value)
                if sym:
                    t_type = sym['tipo']
                    
            if t_type:
                types_in_expr.add(t_type)

        # Banderas para saber qué tipos de datos hay mezclados en la expresión
        has_string = 'string' in types_in_expr
        has_numeric = 'int' in types_in_expr or 'float' in types_in_expr or 'double' in types_in_expr
        has_bool = 'bool' in types_in_expr

        #2. Validación de Expresiones Matemáticas
        if found_math:
            if has_string:
                self.errors.append(f"Error Semántico: No se puede aplicar operadores matemáticos (+, -, *, /) con cadenas de texto. (Línea {line}, Col {col})")
            if has_bool:
                self.errors.append(f"Error Semántico: No se pueden realizar operaciones matemáticas con booleanos. (Línea {line}, Col {col})")

        #3. Validación de Expresiones Lógicas
        if found_log:
            # Si hay números o strings puros (y no hay comparadores como < o ==), es error.
            if (has_numeric or has_string) and not found_rel:
                self.errors.append(f"Error Semántico: Los operadores lógicos (&&, ||) requieren operandos booleanos. (Línea {line}, Col {col})")

        # 4. Validación de Comparaciones
        if found_rel:
            if has_string and has_numeric:
                self.errors.append(f"Error Semántico: No se puede comparar un texto con un número. Tipos incompatibles. (Línea {line}, Col {col})")

        # Determinar y devolver el tipo dominante de toda la expresión
        if found_rel or found_log:
            return 'bool' # Todas las comparaciones devuelven un bool (ej. 5 > 3 es un bool)
        elif has_string:
            return 'string'
        elif 'float' in types_in_expr or 'double' in types_in_expr:
            return 'float'
        elif 'int' in types_in_expr:
            return 'int'
        elif 'char' in types_in_expr:
            return 'char'
        elif 'bool' in types_in_expr:
            return 'bool'
            
        return None

    def types_are_compatible(self, target_type, source_type):
        """Reglas de compatibilidad estrictas."""
        # Solo permite la asignación si ambos tipos son EXACTAMENTE iguales
        if target_type == source_type: 
            return True
        return False