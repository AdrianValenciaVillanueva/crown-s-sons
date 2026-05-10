// 1. Código Inalcanzable (Salto incondicional)
x = 10;
goto L2;
y = 20;
L2:
// 2. Variables No Utilizadas
a = 5; 
b = 10;
c = b + 2;
result1 = c;

// 3. Cálculos Repetidos (CSE)
t1 = d + e;
t2 = d + e; 
result2 = t1;

// 4. Asignaciones innecesarias
temp = m; 
temp = n; 
result3 = temp;