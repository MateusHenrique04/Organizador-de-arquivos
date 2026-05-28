# Prompt Estruturado — Organizador Inteligente de Arquivos

## Papel
Você é um desenvolvedor Python especialista em interfaces gráficas com CustomTkinter.
Crie um programa desktop completo de organização de arquivos seguindo rigorosamente as especificações abaixo.

---

## Objetivo
Criar um aplicativo com interface gráfica que organize arquivos de uma pasta em subpastas por categoria, com suporte a pré-visualização, log de operações, regras personalizáveis e desfazer.

---

## Stack obrigatória
- **Python 3.10+**
- **CustomTkinter 5.2.2** — toda a interface deve usar exclusivamente componentes CTk
- **Bibliotecas padrão apenas:** `os`, `shutil`, `re`, `json`, `datetime`
- `tkinter.filedialog` e `tkinter.messagebox` são permitidos como suporte
- Nenhuma dependência externa além do CustomTkinter

---

## Estrutura do programa

### Arquivos gerados em tempo de execução
| Arquivo | Conteúdo |
|---|---|
| `categorias.json` | Regras de categoria personalizadas pelo usuário |
| `log_operacoes.json` | Histórico das últimas 50 organizações |
| `historico_desfazer.json` | Mapa das movimentações da última organização |

---

## Funcionalidades obrigatórias

### 1. Organização de arquivos
- Percorrer todos os arquivos (não subpastas) da pasta selecionada
- Mover cada arquivo para uma subpasta com o nome da sua categoria
- Ignorar arquivos sem extensão
- Normalizar nomes: remover números, espaços, hífens e underscores do início do nome
- Evitar sobrescrever arquivos: se o nome já existir no destino, adicionar sufixo ` (1)`, ` (2)`, etc.
- Criar a subpasta de destino caso não exista

### 2. Categorias padrão
Usar exatamente este mapeamento inicial:
```
Imagens:     .jpg .jpeg .png .gif .bmp .svg .webp
PDFs:        .pdf
Vídeos:      .mp4 .mkv .avi .mov .wmv .flv
Documentos:  .doc .docx .txt .rtf .odt
Planilhas:   .xls .xlsx .csv .ods
Compactados: .zip .rar .7z .tar .gz
Músicas:     .mp3 .wav .flac .aac .ogg
```
Arquivos com extensão não mapeada vão para a pasta `Outros`.

### 3. Pré-visualização (dry run)
- Analisar a pasta sem mover nenhum arquivo
- Exibir uma janela modal (`CTkToplevel`) com tabela rolável contendo:
  - Nome original do arquivo
  - Categoria de destino
  - Nome final (após normalização e resolução de conflitos)
- Dois botões: **Confirmar e Organizar** e **Cancelar**
- Ao confirmar, executar a organização normalmente

### 4. Log de operações
- Após cada organização, registrar em `log_operacoes.json`:
  - Data e hora (`dd/mm/yyyy HH:MM:SS`)
  - Caminho da pasta
  - Número de arquivos movidos
  - Número de categorias utilizadas
  - Número de erros
- Manter apenas as 50 entradas mais recentes (mais nova primeiro)
- Janela modal com tabela rolável exibindo o histórico completo

### 5. Regras personalizadas de categoria
- Janela modal com dois painéis:
  - **Esquerdo:** lista de categorias (botões clicáveis)
  - **Direito:** campo de texto com as extensões da categoria selecionada, separadas por vírgula
- Ações disponíveis:
  - Editar extensões de uma categoria existente
  - Adicionar nova categoria (campo + botão)
  - Remover categoria selecionada (com confirmação)
  - Salvar tudo (persiste em `categorias.json` e atualiza o estado em memória)
- Extensões devem ser normalizadas para minúsculas e prefixadas com ponto automaticamente

### 6. Desfazer última operação
- Após cada organização, salvar em `historico_desfazer.json`:
  - Caminho da pasta original
  - Data e hora da operação
  - Lista de movimentações: `[{origem, destino}]`
- Ao desfazer:
  - Mover cada arquivo de volta ao caminho original
  - Remover pastas de categoria que ficarem vazias
  - Apagar `historico_desfazer.json` após concluir
- O botão de desfazer deve exibir a data da última operação quando disponível
- O botão deve ficar desabilitado quando não há operação para desfazer
- Exibir janela de confirmação antes de executar

---

## Interface principal (janela única, não redimensionável, 460×380 px)

### Componentes em ordem vertical:
1. **Título** — `"📁 Organizador Inteligente"` — fonte 22px bold
2. **Subtítulo** — `"Organize sua pasta em segundos, com segurança."` — fonte 13px
3. **Linha de pasta** — label com nome da pasta selecionada (truncado) + botão `"📂 Selecionar pasta"`
4. **Botão Pré-visualizar** — desabilitado até pasta ser selecionada — altura 42px
5. **Botão Organizar agora** — verde (`#2a7a2a`) — desabilitado até pasta ser selecionada — altura 42px
6. **Linha de ações secundárias** — três botões lado a lado:
   - `"↩ Desfazer última operação"` — laranja escuro (`#8b4a00`) — desabilitado sem histórico
   - `"📋 Log"` — largura fixa 70px
   - `"⚙ Categorias"` — largura fixa 110px

### Comportamento dos botões:
- **Organizar agora** muda texto para `"Organizando…"` e desabilita ambos os botões de ação durante a execução
- Após organizar, exibir `messagebox.showinfo` com resumo ou `showwarning` se houver erros
- O botão Desfazer deve se atualizar automaticamente após cada organização e após desfazer

---

## Janelas modais — requisitos visuais

- Todas devem usar `self.grab_set()` para comportamento modal
- Linhas alternadas na tabela devem usar cores distintas para claro/escuro:
  - Par: `("gray85", "gray20")`
  - Ímpar: `("gray90", "gray17")`
- Botões destrutivos (remover, cancelar) em vermelho escuro `#8b1a1a`
- Botões de confirmação em verde escuro `#2a7a2a`

---

## Organização do código

Separar em seções claramente comentadas:
1. Configuração do CustomTkinter e constantes
2. Persistência de categorias (`carregar_categorias`, `salvar_categorias`)
3. Funções auxiliares (`normatizar_nome`, `obter_categoria`, `gerar_nome_unico`)
4. Pré-visualização (`pre_visualizar`)
5. Organização efetiva (`organizar_pasta`)
6. Log (`registrar_log`)
7. Desfazer (`salvar_historico_desfazer`, `carregar_historico_desfazer`, `desfazer_organizacao`)
8. Classes de janelas modais (`JanelaPreview`, `JanelaLog`, `JanelaCategorias`)
9. Classe principal `OrganizadorApp(ctk.CTk)`
10. Bloco `if __name__ == "__main__"`

---

## Restrições
- Não usar `ttk`, `tk.Frame`, `tk.Button` ou qualquer widget Tk nativo (exceto `filedialog` e `messagebox`)
- Não usar threads — a operação de organização roda na thread principal
- Não usar banco de dados — toda persistência é em JSON
- O programa deve funcionar sem conexão com internet
- Arquivo único (`organizador.py`) — sem módulos externos ao arquivo