import os
import shutil
import sqlite3
import sys
from contextlib import contextmanager
from decimal import Decimal, InvalidOperation
from tkinter import *
from tkinter import messagebox

# Configuração da Janela Principal
janela = Tk()
janela.geometry("950x450")
janela.title("Controle de Faca e Contra-Facas")
janela.configure(bg="white")

# Paleta de Cores Baseada nas Imagens
COR_AZUL_TOPO = "#5b9bd5"
COR_AZUL_LATERAL = "#5b9bd5"
COR_BOTAO_LATERAL = "#d9e1f2"
COR_BOTAO_ATIVO = "#ffffff"  # Cor para destacar qual botão está clicado
COR_CADASTRAR = "#bdd7ee"
COR_EDITAR = "#ffc000"
COR_EXCLUIR = "#ff0000"

# O executável guarda o banco em uma pasta persistente, fora do arquivo temporário do PyInstaller.
if getattr(sys, "frozen", False):
    diretorio_dados = os.path.join(
        os.environ.get("LOCALAPPDATA", os.path.expanduser("~")),
        "ControleFacas",
    )
    os.makedirs(diretorio_dados, exist_ok=True)
    DB_PATH = os.path.join(diretorio_dados, "controle_facas.db")
    banco_inicial = os.path.join(getattr(sys, "_MEIPASS", os.path.dirname(sys.executable)), "controle_facas.db")
    if not os.path.exists(DB_PATH) and os.path.isfile(banco_inicial):
        shutil.copy2(banco_inicial, DB_PATH)
else:
    DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "controle_facas.db")


@contextmanager
def conectar_db():
    conexao = sqlite3.connect(DB_PATH)
    conexao.row_factory = sqlite3.Row
    try:
        with conexao:
            yield conexao
    finally:
        conexao.close()


