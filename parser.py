import lexer
from typing import List

def parse(tokens: List[lexer.Token]) -> List[str]:
    errors = []
    # Filtramos espacios y comentarios
    filtered_tokens = [t for t in tokens if t.type not in ('WHITESPACE', 'COMMENT')]
    
    # Tipos válidos (Agregamos validación por valor, sin importar si el lexer lo marcó como keyword o identificador)
    valid_types = ["int", "float", "double", "char", "bool", "string", "const"]
    invalid_types = ["entero", "flotante", "booleano", "cadena"]
    
    i = 0
    while i < len(filtered_tokens):
        t = filtered_tokens[i]
        
        # 1. VERIFICAR SI EMPIEZA UNA DECLARACIÓN
        is_valid_type = t.value in valid_types
        is_invalid_type = t.value in invalid_types
        
        if is_valid_type or is_invalid_type:
            # Reportar si usaron un tipo en español (inválido)
            if is_invalid_type:
                errors.append(f"Error Sintáctico: Tipo no válido '{t.value}' en línea {t.line}, columna {t.column}. Los tipos válidos son: {', '.join(valid_types)}.")
            
            i += 1
            if i >= len(filtered_tokens):
                errors.append(f"Error Sintáctico: Declaración incompleta al final del archivo.")
                break
            
            # 2. VERIFICAR EL IDENTIFICADOR
            next_t = filtered_tokens[i]
            
            # Si el lexer detectó un identificador mal formado (ej. empieza con número)
            if next_t.type == 'ERROR' and next_t.value[0].isdigit():
                errors.append(f"Error Sintáctico: Identificador inválido '{next_t.value}' en línea {next_t.line}, columna {next_t.column}. Un identificador debe comenzar con letra o guion bajo.")
                i += 1
            # Si en lugar de variable pusieron un número, símbolo, etc. (y no es el ERROR anterior)
            elif next_t.type != 'IDENTIFIER' and next_t.type != 'ERROR':
                errors.append(f"Error Sintáctico: Se esperaba un identificador en línea {next_t.line}, columna {next_t.column}. Se encontró '{next_t.value}'.")
                i += 1
            else:
                # Es un identificador válido (o un error distinto ya manejado), avanzamos
                i += 1
            
            # 3. VERIFICAR EL PUNTO Y COMA (;)
            if i < len(filtered_tokens):
                semi_t = filtered_tokens[i]
                if semi_t.value == ';':
                    # Todo bien, consumimos el punto y coma
                    i += 1
                else:
                    # Falta el punto y coma. Calculamos la posición del error basándonos en la variable anterior.
                    last_t = filtered_tokens[i-1]
                    col = last_t.column + len(last_t.value)
                    errors.append(f"Error Sintáctico: Se esperaba ';' al final de la declaración en la línea {last_t.line}, columna {col}.")
                    # NO incrementamos 'i' aquí, porque el token actual pertenece a la siguiente línea/declaración.
        else:
            # Si no es un tipo (ej. código suelto u otras estructuras), lo saltamos por ahora
            i += 1

    return errors