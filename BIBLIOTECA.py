import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import os
import json
import shutil
import ttkbootstrap as ttk
from dataclasses import dataclass
from typing import List, Optional
import logging

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='biblioteca_jogos.log'
)

# Constantes
class Config:
    SAVE_FILE = "biblioteca_jogos.json"
    IMAGE_FOLDER = "capas"
    CATEGORIES_FILE = "categorias.json"
    WINDOW_SIZE = "900x600"
    DEFAULT_CATEGORIES = ["Ação", "RPG", "Estratégia", "Simulação", "Outro"]
    THUMBNAIL_SIZE = (100, 100)
    GRID_COLUMNS = 3

@dataclass
class Jogo:
    nome: str
    caminho: str
    imagem: str
    categoria: str

class BibliotecaJogos:
    def __init__(self):
        self.jogos: List[Jogo] = []
        self.categorias: List[str] = []
        self.setup_folders()
        self.load_data()
        self.setup_ui()

    def setup_folders(self):
        """Cria as pastas necessárias para a aplicação."""
        os.makedirs(Config.IMAGE_FOLDER, exist_ok=True)

    def load_data(self):
        """Carrega os dados dos jogos e categorias."""
        self.jogos = [Jogo(**j) for j in self._load_json(Config.SAVE_FILE, [])]
        self.categorias = self._load_json(Config.CATEGORIES_FILE, Config.DEFAULT_CATEGORIES)

    def _load_json(self, arquivo: str, padrao: any) -> any:
        """Carrega dados de um arquivo JSON."""
        try:
            if os.path.exists(arquivo):
                with open(arquivo, "r", encoding='utf-8') as file:
                    return json.load(file)
        except Exception as e:
            logging.error(f"Erro ao carregar {arquivo}: {e}")
        return padrao

    def save_data(self):
        """Salva os dados dos jogos e categorias."""
        self._save_json(Config.SAVE_FILE, [vars(j) for j in self.jogos])

    def _save_json(self, arquivo: str, dados: any):
        """Salva dados em um arquivo JSON."""
        try:
            with open(arquivo, "w", encoding='utf-8') as file:
                json.dump(dados, file, ensure_ascii=False, indent=2)
        except Exception as e:
            logging.error(f"Erro ao salvar {arquivo}: {e}")
            messagebox.showerror("Erro", f"Não foi possível salvar os dados: {e}")

    def setup_ui(self):
        """Configura a interface do usuário."""
        self.window = ttk.Window(themename="darkly")
        self.window.title("Biblioteca de Jogos")
        self.window.geometry(Config.WINDOW_SIZE)
        self.window.resizable(False, False)

        self._create_top_frame()
        self._create_games_frame()
        self.update_interface()

    def _create_top_frame(self):
        """Cria o frame superior com controles."""
        frame = ttk.Frame(self.window, padding=10, bootstyle="dark")
        frame.pack(fill="x")

        # Barra de busca
        self.search_entry = ttk.Entry(frame, width=40, bootstyle="dark")
        self.search_entry.pack(side="left", padx=5)
        self.search_entry.bind("<Return>", self.search_games)

        # Filtro de categorias
        self.category_filter = ttk.Combobox(
            frame,
            values=["Todas"] + self.categorias,
            bootstyle="dark",
            state="readonly"
        )
        self.category_filter.set("Todas")
        self.category_filter.pack(side="left", padx=5)
        self.category_filter.bind("<<ComboboxSelected>>", self.search_games)

        # Botões
        ttk.Button(frame, text="Buscar", command=self.search_games,
                  bootstyle="primary", width=10).pack(side="left", padx=5)
        ttk.Button(frame, text="Adicionar Jogo", command=self.show_add_game_dialog,
                  bootstyle="success-outline", width=15).pack(side="right", padx=5)
        ttk.Button(frame, text="Criar Categoria", command=self.show_add_category_dialog,
                  bootstyle="info-outline", width=15).pack(side="right", padx=5)

        ttk.Separator(self.window, orient="horizontal").pack(fill="x", pady=5)

    def _create_games_frame(self):
        """Cria o frame que contém a grade de jogos."""
        self.games_frame = ttk.Frame(self.window, padding=10, bootstyle="dark")
        self.games_frame.pack(fill="both", expand=True)

    def update_interface(self, categoria: Optional[str] = None, busca: str = ""):
        """Atualiza a interface com os jogos filtrados."""
        for widget in self.games_frame.winfo_children():
            widget.destroy()

        jogos_filtrados = self.filter_games(categoria, busca)
        
        if not jogos_filtrados:
            ttk.Label(self.games_frame, text="Nenhum jogo encontrado.",
                     bootstyle="light", font=("Helvetica", 12)).pack(pady=10)
            return

        self._create_game_grid(jogos_filtrados)

    def filter_games(self, categoria: Optional[str], busca: str) -> List[Jogo]:
        """Filtra os jogos por categoria e termo de busca."""
        return [
            jogo for jogo in self.jogos
            if (not categoria or categoria == "Todas" or jogo.categoria == categoria)
            and (busca.lower() in jogo.nome.lower())
        ]

    def _create_game_grid(self, jogos: List[Jogo]):
        """Cria a grade de jogos."""
        for idx, jogo in enumerate(jogos):
            frame = ttk.Frame(self.games_frame, padding=10, bootstyle="secondary")
            frame.grid(
                row=idx // Config.GRID_COLUMNS,
                column=idx % Config.GRID_COLUMNS,
                padx=10, pady=10
            )

            self._add_game_thumbnail(frame, jogo)
            ttk.Label(frame, text=jogo.nome, bootstyle="light",
                     font=("Helvetica", 10)).pack()
            ttk.Label(frame, text=f"Categoria: {jogo.categoria}",
                     bootstyle="light", font=("Helvetica", 10)).pack()
            
            ttk.Button(frame, text="Abrir",
                      command=lambda j=jogo: self.open_game(j),
                      bootstyle="primary", width=10).pack()
            ttk.Button(frame, text="Remover",
                      command=lambda j=jogo: self.remove_game(j),
                      bootstyle="danger", width=10).pack()

    def _add_game_thumbnail(self, frame: ttk.Frame, jogo: Jogo):
        """Adiciona a thumbnail do jogo ao frame."""
        try:
            if os.path.exists(jogo.imagem):
                image = Image.open(jogo.imagem).resize(Config.THUMBNAIL_SIZE)
                photo = ImageTk.PhotoImage(image)
                label = ttk.Label(frame, image=photo, bootstyle="secondary")
                label.image = photo  # Mantém uma referência
                label.pack()
        except Exception as e:
            logging.error(f"Erro ao carregar imagem do jogo {jogo.nome}: {e}")

    def show_add_game_dialog(self):
        """Mostra o diálogo para adicionar um novo jogo."""
        dialog = AddGameDialog(self.window, self)
        self.window.wait_window(dialog)

    def show_add_category_dialog(self):
        """Mostra o diálogo para adicionar uma nova categoria."""
        dialog = AddCategoryDialog(self.window, self)
        self.window.wait_window(dialog)

    def add_game(self, nome: str, caminho: str, imagem: str, categoria: str):
        """Adiciona um novo jogo à biblioteca."""
        try:
            nova_imagem = os.path.join(Config.IMAGE_FOLDER, f"{nome}.png")
            shutil.copy(imagem, nova_imagem)
            
            novo_jogo = Jogo(nome=nome, caminho=caminho,
                           imagem=nova_imagem, categoria=categoria)
            self.jogos.append(novo_jogo)
            self.save_data()
            self.update_interface()
            
        except Exception as e:
            logging.error(f"Erro ao adicionar jogo: {e}")
            messagebox.showerror("Erro", str(e))

    def remove_game(self, jogo: Jogo):
        """Remove um jogo da biblioteca."""
        if messagebox.askyesno("Remover Jogo",
                             f"Tem certeza que deseja remover '{jogo.nome}'?"):
            try:
                if os.path.exists(jogo.imagem):
                    os.remove(jogo.imagem)
                self.jogos.remove(jogo)
                self.save_data()
                self.update_interface()
            except Exception as e:
                logging.error(f"Erro ao remover jogo: {e}")
                messagebox.showerror("Erro", str(e))

    def open_game(self, jogo: Jogo):
        """Abre um jogo."""
        try:
            if os.path.exists(jogo.caminho):
                os.startfile(jogo.caminho)
            else:
                raise FileNotFoundError("Caminho do jogo não encontrado")
        except Exception as e:
            logging.error(f"Erro ao abrir jogo {jogo.nome}: {e}")
            messagebox.showerror("Erro", "Não foi possível abrir o jogo!")

    def search_games(self, event=None):
        """Realiza a busca de jogos."""
        busca = self.search_entry.get()
        categoria = self.category_filter.get()
        self.update_interface(categoria, busca)

