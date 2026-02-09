# test_lexer.py
# Script simple para probar lexer.tokenize leyendo un archivo y mostrando tokens
import sys
import lexer

def main(path: str):
    with open(path, 'r', encoding='utf-8') as f:
        src = f.read()
    tokens = lexer.tokenize(src)
    for t in tokens:
        print(f'{t.type:10} {repr(t.value):30} {t.span}')

if __name__ == '__main__':
    path = sys.argv[1] if len(sys.argv) > 1 else 'example.cpp'
    main(path)
