from tkinter import *
from tkinter import ttk

# Configuração da Janela Principal
janela = Tk()
janela.geometry("900x420")
janela.title("Controle de Faca e Contra-Facas")
janela.configure(bg="white")

# Definição de Cores Baseadas na Imagem
COR_AZUL_TOPO = "#5b9bd5"
COR_AZUL_LATERAL = "#5b9bd5"
COR_BOTAO_LATERAL = "#d9e1f2"
COR_CADASTRAR = "#bdd7ee"
COR_EDITAR = "#ffc000"
COR_EXCLUIR = "#ff0000"

# --- 1. FRAME SUPERIOR (TÍTULO) ---
frame_topo = Frame(janela, bg=COR_AZUL_TOPO, height=70, bd=1, relief="solid")
frame_topo.pack(side=TOP, fill=X)
frame_topo.pack_propagate(False)

label_titulo = Label(
    frame_topo, 
    text="Controle de faca e contra facas", 
    bg=COR_AZUL_TOPO, 
    font=("Arial", 18)
)
label_titulo.pack(expand=True)


# --- CONTAINER PRINCIPAL (ABAIXO DO TÍTULO) ---
container = Frame(janela, bg="white")
container.pack(side=TOP, fill=BOTH, expand=True)


# --- 2. FRAME MENU LATERAL ---
frame_lateral = Frame(container, bg=COR_AZUL_LATERAL, width=160, bd=1, relief="solid")
frame_lateral.pack(side=LEFT, fill=Y)
frame_lateral.pack_propagate(False)

# Botões do Menu Lateral
botoes_menu = ["Facas", "Contra-Facas", "Retifica", "Slitter", "Sair"]
for nome_botao in botoes_menu:
    btn = Button(
        frame_lateral, 
        text=nome_botao, 
        bg=COR_BOTAO_LATERAL, 
        font=("Arial", 10),
        width=14, 
        relief="raised", 
        bd=2
    )
    btn.pack(pady=12, padx=15)
    
    # Fecha o programa se clicar em Sair
    if nome_botao == "Sair":
        btn.configure(command=janela.quit)


# --- 3. ÁREA DE CONTEÚDO (DIREITA) ---
frame_conteudo = Frame(container, bg="white", bd=1, relief="solid")
frame_conteudo.pack(side=LEFT, fill=BOTH, expand=True)

# Grid configurada para distribuir as colunas igualmente
for i in range(6):
    frame_conteudo.grid_columnconfigure(i, weight=1, minsize=110)


# --- Bloco A: Formulário de Cadastro ---
colunas_cadastro = ["Diametro", "quantidade", "Retificadas", "Slitter", "Retifica"]

# Gerar Labels e Inputs dinamicamente na primeira e segunda linha do Grid
for idx, nome in enumerate(colunas_cadastro):
    # Label
    lbl = Label(frame_conteudo, text=nome, bg="white", font=("Arial", 9))
    lbl.grid(row=0, column=idx, pady=(15, 2), padx=5, sticky="s")
    
    # Entry (Campo de texto)
    entry = Entry(frame_conteudo, width=10, justify="center", bd=1, relief="solid")
    entry.grid(row=1, column=idx, pady=(0, 15), padx=5)

# Botão Cadastrar à direita do formulário
btn_cadastrar = Button(
    frame_conteudo, 
    text="cadastrar", 
    bg=COR_CADASTRAR, 
    font=("Arial", 10),
    bd=1, 
    relief="solid", 
    padx=10
)
btn_cadastrar.grid(row=1, column=5, padx=10, pady=(0, 15), sticky="w")


# Linha divisória horizontal para separar o cadastro dos dados simulando a tabela da imagem
divisor = Frame(frame_conteudo, height=1, bg="black")
divisor.grid(row=2, column=0, columnspan=6, sticky="we")



# --- Bloco B: Visualização dos Dados (Tabela) ---
# Replicando os nomes na linha da tabela conforme a imagem
for idx, nome in enumerate(colunas_cadastro):
    lbl_tab = Label(frame_conteudo, text=nome, bg="white", font=("Arial", 9), fg="gray20")
    lbl_tab.grid(row=3, column=idx, pady=(10, 5), padx=5)

# Dados da linha de exemplo da imagem
dados_exemplo = ["240", "60", "sim", "sim", "não"]

for idx, valor in enumerate(dados_exemplo):
    lbl_val = Label(frame_conteudo, text=valor, bg="white", font=("Arial", 10))
    lbl_val.grid(row=4, column=idx, pady=5, padx=5)

# Container para agrupar os botões de Ação na última coluna
frame_acoes = Frame(frame_conteudo, bg="white")
frame_acoes.grid(row=4, column=5, padx=5, pady=5, sticky="w")

btn_editar = Button(
    frame_acoes, 
    text="editar", 
    bg=COR_EDITAR, 
    font=("Arial", 9), 
    bd=1, 
    relief="solid"
)
btn_editar.pack(side=LEFT, padx=2)

btn_excluir = Button(
    frame_acoes, 
    text="Excluir", 
    bg=COR_EXCLUIR, 
    fg="white", 
    font=("Arial", 9), 
    bd=1, 
    relief="solid"
)
btn_excluir.pack(side=LEFT, padx=2)


janela.mainloop()

