# Proyecto: Mini-lexer + Editor

Requisitos
- Python 3.10+ (se desarrolló con 3.10 en un virtualenv dentro del workspace).
- En Windows, PowerShell es el shell usado en los ejemplos.

Instalación (recomendado: virtualenv)
1. Crear y activar un entorno virtual (si aún no lo tienes):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Instalar dependencias:

```powershell
pip install -r requirements.txt
```

Uso

- Ejecutar el editor GUI:

```powershell
C:/workspace/.venv/Scripts/python.exe c:\workspace\editor.py
# o
python c:\workspace\editor.py
```

- Probar el lexer desde la línea de comandos (muestra tokens para `example.cpp` o para el archivo que indiques):

```powershell
python c:\workspace\test_lexer.py            # usa example.cpp por defecto
python c:\workspace\test_lexer.py ruta\a\tu\archivo.cpp
```

