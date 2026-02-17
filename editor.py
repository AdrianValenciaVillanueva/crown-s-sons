import os
import tkinter.filedialog as fd
import tkinter.messagebox as mb
import customtkinter as ctk
import lexer 

class SimpleEditor(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title('Compilador C++ - Analizador Léxico')
        self.geometry('1000x700')
        self._file_path = None

        # Configuración de la rejilla
        self.grid_rowconfigure(0, weight=3)
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # --- ÁREA DE CÓDIGO ---
        self.text = ctk.CTkTextbox(self, wrap='none', font=("Consolas", 14), undo=True)
        self.text.grid(row=0, column=0, sticky='nsew', padx=10, pady=(10, 5))

        # TERMINAL
        self.output = ctk.CTkTextbox(self, height=150, wrap='word', font=("Consolas", 12))
        self.output.grid(row=1, column=0, sticky='nsew', padx=10, pady=(5, 10))
        
        # Estilos de la consola
        self.output.configure(fg_color="#1e1e1e", text_color="#00ff00") 
        
        # Configuramos un "tag" llamado 'error_style' con color rojo para los errores
        self.output.tag_config("error_style", foreground="#FF5555") 
        
        self.output.insert("0.0", "--- Esperando análisis (Presiona Ctrl+T) ---\n")
        self.output.configure(state="disabled")

        # MENÚ SUPERIOR 
        import tkinter as tk
        menubar = tk.Menu(self)
        
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label='Nuevo', command=self.new_file, accelerator='Ctrl+N')
        file_menu.add_command(label='Abrir...', command=self.open_file, accelerator='Ctrl+O')
        file_menu.add_command(label='Guardar', command=self.save_file, accelerator='Ctrl+S')
        file_menu.add_command(label='Guardar Como...', command=self.save_file_as)
        file_menu.add_separator()
        file_menu.add_command(label='Salir', command=self.quit)
        menubar.add_cascade(label='Archivo', menu=file_menu)

        run_menu = tk.Menu(menubar, tearoff=0)
        run_menu.add_command(label='Analizar Lexer', command=self.analyze_syntax, accelerator='Ctrl+T')
        menubar.add_cascade(label='Compilar', menu=run_menu)

        self.config(menu=menubar)

        # Atajos
        self.bind('<Control-n>', lambda e: self.new_file())
        self.bind('<Control-o>', lambda e: self.open_file())
        self.bind('<Control-s>', lambda e: self.save_file())
        self.bind('<Control-t>', lambda e: self.analyze_syntax())

    def _append_output(self, text: str, tags=None):
        """Función auxiliar para escribir en la consola con o sin tags."""
        self.output.configure(state="normal")
       
        self.output.insert('end', text + '\n', tags)
        self.output.see('end')
        self.output.configure(state="disabled")

    def analyze_syntax(self):
        """Tokeniza el código y muestra resultados coloreados."""
        self.output.configure(state="normal")
        self.output.delete('0.0', 'end')
        self.output.configure(state="disabled")

        code = self.text.get('0.0', 'end')
        
        try:
            tokens = lexer.tokenize(code)
            
            # Encabezado
            header = f"{'LÍN:COL':<10} | {'TIPO':<15} | {'VALOR':<25} | {'DESC/ERROR'}"
            self._append_output(header)
            self._append_output("-" * 85)
            
            if not tokens:
                self._append_output('No se encontraron tokens.')
                return
            
            error_count = 0

            for t in tokens:
                pos_str = f"{t.line}:{t.column}"
                val_str = repr(t.value)
                if len(val_str) > 22: val_str = val_str[:22] + "..."
                
                if t.type == 'ERROR':
                    error_count += 1
                    row_str = f"{pos_str:<10} | {'ERROR':<15} | {val_str:<25} | {t.error}"
                    # Llamamos a append pasando el tag "error_style"
                    self._append_output(row_str, "error_style")
                else:
                    row_str = f"{pos_str:<10} | {t.type:<15} | {val_str:<25} |"
                    self._append_output(row_str)
            
            self._append_output("-" * 85)
            
            # Resumen final
            if error_count > 0:
                self._append_output(f"\n[!] SE ENCONTRARON {error_count} ERRORES LÉXICOS.", "error_style")
            else:
                self._append_output(f"\n[OK] ARRE CERO ERRORES.")

        except Exception as e:
            self._append_output(f'Error Fatal: {e}', "error_style")

    # --- MÉTODOS DE ARCHIVO (Igual que antes, sin cambios) ---
    def new_file(self):
        if self._maybe_save():
            self.text.delete('0.0', 'end')
            self._file_path = None
            self.title('Compilador C++ - Sin Título')

    def open_file(self):
        if not self._maybe_save(): return
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
        path = fd.asksaveasfilename(defaultextension='.cpp', filetypes=[('C++ Source', '*.cpp *.h'), ('Todos', '*.*')])
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