def inicializar_db():
    with conectar_db() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS facas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                diametro TEXT NOT NULL,
                quantidade TEXT NOT NULL,
                retificadas TEXT,
                slitter TEXT,
                retifica TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS contra_facas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                largura TEXT NOT NULL,
                quantidade TEXT NOT NULL,
                boas_para_uso TEXT,
                retifica_externa TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS configuracao (
                chave TEXT PRIMARY KEY,
                valor TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS historico (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tabela TEXT NOT NULL,
                acao TEXT NOT NULL,
                registro_id INTEGER,
                detalhes TEXT,
                data_hora TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            "INSERT OR IGNORE INTO configuracao (chave, valor) VALUES ('retifica_aba', 'Facas')"
        )
        conn.execute(
            "INSERT OR IGNORE INTO configuracao (chave, valor) VALUES ('slitter_aba', 'Facas')"
        )


def registrar_historico(conn, tabela, acao, registro_id=None, detalhes=""):
    conn.execute(
        "INSERT INTO historico (tabela, acao, registro_id, detalhes) VALUES (?, ?, ?, ?)",
        (tabela, acao, registro_id, detalhes),
    )


def carregar_dados_do_banco():
    global dados_sistema
    with conectar_db() as conn:
        facas = conn.execute(
            "SELECT id, diametro, quantidade, retificadas, slitter, retifica FROM facas ORDER BY id"
        ).fetchall()
        contra_facas = conn.execute(
            "SELECT id, largura, quantidade, boas_para_uso, retifica_externa FROM contra_facas ORDER BY id"
        ).fetchall()
        retifica_aba = conn.execute(
            "SELECT valor FROM configuracao WHERE chave = 'retifica_aba'"
        ).fetchone()
        slitter_aba = conn.execute(
            "SELECT valor FROM configuracao WHERE chave = 'slitter_aba'"
        ).fetchone()

    dados_sistema = {
        "Facas": [
            {
                "id": item["id"],
                "Diametro": item["diametro"],
                "quantidade": item["quantidade"],
                "Retificadas": item["retificadas"],
                "Slitter": item["slitter"],
                "Retifica": item["retifica"],
            }
            for item in facas
        ],
        "Contra-Facas": [
            {
                "id": item["id"],
                "Largura": item["largura"],
                "quantidade": item["quantidade"],
                "Boas para uso": item["boas_para_uso"],
                "Retifica externa": item["retifica_externa"],
            }
            for item in contra_facas
        ],
        "Retifica": {"aba_atual": (retifica_aba["valor"] if retifica_aba else "Facas")},
        "Slitter": {"aba_atual": (slitter_aba["valor"] if slitter_aba else "Facas")},
    }


def salvar_configuracao(chave, valor):
    with conectar_db() as conn:
        conn.execute(
            "INSERT INTO configuracao (chave, valor) VALUES (?, ?) ON CONFLICT(chave) DO UPDATE SET valor = excluded.valor",
            (chave, valor),
        )


def inserir_registro_faca(novo_registro):
    with conectar_db() as conn:
        cursor = conn.execute(
            "INSERT INTO facas (diametro, quantidade, retificadas, slitter, retifica) VALUES (?, ?, ?, ?, ?)",
            (
                novo_registro["Diametro"],
                novo_registro["quantidade"],
                novo_registro["Retificadas"],
                novo_registro["Slitter"],
                novo_registro["Retifica"],
            ),
        )
        registrar_historico(
            conn,
            "facas",
            "INSERT",
            cursor.lastrowid,
            f"Diametro={novo_registro['Diametro']}; Quantidade={novo_registro['quantidade']}",
        )


def atualizar_registro_faca(registro_id, novo_registro):
    with conectar_db() as conn:
        conn.execute(
            "UPDATE facas SET diametro = ?, quantidade = ?, retificadas = ?, slitter = ?, retifica = ? WHERE id = ?",
            (
                novo_registro["Diametro"],
                novo_registro["quantidade"],
                novo_registro["Retificadas"],
                novo_registro["Slitter"],
                novo_registro["Retifica"],
                registro_id,
            ),
        )
        registrar_historico(
            conn,
            "facas",
            "UPDATE",
            registro_id,
            f"Diametro={novo_registro['Diametro']}; Quantidade={novo_registro['quantidade']}",
        )


def inserir_registro_contra_faca(novo_registro):
    with conectar_db() as conn:
        cursor = conn.execute(
            "INSERT INTO contra_facas (largura, quantidade, boas_para_uso, retifica_externa) VALUES (?, ?, ?, ?)",
            (
                novo_registro["Largura"],
                novo_registro["quantidade"],
                novo_registro["Boas para uso"],
                novo_registro["Retifica externa"],
            ),
        )
        registrar_historico(
            conn,
            "contra_facas",
            "INSERT",
            cursor.lastrowid,
            f"Largura={novo_registro['Largura']}; Quantidade={novo_registro['quantidade']}",
        )


def atualizar_registro_contra_faca(registro_id, novo_registro):
    with conectar_db() as conn:
        conn.execute(
            "UPDATE contra_facas SET largura = ?, quantidade = ?, boas_para_uso = ?, retifica_externa = ? WHERE id = ?",
            (
                novo_registro["Largura"],
                novo_registro["quantidade"],
                novo_registro["Boas para uso"],
                novo_registro["Retifica externa"],
                registro_id,
            ),
        )
        registrar_historico(
            conn,
            "contra_facas",
            "UPDATE",
            registro_id,
            f"Largura={novo_registro['Largura']}; Quantidade={novo_registro['quantidade']}",
        )


def converter_decimal(valor):
    try:
        numero = Decimal(str(valor).strip().replace(",", "."))
        return numero if numero.is_finite() else None
    except (InvalidOperation, ValueError):
        return None


def formatar_quantidade(valor):
    if valor == valor.to_integral_value():
        return f"{valor:,.0f}".replace(",", ".")
    return f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def gerar_analise_dashboard(facas, contra_facas):
    def resumir_quantidades(registros):
        total = Decimal("0")
        invalidas = 0
        for registro in registros:
            quantidade = converter_decimal(registro.get("quantidade", ""))
            if quantidade is None:
                invalidas += 1
            else:
                total += quantidade
        return total, invalidas

    def quantidade_com_status(registros, campo):
        selecionados = [
            registro for registro in registros
            if str(registro.get(campo, "")).strip().lower() == "sim"
        ]
        total, _ = resumir_quantidades(selecionados)
        return len(selecionados), total

    total_facas, qtd_facas_invalidas = resumir_quantidades(facas)
    total_contra_facas, qtd_contra_invalidas = resumir_quantidades(contra_facas)

    diametros = {}
    diametros_invalidos = 0
    for faca in facas:
        diametro = converter_decimal(faca.get("Diametro", ""))
        quantidade = converter_decimal(faca.get("quantidade", ""))
        if diametro is None:
            diametros_invalidos += 1
            continue
        chave = f"{diametro:.2f}".replace(".", ",")
        diametros[chave] = diametros.get(chave, Decimal("0")) + (
            quantidade if quantidade is not None else Decimal("0")
        )

    fluxos = [
        ("Facas em retífica", *quantidade_com_status(facas, "Retifica")),
        ("Facas no Slitter", *quantidade_com_status(facas, "Slitter")),
        ("Contra-facas em retífica externa", *quantidade_com_status(contra_facas, "Retifica externa")),
        ("Contra-facas boas para uso", *quantidade_com_status(contra_facas, "Boas para uso")),
    ]

    return {
        "registros_facas": len(facas),
        "quantidade_facas": total_facas,
        "registros_contra_facas": len(contra_facas),
        "quantidade_contra_facas": total_contra_facas,
        "invalidas": qtd_facas_invalidas + qtd_contra_invalidas,
        "diametros_invalidos": diametros_invalidos,
        "diametros": sorted(diametros.items(), key=lambda item: (-item[1], item[0])),
        "fluxos": fluxos,
    }


def buscar_registros(tabela, campo, valor):
    if not valor:
        return []
    campo_mapeado = {
        "Diametro": "diametro",
        "quantidade": "quantidade",
        "Retificadas": "retificadas",
        "Slitter": "slitter",
        "Retifica": "retifica",
        "Largura": "largura",
        "Boas para uso": "boas_para_uso",
        "Retifica externa": "retifica_externa",
    }.get(campo, campo)

    query = f"SELECT * FROM {tabela} WHERE {campo_mapeado} LIKE ? ORDER BY id"
    with conectar_db() as conn:
        return conn.execute(query, (f"%{valor}%",)).fetchall()


def excluir_registro_por_id(tabela, registro_id):
    with conectar_db() as conn:
        conn.execute(f"DELETE FROM {tabela} WHERE id = ?", (registro_id,))
        registrar_historico(conn, tabela, "DELETE", registro_id, "Registro removido")


inicializar_db()
carregar_dados_do_banco()

# Variável global para monitorar se estamos editando um registro existente
index_edicao = None

# ==========================================
# STRUCTURAL LAYOUT (TOPO E MENU LATERAL)
# ==========================================

# 1. Frame Superior (Título)
frame_topo = Frame(janela, bg=COR_AZUL_TOPO, height=70, bd=1, relief="solid")
frame_topo.pack(side=TOP, fill=X)
frame_topo.pack_propagate(False)

label_titulo = Label(frame_topo, text="Controle de faca e contra facas", bg=COR_AZUL_TOPO, font=("Arial", 18))
label_titulo.pack(expand=True)

# Container Principal (Abaixo do Título)
container = Frame(janela, bg="white")
container.pack(side=TOP, fill=BOTH, expand=True)

# 2. Frame Menu Lateral
frame_lateral = Frame(container, bg=COR_AZUL_LATERAL, width=160, bd=1, relief="solid")
frame_lateral.pack(side=LEFT, fill=Y)
frame_lateral.pack_propagate(False)

# 3. Área de Conteúdo Dinâmico (Direita)
frame_conteudo = Frame(container, bg="white", bd=1, relief="solid")
frame_conteudo.pack(side=LEFT, fill=BOTH, expand=True)

# ==========================================
# FUNÇÕES DE LIMPEZA E ESTILIZAÇÃO DO MENU
# ==========================================

def limpar_tela():
    """Remove todos os widgets da área de conteúdo para desenhar a nova tela."""
    global index_edicao
    index_edicao = None  # Cancela qualquer edição pendente ao mudar de tela
    for widget in frame_conteudo.winfo_children():
        widget.destroy()


def limpar_campos_form(dicionario_entries, btn_cadastrar=None, texto_padrao="cadastrar", cor_padrao=COR_CADASTRAR):
    global index_edicao
    index_edicao = None
    for entry in dicionario_entries.values():
        entry.delete(0, END)
    if btn_cadastrar is not None:
        btn_cadastrar.configure(text=texto_padrao, bg=cor_padrao)


def atualizar_botoes_menu(botao_ativo):
    """Muda a cor do botão selecionado no menu lateral para destacar a tela ativa."""
    for nome, btn in botoes_menu_objetos.items():
        if nome == botao_ativo:
            btn.configure(bg=COR_BOTAO_ATIVO, relief="sunken")
        else:
            btn.configure(bg=COR_BOTAO_LATERAL, relief="raised")


def redirecionar_apos_cadastro(tipo_registro, registro):
    """Direciona para a tela correta conforme os campos de retifica/slitter marcados como 'sim'."""
    if tipo_registro == "Facas":
        if str(registro.get("Retificadas", "")).strip().lower() == "sim":
            dados_sistema["Retifica"]["aba_atual"] = "Facas"
            salvar_configuracao("retifica_aba", "Facas")
            mostrar_tela_retifica()
            return
        if str(registro.get("Slitter", "")).strip().lower() == "sim":
            dados_sistema["Slitter"]["aba_atual"] = "Facas"
            salvar_configuracao("slitter_aba", "Facas")
            mostrar_tela_slitter()
            return
        return

    if tipo_registro == "Contra-Facas":
        dados_sistema["Slitter"]["aba_atual"] = "Contra-Facas"
        salvar_configuracao("slitter_aba", "Contra-Facas")
        mostrar_tela_slitter()

# ==========================================
# CRIAÇÃO DAS TELAS DO SISTEMA
# ==========================================

# --- TELA 1: FACAS ---
def mostrar_tela_facas(aba_carregar_edicao=None):
    carregar_dados_do_banco()
    limpar_tela()
    atualizar_botoes_menu("Facas")
    
    colunas = ["Diametro", "quantidade", "Retificadas", "Slitter", "Retifica"]
    
    for i in range(6):
        frame_conteudo.grid_columnconfigure(i, weight=1, minsize=110)
        
    dicionario_entries = {}
    for idx, nome in enumerate(colunas):
        Label(frame_conteudo, text=nome, bg="white", font=("Arial", 9)).grid(row=0, column=idx, pady=(15, 2), sticky="s")
        entry = Entry(frame_conteudo, width=10, justify="center", bd=1, relief="solid")
        entry.grid(row=1, column=idx, pady=(0, 15))
        dicionario_entries[nome] = entry

    btn_cadastrar = Button(frame_conteudo, text="cadastrar", bg=COR_CADASTRAR, font=("Arial", 10), bd=1, relief="solid", padx=10)
    btn_cadastrar.grid(row=1, column=5, padx=10, pady=(0, 15), sticky="w")

    btn_limpar = Button(
        frame_conteudo,
        text="limpar",
        bg="#e2e2e2",
        font=("Arial", 10),
        bd=1,
        relief="solid",
        padx=10,
        command=lambda: limpar_campos_form(dicionario_entries, btn_cadastrar, "cadastrar", COR_CADASTRAR),
    )
    btn_limpar.grid(row=1, column=6, padx=(0, 10), pady=(0, 15), sticky="w")

    Frame(frame_conteudo, height=1, bg="black").grid(row=2, column=0, columnspan=7, sticky="we")

    for idx, nome in enumerate(colunas):
        Label(frame_conteudo, text=nome, bg="white", font=("Arial", 9), fg="gray20").grid(row=3, column=idx, pady=(10, 5))

    def atualizar_tabela_facas():
        carregar_dados_do_banco()
        for widget in frame_conteudo.grid_slaves():
            if int(widget.grid_info()["row"]) >= 4:
                widget.destroy()

        for row_idx, item in enumerate(dados_sistema["Facas"], start=4):
            for col_idx, nome_col in enumerate(colunas):
                Label(frame_conteudo, text=item[nome_col], bg="white", font=("Arial", 10)).grid(row=row_idx, column=col_idx, pady=5)

            frame_acoes = Frame(frame_conteudo, bg="white")
            frame_acoes.grid(row=row_idx, column=5, padx=5, pady=5, sticky="w")

            Button(frame_acoes, text="editar", bg=COR_EDITAR, font=("Arial", 9), bd=1, relief="solid",
                   command=lambda r=row_idx-4: carregar_edicao_faca(r)).pack(side=LEFT, padx=2)
            Button(frame_acoes, text="Excluir", bg=COR_EXCLUIR, fg="white", font=("Arial", 9), bd=1, relief="solid",
                   command=lambda r=row_idx-4: excluir_faca(r)).pack(side=LEFT, padx=2)

    def salvar_faca():
        global index_edicao
        novo_registro = {nome: dicionario_entries[nome].get() for nome in colunas}

        if not novo_registro["Diametro"] or not novo_registro["quantidade"]:
            messagebox.showwarning("Aviso", "Preencha os campos obrigatórios!")
            return

        cadastro_novo = index_edicao is None

        if cadastro_novo:
            inserir_registro_faca(novo_registro)
        else:
            atualizar_registro_faca(index_edicao, novo_registro)
            index_edicao = None

        carregar_dados_do_banco()
        limpar_campos_form(dicionario_entries, btn_cadastrar, "cadastrar", COR_CADASTRAR)
        atualizar_tabela_facas()

        if cadastro_novo:
            redirecionar_apos_cadastro("Facas", novo_registro)

    def carregar_edicao_faca(idx):
        global index_edicao
        registro = dados_sistema["Facas"][idx]
        index_edicao = registro["id"]
        for nome in colunas:
            dicionario_entries[nome].delete(0, END)
            dicionario_entries[nome].insert(0, registro[nome])
        btn_cadastrar.configure(text="salvar", bg=COR_EDITAR)

    def excluir_faca(idx):
        if messagebox.askyesno("Confirmar", "Deseja realmente excluir este registro?"):
            registro_id = dados_sistema["Facas"][idx]["id"]
            excluir_registro_por_id("facas", registro_id)
            carregar_dados_do_banco()
            atualizar_tabela_facas()

    btn_cadastrar.configure(command=salvar_faca)
    atualizar_tabela_facas()

    if aba_carregar_edicao is not None:
        carregar_edicao_faca(aba_carregar_edicao)

# --- TELA 2: CONTRA-FACAS ---
def mostrar_tela_contra_facas(aba_carregar_edicao=None):
    carregar_dados_do_banco()
    limpar_tela()
    atualizar_botoes_menu("Contra-Facas")
    
    colunas = ["Largura", "quantidade", "Boas para uso", "Retifica externa"]
    
    for i in range(5):
        frame_conteudo.grid_columnconfigure(i, weight=1, minsize=130)
        
    dicionario_entries = {}
    for idx, nome in enumerate(colunas):
        Label(frame_conteudo, text=nome, bg="white", font=("Arial", 9)).grid(row=0, column=idx, pady=(15, 2), sticky="s")
        entry = Entry(frame_conteudo, width=10, justify="center", bd=1, relief="solid")
        entry.grid(row=1, column=idx, pady=(0, 15))
        dicionario_entries[nome] = entry

    btn_cadastrar = Button(frame_conteudo, text="cadastrar", bg=COR_CADASTRAR, font=("Arial", 10), bd=1, relief="solid", padx=10)
    btn_cadastrar.grid(row=1, column=4, padx=10, pady=(0, 15), sticky="w")

    btn_limpar = Button(
        frame_conteudo,
        text="limpar",
        bg="#e2e2e2",
        font=("Arial", 10),
        bd=1,
        relief="solid",
        padx=10,
        command=lambda: limpar_campos_form(dicionario_entries, btn_cadastrar, "cadastrar", COR_CADASTRAR),
    )
    btn_limpar.grid(row=1, column=5, padx=(0, 10), pady=(0, 15), sticky="w")

    Frame(frame_conteudo, height=1, bg="black").grid(row=2, column=0, columnspan=6, sticky="we")

    for idx, nome in enumerate(colunas):
        Label(frame_conteudo, text=nome, bg="white", font=("Arial", 9), fg="gray20").grid(row=3, column=idx, pady=(10, 5))

    def atualizar_tabela_contra_facas():
        carregar_dados_do_banco()
        for widget in frame_conteudo.grid_slaves():
            if int(widget.grid_info()["row"]) >= 4:
                widget.destroy()

        for row_idx, item in enumerate(dados_sistema["Contra-Facas"], start=4):
            for col_idx, nome_col in enumerate(colunas):
                Label(frame_conteudo, text=item[nome_col], bg="white", font=("Arial", 10)).grid(row=row_idx, column=col_idx, pady=5)

            frame_acoes = Frame(frame_conteudo, bg="white")
            frame_acoes.grid(row=row_idx, column=4, padx=5, pady=5, sticky="w")

            Button(frame_acoes, text="editar", bg=COR_EDITAR, font=("Arial", 9), bd=1, relief="solid",
                   command=lambda r=row_idx-4: carregar_edicao_cf(r)).pack(side=LEFT, padx=2)
            Button(frame_acoes, text="Excluir", bg=COR_EXCLUIR, fg="white", font=("Arial", 9), bd=1, relief="solid",
                   command=lambda r=row_idx-4: excluir_cf(r)).pack(side=LEFT, padx=2)

    def salvar_contra_faca():
        global index_edicao
        novo_registro = {nome: dicionario_entries[nome].get() for nome in colunas}

        if not novo_registro["Largura"] or not novo_registro["quantidade"]:
            messagebox.showwarning("Aviso", "Preencha os campos obrigatórios!")
            return

        cadastro_novo = index_edicao is None

        if cadastro_novo:
            inserir_registro_contra_faca(novo_registro)
        else:
            atualizar_registro_contra_faca(index_edicao, novo_registro)
            index_edicao = None

        carregar_dados_do_banco()
        limpar_campos_form(dicionario_entries, btn_cadastrar, "cadastrar", COR_CADASTRAR)
        atualizar_tabela_contra_facas()

        if cadastro_novo:
            redirecionar_apos_cadastro("Contra-Facas", novo_registro)

    def carregar_edicao_cf(idx):
        global index_edicao
        registro = dados_sistema["Contra-Facas"][idx]
        index_edicao = registro["id"]
        for nome in colunas:
            dicionario_entries[nome].delete(0, END)
            dicionario_entries[nome].insert(0, registro[nome])
        btn_cadastrar.configure(text="salvar", bg=COR_EDITAR)

    def excluir_cf(idx):
        if messagebox.askyesno("Confirmar", "Deseja realmente excluir este registro?"):
            registro_id = dados_sistema["Contra-Facas"][idx]["id"]
            excluir_registro_por_id("contra_facas", registro_id)
            carregar_dados_do_banco()
            atualizar_tabela_contra_facas()

    btn_cadastrar.configure(command=salvar_contra_faca)
    atualizar_tabela_contra_facas()

    if aba_carregar_edicao is not None:
        carregar_edicao_cf(aba_carregar_edicao)

# --- TELA 3: RETIFICA ---
def mostrar_tela_retifica():
    carregar_dados_do_banco()
    limpar_tela()
    atualizar_botoes_menu("Retifica")
    
    frame_abas = Frame(frame_conteudo, bg="white")
    frame_abas.pack(side=TOP, fill=X, pady=10)
    
    aba_ativa = dados_sistema["Retifica"]["aba_atual"]
    
    btn_aba_faca = Button(frame_abas, text="Facas", width=12, bd=1, relief="solid",
                          bg=COR_CADASTRAR if aba_ativa == "Facas" else "white",
                          command=lambda: alternar_aba_retifica("Facas"))
    btn_aba_faca.pack(side=LEFT, padx=(150, 10))
    
    btn_aba_cf = Button(frame_abas, text="Contra-facas", width=12, bd=1, relief="solid",
                         bg=COR_CADASTRAR if aba_ativa == "Contra-Facas" else "white",
                         command=lambda: alternar_aba_retifica("Contra-Facas"))
    btn_aba_cf.pack(side=LEFT, padx=10)
    
    Frame(frame_conteudo, height=1, bg="black").pack(side=TOP, fill=X, padx=10, pady=5)
    
    frame_tabela = Frame(frame_conteudo, bg="white")
    frame_tabela.pack(side=TOP, fill=BOTH, expand=True, padx=10)
    
    if aba_ativa == "Facas":
        colunas = ["Diametro", "quantidade", "Retificadas", "Slitter", "Retifica"]
        lista_dados = dados_sistema["Facas"]
    else:
        colunas = ["Largura", "quantidade", "Boas para uso", "Retifica externa"]
        lista_dados = dados_sistema["Contra-Facas"]
        
    for i in range(len(colunas) + 1):
        frame_tabela.grid_columnconfigure(i, weight=1, minsize=110)
        
    for idx, nome in enumerate(colunas):
        Label(frame_tabela, text=nome, bg="white", font=("Arial", 9, "bold"), fg="gray20").grid(row=0, column=idx, pady=5)
        
    for row_idx, item in enumerate(lista_dados, start=1):
        for col_idx, nome_col in enumerate(colunas):
            Label(frame_tabela, text=item[nome_col], bg="white", font=("Arial", 10)).grid(row=row_idx, column=col_idx, pady=5)
            
        frame_acoes = Frame(frame_tabela, bg="white")
        frame_acoes.grid(row=row_idx, column=len(colunas), padx=5, pady=5, sticky="w")
        
        Button(frame_acoes, text="editar", bg=COR_EDITAR, font=("Arial", 9), bd=1, relief="solid",
               command=lambda r=row_idx-1: acao_editar_via_subtela(aba_ativa, r)).pack(side=LEFT, padx=2)
        Button(frame_acoes, text="Excluir", bg=COR_EXCLUIR, fg="white", font=("Arial", 9), bd=1, relief="solid",
               command=lambda r=row_idx-1: acao_excluir_via_subtela(aba_ativa, r, mostrar_tela_retifica)).pack(side=LEFT, padx=2)
        if aba_ativa == "Facas":
            Button(
                frame_acoes,
                text="Retificar",
                bg=COR_CADASTRAR,
                font=("Arial", 9),
                bd=1,
                relief="solid",
                command=lambda registro=item: retificar_faca(registro),
            ).pack(side=LEFT, padx=2)

def alternar_aba_retifica(nome_aba):
    dados_sistema["Retifica"]["aba_atual"] = nome_aba
    salvar_configuracao("retifica_aba", nome_aba)
    carregar_dados_do_banco()
    mostrar_tela_retifica()

# --- TELA 4: SLITTER ---
def mostrar_tela_slitter():
    carregar_dados_do_banco()
    limpar_tela()
    atualizar_botoes_menu("Slitter")
    
    frame_abas = Frame(frame_conteudo, bg="white")
    frame_abas.pack(side=TOP, fill=X, pady=10)
    
    aba_ativa = dados_sistema["Slitter"]["aba_atual"]
    
    btn_aba_faca = Button(frame_abas, text="Facas", width=12, bd=1, relief="solid",
                          bg=COR_CADASTRAR if aba_ativa == "Facas" else "white",
                          command=lambda: alternar_aba_slitter("Facas"))
    btn_aba_faca.pack(side=LEFT, padx=(150, 10))
    
    btn_aba_cf = Button(frame_abas, text="Contra-facas", width=12, bd=1, relief="solid",
                         bg=COR_CADASTRAR if aba_ativa == "Contra-Facas" else "white",
                         command=lambda: alternar_aba_slitter("Contra-Facas"))
    btn_aba_cf.pack(side=LEFT, padx=10)
    
    Frame(frame_conteudo, height=1, bg="black").pack(side=TOP, fill=X, padx=10, pady=5)
    
    frame_tabela = Frame(frame_conteudo, bg="white")
    frame_tabela.pack(side=TOP, fill=BOTH, expand=True, padx=10)
    
    if aba_ativa == "Facas":
        colunas = ["Diametro", "quantidade", "Retificadas", "Slitter", "Retifica"]
        lista_dados = dados_sistema["Facas"]
    else:
        colunas = ["Largura", "quantidade", "Boas para uso", "Retifica externa"]
        lista_dados = dados_sistema["Contra-Facas"]
        
    for i in range(len(colunas) + 1):
        frame_tabela.grid_columnconfigure(i, weight=1, minsize=110)
        
    for idx, nome in enumerate(colunas):
        Label(frame_tabela, text=nome, bg="white", font=("Arial", 9, "bold"), fg="gray20").grid(row=0, column=idx, pady=5)
        
    for row_idx, item in enumerate(lista_dados, start=1):
        for col_idx, nome_col in enumerate(colunas):
            Label(frame_tabela, text=item[nome_col], bg="white", font=("Arial", 10)).grid(row=row_idx, column=col_idx, pady=5)
            
        frame_acoes = Frame(frame_tabela, bg="white")
        frame_acoes.grid(row=row_idx, column=len(colunas), padx=5, pady=5, sticky="w")
        
        Button(frame_acoes, text="editar", bg=COR_EDITAR, font=("Arial", 9), bd=1, relief="solid",
               command=lambda r=row_idx-1: acao_editar_via_subtela(aba_ativa, r)).pack(side=LEFT, padx=2)
        Button(frame_acoes, text="Excluir", bg=COR_EXCLUIR, fg="white", font=("Arial", 9), bd=1, relief="solid",
               command=lambda r=row_idx-1: acao_excluir_via_subtela(aba_ativa, r, mostrar_tela_slitter)).pack(side=LEFT, padx=2)

def alternar_aba_slitter(nome_aba):
    dados_sistema["Slitter"]["aba_atual"] = nome_aba
    salvar_configuracao("slitter_aba", nome_aba)
    carregar_dados_do_banco()
    mostrar_tela_slitter()


def mostrar_tela_busca():
    carregar_dados_do_banco()
    limpar_tela()
    atualizar_botoes_menu("Busca")

    frame_busca = Frame(frame_conteudo, bg="white")
    frame_busca.pack(fill=X, padx=20, pady=20)

    Label(frame_busca, text="Busca e Relatórios", bg="white", font=("Arial", 16, "bold")).pack(anchor="w")

    campos_por_tabela = {
        "Facas": ["Diametro", "quantidade", "Retificadas", "Slitter", "Retifica"],
        "Contra-Facas": ["Largura", "quantidade", "Boas para uso", "Retifica externa"],
    }

    tabela_var = StringVar(value="Facas")
    campo_var = StringVar(value=campos_por_tabela["Facas"][0])
    filtro_var = StringVar()

    def atualizar_campos_por_tabela(*args):
        opcoes = campos_por_tabela[tabela_var.get()]
        menu = campo_select['menu']
        menu.delete(0, "end")
        for opcao in opcoes:
            menu.add_command(label=opcao, command=lambda valor=opcao: campo_var.set(valor))
        campo_var.set(opcoes[0])

    frame_filtros = Frame(frame_busca, bg="white")
    frame_filtros.pack(fill=X, pady=10)

    Label(frame_filtros, text="Tabela:", bg="white").grid(row=0, column=0, padx=(0, 10), sticky="w")
    tabela_select = OptionMenu(frame_filtros, tabela_var, *campos_por_tabela.keys(), command=atualizar_campos_por_tabela)
    tabela_select.grid(row=0, column=1, padx=(0, 20), sticky="w")

    Label(frame_filtros, text="Campo:", bg="white").grid(row=0, column=2, padx=(0, 10), sticky="w")
    campo_select = OptionMenu(frame_filtros, campo_var, *campos_por_tabela["Facas"])
    campo_select.grid(row=0, column=3, padx=(0, 20), sticky="w")

    Label(frame_filtros, text="Valor:", bg="white").grid(row=0, column=4, padx=(0, 10), sticky="w")
    entrada_valor = Entry(frame_filtros, width=25, bd=1, relief="solid")
    entrada_valor.grid(row=0, column=5, sticky="w")

    def executar_busca():
        nome_tabela = tabela_var.get()
        tabela_sql = "facas" if nome_tabela == "Facas" else "contra_facas"
        campo = campo_var.get()
        valor = entrada_valor.get().strip()

        if not valor:
            messagebox.showwarning("Aviso", "Informe um valor para a busca.")
            return

        resultados = buscar_registros(tabela_sql, campo, valor)

        for widget in frame_resultados.winfo_children():
            widget.destroy()

        if not resultados:
            Label(frame_resultados, text="Nenhum registro encontrado.", bg="white", font=("Arial", 10), fg="gray40").pack(anchor="w", pady=10)
            return

        colunas_tabela = campos_por_tabela[nome_tabela]
        for idx, nome in enumerate(colunas_tabela):
            Label(frame_resultados, text=nome, bg="#d9e1f2", font=("Arial", 9, "bold"), bd=1, relief="solid").grid(row=0, column=idx, padx=2, pady=2, sticky="nsew")

        for row_idx, item in enumerate(resultados, start=1):
            for col_idx, nome_col in enumerate(colunas_tabela):
                chave = {
                    "Diametro": "diametro",
                    "quantidade": "quantidade",
                    "Retificadas": "retificadas",
                    "Slitter": "slitter",
                    "Retifica": "retifica",
                    "Largura": "largura",
                    "Boas para uso": "boas_para_uso",
                    "Retifica externa": "retifica_externa",
                }.get(nome_col, nome_col.lower())
                valor_exibido = item[chave] if chave in item.keys() else ""
                Label(frame_resultados, text=str(valor_exibido), bg="white", font=("Arial", 9), bd=1, relief="solid").grid(row=row_idx, column=col_idx, padx=2, pady=2, sticky="nsew")

    Button(frame_filtros, text="Buscar", bg=COR_CADASTRAR, bd=1, relief="solid", command=executar_busca).grid(row=0, column=6, padx=(10, 0), sticky="w")

    frame_resultados = Frame(frame_busca, bg="white")
    frame_resultados.pack(fill=BOTH, expand=True, pady=(20, 0))

    atualizar_campos_por_tabela()


def mostrar_dashboard():
    carregar_dados_do_banco()
    limpar_tela()
    atualizar_botoes_menu("Dashboard")

    cabecalho = Frame(frame_conteudo, bg="white")
    cabecalho.pack(fill=X, padx=16, pady=(10, 4))
    Label(cabecalho, text="Dashboard de estoque", bg="white", font=("Arial", 16, "bold")).pack(side=LEFT)
    Button(
        cabecalho,
        text="Atualizar",
        bg=COR_CADASTRAR,
        bd=1,
        relief="solid",
        command=mostrar_dashboard,
    ).pack(side=RIGHT)

    analise = gerar_analise_dashboard(dados_sistema["Facas"], dados_sistema["Contra-Facas"])

    frame_indicadores = Frame(frame_conteudo, bg="white")
    frame_indicadores.pack(fill=X, padx=12, pady=4)

    indicadores = [
        (
            "Facas",
            f"{analise['registros_facas']} modelos",
            f"{formatar_quantidade(analise['quantidade_facas'])} peças",
        ),
        (
            "Contra-facas",
            f"{analise['registros_contra_facas']} modelos",
            f"{formatar_quantidade(analise['quantidade_contra_facas'])} peças",
        ),
        (
            "Facas em retífica",
            f"{formatar_quantidade(analise['fluxos'][0][2])} peças",
            f"{analise['fluxos'][0][1]} registros",
        ),
        (
            "Contra-facas em retífica externa",
            f"{formatar_quantidade(analise['fluxos'][2][2])} peças",
            f"{analise['fluxos'][2][1]} registros",
        ),
    ]

    for titulo, valor, detalhe in indicadores:
        cartao = Frame(frame_indicadores, bg="#eef4fa", bd=1, relief="solid", padx=8, pady=6)
        cartao.pack(side=LEFT, fill=BOTH, expand=True, padx=3)
        Label(cartao, text=titulo, bg="#eef4fa", font=("Arial", 9, "bold"), anchor="w").pack(fill=X)
        Label(cartao, text=valor, bg="#eef4fa", font=("Arial", 13, "bold"), anchor="w").pack(fill=X, pady=(3, 0))
        Label(cartao, text=detalhe, bg="#eef4fa", font=("Arial", 8), anchor="w").pack(fill=X)

    frame_analises = Frame(frame_conteudo, bg="white")
    frame_analises.pack(fill=BOTH, expand=True, padx=15, pady=(7, 0))
    frame_analises.grid_columnconfigure(0, weight=1)
    frame_analises.grid_columnconfigure(1, weight=1)
    frame_analises.grid_rowconfigure(0, weight=1)

    frame_diametros = Frame(frame_analises, bg="white", bd=1, relief="solid")
    frame_diametros.grid(row=0, column=0, sticky="nsew", padx=(0, 5), pady=2)
    Label(
        frame_diametros,
        text="Estoque por diâmetro de faca",
        bg="white",
        font=("Arial", 10, "bold"),
    ).pack(anchor="w", padx=8, pady=(6, 2))
    grafico = Canvas(frame_diametros, bg="white", height=190, highlightthickness=0)
    grafico.pack(fill=BOTH, expand=True, padx=5, pady=3)

    maiores_diametros = analise["diametros"][:7]
    if not maiores_diametros:
        grafico.create_text(15, 25, text="Sem dados numéricos de diâmetro.", anchor="nw", font=("Arial", 9))
    else:
        max_quantidade = max((quantidade for _, quantidade in maiores_diametros), default=Decimal("0"))
        largura = 255
        if max_quantidade <= 0:
            max_quantidade = Decimal("1")
        for indice, (diametro, quantidade) in enumerate(maiores_diametros):
            y = 12 + indice * 25
            grafico.create_text(
                4, y + 7, text=f"{diametro} mm", anchor="w", font=("Arial", 8)
            )
            comprimento = max(2, int(float(quantidade / max_quantidade) * largura))
            grafico.create_rectangle(
                92, y, 92 + comprimento, y + 15, fill=COR_AZUL_TOPO, outline=""
            )
            grafico.create_text(
                98 + comprimento, y + 7,
                text=formatar_quantidade(quantidade),
                anchor="w",
                font=("Arial", 8),
            )

    frame_fluxo = Frame(frame_analises, bg="white", bd=1, relief="solid")
    frame_fluxo.grid(row=0, column=1, sticky="nsew", padx=(5, 0), pady=2)
    Label(
        frame_fluxo,
        text="Fluxo atual por situação",
        bg="white",
        font=("Arial", 10, "bold"),
    ).pack(anchor="w", padx=8, pady=(6, 2))

    for titulo, quantidade_registros, quantidade_pecas in analise["fluxos"]:
        linha = Frame(frame_fluxo, bg="white")
        linha.pack(fill=X, padx=8, pady=5)
        Label(linha, text=titulo, bg="white", font=("Arial", 9), anchor="w").pack(fill=X)
        Label(
            linha,
            text=f"{quantidade_registros} registros  |  {formatar_quantidade(quantidade_pecas)} peças",
            bg="white",
            font=("Arial", 9, "bold"),
            anchor="w",
        ).pack(fill=X)

    observacoes = [
        "Dica: compare o estoque em retífica com o estoque disponível para planejar reposições.",
        "O fluxo mostra a situação atual cadastrada; não representa histórico por período.",
    ]
    if analise["invalidas"]:
        observacoes.append(
            f"Atenção: {analise['invalidas']} registro(s) têm quantidade não numérica e não entram nas somas."
        )
    if analise["diametros_invalidos"]:
        observacoes.append(
            f"{analise['diametros_invalidos']} faca(s) têm diâmetro não numérico e não entram no gráfico."
        )
    Label(
        frame_conteudo,
        text="\n".join(observacoes),
        bg="white",
        fg="gray30",
        justify=LEFT,
        anchor="w",
        font=("Arial", 8),
    ).pack(fill=X, padx=18, pady=(4, 8))


# ==========================================
# REGRAS DE INTEGRAÇÃO CRUDS ENTRE SUBTELAS
# ==========================================
def acao_editar_via_subtela(origem, idx):
    """Redireciona para o formulário correto abrindo os dados direto no modo edição."""
    if origem == "Facas":
        mostrar_tela_facas(aba_carregar_edicao=idx)
    else:
        mostrar_tela_contra_facas(aba_carregar_edicao=idx)

def acao_excluir_via_subtela(origem, idx, atualizar_subtela_fn):
    """Deleta o dado do banco central e atualiza a própria aba de visualização."""
    if messagebox.askyesno("Confirmar", f"Deseja realmente excluir este item de {origem}?"):
        tabela = "facas" if origem == "Facas" else "contra_facas"
        registro_id = dados_sistema[origem][idx]["id"]
        excluir_registro_por_id(tabela, registro_id)
        carregar_dados_do_banco()
        atualizar_subtela_fn()


def retificar_faca(registro):
    try:
        diametro_atual = Decimal(str(registro["Diametro"]).strip().replace(",", "."))
        if not diametro_atual.is_finite():
            raise InvalidOperation
        novo_diametro = diametro_atual - Decimal("0.50")
        if novo_diametro <= 0:
            messagebox.showwarning("Diâmetro inválido", "O diâmetro precisa ser maior que 0,50 mm para retificar.")
            return
    except (InvalidOperation, ValueError):
        messagebox.showwarning("Diâmetro inválido", "Não foi possível calcular: informe o diâmetro como um número.")
        return

    novo_registro = {
        "Diametro": f"{novo_diametro:.2f}".replace(".", ","),
        "quantidade": registro["quantidade"],
        "Retificadas": "sim",
        "Slitter": "não",
        "Retifica": "sim",
    }
    inserir_registro_faca(novo_registro)
    salvar_configuracao("slitter_aba", "Facas")
    carregar_dados_do_banco()
    mostrar_tela_slitter()


# ==========================================
# RENDERIZANDO OS BOTÕES DO MENU LATERAL
# ==========================================
botoes_menu_config = [
    ("Facas", mostrar_tela_facas),
    ("Contra-Facas", mostrar_tela_contra_facas),
    ("Retifica", mostrar_tela_retifica),
    ("Slitter", mostrar_tela_slitter),
    ("Dashboard", mostrar_dashboard),
    ("Busca", mostrar_tela_busca),
    ("Sair", janela.quit)
]

botoes_menu_objetos = {}

for nome_botao, comando_funcao in botoes_menu_config:
    btn = Button(
        frame_lateral, 
        text=nome_botao, 
        bg=COR_BOTAO_LATERAL, 
        font=("Arial", 10),
        width=14, 
        relief="raised", 
        bd=2,
        command=comando_funcao
    )
    btn.pack(pady=12, padx=15)
    botoes_menu_objetos[nome_botao] = btn

# Inicializa o sistema abrindo por padrão na tela de Facas
mostrar_tela_facas()

janela.mainloop()