class AddGameDialog(tk.Toplevel):
    def __init__(self, parent, biblioteca):
        super().__init__(parent)
        self.biblioteca = biblioteca
        self.setup_dialog()

    def setup_dialog(self):
        self.title("Adicionar Jogo")
        self.geometry("500x500")
        self.configure(bg="#2c2c34")
        self.resizable(False, False)

        # Campos do formulário
        self.nome = self._add_entry_field("Nome:")
        self.caminho = self._add_entry_field("Caminho do Executável ou Atalho:")
        ttk.Button(self, text="Selecionar Caminho",
                  command=self._select_path,
                  bootstyle="primary", width=20).pack(pady=5)

        self.imagem = self._add_entry_field("Imagem de Capa:")
        ttk.Button(self, text="Selecionar Imagem",
                  command=self._select_image,
                  bootstyle="primary", width=20).pack(pady=5)

        ttk.Label(self, text="Categoria:", bootstyle="light",
                 font=("Helvetica", 12)).pack(pady=5)
        self.categoria = ttk.Combobox(self, values=self.biblioteca.categorias,
                                    bootstyle="dark", font=("Helvetica", 10))
        self.categoria.pack(pady=5)

        ttk.Button(self, text="Salvar",
                  command=self._save_game,
                  bootstyle="success", width=15).pack(pady=15)

    def _add_entry_field(self, label: str) -> ttk.Entry:
        ttk.Label(self, text=label, bootstyle="light",
                 font=("Helvetica", 12)).pack(pady=5)
        entry = ttk.Entry(self, bootstyle="dark", font=("Helvetica", 10))
        entry.pack(pady=5)
        return entry

    def _select_path(self):
        path = filedialog.askopenfilename(
            title="Selecione o executável ou atalho do jogo",
            filetypes=[("Executáveis e Atalhos", "*.exe;*.lnk;*.url")]
        )
        if path:
            self.caminho.delete(0, tk.END)
            self.caminho.insert(0, path)

    def _select_image(self):
        path = filedialog.askopenfilename(
            title="Selecione a imagem de capa",
            filetypes=[("Imagens", "*.png;*.jpg;*.jpeg")]
        )
        if path:
            self.imagem.delete(0, tk.END)
            self.imagem.insert(0, path)

    def _save_game(self):
        """Salva um novo jogo."""
        nome = self.nome.get()
        caminho = self.caminho.get()
        imagem = self.imagem.get()
        categoria = self.categoria.get()

        if not all([nome, caminho, imagem, categoria]):
            messagebox.showerror("Erro", "Preencha todos os campos!")
            return

        if not os.path.isfile(caminho):
            messagebox.showerror("Erro", "Caminho do executável ou atalho inválido!")
            return

        self.biblioteca.add_game(nome, caminho, imagem, categoria)
        self.destroy()

