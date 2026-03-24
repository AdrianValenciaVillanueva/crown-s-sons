class SymbolTable:
    def __init__(self):
        self.scopes = [{}]
        self.all_symbols = {} 

    def push_scope(self):
        self.scopes.append({})

    def pop_scope(self):
        if len(self.scopes) > 1:
            self.scopes.pop()

    def insert(self, name, symbol_type, extra_data=None):
        current_scope = self.scopes[-1]
        if name in current_scope:
            return False 
        
        alcance = 'global' if len(self.scopes) == 1 else 'local'
        simbolo_info = {'tipo': symbol_type, 'alcance': alcance}
        
        if extra_data:
            simbolo_info.update(extra_data)
            
        current_scope[name] = simbolo_info
        self.all_symbols[name] = simbolo_info 
        return True

    def lookup(self, name):
        for scope in reversed(self.scopes):
            if name in scope:
                return scope[name]
        return None

class SemanticAnalyzer:
    def __init__(self, tokens):
        self.tokens = [t for t in tokens if t.type not in ('WHITESPACE', 'COMMENT')]
        self.pos = 0
        self.errors = []
        self.sym_table = SymbolTable()
        self.valid_types = ["int", "float", "double", "char", "bool", "string", "void"]
        self.current_return_type = None

    def peek(self, offset=0):
        if self.pos + offset < len(self.tokens):
            return self.tokens[self.pos + offset]
        return None

    def analyze(self):
        while self.pos < len(self.tokens):
            t = self.tokens[self.pos]

            if t.value == '{':
                self.sym_table.push_scope()
                self.pos += 1
                continue
            if t.value == '}':
                self.sym_table.pop_scope()
                if len(self.sym_table.scopes) == 1: 
                    self.current_return_type = None
                self.pos += 1
                continue

            # --- VALIDACIÓN DE FLUJO LÓGICO Y ESTRUCTURAS ---
            if t.value in ('if', 'while'):
                self.pos += 1
                if self.peek() and self.peek().value == '(':
                    self.pos += 1
                    cond_tokens = self.extract_until_matching_paren()
                    cond_type = self.infer_expression_type(cond_tokens, t.line, t.column)
                    if cond_type and cond_type != 'bool':
                        err = f"Error Semántico: La condición en '{t.value}' debe ser una expresión booleana, se detectó '{cond_type}'. (Línea {t.line})"
                        if err not in self.errors: self.errors.append(err)
                continue

            # --- VALIDACIÓN DE TIPOS DE RETORNO ---
            if t.value == 'return':
                self.pos += 1
                ret_tokens = []
                while self.pos < len(self.tokens) and self.tokens[self.pos].value != ';':
                    ret_tokens.append(self.tokens[self.pos])
                    self.pos += 1
                
                if self.current_return_type:
                    if not ret_tokens and self.current_return_type != 'void':
                        self.errors.append(f"Error Semántico: Método requiere retornar tipo '{self.current_return_type}', pero el return está vacío. (Línea {t.line})")
                    elif ret_tokens:
                        ret_type = self.infer_expression_type(ret_tokens, t.line, t.column)
                        if ret_type and not self.types_are_compatible(self.current_return_type, ret_type):
                            err = f"Error Semántico: Retorno incompatible. Se esperaba '{self.current_return_type}' pero se intenta retornar '{ret_type}'. (Línea {t.line})"
                            if err not in self.errors: self.errors.append(err)
                self.pos += 1
                continue

            # --- DEFINICIÓN DE MÉTODOS Y VARIABLES ---
            if t.value in self.valid_types:
                next_t = self.peek(1)
                if next_t and next_t.type == 'IDENTIFIER':
                    var_type = t.value
                    var_name = next_t.value
                    
                    if self.peek(2) and self.peek(2).value == '(':
                        self.current_return_type = var_type
                        self.pos += 3
                        
                        params_esperados = []
                        while self.pos < len(self.tokens) and self.tokens[self.pos].value != ')':
                            pt = self.tokens[self.pos]
                            if pt.value in self.valid_types:
                                params_esperados.append(pt.value)
                            self.pos += 1
                            
                        if not self.sym_table.insert(var_name, 'metodo', {'retorno': var_type, 'params': params_esperados}):
                            self.errors.append(f"Error Semántico: El método '{var_name}' ya fue declarado. (Línea {next_t.line})")
                        self.pos += 1
                        continue
                    else:
                        if not self.sym_table.insert(var_name, var_type):
                            self.errors.append(f"Error Semántico: El identificador '{var_name}' ya fue declarado. (Línea {next_t.line})")

                        if self.peek(2) and self.peek(2).value == '=':
                            self.pos += 2
                            self.check_assignment(var_name, var_type, next_t.line, next_t.column)
                            continue
            
            # --- LLAMADAS A MÉTODOS Y ASIGNACIONES ---
            if t.type == 'IDENTIFIER':
                var_name = t.value
                symbol = self.sym_table.lookup(var_name)
                next_t = self.peek(1)
                
                if next_t and next_t.value == '(':
                    if not symbol:
                        self.errors.append(f"Error Semántico: Método '{var_name}' no declarado. (Línea {t.line})")
                        self.pos += 2
                        self.extract_until_matching_paren()
                        continue
                    elif symbol['tipo'] != 'metodo':
                        self.errors.append(f"Error Semántico: '{var_name}' no es un método. (Línea {t.line})")
                    else:
                        self.pos += 2
                        argument_tokens_list = self.extract_arguments()
                        params_requeridos = symbol.get('params', [])
                        
                        if len(argument_tokens_list) != len(params_requeridos):
                            err = f"Error Semántico: Llamada al método '{var_name}' requiere {len(params_requeridos)} argumentos, se dieron {len(argument_tokens_list)}. (Línea {t.line})"
                            if err not in self.errors: self.errors.append(err)
                        else:
                            for i, arg_tokens in enumerate(argument_tokens_list):
                                arg_type = self.infer_expression_type(arg_tokens, t.line, t.column)
                                if arg_type and not self.types_are_compatible(params_requeridos[i], arg_type):
                                    err = f"Error Semántico: Argumento {i+1} de '{var_name}' debe ser '{params_requeridos[i]}', no '{arg_type}'. (Línea {t.line})"
                                    if err not in self.errors: self.errors.append(err)
                        continue
                
                if not symbol:
                    self.errors.append(f"Error Semántico: Identificador '{var_name}' no declarado. (Línea {t.line})")
                else:
                    var_type = symbol['tipo']
                    if next_t and next_t.value == '=':
                        self.pos += 1
                        self.check_assignment(var_name, var_type, t.line, t.column)
                        continue

            self.pos += 1

        return self.errors, self.sym_table

    def extract_until_matching_paren(self):
        tokens_extr = []
        paren_count = 0
        while self.pos < len(self.tokens):
            tok = self.tokens[self.pos]
            if tok.value == '(': paren_count += 1
            elif tok.value == ')':
                if paren_count == 0: break
                paren_count -= 1
            tokens_extr.append(tok)
            self.pos += 1
        return tokens_extr

    def extract_arguments(self):
        args_list = []
        current_arg = []
        paren_count = 0
        while self.pos < len(self.tokens):
            tok = self.tokens[self.pos]
            if tok.value == '(': paren_count += 1
            elif tok.value == ')':
                if paren_count == 0:
                    if current_arg: args_list.append(current_arg)
                    break
                paren_count -= 1
            elif tok.value == ',' and paren_count == 0:
                args_list.append(current_arg)
                current_arg = []
                self.pos += 1
                continue
            current_arg.append(tok)
            self.pos += 1
        return args_list

    def check_assignment(self, var_name, var_type, line, col):
        self.pos += 1
        expr_tokens = []
        paren_count = 0
        
        while self.pos < len(self.tokens):
            t = self.tokens[self.pos]
            
            # Contamos los paréntesis para saber si estamos dentro de una función o fórmula
            if t.value == '(': 
                paren_count += 1
            elif t.value == ')': 
                paren_count -= 1
            
            # Solo detenerse si encontramos un ';' o una ',' pero fuera de cualquier paréntesis
            if paren_count == 0 and t.value in (';', ','):
                break
                
            expr_tokens.append(t)
            self.pos += 1
            
        if not expr_tokens: return
        expr_type = self.infer_expression_type(expr_tokens, line, col)
        
        if expr_type and not self.types_are_compatible(var_type, expr_type):
            err = f"Error Semántico: Tipo incompatible. Intentó asignar '{expr_type}' a '{var_name}' ({var_type}). (Línea {line})"
            if err not in self.errors: self.errors.append(err)

    def extract_and_validate_args(self, func_name, symbol, tokens, start_index):
        args_list = []
        current_arg = []
        paren_count = 0
        i = start_index
        
        while i < len(tokens):
            tok = tokens[i]
            if tok.value == '(': paren_count += 1
            elif tok.value == ')':
                if paren_count == 0:
                    if current_arg: args_list.append(current_arg)
                    break
                paren_count -= 1
            elif tok.value == ',' and paren_count == 0:
                args_list.append(current_arg)
                current_arg = []
                i += 1
                continue
            
            current_arg.append(tok)
            i += 1

        params_requeridos = symbol.get('params', [])
        line = tokens[start_index - 1].line if start_index > 0 else 0
        
        if len(args_list) != len(params_requeridos):
            err = f"Error Semántico: Llamada al método '{func_name}' requiere {len(params_requeridos)} argumentos, se dieron {len(args_list)}. (Línea {line})"
            if err not in self.errors: self.errors.append(err)
        else:
            for j, arg_tokens in enumerate(args_list):
                arg_type = self.infer_expression_type(arg_tokens, line, 0)
                if arg_type and not self.types_are_compatible(params_requeridos[j], arg_type):
                    err = f"Error Semántico: Argumento {j+1} de '{func_name}' debe ser '{params_requeridos[j]}', no '{arg_type}'. (Línea {line})"
                    if err not in self.errors: self.errors.append(err)
                    
        return args_list, i

    def infer_expression_type(self, tokens, line, col):
        types_in_expr = set()
        math_ops = {'+', '-', '*', '/', '%'}
        rel_ops = {'==', '!=', '<', '>', '<=', '>='}
        log_ops = {'&&', '||'}
        
        found_math = False
        found_rel = False
        found_log = False
        
        i = 0
        while i < len(tokens):
            t = tokens[i]
            
            if t.value in math_ops: found_math = True
            if t.value in rel_ops: found_rel = True
            if t.value in log_ops: found_log = True
            
            if t.value == '/' and i + 1 < len(tokens) and tokens[i+1].value == '0':
                err = f"Error Semántico: División por cero. (Línea {t.line})"
                if err not in self.errors: self.errors.append(err)

            t_type = None
            if t.type == 'STRING': t_type = 'string'
            elif t.type == 'CHAR_LITERAL': t_type = 'char'
            elif t.value in ('true', 'false'): t_type = 'bool'
            elif t.type == 'NUMBER': t_type = 'float' if '.' in t.value else 'int'
            elif t.type == 'IDENTIFIER':
                sym = self.sym_table.lookup(t.value)
                if sym:
                    if sym['tipo'] == 'metodo':
                        t_type = sym.get('retorno')
                        if i + 1 < len(tokens) and tokens[i+1].value == '(':
                            args_list, jump_index = self.extract_and_validate_args(t.value, sym, tokens, i + 2)
                            i = jump_index 
                    else:
                        t_type = sym['tipo']
            
            if t_type: types_in_expr.add(t_type)
            i += 1

        has_string = 'string' in types_in_expr
        has_numeric = 'int' in types_in_expr or 'float' in types_in_expr or 'double' in types_in_expr
        has_bool = 'bool' in types_in_expr

        if found_math and has_string:
            err = f"Error Semántico: Operadores matemáticos no válidos con texto. (Línea {line})"
            if err not in self.errors: self.errors.append(err)
        if found_math and has_bool:
            err = f"Error Semántico: Operaciones matemáticas inválidas con booleanos. (Línea {line})"
            if err not in self.errors: self.errors.append(err)
        if found_log and (has_numeric or has_string) and not found_rel:
            err = f"Error Semántico: Los operadores lógicos requieren booleanos. (Línea {line})"
            if err not in self.errors: self.errors.append(err)
        if found_rel and has_string and has_numeric:
            err = f"Error Semántico: No se puede comparar texto con números. (Línea {line})"
            if err not in self.errors: self.errors.append(err)

        if found_rel or found_log: return 'bool'
        elif has_string: return 'string'
        elif 'float' in types_in_expr or 'double' in types_in_expr: return 'float'
        elif 'int' in types_in_expr: return 'int'
        elif 'char' in types_in_expr: return 'char'
        elif 'bool' in types_in_expr: return 'bool'
        return None

    def types_are_compatible(self, target_type, source_type):
        if target_type == source_type: return True
        return False