// Programa de prueba completo para el Compilador C++

int main() {
    // 1. Prueba de Análisis Léxico y Semántico (Declaración de tipos)
    int limite = 15;
    int contador = 0;
    float factor = 1.5;
    string mensaje = "Calculando...";

    // 2. Prueba de Sintaxis y Código Intermedio (Operaciones combinadas)
    int resultado = (limite * 2) + contador;

    // 3. Prueba de Estructuras de Control (Generación de saltos y etiquetas)
    if (resultado > 20) {
        contador = contador + 1;
    } else {
        contador = contador - 1;
    }

    // 4. Prueba de Bucles (while)
    while (contador < 5) {
        contador = contador + 1;
    }

    // 5. Prueba para el Optimizador (Código redundante e inalcanzable)
    int x = 10;
    x = 10; // El optimizador debería eliminar esta reasignación redundante

    return 0;

    // El optimizador debería eliminar este bloque por estar después de un return
    limite = 999; 
}