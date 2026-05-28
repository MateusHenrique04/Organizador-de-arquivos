import os
import shutil
import re
import json
import datetime
import customtkinter as ctk
from tkinter import filedialog, messagebox

# ─── Configuração do CustomTkinter ───────────────────────────────────────────
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

# ─── Arquivos de dados ────────────────────────────────────────────────────────
ARQUIVO_CATEGORIAS  = "categorias.json"
ARQUIVO_LOG         = "log_operacoes.json"
ARQUIVO_HISTORICO   = "historico_desfazer.json"

# ─── Categorias padrão ───────────────────────────────────────────────────────
CATEGORIAS_PADRAO = {
    "Imagens":     [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg", ".webp"],
    "PDFs":        [".pdf"],
    "Vídeos":      [".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv"],
    "Documentos":  [".doc", ".docx", ".txt", ".rtf", ".odt"],
    "Planilhas":   [".xls", ".xlsx", ".csv", ".ods"],
    "Compactados": [".zip", ".rar", ".7z", ".tar", ".gz"],
    "Músicas":     [".mp3", ".wav", ".flac", ".aac", ".ogg"],
}

# ─── Persistência de categorias ───────────────────────────────────────────────
def carregar_categorias():
    """Carrega categorias do arquivo JSON, ou usa o padrão."""
    if os.path.exists(ARQUIVO_CATEGORIAS):
        try:
            with open(ARQUIVO_CATEGORIAS, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return dict(CATEGORIAS_PADRAO)

def salvar_categorias(categorias):
    """Salva as categorias no arquivo JSON."""
    with open(ARQUIVO_CATEGORIAS, "w", encoding="utf-8") as f:
        json.dump(categorias, f, ensure_ascii=False, indent=2)

# ─── Funções auxiliares ───────────────────────────────────────────────────────
def normatizar_nome(nome_arquivo):
    """Remove números e caracteres especiais do início do nome."""
    nome_base, extensao = os.path.splitext(nome_arquivo)
    novo_nome_base = re.sub(r'^[\d\s\-_]+', '', nome_base)
    return f"{novo_nome_base}{extensao}" if novo_nome_base else nome_arquivo

def obter_categoria(extensao, categorias):
    """Retorna a categoria da extensão, ou 'Outros'."""
    for categoria, extensoes in categorias.items():
        if extensao.lower() in extensoes:
            return categoria
    return "Outros"

def gerar_nome_unico(caminho_destino, nome_arquivo):
    """Gera nome único para evitar sobrescrever arquivos."""
    nome_base, extensao = os.path.splitext(nome_arquivo)
    contador = 1
    novo_nome = nome_arquivo
    while os.path.exists(os.path.join(caminho_destino, novo_nome)):
        novo_nome = f"{nome_base} ({contador}){extensao}"
        contador += 1
    return novo_nome

# ─── Pré-visualização ─────────────────────────────────────────────────────────
def pre_visualizar(caminho_pasta, categorias):
    """
    Analisa a pasta sem mover nada.
    Retorna lista de dicts: {arquivo, categoria, nome_final}
    """
    preview = []
    try:
        itens = os.listdir(caminho_pasta)
    except Exception as e:
        return None, str(e)

    for item in itens:
        caminho_completo = os.path.join(caminho_pasta, item)
        if os.path.isdir(caminho_completo):
            continue
        _, extensao = os.path.splitext(item)
        if not extensao:
            continue

        categoria = obter_categoria(extensao, categorias)
        caminho_categoria = os.path.join(caminho_pasta, categoria)
        nome_processado = normatizar_nome(item)
        nome_final = gerar_nome_unico(caminho_categoria, nome_processado)

        preview.append({
            "arquivo":    item,
            "categoria":  categoria,
            "nome_final": nome_final,
        })

    return preview, None

# ─── Organização efetiva ──────────────────────────────────────────────────────
def organizar_pasta(caminho_pasta, categorias):
    """
    Move os arquivos para suas categorias.
    Retorna dict com resultados e lista de movimentações para desfazer.
    """
    arquivos_movidos = 0
    erros = 0
    categorias_usadas = set()
    movimentacoes = []   # [{origem, destino}] — para desfazer

    try:
        itens = os.listdir(caminho_pasta)
    except Exception as e:
        return {"sucesso": False, "mensagem": str(e)}, []

    for item in itens:
        caminho_completo = os.path.join(caminho_pasta, item)
        if os.path.isdir(caminho_completo):
            continue
        _, extensao = os.path.splitext(item)
        if not extensao:
            continue

        categoria = obter_categoria(extensao, categorias)
        caminho_categoria = os.path.join(caminho_pasta, categoria)

        try:
            if not os.path.exists(caminho_categoria):
                os.makedirs(caminho_categoria)
            categorias_usadas.add(categoria)

            nome_processado = normatizar_nome(item)
            nome_final = gerar_nome_unico(caminho_categoria, nome_processado)
            destino = os.path.join(caminho_categoria, nome_final)

            shutil.move(caminho_completo, destino)
            movimentacoes.append({"origem": caminho_completo, "destino": destino})
            arquivos_movidos += 1

        except Exception as e:
            print(f"Erro ao mover {item}: {e}")
            erros += 1

    return {
        "sucesso":    True,
        "movidos":    arquivos_movidos,
        "categorias": len(categorias_usadas),
        "erros":      erros,
    }, movimentacoes

# ─── Log de operações ─────────────────────────────────────────────────────────
def registrar_log(pasta, resultado, movimentacoes):
    """Salva o resultado de uma operação no arquivo de log."""
    log = []
    if os.path.exists(ARQUIVO_LOG):
        try:
            with open(ARQUIVO_LOG, "r", encoding="utf-8") as f:
                log = json.load(f)
        except Exception:
            pass

    entrada = {
        "data":       datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        "pasta":      pasta,
        "movidos":    resultado.get("movidos", 0),
        "categorias": resultado.get("categorias", 0),
        "erros":      resultado.get("erros", 0),
    }
    log.insert(0, entrada)
    log = log[:50]   # mantém só as 50 últimas

    with open(ARQUIVO_LOG, "w", encoding="utf-8") as f:
        json.dump(log, f, ensure_ascii=False, indent=2)

# ─── Desfazer ─────────────────────────────────────────────────────────────────
def salvar_historico_desfazer(pasta, movimentacoes):
    """Salva as movimentações para permitir desfazer."""
    historico = {
        "pasta":          pasta,
        "data":           datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        "movimentacoes":  movimentacoes,
    }
    with open(ARQUIVO_HISTORICO, "w", encoding="utf-8") as f:
        json.dump(historico, f, ensure_ascii=False, indent=2)

def carregar_historico_desfazer():
    """Carrega o histórico de desfazer, se existir."""
    if os.path.exists(ARQUIVO_HISTORICO):
        try:
            with open(ARQUIVO_HISTORICO, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return None

def desfazer_organizacao():
    """
    Reverte a última organização:
    move arquivos de volta e remove pastas vazias.
    """
    historico = carregar_historico_desfazer()
    if not historico:
        return {"sucesso": False, "mensagem": "Nenhuma operação para desfazer."}

    erros = 0
    revertidos = 0

    for mov in reversed(historico["movimentacoes"]):
        origem_original = mov["origem"]
        destino_atual   = mov["destino"]

        if not os.path.exists(destino_atual):
            continue

        pasta_origem = os.path.dirname(origem_original)
        try:
            if not os.path.exists(pasta_origem):
                os.makedirs(pasta_origem)
            shutil.move(destino_atual, origem_original)
            revertidos += 1

            # Remove a pasta de categoria se ficar vazia
            pasta_categoria = os.path.dirname(destino_atual)
            if os.path.isdir(pasta_categoria) and not os.listdir(pasta_categoria):
                os.rmdir(pasta_categoria)

        except Exception as e:
            print(f"Erro ao desfazer: {e}")
            erros += 1

    # Apaga o histórico após desfazer
    if os.path.exists(ARQUIVO_HISTORICO):
        os.remove(ARQUIVO_HISTORICO)

    return {"sucesso": True, "revertidos": revertidos, "erros": erros}


# ═════════════════════════════════════════════════════════════════════════════
#  JANELAS AUXILIARES
# ═════════════════════════════════════════════════════════════════════════════

class JanelaPreview(ctk.CTkToplevel):
    """Janela de pré-visualização das movimentações."""

    def __init__(self, master, preview, callback_confirmar):
        super().__init__(master)
        self.title("Pré-visualização")
        self.geometry("600x450")
        self.resizable(True, True)
        self.grab_set()   # modal

        self.callback_confirmar = callback_confirmar

        ctk.CTkLabel(self, text="O que será organizado:",
                     font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(15, 5))

        ctk.CTkLabel(self, text=f"{len(preview)} arquivo(s) serão movidos",
                     font=ctk.CTkFont(size=13)).pack(pady=(0, 10))

        # Tabela scrollável
        frame_tabela = ctk.CTkScrollableFrame(self, height=300)
        frame_tabela.pack(fill="both", expand=True, padx=15, pady=5)

        # Cabeçalho
        for col, texto in enumerate(["Arquivo original", "Categoria", "Nome final"]):
            ctk.CTkLabel(frame_tabela, text=texto,
                         font=ctk.CTkFont(weight="bold"),
                         anchor="w").grid(row=0, column=col, padx=8, pady=4, sticky="w")

        # Linhas
        for i, item in enumerate(preview, start=1):
            bg = ("gray85", "gray20") if i % 2 == 0 else ("gray90", "gray17")
            for col, chave in enumerate(["arquivo", "categoria", "nome_final"]):
                ctk.CTkLabel(frame_tabela, text=item[chave],
                             anchor="w", fg_color=bg, corner_radius=4).grid(
                    row=i, column=col, padx=4, pady=2, sticky="ew")

        frame_tabela.grid_columnconfigure((0, 1, 2), weight=1)

        # Botões
        frame_btns = ctk.CTkFrame(self, fg_color="transparent")
        frame_btns.pack(pady=12)

        ctk.CTkButton(frame_btns, text="✅  Confirmar e Organizar",
                      command=self._confirmar,
                      font=ctk.CTkFont(size=14), height=38,
                      fg_color="#2a7a2a", hover_color="#1e5c1e").pack(side="left", padx=10)

        ctk.CTkButton(frame_btns, text="✖  Cancelar",
                      command=self.destroy,
                      font=ctk.CTkFont(size=14), height=38,
                      fg_color="#8b1a1a", hover_color="#6b1212").pack(side="left", padx=10)

    def _confirmar(self):
        self.destroy()
        self.callback_confirmar()


class JanelaLog(ctk.CTkToplevel):
    """Janela que exibe o histórico de operações."""

    def __init__(self, master):
        super().__init__(master)
        self.title("Log de Operações")
        self.geometry("620x400")
        self.resizable(True, True)
        self.grab_set()

        ctk.CTkLabel(self, text="Histórico de Operações",
                     font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(15, 10))

        log = []
        if os.path.exists(ARQUIVO_LOG):
            try:
                with open(ARQUIVO_LOG, "r", encoding="utf-8") as f:
                    log = json.load(f)
            except Exception:
                pass

        frame = ctk.CTkScrollableFrame(self, height=300)
        frame.pack(fill="both", expand=True, padx=15, pady=5)

        if not log:
            ctk.CTkLabel(frame, text="Nenhuma operação registrada ainda.",
                         font=ctk.CTkFont(size=13)).pack(pady=20)
        else:
            cabecalhos = ["Data/Hora", "Pasta", "Movidos", "Categorias", "Erros"]
            for col, txt in enumerate(cabecalhos):
                ctk.CTkLabel(frame, text=txt,
                             font=ctk.CTkFont(weight="bold"),
                             anchor="w").grid(row=0, column=col, padx=8, pady=4, sticky="w")

            for i, entrada in enumerate(log, start=1):
                bg = ("gray85", "gray20") if i % 2 == 0 else ("gray90", "gray17")
                valores = [
                    entrada.get("data", ""),
                    entrada.get("pasta", "")[-40:],   # trunca caminhos longos
                    str(entrada.get("movidos", 0)),
                    str(entrada.get("categorias", 0)),
                    str(entrada.get("erros", 0)),
                ]
                for col, val in enumerate(valores):
                    ctk.CTkLabel(frame, text=val, anchor="w",
                                 fg_color=bg, corner_radius=4).grid(
                        row=i, column=col, padx=4, pady=2, sticky="ew")

            frame.grid_columnconfigure((0, 1, 2, 3, 4), weight=1)

        ctk.CTkButton(self, text="Fechar", command=self.destroy,
                      font=ctk.CTkFont(size=13), height=34).pack(pady=12)


class JanelaCategorias(ctk.CTkToplevel):
    """Janela para editar as regras de categoria."""

    def __init__(self, master, categorias, callback_salvar):
        super().__init__(master)
        self.title("Regras de Categoria")
        self.geometry("520x520")
        self.resizable(True, True)
        self.grab_set()

        self.categorias      = {k: list(v) for k, v in categorias.items()}
        self.callback_salvar = callback_salvar

        ctk.CTkLabel(self, text="Regras de Categoria",
                     font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(15, 5))
        ctk.CTkLabel(self,
                     text="Selecione uma categoria e edite as extensões (separadas por vírgula)",
                     font=ctk.CTkFont(size=12)).pack(pady=(0, 10))

        # Painel esquerdo — lista de categorias
        frame_main = ctk.CTkFrame(self, fg_color="transparent")
        frame_main.pack(fill="both", expand=True, padx=15, pady=5)

        frame_lista = ctk.CTkFrame(frame_main, width=160)
        frame_lista.pack(side="left", fill="y", padx=(0, 10))
        frame_lista.pack_propagate(False)

        ctk.CTkLabel(frame_lista, text="Categorias",
                     font=ctk.CTkFont(weight="bold")).pack(pady=(8, 4))

        self.lista_categorias = ctk.CTkScrollableFrame(frame_lista)
        self.lista_categorias.pack(fill="both", expand=True, padx=4, pady=4)

        # Painel direito — extensões da categoria selecionada
        frame_dir = ctk.CTkFrame(frame_main)
        frame_dir.pack(side="left", fill="both", expand=True)

        ctk.CTkLabel(frame_dir, text="Extensões:",
                     font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=10, pady=(10, 2))

        self.txt_extensoes = ctk.CTkTextbox(frame_dir, height=120)
        self.txt_extensoes.pack(fill="x", padx=10, pady=4)

        ctk.CTkButton(frame_dir, text="Salvar extensões desta categoria",
                      command=self._salvar_extensoes_categoria,
                      height=32).pack(padx=10, pady=(4, 10))

        # Adicionar nova categoria
        ctk.CTkLabel(frame_dir, text="Nova categoria:",
                     font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=10)

        frame_nova = ctk.CTkFrame(frame_dir, fg_color="transparent")
        frame_nova.pack(fill="x", padx=10, pady=4)

        self.entry_nova = ctk.CTkEntry(frame_nova, placeholder_text="Ex: Fontes")
        self.entry_nova.pack(side="left", fill="x", expand=True, padx=(0, 6))

        ctk.CTkButton(frame_nova, text="➕ Adicionar", width=110,
                      command=self._adicionar_categoria).pack(side="left")

        # Remover categoria selecionada
        ctk.CTkButton(frame_dir, text="🗑  Remover categoria selecionada",
                      fg_color="#8b1a1a", hover_color="#6b1212",
                      command=self._remover_categoria, height=32).pack(padx=10, pady=4)

        # Botões finais
        frame_btns = ctk.CTkFrame(self, fg_color="transparent")
        frame_btns.pack(pady=10)

        ctk.CTkButton(frame_btns, text="💾  Salvar tudo",
                      command=self._salvar_tudo,
                      fg_color="#2a7a2a", hover_color="#1e5c1e",
                      height=36).pack(side="left", padx=8)

        ctk.CTkButton(frame_btns, text="Cancelar",
                      command=self.destroy, height=36).pack(side="left", padx=8)

        self.categoria_selecionada = None
        self._atualizar_lista()

    def _atualizar_lista(self):
        for widget in self.lista_categorias.winfo_children():
            widget.destroy()
        for cat in self.categorias:
            btn = ctk.CTkButton(self.lista_categorias, text=cat,
                                anchor="w", height=30,
                                command=lambda c=cat: self._selecionar(c))
            btn.pack(fill="x", pady=2)

    def _selecionar(self, categoria):
        self.categoria_selecionada = categoria
        exts = ", ".join(self.categorias[categoria])
        self.txt_extensoes.delete("1.0", "end")
        self.txt_extensoes.insert("1.0", exts)

    def _salvar_extensoes_categoria(self):
        if not self.categoria_selecionada:
            messagebox.showwarning("Aviso", "Selecione uma categoria primeiro.", parent=self)
            return
        texto = self.txt_extensoes.get("1.0", "end").strip()
        exts = [e.strip().lower() for e in texto.split(",") if e.strip()]
        # Garante que todas começam com ponto
        exts = [e if e.startswith(".") else f".{e}" for e in exts]
        self.categorias[self.categoria_selecionada] = exts
        messagebox.showinfo("Salvo", f"Extensões de '{self.categoria_selecionada}' atualizadas.", parent=self)

    def _adicionar_categoria(self):
        nome = self.entry_nova.get().strip()
        if not nome:
            return
        if nome in self.categorias:
            messagebox.showwarning("Aviso", "Categoria já existe.", parent=self)
            return
        self.categorias[nome] = []
        self.entry_nova.delete(0, "end")
        self._atualizar_lista()
        self._selecionar(nome)

    def _remover_categoria(self):
        if not self.categoria_selecionada:
            messagebox.showwarning("Aviso", "Selecione uma categoria primeiro.", parent=self)
            return
        if messagebox.askyesno("Confirmar",
                               f"Remover a categoria '{self.categoria_selecionada}'?",
                               parent=self):
            del self.categorias[self.categoria_selecionada]
            self.categoria_selecionada = None
            self.txt_extensoes.delete("1.0", "end")
            self._atualizar_lista()

    def _salvar_tudo(self):
        self.callback_salvar(self.categorias)
        messagebox.showinfo("Sucesso", "Categorias salvas com sucesso!", parent=self)
        self.destroy()


# ═════════════════════════════════════════════════════════════════════════════
#  JANELA PRINCIPAL
# ═════════════════════════════════════════════════════════════════════════════

class OrganizadorApp(ctk.CTk):

    def __init__(self):
        super().__init__()

        self.title("Organizador Inteligente")
        self.geometry("460x380")
        self.resizable(False, False)

        self.categorias        = carregar_categorias()
        self.pasta_selecionada = None

        # ── Título ────────────────────────────────────────────────────────────
        ctk.CTkLabel(self, text="📁  Organizador Inteligente",
                     font=ctk.CTkFont(size=22, weight="bold")).pack(pady=(22, 4))

        ctk.CTkLabel(self,
                     text="Organize sua pasta em segundos, com segurança.",
                     font=ctk.CTkFont(size=13)).pack(pady=(0, 16))

        # ── Seleção de pasta ──────────────────────────────────────────────────
        frame_pasta = ctk.CTkFrame(self, fg_color="transparent")
        frame_pasta.pack(fill="x", padx=30, pady=4)

        self.lbl_pasta = ctk.CTkLabel(frame_pasta,
                                      text="Nenhuma pasta selecionada",
                                      font=ctk.CTkFont(size=12),
                                      text_color="gray",
                                      anchor="w")
        self.lbl_pasta.pack(side="left", fill="x", expand=True)

        ctk.CTkButton(frame_pasta, text="📂  Selecionar pasta",
                      command=self._selecionar_pasta,
                      height=34, width=160).pack(side="right")

        # ── Botões principais ─────────────────────────────────────────────────
        frame_acoes = ctk.CTkFrame(self, fg_color="transparent")
        frame_acoes.pack(fill="x", padx=30, pady=14)

        self.btn_preview = ctk.CTkButton(
            frame_acoes,
            text="🔍  Pré-visualizar",
            command=self._abrir_preview,
            height=42, font=ctk.CTkFont(size=14),
            state="disabled"
        )
        self.btn_preview.pack(fill="x", pady=4)

        self.btn_organizar = ctk.CTkButton(
            frame_acoes,
            text="⚡  Organizar agora",
            command=self._organizar,
            height=42, font=ctk.CTkFont(size=14),
            fg_color="#2a7a2a", hover_color="#1e5c1e",
            state="disabled"
        )
        self.btn_organizar.pack(fill="x", pady=4)

        # ── Botões secundários ────────────────────────────────────────────────
        frame_sec = ctk.CTkFrame(self, fg_color="transparent")
        frame_sec.pack(fill="x", padx=30, pady=4)

        self.btn_desfazer = ctk.CTkButton(
            frame_sec,
            text="↩  Desfazer última operação",
            command=self._desfazer,
            height=34, font=ctk.CTkFont(size=13),
            fg_color="#8b4a00", hover_color="#6b3800",
        )
        self.btn_desfazer.pack(side="left", expand=True, fill="x", padx=(0, 5))

        ctk.CTkButton(
            frame_sec,
            text="📋  Log",
            command=self._abrir_log,
            height=34, font=ctk.CTkFont(size=13),
            width=70,
        ).pack(side="left", padx=(0, 5))

        ctk.CTkButton(
            frame_sec,
            text="⚙  Categorias",
            command=self._abrir_categorias,
            height=34, font=ctk.CTkFont(size=13),
            width=110,
        ).pack(side="left")

        # Status de desfazer
        self._atualizar_status_desfazer()

    # ── Helpers de UI ─────────────────────────────────────────────────────────

    def _selecionar_pasta(self):
        pasta = filedialog.askdirectory(title="Selecione a pasta para organizar")
        if not pasta:
            return
        self.pasta_selecionada = pasta
        nome_curto = os.path.basename(pasta) or pasta
        self.lbl_pasta.configure(text=nome_curto, text_color=("black", "white"))
        self.btn_preview.configure(state="normal")
        self.btn_organizar.configure(state="normal")

    def _atualizar_status_desfazer(self):
        historico = carregar_historico_desfazer()
        if historico:
            data = historico.get("data", "")
            self.btn_desfazer.configure(
                text=f"↩  Desfazer  ({data})",
                state="normal"
            )
        else:
            self.btn_desfazer.configure(
                text="↩  Desfazer última operação",
                state="disabled"
            )

    # ── Pré-visualização ──────────────────────────────────────────────────────

    def _abrir_preview(self):
        if not self.pasta_selecionada:
            return
        preview, erro = pre_visualizar(self.pasta_selecionada, self.categorias)
        if erro:
            messagebox.showerror("Erro", erro)
            return
        if not preview:
            messagebox.showinfo("Vazio", "Nenhum arquivo encontrado para organizar.")
            return
        JanelaPreview(self, preview, self._organizar)

    # ── Organizar ─────────────────────────────────────────────────────────────

    def _organizar(self):
        if not self.pasta_selecionada:
            return

        self.btn_organizar.configure(state="disabled", text="Organizando…")
        self.btn_preview.configure(state="disabled")
        self.update()

        resultado, movimentacoes = organizar_pasta(self.pasta_selecionada, self.categorias)

        self.btn_organizar.configure(state="normal", text="⚡  Organizar agora")
        self.btn_preview.configure(state="normal")

        if resultado["sucesso"]:
            registrar_log(self.pasta_selecionada, resultado, movimentacoes)
            if movimentacoes:
                salvar_historico_desfazer(self.pasta_selecionada, movimentacoes)
            self._atualizar_status_desfazer()

            msg = (
                f"Organização concluída!\n\n"
                f"Arquivos organizados: {resultado['movidos']}\n"
                f"Categorias utilizadas: {resultado['categorias']}\n"
                f"Erros encontrados: {resultado['erros']}"
            )
            if resultado["erros"] > 0:
                messagebox.showwarning("Concluído com avisos", msg)
            else:
                messagebox.showinfo("Sucesso", msg)
        else:
            messagebox.showerror("Erro", resultado["mensagem"])

    # ── Desfazer ──────────────────────────────────────────────────────────────

    def _desfazer(self):
        historico = carregar_historico_desfazer()
        if not historico:
            messagebox.showinfo("Desfazer", "Nenhuma operação para desfazer.")
            return

        confirmado = messagebox.askyesno(
            "Confirmar",
            f"Desfazer a organização feita em:\n{historico['data']}\n\n"
            f"Pasta: {historico['pasta']}\n\n"
            f"{len(historico['movimentacoes'])} arquivo(s) serão movidos de volta."
        )
        if not confirmado:
            return

        resultado = desfazer_organizacao()
        self._atualizar_status_desfazer()

        if resultado["sucesso"]:
            messagebox.showinfo(
                "Desfazer",
                f"Operação desfeita!\n\n"
                f"Arquivos revertidos: {resultado['revertidos']}\n"
                f"Erros: {resultado['erros']}"
            )
        else:
            messagebox.showerror("Erro", resultado["mensagem"])

    # ── Log ───────────────────────────────────────────────────────────────────

    def _abrir_log(self):
        JanelaLog(self)

    # ── Categorias ────────────────────────────────────────────────────────────

    def _abrir_categorias(self):
        def salvar(novas):
            self.categorias = novas
            salvar_categorias(novas)
        JanelaCategorias(self, self.categorias, salvar)


if __name__ == "__main__":
    app = OrganizadorApp()
    app.mainloop()