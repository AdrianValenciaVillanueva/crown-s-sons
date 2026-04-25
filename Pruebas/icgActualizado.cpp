// 1. switch y case
switch (n) {
    case 1:
        result = "Uno";
        break;
    case 2:
        result = "Dos";
        break;
    default:
        result = "Otro";
}

// 2. do-while
do {
    count = count + 1;
} while (count < 10);

// 3. Método y llamada
int suma(int a, int b) {
    return a + b;
}
int resultSuma = suma(5, 3);

// 4. Clases y Objetos
class Persona {
    int edad;
    void celebrarCumpleanos() {
        edad = edad + 1;
    }
}
Persona p = new Persona();
p.celebrarCumpleanos();