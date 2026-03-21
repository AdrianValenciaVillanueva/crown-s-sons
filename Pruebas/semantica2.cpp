//1. DECLARACIONES VÁLIDAS ===
    int edad = 25;
    string nombre = "Juan";
    float peso = 70.5;
    bool activo = true;

//2. MATEMÁTICAS CON CADENAS (Error) ===
    int resultado = edad + nombre;

//3. DIVISIÓN POR CERO (Error) ===
    int division = 10 / 0;

//4. LÓGICA CON NÚMEROS (Error) ===
    bool errorLogico = true && 1;

//5. COMPARACIÓN INCOMPATIBLE (Error) ===
    bool errorComp = "5" == 5;

//6. ASIGNACIÓN ESTRICTA (Error) ===
    float flotanteMal = edad; 

//7. VARIABLE NO DECLARADA (Error) ===
    fantasma = 100;

//8. DOBLE DECLARACIÓN (Error) ===
    int edad = 30;