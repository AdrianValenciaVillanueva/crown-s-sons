import lexer

class ICG:
    def __init__(self, tokens):
        self.tokens = [t for t in tokens if t.type not in ('WHITESPACE', 'COMMENT')]
        self.pos = 0
        self.temp_count = 1
        self.code = []

    def new_temp(self):
        """Genera una nueva etiqueta temporal (t1, t2, t3...)."""
        t = f"t{self.temp_count}"
        self.temp_count += 1
        return t

    def add_instruction(self, instr):
        self.code.append(instr)

    def generate(self):
        """Busca asignaciones y genera código intermedio para ellas."""
        while self.pos < len(self.tokens):
            t = self.tokens[self.pos]

            # Detectar declaración con asignación (ej. int x = ...) o asignación simple (ej. x = ...)
            is_simple_assign = (t.type == 'IDENTIFIER' and self.peek(1) and self.peek(1).value == '=')
            is_decl_assign = (t.value in ["int", "float", "double", "char", "bool", "string"] and 
                              self.peek(1) and self.peek(1).type == 'IDENTIFIER' and 
                              self.peek(2) and self.peek(2).value == '=')

            if is_simple_assign or is_decl_assign:
                if t.type == 'IDENTIFIER':
                    target_var = t.value
                    self.pos += 2 # Saltar nombre y '='
                else:
                    target_var = self.peek(1).value
                    self.pos += 3 # Saltar tipo, nombre y '='
                
                expr_tokens = []
                while self.pos < len(self.tokens) and self.tokens[self.pos].value not in (';', ','):
                    expr_tokens.append(self.tokens[self.pos])
                    self.pos += 1
                
                if expr_tokens:
                    self.process_expression(target_var, expr_tokens)
                
                if self.pos < len(self.tokens) and self.tokens[self.pos].value in (';', ','):
                    self.pos += 1
                continue
            
            self.pos += 1
            
        return self.code

    def peek(self, offset=0):
        if self.pos + offset < len(self.tokens):
            return self.tokens[self.pos + offset]
        return None

    def process_expression(self, target, expr_tokens):
        # Jerarquía de operaciones para el algoritmo Shunting Yard
        precedence = {
            '||': 1, '&&': 2,
            '==': 3, '!=': 3, '>': 3, '<': 3, '>=': 3, '<=': 3,
            '+': 4, '-': 4,
            '*': 5, '/': 5, '%': 5
        }
        
       # 1. Validaciones y Errores (División por cero y tipos) solicitados en la rúbrica
        for i, tok in enumerate(expr_tokens):
            if tok.value == '/' and i + 1 < len(expr_tokens):
                # NUEVO: Solo validar si el divisor directo es una variable o un número, ignorando paréntesis
                if expr_tokens[i+1].type in ('IDENTIFIER', 'NUMBER'):
                    divisor = expr_tokens[i+1].value
                    self.add_instruction(f'if {divisor} == 0 then error "Division by zero"')

            if tok.value in ('+', '-', '*', '/'):
                left_tok = expr_tokens[i-1] if i > 0 else None
                right_tok = expr_tokens[i+1] if i+1 < len(expr_tokens) else None
                if left_tok and right_tok:
                    if left_tok.type == 'STRING' or right_tok.type == 'STRING':
                        self.add_instruction(f'if type({left_tok.value}) != integer or type({right_tok.value}) != integer then error "Type mismatch"')

        # 2. Convertir a Notación Polaca Inversa (Postfijo)
        output = []
        stack = []
        
        for tok in expr_tokens:
            if tok.type in ('NUMBER', 'IDENTIFIER', 'STRING', 'CHAR_LITERAL') or tok.value in ('true', 'false'):
                output.append(tok.value)
            elif tok.value == '(':
                stack.append(tok.value)
            elif tok.value == ')':
                while stack and stack[-1] != '(':
                    output.append(stack.pop())
                if stack:
                    stack.pop() # Quitar '('
            elif tok.value in precedence:
                while stack and stack[-1] != '(' and precedence.get(stack[-1], 0) >= precedence[tok.value]:
                    output.append(stack.pop())
                stack.append(tok.value)
        
        while stack:
            output.append(stack.pop())
            
        # 3. Generar el Código de 3 Direcciones
        eval_stack = []
        for item in output:
            if item in precedence:
                if len(eval_stack) >= 2:
                    right_val, right_is_temp = eval_stack.pop()
                    left_val, left_is_temp = eval_stack.pop()
                    temp = self.new_temp()
                    self.add_instruction(f"{temp} = {left_val} {item} {right_val}")
                    eval_stack.append((temp, True)) # Es un temporal
            else:
                eval_stack.append((item, False)) # Es un valor o variable directa
                
        # 4. Asignación final a la variable objetivo
        if len(eval_stack) == 1:
            final_val, is_temp = eval_stack.pop()
            if not is_temp:
                # Si es asignación directa (ej. x = 5), se manda a un temporal primero como pide la rúbrica
                temp = self.new_temp()
                self.add_instruction(f"{temp} = {final_val}")
                self.add_instruction(f"{target} = {temp}")
            else:
                # Si ya viene de temporales (ej. total = t10)
                self.add_instruction(f"{target} = {final_val}")