class AddCategoryDialog(tk.Toplevel):
    def __init__(self, parent, biblioteca):
        super().__init__(parent)
        self.biblioteca = biblioteca
        self.setup_dialog()

    def setup_dialog(self):
        self.title("Criar Categoria")
        self.geometry("300x150")
        self.configure(bg="#2c2c34")
        self.resizable(False, False)

        ttk.Label(self, text="Nova Categoria:", bootstyle="light",
                 font=("Helvetica", 12)).pack(pady=10)
        self.categoria = ttk.Entry(self, bootstyle="dark", font=("Helvetica", 10))
        self.categoria.pack(pady=5)

        ttk.Button(self, text="Salvar",
                  command=self._save_category,
                  bootstyle="success", width=15).pack(pady=15)

    def _save_category(self):
        """Salva uma nova categoria."""
        nova_categoria = self.categoria.get()

        if not nova_categoria:
            messagebox.showerror("Erro", "Digite o nome da categoria!")
            return
            
        if nova_categoria in self.biblioteca.categorias:
            messagebox.showwarning("Atenção", "Essa categoria já existe!")
            return
            
        try:
            self.biblioteca.categorias.append(nova_categoria)
            self.biblioteca._save_json(Config.CATEGORIES_FILE, self.biblioteca.categorias)
            self.biblioteca.category_filter["values"] = ["Todas"] + self.biblioteca.categorias
            self.destroy()
        except Exception as e:
            logging.error(f"Erro ao salvar categoria: {e}")
            messagebox.showerror("Erro", f"Não foi possível salvar a categoria: {e}")

def main():
    """Função principal que inicia a aplicação."""
    try:
        app = BibliotecaJogos()
        app.window.mainloop()
    except Exception as e:
        logging.critical(f"Erro fatal na aplicação: {e}")
        messagebox.showerror("Erro Fatal", 
            "Ocorreu um erro fatal na aplicação. Verifique os logs para mais detalhes.")

if __name__ == "__main__":
    main()