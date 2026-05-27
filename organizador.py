import os
import shutil
import customtkinter as ctk
from tkinter import filedialog, messagebox

# Configuração inicial do CustomTkinter (Aparência e Tema)
ctk.set_appearance_mode("System")  # Segue o tema do sistema (Dark/Light)
ctk.set_default_color_theme("blue")  # Tema de cores dos botões

# Dicionário que mapeia as extensões de arquivos para suas respectivas categorias
CATEGORIAS = {
    "Imagens": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg", ".webp"],
    "PDFs": [".pdf"],
    "Vídeos": [".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv"],
    "Documentos": [".doc", ".docx", ".txt", ".rtf", ".odt"],
    "Planilhas": [".xls", ".xlsx", ".csv", ".ods"],
    "Compactados": [".zip", ".rar", ".7z", ".tar", ".gz"],
    "Músicas": [".mp3", ".wav", ".flac", ".aac", ".ogg"]
}

def obter_categoria(extensao):
    """
    Verifica a qual categoria a extensão do arquivo pertence.
    Retorna o nome da categoria ou 'Outros' caso não encontre.
    """
    for categoria, extensoes in CATEGORIAS.items():
        if extensao.lower() in extensoes:
            return categoria
    return "Outros"

def gerar_nome_unico(caminho_destino, nome_arquivo):
    """
    Gera um nome de arquivo único para evitar sobrescrever arquivos existentes.
    Se o arquivo 'foto.jpg' já existir, ele tenta 'foto (1).jpg', 'foto (2).jpg', etc.
    """
    nome_base, extensao = os.path.splitext(nome_arquivo)
    contador = 1
    novo_nome = nome_arquivo
    
    # Enquanto existir um arquivo com o novo nome no destino, incrementa o contador
    while os.path.exists(os.path.join(caminho_destino, novo_nome)):
        novo_nome = f"{nome_base} ({contador}){extensao}"
        contador += 1
        
    return novo_nome

def organizar_pasta(caminho_pasta):
    """
    Lógica principal para organizar os arquivos da pasta escolhida.
    Retorna um dicionário com os resultados (sucesso, erros, contagens).
    """
    arquivos_movidos = 0
    erros = 0
    categorias_criadas = set() # Usamos set para não contar categorias duplicadas
    
    # Lista todos os itens na pasta
    try:
        itens = os.listdir(caminho_pasta)
    except Exception as e:
        return {"sucesso": False, "mensagem": f"Erro ao acessar a pasta: {str(e)}"}

    for item in itens:
        caminho_completo = os.path.join(caminho_pasta, item)
        
        # Ignora pastas, organiza apenas arquivos
        if os.path.isdir(caminho_completo):
            continue
            
        # Pega a extensão do arquivo
        _, extensao = os.path.splitext(item)
        
        # Se o arquivo não tiver extensão e for um arquivo oculto de sistema, pode pular
        if not extensao:
            continue
            
        categoria = obter_categoria(extensao)
        caminho_categoria = os.path.join(caminho_pasta, categoria)
        
        try:
            # Se a pasta da categoria não existir, cria
            if not os.path.exists(caminho_categoria):
                os.makedirs(caminho_categoria)
                categorias_criadas.add(categoria)
            else:
                # Se já existia, mas precisamos contabilizar que essa categoria foi usada/criada no passado
                # podemos ou não adicionar ao set. Vamos adicionar para mostrar quantas categorias foram afetadas.
                categorias_criadas.add(categoria)
                
            # Trata arquivos com nomes repetidos
            nome_final = gerar_nome_unico(caminho_categoria, item)
            caminho_destino = os.path.join(caminho_categoria, nome_final)
            
            # Move o arquivo
            shutil.move(caminho_completo, caminho_destino)
            arquivos_movidos += 1
            
        except Exception as e:
            print(f"Erro ao mover o arquivo {item}: {e}")
            erros += 1

    return {
        "sucesso": True,
        "movidos": arquivos_movidos,
        "categorias": len(categorias_criadas),
        "erros": erros
    }

class OrganizadorApp(ctk.CTk):
    """
    Classe principal da Interface Gráfica usando CustomTkinter.
    """
    def __init__(self):
        super().__init__()

        self.title("Organizador Inteligente")
        self.geometry("400x250")
        self.resizable(False, False)

        # Rótulo de Título
        self.lbl_titulo = ctk.CTkLabel(
            self, 
            text="Organizador de Arquivos", 
            font=ctk.CTkFont(size=20, weight="bold")
        )
        self.lbl_titulo.pack(pady=(20, 10))

        # Descrição
        self.lbl_descricao = ctk.CTkLabel(
            self, 
            text="Selecione uma pasta para organizar\nautomaticamente seus arquivos.", 
            font=ctk.CTkFont(size=14)
        )
        self.lbl_descricao.pack(pady=(0, 20))

        # Botão para Selecionar Pasta
        self.btn_selecionar = ctk.CTkButton(
            self, 
            text="Escolher Pasta e Organizar", 
            command=self.iniciar_organizacao,
            font=ctk.CTkFont(size=15),
            height=40
        )
        self.btn_selecionar.pack(pady=10)

    def iniciar_organizacao(self):
        """
        Abre o diálogo para escolha da pasta e inicia o processo.
        """
        pasta_selecionada = filedialog.askdirectory(title="Selecione a pasta para organizar")
        
        # Se o usuário cancelar a seleção, apenas retorna
        if not pasta_selecionada:
            return
            
        # Desabilita o botão enquanto organiza para evitar cliques duplos
        self.btn_selecionar.configure(state="disabled", text="Organizando...")
        self.update() # Atualiza a interface
        
        # Chama a função de organização
        resultado = organizar_pasta(pasta_selecionada)
        
        # Restaura o botão
        self.btn_selecionar.configure(state="normal", text="Escolher Pasta e Organizar")
        
        # Exibe as mensagens de resultado
        if resultado["sucesso"]:
            msg = (
                f"Organização concluída!\n\n"
                f"Arquivos organizados: {resultado['movidos']}\n"
                f"Categorias utilizadas: {resultado['categorias']}\n"
                f"Erros encontrados: {resultado['erros']}"
            )
            # Usa messagebox do tkinter padrão, pois ctk não tem messagebox nativo ainda
            if resultado["erros"] > 0:
                messagebox.showwarning("Concluído com avisos", msg)
            else:
                messagebox.showinfo("Sucesso", msg)
        else:
            messagebox.showerror("Erro", resultado["mensagem"])

if __name__ == "__main__":
    # Inicia o aplicativo
    app = OrganizadorApp()
    app.mainloop()
