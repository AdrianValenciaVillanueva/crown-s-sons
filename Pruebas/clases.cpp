//Definiciones válidas:

class MiClase {
    int miMetodo(int a, float b) {
        // cuerpo del método
    }
    void otroMetodo() {
        // cuerpo del método
    }
}
 
//Definiciones inválidas:

class MiClase {
    int miMetodo(int a float b) {  // Falta coma entre parámetros
        // cuerpo del método
    }
    void otroMetodo {  // Faltan paréntesis
        // cuerpo del método
    }
}

