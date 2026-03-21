int a;
a = 5; // Válido

float b;
b = a; // Error: Asignación de int a float

c = 10; // Error: c no declarado

int variable_global;
void miFuncion() {
    int variable_local;
    variable_global = 5; // Válido
    variable_local = 10; // Válido
    int a; // Válido (Shadowing, otro scope)
    int a; // Error: ya declarada en este scope
}