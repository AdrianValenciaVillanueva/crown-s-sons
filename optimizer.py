import re

class Optimizer:
    def __init__(self, tac_code):
        self.code = tac_code

    def optimize(self):
        # Aplicamos las optimizaciones en orden lógico
        code = self.remove_unreachable_code(self.code)
        code = self.eliminate_redundant_assignments(code)
        code = self.eliminate_common_subexpressions(code)
        code = self.remove_unused_variables(code)
        return code

    def remove_unreachable_code(self, code):
        """Elimina instrucciones después de un 'goto' o 'return' hasta encontrar la siguiente etiqueta."""
        optimized = []
        is_dead = False
        
        for line in code:
            stripped_line = line.strip()
            
            if stripped_line.endswith(':'):
                is_dead = False
            
            if not is_dead:
                optimized.append(line)
            
            if stripped_line.startswith('goto ') or stripped_line.startswith('return ') or stripped_line == 'return':
                is_dead = True
                
        return optimized

    def eliminate_redundant_assignments(self, code):
        """Elimina reasignaciones inmediatas a la misma variable (temp = a; temp = b)."""
        optimized = []
        last_assigned_var = None
        
        for i, line in enumerate(code):
            match = re.match(r'^\s*([a-zA-Z0-9_]+)\s*=\s*(.+)$', line)
            if match and not line.strip().startswith('if '):
                var_name = match.group(1)
                
                # Miramos la siguiente línea para ver si se sobreescribe inmediatamente
                if i + 1 < len(code):
                    next_match = re.match(r'^\s*([a-zA-Z0-9_]+)\s*=\s*(.+)$', code[i+1])
                    if next_match and next_match.group(1) == var_name:
                        continue # Saltamos esta instrucción porque es redundante
                        
                last_assigned_var = var_name
            optimized.append(line)
        return optimized

    def eliminate_common_subexpressions(self, code):
        """Reutiliza cálculos previos si los operandos no han cambiado (t1 = a+b; t2 = a+b)."""
        optimized = []
        expressions = {} # Guarda { 'a + b': 't1' }
        
        for line in code:
            # Buscamos asignaciones de operaciones: t1 = a + b
            match = re.match(r'^\s*([a-zA-Z0-9_]+)\s*=\s*([a-zA-Z0-9_]+\s*[\+\-\*\/]\s*[a-zA-Z0-9_]+)$', line)
            if match:
                var_name = match.group(1)
                expr = match.group(2).strip()
                
                if expr in expressions:
                    # Si ya calculamos esto, reasignamos la variable al temporal anterior
                    prev_var = expressions[expr]
                    optimized.append(f"    {var_name} = {prev_var}")
                else:
                    expressions[expr] = var_name
                    optimized.append(line)
            else:
                optimized.append(line)
                
            # Si una variable base se modifica, invalida las expresiones cacheadas (simplificado)
            assign_match = re.match(r'^\s*([a-zA-Z0-9_]+)\s*=', line)
            if assign_match and not line.strip().startswith('if '):
                mod_var = assign_match.group(1)
                # Borrar expresiones que contengan la variable modificada
                expressions = {k: v for k, v in expressions.items() if mod_var not in k}
                
        return optimized

    def remove_unused_variables(self, code):
        """Elimina variables que se les asigna un valor pero nunca se usan."""
        # 1. Recolectar todas las variables que se USAN (lado derecho, if, goto, return, call)
        used_vars = set()
        for line in code:
            if line.strip().startswith('if ') or line.strip().startswith('return '):
                parts = re.findall(r'[a-zA-Z_][a-zA-Z0-9_]*', line)
                used_vars.update(parts)
            elif '=' in line and not line.strip().startswith('if '):
                right_side = line.split('=', 1)[1]
                parts = re.findall(r'[a-zA-Z_][a-zA-Z0-9_]*', right_side)
                used_vars.update(parts)

        # 2. Filtrar las asignaciones a variables que no están en used_vars
        optimized = []
        for line in code:
            match = re.match(r'^\s*([a-zA-Z0-9_]+)\s*=\s*(.+)$', line)
            if match and not line.strip().startswith('if '):
                var_name = match.group(1)
                # No eliminamos variables clave como 'result', 'obj' o si están en uso
                if var_name not in used_vars and not var_name.startswith('result') and var_name != 'obj':
                    continue # Es código muerto, lo saltamos
            optimized.append(line)
            
        return optimized