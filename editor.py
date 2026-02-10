import os
import tkinter.filedialog as fd
import tkinter.messagebox as mb
import customtkinter as ctk
import lexer 

# Configuración visual (opcional)
ctk.set_appearance_mode("Dark")  
ctk.set_default_color_theme("blue")

class SimpleEditor(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title('Compilador C++ - Analizador Léxico')
        self.geometry('1000x700')
        self._file_path = None

        # Configuración de la rejilla principal
        self.grid_rowconfigure(0, weight=3) # El editor ocupa más espacio
        self.grid_rowconfigure(1, weight=1) # La consola ocupa menos
        self.grid_columnconfigure(0, weight=1)

        # --- ÁREA DE CÓDIGO (EDITOR) ---
        # Usamos CTkTextbox que ya trae scrollbar y estilos modernos
        self.text = ctk.CTkTextbox(self, wrap='none', font=("Consolas", 14), undo=True)
        self.text.grid(row=0, column=0, sticky='nsew', padx=10, pady=(10, 5))

        # --- ÁREA DE SALIDA (TOKENS) ---
        self.output = ctk.CTkTextbox(self, height=150, wrap='word', font=("Consolas", 12))
        self.output.grid(row=1, column=0, sticky='nsew', padx=10, pady=(5, 10))
        
        #Color de fondo diferente para diferenciar la consola (simulado)
        self.output.configure(fg_color="#1e1e1e", text_color="#00ff00") # Texto verde tipo hacker
        self.output.insert("0.0", "--- Esperando análisis (Presiona Ctrl+T) ---\n")
        self.output.configure(state="disabled") # Bloqueamos escritura manual en la consola

        #Menu Superior
        import tkinter as tk
        menubar = tk.Menu(self)
        
        #Menú Archivo
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label='Nuevo', command=self.new_file, accelerator='Ctrl+N')
        file_menu.add_command(label='Abrir...', command=self.open_file, accelerator='Ctrl+O')
        file_menu.add_command(label='Guardar', command=self.save_file, accelerator='Ctrl+S')
        file_menu.add_command(label='Guardar Como...', command=self.save_file_as)
        file_menu.add_separator()
        file_menu.add_command(label='Salir', command=self.quit)
        menubar.add_cascade(label='Archivo', menu=file_menu)

        #Menú Compilar
        run_menu = tk.Menu(menubar, tearoff=0)
        run_menu.add_command(label='Analizar Lexer', command=self.analyze_syntax, accelerator='Ctrl+T')
        menubar.add_cascade(label='Compilar', menu=run_menu)

        self.config(menu=menubar)

        #Atajos de teclado
        self.bind('<Control-n>', lambda e: self.new_file())
        self.bind('<Control-o>', lambda e: self.open_file())
        self.bind('<Control-s>', lambda e: self.save_file())
        self.bind('<Control-t>', lambda e: self.analyze_syntax())

    def _append_output(self, text: str):
        self.output.configure(state="normal") # Habilitar para escribir
        self.output.insert('end', text + '\n')
        self.output.see('end') # Auto-scroll al final
        self.output.configure(state="disabled") # Volver a bloquear

    def analyze_syntax(self):
        """Tokeniza el código y muestra resultados."""
        # Limpiar consola
        self.output.configure(state="normal")
        self.output.delete('0.0', 'end')
        self.output.configure(state="disabled")

        # Obtener texto del editor
        code = self.text.get('0.0', 'end')
        
        try:
            tokens = lexer.tokenize(code)
            
            self._append_output(f"{'TIPO':<15} {'VALOR':<25} {'POSICIÓN'}")
            self._append_output("-" * 60)
            
            if not tokens:
                self._append_output('No se encontraron tokens.')
                return
            
            for t in tokens:
                #Como definimos la dataclass en lexer, podemos acceder directo a los atributos
                val_str = repr(t.value)
                #Recortar si el valor es muy largo para que no rompa la tabla visual
                if len(val_str) > 22: val_str = val_str[:22] + "..."
                
                self._append_output(f"{t.type:<15} {val_str:<25} {t.span}")
                
        except Exception as e:
            self._append_output(f'Error Fatal: {e}')

    def new_file(self):
        if self._maybe_save():
            self.text.delete('0.0', 'end')
            self._file_path = None
            self.title('Compilador C++ - Sin Título')

    def open_file(self):
        if not self._maybe_save():
            return
        #Filtro para archivos C++ y todos los archivos
        path = fd.askopenfilename(filetypes=[('C++ Source', '*.cpp *.h'), ('Todos', '*.*')])
        if path:
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    data = f.read()
                self.text.delete('0.0', 'end')
                self.text.insert('0.0', data)
                self._file_path = path
                self.title(f'Compilador C++ - {os.path.basename(path)}')
            except Exception as e:
                mb.showerror('Error', str(e))

    def save_file(self):
        if self._file_path:
            try:
                with open(self._file_path, 'w', encoding='utf-8') as f:
                    f.write(self.text.get('0.0', 'end'))
            except Exception as e:
                mb.showerror('Error', str(e))
        else:
            self.save_file_as()

    def save_file_as(self):
        # CORREGIDO: Extensión por defecto .cpp
        path = fd.asksaveasfilename(defaultextension='.cpp', 
                                  filetypes=[('C++ Source', '*.cpp *.h'), ('Todos', '*.*')])
        if path:
            try:
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(self.text.get('0.0', 'end'))
                self._file_path = path
                self.title(f'Compilador C++ - {os.path.basename(path)}')
            except Exception as e:
                mb.showerror('Error', str(e))

    def _maybe_save(self):
        return True 

def main():
    app = SimpleEditor()
    app.mainloop()

if __name__ == '__main__':
    main()