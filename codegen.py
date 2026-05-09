import re

class CodeGenerator:
    def __init__(self, optimized_code):
        self.tac = [line.strip() for line in optimized_code if line.strip()]
        self.machine_code = []
        self.symbol_table = {}
        
        # Asignación de Direcciones solicitada por la rúbrica
        self.inst_addr_counter = 0x1000  # Las instrucciones inician aquí
        self.var_addr_counter = 0x2000   # Las variables inician aquí
        
        self.current_r1 = None
        self.pending_store = None

    def get_addr(self, var):
        # Si es un número o texto directo, se pasa como literal
        if var.isdigit() or var.startswith('"'):
            return var 
        # Si es una variable, le asignamos dirección en memoria
        if var not in self.symbol_table:
            self.symbol_table[var] = f"0x{self.var_addr_counter:04X}"
            self.var_addr_counter += 4
        return self.symbol_table[var]

    def emit(self, instruction, op1="", op2=""):
        addr = f"0x{self.inst_addr_counter:04X}"
        if op2:
            line = f"{addr}: {instruction:<5} {op1}, {op2}"
        elif op1:
            line = f"{addr}: {instruction:<5} {op1}"
        else:
            line = f"{addr}: {instruction:<5}"
        self.machine_code.append(line)
        self.inst_addr_counter += 4

    def flush_store(self):
        """Fuerza el guardado de una variable temporal si el flujo cambia."""
        if self.pending_store:
            var, addr = self.pending_store
            self.emit("STORE", addr, "R1")
            self.pending_store = None

    def generate(self):
        # Primera pasada: Mapear Etiquetas (L1, L2) a direcciones de instrucción
        for line in self.tac:
            if line.endswith(':'):
                label = line[:-1]
                self.symbol_table[label] = f"0x{self.inst_addr_counter:04X}"

        # Segunda pasada: Traducción y Optimización
        for line in self.tac:
            if line.endswith(':'):
                self.flush_store()
                continue

            # Operación Binaria: t1 = a + b
            match_bin = re.match(r'(\w+)\s*=\s*(\w+)\s*([\+\-\*\/<>=!]+)\s*(\w+)', line)
            if match_bin:
                target = match_bin.group(1)
                op1 = match_bin.group(2)
                operator = match_bin.group(3)
                op2 = match_bin.group(4)

                # Optimización: Si op1 NO está en R1, lo cargamos. Si ya está, nos ahorramos la instrucción LOAD
                if self.current_r1 != op1:
                    self.flush_store()
                    self.emit("LOAD", "R1", self.get_addr(op1))

                op_map = {'+': 'ADD', '-': 'SUB', '*': 'MUL', '/': 'DIV', '<': 'CMPL', '>': 'CMPG', '==': 'CMPE', '&&': 'AND', '||': 'OR'}
                asm_op = op_map.get(operator, 'OP')
                self.emit(asm_op, "R1", self.get_addr(op2))

                self.current_r1 = target
                # Optimización: Retrasamos el STORE si es un temporal (t1, t2)
                if target.startswith('t'):
                    self.pending_store = (target, self.get_addr(target))
                else:
                    self.emit("STORE", self.get_addr(target), "R1")
                    self.current_r1 = None
                continue

            # Asignación simple: x = 10 o x = y
            match_assign = re.match(r'(\w+)\s*=\s*(.+)', line)
            if match_assign:
                target = match_assign.group(1)
                val = match_assign.group(2)
                
                # Optimización de reasignación directa
                if self.current_r1 != val:
                    self.flush_store()
                    self.emit("LOAD", "R1", self.get_addr(val))
                self.emit("STORE", self.get_addr(target), "R1")
                self.current_r1 = target
                continue

        self.flush_store()
        return self.machine_code, self.symbol_table

    def generate_executable_header(self):
        """Simula la creación del Archivo Ejecutable y entorno .exe/.bin"""
        exe = "=== ARCHIVO EJECUTABLE GENERADO (programa.bin) ===\n"
        exe += "[HEADER] MAGIC: 0x7F454C46 (Formato ELF)\n"
        exe += "[HEADER] ENTRY_POINT: 0x1000\n"
        exe += "[ENV] PERMISOS: +x (Ejecución permitida)\n"
        exe += "[ENV] LIBRERÍAS: std_math.dll cargada\n"
        exe += "-" * 50 + "\n"
        # Simulación de Hex Dump para el archivo
        for line in self.machine_code:
            addr = line.split(':')[0]
            exe += f"{addr}  AF 2B 00 {self.var_addr_counter % 255:02X} ... (Instrucción Máquina)\n"
        return exe