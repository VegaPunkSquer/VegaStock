import requests
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QLineEdit, QPushButton, QMessageBox, QFrame, 
                               QTableWidget, QTableWidgetItem, QHeaderView, 
                               QCheckBox, QFormLayout, QAbstractItemView)
from PySide6.QtCore import Qt

# IMPORTANTE: Importa a janela de vendas lá do seu arquivo de configurações!
from aba_configuracoes import DialogUpgradePRO 

API_BASE_URL = "http://127.0.0.1:8000"

class AbaEquipe(QWidget):
    def __init__(self, cliente_dados):
        super().__init__()
        self.cliente_dados = cliente_dados
        self.usuario_selecionado_id = None # Controla se estamos criando ou editando

        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(20, 20, 20, 20)

        lbl_titulo = QLabel("Gestão de Equipe e Permissões")
        lbl_titulo.setStyleSheet("font-size: 24px; font-weight: bold; color: #333; margin-bottom: 10px;")
        layout_principal.addWidget(lbl_titulo, alignment=Qt.AlignCenter)

        # ==========================================
        # TELA 1: BLOQUEIO PRO (A Isca)
        # ==========================================
        self.frame_bloqueado = QFrame()
        layout_bloq = QVBoxLayout(self.frame_bloqueado)

        # 1. Adicione um stretch no topo (valor 1) para empurrar para baixo
        layout_bloq.addStretch(1)
        
        layout_bloq.setAlignment(Qt.AlignCenter)
        
        lbl_lock = QLabel("🔒")
        lbl_lock.setStyleSheet("font-size: 60px; border: none; margin-bottom: 10px;")
        layout_bloq.addWidget(lbl_lock, alignment=Qt.AlignCenter)
        
        lbl_aviso = QLabel("Recurso Exclusivo do Plano PRO")
        lbl_aviso.setStyleSheet("font-size: 20px; font-weight: bold; color: #555;")
        layout_bloq.addWidget(lbl_aviso, alignment=Qt.AlignCenter)

        lbl_sub = QLabel("Crie logins individuais para seus funcionários e bloqueie o acesso a\npreços, relatórios de prejuízo e configurações.")
        lbl_sub.setAlignment(Qt.AlignCenter)
        lbl_sub.setStyleSheet("color: #777; margin-bottom: 20px;")
        layout_bloq.addWidget(lbl_sub, alignment=Qt.AlignCenter)

        btn_liberar = QPushButton("CONHECER O PLANO PRO 👑")
        btn_liberar.setStyleSheet("background-color: #FFD700; color: #000; font-weight: bold; font-size: 16px; padding: 15px 30px; border-radius: 5px; border: 1px solid #E6C200;")
        btn_liberar.clicked.connect(self.abrir_vendas_pro)
        layout_bloq.addWidget(btn_liberar, alignment=Qt.AlignCenter)

        # 2. Adicione um stretch maior no fundo (valor 2) para empurrar tudo para CIMA
        layout_bloq.addStretch(2)

        layout_principal.addWidget(self.frame_bloqueado)

        # ==========================================
        # TELA 2: GESTÃO LIVRE (A Recompensa)
        # ==========================================
        self.frame_livre = QFrame()
        layout_livre = QHBoxLayout(self.frame_livre) # Lado a lado: Tabela e Formulário
        layout_livre.setSpacing(20)

        # ESQUERDA: Tabela de Funcionários
        frame_tabela = QFrame()
        layout_esq = QVBoxLayout(frame_tabela)
        
        lbl_equipe = QLabel("Membros da Equipe")
        lbl_equipe.setStyleSheet("font-weight: bold; font-size: 16px;")
        layout_esq.addWidget(lbl_equipe)

        self.tabela = QTableWidget()
        self.tabela.setColumnCount(4)
        self.tabela.setHorizontalHeaderLabels(["ID", "Login", "Cargo", "Acessos"])
        self.tabela.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabela.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tabela.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tabela.setColumnHidden(0, True) # Esconde o ID
        self.tabela.itemClicked.connect(self.selecionar_funcionario)
        layout_esq.addWidget(self.tabela)

        btn_novo = QPushButton("Limpar Seleção (Novo Funcionário)")
        btn_novo.clicked.connect(self.limpar_formulario)
        layout_esq.addWidget(btn_novo)

        layout_livre.addWidget(frame_tabela, stretch=6)

        # DIREITA: Formulário de Permissões
        frame_form = QFrame()
        frame_form.setStyleSheet("background-color: #f9f9f9; border: 1px solid #ddd; border-radius: 5px;")
        layout_dir = QVBoxLayout(frame_form)
        layout_dir.setContentsMargins(15, 15, 15, 15)

        self.lbl_form_tit = QLabel("Cadastrar Novo Membro")
        self.lbl_form_tit.setStyleSheet("font-weight: bold; font-size: 16px; border: none; margin-bottom: 10px;")
        layout_dir.addWidget(self.lbl_form_tit)

        form_inputs = QFormLayout()
        self.input_login = QLineEdit()
        self.input_senha = QLineEdit()
        self.input_senha.setPlaceholderText("Deixe em branco para não alterar")
        self.input_cargo = QLineEdit()
        self.input_cargo.setPlaceholderText("Ex: Estoquista, Gerente")

        form_inputs.addRow("Login:", self.input_login)
        form_inputs.addRow("Senha:", self.input_senha)
        form_inputs.addRow("Cargo:", self.input_cargo)
        layout_dir.addLayout(form_inputs)

        lbl_perm = QLabel("O que este funcionário pode acessar?")
        lbl_perm.setStyleSheet("font-weight: bold; margin-top: 15px; border: none;")
        layout_dir.addWidget(lbl_perm)

        # Checkboxes de Permissão (Dashboard é padrão, nem precisa marcar)
        self.chk_catalogo = QCheckBox("Catálogo de Produtos")
        self.chk_estoque = QCheckBox("Operação de Estoque")
        self.chk_relatorios = QCheckBox("Análise de Desperdício (Financeiro)")
        self.chk_config = QCheckBox("Configurações do Sistema")

        layout_dir.addWidget(self.chk_catalogo)
        layout_dir.addWidget(self.chk_estoque)
        layout_dir.addWidget(self.chk_relatorios)
        layout_dir.addWidget(self.chk_config)

        layout_dir.addStretch()

        self.btn_salvar = QPushButton("SALVAR FUNCIONÁRIO")
        self.btn_salvar.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 10px;")
        self.btn_salvar.clicked.connect(self.salvar_funcionario)
        layout_dir.addWidget(self.btn_salvar)

        self.btn_excluir = QPushButton("EXCLUIR FUNCIONÁRIO")
        self.btn_excluir.setStyleSheet("background-color: transparent; color: red; text-decoration: underline; border: none; margin-top: 5px;")
        self.btn_excluir.clicked.connect(self.excluir_funcionario)
        self.btn_excluir.hide() # Só aparece se estiver editando alguém
        layout_dir.addWidget(self.btn_excluir)

        layout_livre.addWidget(frame_form, stretch=4)
        layout_principal.addWidget(self.frame_livre)

    # --- LÓGICA DE INTERFACE E API ---

    def showEvent(self, event):
        super().showEvent(event)
        # Trava Mestra de Acesso
        if self.cliente_dados.get('status_assinatura') == "PRO":
            self.frame_bloqueado.hide()
            self.frame_livre.show()
            self.carregar_equipe()
        else:
            self.frame_livre.hide()
            self.frame_bloqueado.show()

    def abrir_vendas_pro(self):
        dialog = DialogUpgradePRO(self.cliente_dados['cliente_id'])
        dialog.exec()
        # Se ele comprou e atualizou o status (você pode precisar recarregar o login do app.py, mas como mock, vamos só avisar)
        QMessageBox.information(self, "Aviso", "Se você ativou o PRO, saia e entre novamente no sistema para atualizar suas permissões!")

    def carregar_equipe(self):
        self.tabela.setRowCount(0)
        try:
            resp = requests.get(f"{API_BASE_URL}/equipe/{self.cliente_dados['cliente_id']}")
            if resp.status_code == 200:
                for i, func in enumerate(resp.json()):
                    self.tabela.insertRow(i)
                    self.tabela.setItem(i, 0, QTableWidgetItem(str(func["id"])))
                    self.tabela.setItem(i, 1, QTableWidgetItem(func["login"]))
                    self.tabela.setItem(i, 2, QTableWidgetItem(func["cargo"] or "Sem Cargo"))
                    
                    # Salva a lista de permissões crua no campo para recuperar depois
                    item_acessos = QTableWidgetItem(", ".join(func["permissoes"]))
                    item_acessos.setData(Qt.UserRole, func["permissoes"]) 
                    self.tabela.setItem(i, 3, item_acessos)
        except: pass

    def limpar_formulario(self):
        self.usuario_selecionado_id = None
        self.lbl_form_tit.setText("Cadastrar Novo Membro")
        self.input_login.clear()
        self.input_senha.clear()
        self.input_cargo.clear()
        self.chk_catalogo.setChecked(False)
        self.chk_estoque.setChecked(False)
        self.chk_relatorios.setChecked(False)
        self.chk_config.setChecked(False)
        self.btn_salvar.setText("SALVAR FUNCIONÁRIO")
        self.btn_excluir.hide()

    def selecionar_funcionario(self, item):
        linha = item.row()
        self.usuario_selecionado_id = int(self.tabela.item(linha, 0).text())
        self.lbl_form_tit.setText(f"Editando: {self.tabela.item(linha, 1).text()}")
        self.btn_salvar.setText("ATUALIZAR DADOS")
        self.btn_excluir.show()

        self.input_login.setText(self.tabela.item(linha, 1).text())
        self.input_senha.clear() # Deixa em branco por segurança
        self.input_cargo.setText(self.tabela.item(linha, 2).text())

        # Recupera e marca as checkboxes
        permissoes = self.tabela.item(linha, 3).data(Qt.UserRole)
        self.chk_catalogo.setChecked("catalogo" in permissoes)
        self.chk_estoque.setChecked("estoque" in permissoes)
        self.chk_relatorios.setChecked("relatorios" in permissoes)
        self.chk_config.setChecked("configuracoes" in permissoes)

    def salvar_funcionario(self):
        if not self.input_login.text().strip():
            QMessageBox.warning(self, "Aviso", "O campo Login é obrigatório.")
            return

        # Monta a lista de permissões
        permissoes = ["dashboard"] # Dashboard sempre vai
        if self.chk_catalogo.isChecked(): permissoes.append("catalogo")
        if self.chk_estoque.isChecked(): permissoes.append("estoque")
        if self.chk_relatorios.isChecked(): permissoes.append("relatorios")
        if self.chk_config.isChecked(): permissoes.append("configuracoes")

        dados = {
            "cliente_id": self.cliente_dados['cliente_id'],
            "login": self.input_login.text().strip(),
            "cargo": self.input_cargo.text().strip(),
            "permissoes": permissoes
        }

        # Se for edição, envia o ID. Só envia senha se ele digitou uma nova.
        if self.usuario_selecionado_id:
            dados["id"] = self.usuario_selecionado_id
        elif not self.input_senha.text(): # Se for NOVO, tem que ter senha
            QMessageBox.warning(self, "Aviso", "A senha é obrigatória para novos usuários.")
            return

        if self.input_senha.text():
            dados["senha"] = self.input_senha.text()

        try:
            resp = requests.post(f"{API_BASE_URL}/equipe", json=dados)
            if resp.status_code == 200:
                QMessageBox.information(self, "Sucesso", "Funcionário salvo com sucesso!")
                self.limpar_formulario()
                self.carregar_equipe()
        except:
            QMessageBox.critical(self, "Erro", "Falha de conexão com o servidor.")

    def excluir_funcionario(self):
        resposta = QMessageBox.question(self, "Confirmar Exclusão", "Tem certeza que deseja demitir/remover este acesso?", QMessageBox.Yes | QMessageBox.No)
        if resposta == QMessageBox.Yes and self.usuario_selecionado_id:
            try:
                requests.delete(f"{API_BASE_URL}/equipe/{self.usuario_selecionado_id}")
                self.limpar_formulario()
                self.carregar_equipe()
            except: pass