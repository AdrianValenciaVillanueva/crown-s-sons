import os
import tkinter.filedialog as fd
import tkinter.messagebox as mb

import customtkinter as ctk
import lexer


class SimpleEditor(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title('Simple Editor')
        self.geometry('900x600')
        self._file_path = None

        # Main frames
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Text widget for code (use native Text inside a CTkFrame)
        frame = ctk.CTkFrame(self)
        frame.grid(row=0, column=0, sticky='nsew', padx=8, pady=8)
        frame.grid_rowconfigure(0, weight=1)
        frame.grid_columnconfigure(0, weight=1)

        import tkinter as tk

        self.text = tk.Text(frame, wrap='none', undo=True)
        self.text.grid(row=0, column=0, sticky='nsew')

        #terminal
        # Output area: muestra tokens del lexer
        self.output = tk.Text(frame, height=10, wrap='word', bg='#111111', fg='#dcdcdc')
        self.output.grid(row=1, column=0, sticky='nsew', pady=(8, 0))

        # Asegúrate de que el frame tenga dos filas configuradas para que el editor y la salida se redimensionen
        frame.grid_rowconfigure(0, weight=3)   # editor (texto)
        frame.grid_rowconfigure(1, weight=1)   # salida (tokens)
        # Menubar (tk menu works with CTk)
        menubar = tk.Menu(self)
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label='New', command=self.new_file, accelerator='Ctrl+N')
        file_menu.add_command(label='Open...', command=self.open_file, accelerator='Ctrl+O')
        file_menu.add_command(label='Save', command=self.save_file, accelerator='Ctrl+S')
        file_menu.add_command(label='Save As...', command=self.save_file_as)
        menubar.add_cascade(label='File', menu=file_menu)

        # Run menu present but disabled while Run feature is under development
        run_menu = tk.Menu(menubar, tearoff=0)
        run_menu.add_command(label='Run', command=self.run_stub, accelerator='F5', state='disabled')
        menubar.add_cascade(label='Run', menu=run_menu)

        # Atajo de teclado
        self.bind_all('<Control-t>', lambda e: self.analyze_syntax())

        self.config(menu=menubar)

        # Bindings
        self.bind_all('<Control-n>', lambda e: self.new_file())
        self.bind_all('<Control-o>', lambda e: self.open_file())
        self.bind_all('<Control-s>', lambda e: self.save_file())

    def _append_output(self, text: str):
        """Append a line to the output panel."""
        # Crear la salida si por alguna razón no existe
        if not hasattr(self, 'output') or self.output is None:
            return
        self.output.insert('end', text + '\n')
        self.output.see('end')

    def analyze_syntax(self):
        """Tokeniza el buffer actual usando lexer.tokenize y muestra los tokens en la salida."""
        # Limpia la salida
        if hasattr(self, 'output'):
            self.output.delete('1.0', 'end')

        code = self.text.get('1.0', 'end')
        try:
            tokens = lexer.tokenize(code)
            if not tokens:
                self._append_output('No tokens produced')
                return
            for t in tokens:
                # t tiene .type, .value, .span
                typ = getattr(t, 'type', '?')
                val = getattr(t, 'value', '')
                span = getattr(t, 'span', None)
                self._append_output(f"{typ:10} {repr(val):30} {span}")
        except Exception as e:
            self._append_output(f'Lexer error: {e}')

    def new_file(self):
        if self._maybe_save():
            self.text.delete('1.0', 'end')
            self._file_path = None
            self.title('Simple Editor - Untitled')

    def open_file(self):
        if not self._maybe_save():
            return
        path = fd.askopenfilename(filetypes=[('Python', '*.py'), ('All files', '*.*')])
        if path:
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    data = f.read()
                self.text.delete('1.0', 'end')
                self.text.insert('1.0', data)
                self._file_path = path
                self.title(f'Simple Editor - {os.path.basename(path)}')
            except Exception as e:
                mb.showerror('Open file', str(e))

    def save_file(self):
        if self._file_path:
            try:
                with open(self._file_path, 'w', encoding='utf-8') as f:
                    f.write(self.text.get('1.0', 'end'))
            except Exception as e:
                mb.showerror('Save file', str(e))
        else:
            self.save_file_as()

    def save_file_as(self):
        path = fd.asksaveasfilename(defaultextension='.py', filetypes=[('Python', '*.py'), ('All files', '*.*')])
        if path:
            try:
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(self.text.get('1.0', 'end'))
                self._file_path = path
                self.title(f'Simple Editor - {os.path.basename(path)}')
            except Exception as e:
                mb.showerror('Save file', str(e))

    def run_stub(self):
        # Run is intentionally disabled while C/C++ support is being developed.
        # This method is a no-op placeholder so the menu entry can exist.
        return

    def _maybe_save(self):
        if self.text.edit_modified():
            resp = mb.askyesnocancel('Save', 'Save changes?')
            if resp is None:
                return False
            if resp:
                self.save_file()
        return True
    


def main():
    app = SimpleEditor()
    app.mainloop()


if __name__ == '__main__':
    main()
