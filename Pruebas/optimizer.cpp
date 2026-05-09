// 1. Código Inalcanzable (Salto incondicional)
x = 10;
goto L2;
y = 20; // Esto no debe aparecer optimizado

// 2. Variables No Utilizadas
a = 5; // Nunca se usa, debe desaparecer
b = 10;
c = b + 2;
result1 = c;

// 3. Cálculos Repetidos (CSE)
t1 = d + e;
t2 = d + e; // Redundante, t2 debe asignarse a t1
result2 = t1;

// 4. Asignaciones innecesarias
temp = m; // Se sobreescribe luego luego, debe desaparecer
temp = n; 
result3 = temp;