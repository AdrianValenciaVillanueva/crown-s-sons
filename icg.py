import lexer

class ICG:
    def __init__(self, tokens):
        # Filtramos espacios y comentarios
        self.tokens = [t for t in tokens if t.type not in ('WHITESPACE', 'COMMENT')]
        self.pos = 0
        self.temp_count = 1
        self.label_count = 1
        self.code = []

    def new_temp(self):
        t = f"t{self.temp_count}"
        self.temp_count += 1
        return t

    def new_label(self):
        l = f"L{self.label_count}"
        self.label_count += 1
        return l

    def add_instruction(self, instr):
        self.code.append(instr)

    def peek(self, offset=0):
        if self.pos + offset < len(self.tokens):
            return self.tokens[self.pos + offset]
        return None

    def consume(self):
        t = self.peek()
        self.pos += 1
        return t

    def generate(self):
        """Punto de entrada principal"""
        while self.pos < len(self.tokens):
            self.process_statement()
        return self.code

    def process_statement(self):
        t = self.peek()
        if not t: return

        # --- ESTRUCTURA IF / ELSE ---
        if t.value == "if":
            self.consume() # consume 'if'
            self.consume() # consume '('
            cond_temp = self.process_expression(stop_at=[')'])
            self.consume() # consume ')'
            
            label_else = self.new_label()
            label_end = self.new_label()
            
            self.add_instruction(f"if not {cond_temp} goto {label_else}")
            
            # Bloque IF (Verdadero)
            self.process_block_or_statement()
            self.add_instruction(f"goto {label_end}")
            
            # Bloque ELSE (Falso)
            self.add_instruction(f"{label_else}:")
            if self.peek() and self.peek().value == "else":
                self.consume() # consume 'else'
                self.process_block_or_statement()
                
            self.add_instruction(f"{label_end}:")

        # --- ESTRUCTURA SWITCH ---
        elif t.value == "switch":
            self.consume() # 'switch'
            self.consume() # '('
            switch_temp = self.process_expression(stop_at=[')'])
            self.consume() # ')'
            self.consume() # '{'
            
            # 1. Escaneo rápido para encontrar casos y organizar los saltos (Jump Table)
            saved_pos = self.pos
            case_values = []
            has_default = False
            
            while self.peek() and self.peek().value != '}':
                if self.peek().value == 'case':
                    self.pos += 1
                    case_values.append(self.consume().value)
                elif self.peek().value == 'default':
                    has_default = True
                    self.pos += 1
                else:
                    self.pos += 1
                    
            self.pos = saved_pos # Regresamos a la posición original
            
            case_labels = {val: self.new_label() for val in case_values}
            default_label = self.new_label() if has_default else self.new_label()
            end_label = self.new_label()
            
            # 2. Imprimir las validaciones de saltos primero (Como pide la rúbrica)
            for val in case_values:
                self.add_instruction(f"if {switch_temp} == {val} goto {case_labels[val]}")
            self.add_instruction(f"goto {default_label}")
            
            # 3. Imprimir el cuerpo de cada caso
            while self.peek() and self.peek().value != '}':
                tok = self.consume()
                if tok.value == 'case':
                    val = self.consume().value
                    self.consume() # ':'
                    self.add_instruction(f"{case_labels[val]}:")
                elif tok.value == 'default':
                    self.consume() # ':'
                    self.add_instruction(f"{default_label}:")
                elif tok.value == 'break':
                    if self.peek() and self.peek().value == ';':
                        self.consume() # ';'
                    self.add_instruction(f"goto {end_label}")
                else:
                    self.pos -= 1
                    self.process_statement()
                    
            self.consume() # '}'
            if not has_default:
                self.add_instruction(f"{default_label}:")
            self.add_instruction(f"{end_label}:")

        # --- ESTRUCTURA DO-WHILE ---
        elif t.value == "do":
            self.consume() # 'do'
            l_start = self.new_label()
            
            self.add_instruction(f"{l_start}:")
            self.process_block_or_statement()
            
            if self.peek() and self.peek().value == "while":
                self.consume() # 'while'
                self.consume() # '('
                cond = self.process_expression(stop_at=[')'])
                self.consume() # ')'
                if self.peek() and self.peek().value == ';':
                    self.consume() # ';'
                self.add_instruction(f"if {cond} goto {l_start}")

        # --- ESTRUCTURA RETURN ---
        elif t.value == "return":
            self.consume() # 'return'
            ret_expr = self.process_expression(stop_at=[';'])
            if self.peek() and self.peek().value == ';': 
                self.consume()
            self.add_instruction(f"return {ret_expr}")

        # --- ESTRUCTURA WHILE ---
        elif t.value == "while":
            self.consume()
            l_start = self.new_label()
            l_end = self.new_label()
            
            self.add_instruction(f"{l_start}:")
            self.consume() # '('
            cond = self.process_expression(stop_at=[')'])
            self.consume() # ')'
            
            self.add_instruction(f"if not {cond} goto {l_end}")
            self.process_block_or_statement()
            self.add_instruction(f"goto {l_start}")
            self.add_instruction(f"{l_end}:")

        # --- ESTRUCTURA FOR ---
        elif t.value == "for":
            self.consume() # 'for'
            self.consume() # '('
            self.process_statement() # Inicialización
            
            l_start = self.new_label()
            l_end = self.new_label()
            
            self.add_instruction(f"{l_start}:")
            cond = self.process_expression(stop_at=[';'])
            self.consume() # ';'
            
            self.add_instruction(f"if not {cond} goto {l_end}")
            
            inc_tokens = []
            while self.peek() and self.peek().value != ')':
                inc_tokens.append(self.consume())
            self.consume() # ')'
            
            self.process_block_or_statement()
            
            if inc_tokens:
                # TAC simplificado para el incremento
                self.add_instruction(f"{inc_tokens[0].value} = {inc_tokens[0].value} + 1")
                
            self.add_instruction(f"goto {l_start}")
            self.add_instruction(f"{l_end}:")

        # --- CLASES ---
        elif t.value == "class":
            self.consume() # 'class'
            class_name = self.consume().value
            self.add_instruction(f"# Definición de la clase {class_name}")
            self.consume() # '{'
            while self.peek() and self.peek().value != '}':
                self.process_statement()
            self.consume() # '}'

        # --- MÉTODOS / FUNCIONES ---
        elif t.type == 'KEYWORD' and self.peek(2) and self.peek(2).value == '(':
            self.consume() # tipo retorno
            name = self.consume()
            l_func = self.new_label()
            self.add_instruction(f"# Definición del método {name.value}")
            self.add_instruction(f"{l_func}:")
            while self.peek() and self.peek().value != ')': self.consume()
            self.consume() # ')'
            self.process_block_or_statement()
            
        elif t.value == "goto":
            self.consume() # Consume 'goto'
            target_label = self.consume().value # Lee 'L2'
            if self.peek() and self.peek().value == ';': 
                self.consume() # Consume el ';'
            self.add_instruction(f"goto {target_label}")

        # --- ETIQUETAS MANUALES (Ej. L2:) ---
        elif t.type == 'IDENTIFIER' and self.peek(1) and self.peek(1).value == ':':
            label_name = self.consume().value # Lee el nombre (L2)
            self.consume() # Consume los dos puntos ':'
            self.add_instruction(f"{label_name}:")

        # --- ASIGNACIONES / LLAMADAS A OBJETOS ---
        elif t.type == 'IDENTIFIER' or t.value in ["int", "float", "bool", "string"]:
            target = None
            
            # 1. Determinar quién es el objetivo (Ej. 'int x', 'Persona p' o solo 'x')
            if t.value in ["int", "float", "bool", "string"]: 
                self.consume() # Tipo
                target = self.consume().value
            else:
                if self.peek(1) and self.peek(1).type == 'IDENTIFIER':
                    self.consume() # Nombre de clase (Ej. Persona)
                    target = self.consume().value
                else:
                    target = self.consume().value

            # 2. Es llamada a método de un objeto? (Ej. p.celebrarCumpleaños())
            if self.peek() and self.peek().value == '.':
                self.consume() # '.'
                method_name = self.consume().value
                self.consume() # '('
                while self.peek() and self.peek().value != ')': self.consume()
                self.consume() # ')'
                if self.peek() and self.peek().value == ';': self.consume()
                self.add_instruction(f"call {method_name}")

            # 3. Asignación convencional (=)
            elif self.peek() and self.peek().value == "=":
                self.consume() # '='
                
                # Creación de objetos
                if self.peek() and self.peek().value == "new":
                    self.consume() # 'new'
                    class_name = self.consume().value
                    self.consume() # '('
                    self.consume() # ')'
                    if self.peek() and self.peek().value == ';': self.consume()
                    self.add_instruction(f"obj = create {class_name}") 
                
                # Llamada a método que retorna valor (result = suma(5, 3))
                elif self.peek() and self.peek().type == 'IDENTIFIER' and self.peek(1) and self.peek(1).value == '(':
                    method_name = self.consume().value
                    self.consume() # '('
                    
                    args = []
                    while self.peek() and self.peek().value != ')':
                        if self.peek().value != ',':
                            args.append(self.consume().value)
                        else:
                            self.consume()
                    self.consume() # ')'
                    
                    # Temporales para los parámetros
                    for arg in args:
                        t_param = self.new_temp()
                        self.add_instruction(f"{t_param} = {arg}")
                        
                    self.add_instruction(f"call {method_name}")
                    self.add_instruction(f"{target} = return_value")
                    if self.peek() and self.peek().value == ';': self.consume()
                    
                # Expresión matemática normal
                else:
                    expr_res = self.process_expression(stop_at=[';'])
                    if self.peek() and self.peek().value == ';': self.consume()
                    self.add_instruction(f"{target} = {expr_res}")
            else:
                pass # Evita atorarse
        else:
            self.consume()

    def process_block_or_statement(self):
        if self.peek() and self.peek().value == "{":
            self.consume() # '{'
            while self.peek() and self.peek().value != "}":
                self.process_statement()
            self.consume() # '}'
        else:
            self.process_statement()

    def process_expression(self, stop_at=[]):
        tokens_to_process = []
        while self.peek() and self.peek().value not in stop_at and self.peek().value != ';':
            tokens_to_process.append(self.consume())
        
        if not tokens_to_process: return "0"
        
        if len(tokens_to_process) == 1:
            return tokens_to_process[0].value

        t = self.new_temp()
        expr_str = " ".join([tok.value for tok in tokens_to_process])
        self.add_instruction(f"{t} = {expr_str}")
        return t