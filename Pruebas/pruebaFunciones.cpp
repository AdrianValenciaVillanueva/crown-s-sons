int sumar(int a, int b) {
    return a + b; // Correcto: Retorna int
}

bool esMayor(int x) {
    return 100; // Error Semántico: Se esperaba bool, se intenta retornar int
}

void miFuncion() {
    int m = 15;
    
    // Correcto: Llamada con parámetros exactos
    int resultado = sumar(5, 3); 
    
    // Error Semántico: Espera 2 args, se manda 1
    int errorArgumentos = sumar(10); 
    
    // Error Semántico: Tipos incompatibles (texto en vez de int)
    int errorTipos = sumar("Hola", 3); 

    // Error Semántico: if con string en vez de booleano
    if ("texto") {
        m = 20;
    }

    // Correcto: if con booleano
    if (m > 10) {
        m = 30;
    }

    // Error Semántico: Excepción división por cero atrapada
    int peligro = 10 / 0; 
}