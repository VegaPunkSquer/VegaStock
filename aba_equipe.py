import requests
import re
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QLineEdit, QPushButton, QMessageBox, QFrame, 
                               QTableWidget, QTableWidgetItem, QHeaderView, 
                               QCheckBox, QFormLayout, QAbstractItemView)
import os
import re
from PySide6.QtCore import Qt, QThread, Signal, QSize
from PySide6.QtGui import QMovie

# IMPORTANTE: Importa a janela de vendas lá do seu arquivo de configurações!
from aba_configuracoes import DialogUpgradePRO 

API_BASE_URL = "https://vegap-vega-stock.hf.space"

class WorkerEquipe(QThread):
    resultado = Signal(list)
    erro = Signal(str)

    def __init__(self, cliente_id):
        super().__init__()
        self.cliente_id = cliente_id

    def run(self):
        try:
            resp = requests.get(f"{API_BASE_URL}/equipe/{self.cliente_id}")
            if resp.status_code == 200:
                self.resultado.emit(resp.json())
            else:
                self.resultado.emit([])
        except Exception:
            self.erro.emit("Falha de conexão.")

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

        self.btn_novo = QPushButton("+ ADICIONAR MEMBRO")
        self.btn_novo.setStyleSheet("background-color: #009EE3; color: white; font-weight: bold; padding: 10px; border-radius: 5px; margin-top: 10px;")
        self.btn_novo.clicked.connect(self.limpar_formulario)
        layout_esq.addWidget(self.btn_novo)

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
        self.input_senha.setEchoMode(QLineEdit.Password) # <--- A MÁGICA DOS ASTERISCOS (***) AQUI
        self.input_senha.setPlaceholderText("Deixe em branco para não alterar")
        self.input_cargo = QLineEdit()
        self.input_cargo.setPlaceholderText("Ex: Estoquista, Gerente")

        form_inputs.addRow("Login:", self.input_login)
        
        # Container horizontal para o campo e o botão do olhinho ficarem lado a lado
        layout_senha_olho = QHBoxLayout()
        layout_senha_olho.addWidget(self.input_senha)
        
        self.btn_olho_equipe = QPushButton("👁️")
        self.btn_olho_equipe.setFixedWidth(35)
        self.btn_olho_equipe.setStyleSheet("padding: 5px; background-color: #eee; border: 1px solid #ccc; border-radius: 3px; font-size: 12px;")
        self.btn_olho_equipe.clicked.connect(self.toggle_senha_equipe)
        layout_senha_olho.addWidget(self.btn_olho_equipe)
        
        form_inputs.addRow("Senha:", layout_senha_olho)
        
        # --- INÍCIO: FEEDBACK VISUAL DA SENHA (NOVO) ---
        self.input_senha.textChanged.connect(self.validar_senha_tempo_real)
        self.lbl_regra_tamanho = QLabel("❌ Mínimo de 8 caracteres")
        self.lbl_regra_letra = QLabel("❌ Pelo menos 1 letra")
        self.lbl_regra_numero = QLabel("❌ Pelo menos 1 número")
        
        estilo_invalido = "color: gray; font-size: 11px;"
        self.lbl_regra_tamanho.setStyleSheet(estilo_invalido)
        self.lbl_regra_letra.setStyleSheet(estilo_invalido)
        self.lbl_regra_numero.setStyleSheet(estilo_invalido)
        
        # Ficam escondidos até ele começar a digitar a senha
        self.lbl_regra_tamanho.hide()
        self.lbl_regra_letra.hide()
        self.lbl_regra_numero.hide()
        
        form_inputs.addRow("", self.lbl_regra_tamanho)
        form_inputs.addRow("", self.lbl_regra_letra)
        form_inputs.addRow("", self.lbl_regra_numero)
        # --- FIM: FEEDBACK VISUAL DA SENHA ---
        
        form_inputs.addRow("Cargo:", self.input_cargo)
        layout_dir.addLayout(form_inputs)

        lbl_perm = QLabel("O que este funcionário pode acessar?")
        lbl_perm.setStyleSheet("font-weight: bold; margin-top: 15px; border: none;")
        layout_dir.addWidget(lbl_perm)

        # Checkboxes de Permissão (Dashboard é padrão, nem precisa marcar)
        # Checkboxes de Permissão (NADA É PADRÃO, VOCÊ ESCOLHE TUDO)
        self.chk_dashboard = QCheckBox("Dashboard Geral")
        self.chk_catalogo = QCheckBox("Catálogo de Produtos")
        
        layout_dir.addWidget(self.chk_dashboard)
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

        self.btn_cancelar = QPushButton("CANCELAR EDIÇÃO")
        self.btn_cancelar.setStyleSheet("background-color: #777; color: white; font-weight: bold; padding: 10px; margin-top: 5px;")
        self.btn_cancelar.clicked.connect(self.limpar_formulario)
        self.btn_cancelar.hide()
        layout_dir.addWidget(self.btn_cancelar)

        self.btn_excluir = QPushButton("EXCLUIR FUNCIONÁRIO")
        self.btn_excluir.setStyleSheet("background-color: transparent; color: red; text-decoration: underline; border: none; margin-top: 5px;")
        self.btn_excluir.clicked.connect(self.excluir_funcionario)
        self.btn_excluir.hide() 
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
        # 1. Prepara a Tabela com o GIF
        self.tabela.setRowCount(1)
        lbl_gif = QLabel()
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        caminho_gif = os.path.join(BASE_DIR, "assets", 'hourglass.gif')
        
        self.movie = QMovie(caminho_gif)
        self.movie.setScaledSize(QSize(20, 20))
        lbl_gif.setMovie(self.movie)
        lbl_gif.setAlignment(Qt.AlignCenter)
        self.movie.start()
        
        # Coluna 0 (ID) tá oculta, então botamos o GIF na coluna 1 (Login)
        self.tabela.setCellWidget(0, 1, lbl_gif)
        self.tabela.setItem(0, 2, QTableWidgetItem("Buscando equipe..."))
        self.tabela.setItem(0, 3, QTableWidgetItem("..."))

        # 2. Manda pro porão
        self.worker = WorkerEquipe(self.cliente_dados['cliente_id'])
        self.worker.resultado.connect(self.atualizar_tela)
        self.worker.start()

    def atualizar_tela(self, dados):
        # 3. O trabalhador voltou, esmaga o GIF e preenche os reais
        self.tabela.setRowCount(0)
        for i, func in enumerate(dados):
            self.tabela.insertRow(i)
            self.tabela.setItem(i, 0, QTableWidgetItem(str(func["id"])))
            self.tabela.setItem(i, 1, QTableWidgetItem(func["login"]))
            self.tabela.setItem(i, 2, QTableWidgetItem(func["cargo"] or "Sem Cargo"))
            
            # Salva a lista de permissões crua no campo para recuperar depois
            item_acessos = QTableWidgetItem(", ".join(func["permissoes"]))
            item_acessos.setData(Qt.UserRole, func["permissoes"]) 
            self.tabela.setItem(i, 3, item_acessos)
            
    def validar_senha_tempo_real(self, texto=""):
        if not texto:
            self.lbl_regra_tamanho.hide()
            self.lbl_regra_letra.hide()
            self.lbl_regra_numero.hide()
            return
        else:
            self.lbl_regra_tamanho.show()
            self.lbl_regra_letra.show()
            self.lbl_regra_numero.show()
            
        estilo_ok = "color: green; font-size: 11px; font-weight: bold;"
        estilo_erro = "color: gray; font-size: 11px;"

        if len(texto) >= 8:
            self.lbl_regra_tamanho.setText("✅ Mínimo de 8 caracteres")
            self.lbl_regra_tamanho.setStyleSheet(estilo_ok)
        else:
            self.lbl_regra_tamanho.setText("❌ Mínimo de 8 caracteres")
            self.lbl_regra_tamanho.setStyleSheet(estilo_erro)
            
        if re.search(r'[A-Za-z]', texto):
            self.lbl_regra_letra.setText("✅ Pelo menos 1 letra")
            self.lbl_regra_letra.setStyleSheet(estilo_ok)
        else:
            self.lbl_regra_letra.setText("❌ Pelo menos 1 letra")
            self.lbl_regra_letra.setStyleSheet(estilo_erro)
            
        if re.search(r'\d', texto):
            self.lbl_regra_numero.setText("✅ Pelo menos 1 número")
            self.lbl_regra_numero.setStyleSheet(estilo_ok)
        else:
            self.lbl_regra_numero.setText("❌ Pelo menos 1 número")
            self.lbl_regra_numero.setStyleSheet(estilo_erro)

    def limpar_formulario(self):
        # ========================================================
        # O LEÃO DE CHÁCARA: Conta as linhas da tabela vs Limite do Plano
        # ========================================================
        limite = self.cliente_dados.get('limite_contas', 2)
        qtd_atual = self.tabela.rowCount()
        
        if qtd_atual >= limite:
            mensagem = (f"Você atingiu o limite de {limite} contas do seu plano atual!\n\n"
                        "O VegaStock acompanha o crescimento do seu negócio. "
                        "Para adicionar mais funcionários (R$ 25,00/mês por vaga extra), "
                        "entre em contato com o nosso suporte.")
            
            QMessageBox.information(self, "Expanda sua Equipe", mensagem)
            return # Aborta a missão! O código para de ler aqui e não libera o formulário.
        # ========================================================

        # Se passou da barreira, continua normal:
        self.usuario_selecionado_id = None
        self.lbl_form_tit.setText("Cadastrar Novo Membro")
        
        self.input_login.setText("")
        
        # Destranca a senha
        self.input_senha.setEnabled(True)
        self.input_senha.setText("")
        self.input_senha.setPlaceholderText("Digite a senha do novo membro")
        
        self.lbl_regra_tamanho.hide()
        self.lbl_regra_letra.hide()
        self.lbl_regra_numero.hide()
        
        self.input_cargo.setText("")
        
        # Destranca e zera as permissões
        self.chk_catalogo.setEnabled(True)
        self.chk_estoque.setEnabled(True)
        self.chk_relatorios.setEnabled(True)
        self.chk_config.setEnabled(True)
        
        self.chk_catalogo.setChecked(False)
        self.chk_estoque.setChecked(False)
        self.chk_relatorios.setChecked(False)
        self.chk_config.setChecked(False)
        
        self.btn_salvar.setText("SALVAR FUNCIONÁRIO")
        self.btn_excluir.hide()
        self.btn_cancelar.hide() # Esconde o Cancelar

    def selecionar_funcionario(self, item):
        linha = item.row()
        self.usuario_selecionado_id = int(self.tabela.item(linha, 0).text())
        nome_selecionado = self.tabela.item(linha, 1).text()
        
        self.lbl_form_tit.setText(f"Editando: {nome_selecionado}")
        self.btn_salvar.setText("ATUALIZAR DADOS")
        self.btn_cancelar.show() # Mostra o Cancelar

        self.input_login.setText(nome_selecionado)
        self.input_senha.clear()
        self.input_cargo.setText(self.tabela.item(linha, 2).text())

        permissoes = self.tabela.item(linha, 3).data(Qt.UserRole)
        self.chk_catalogo.setChecked("catalogo" in permissoes)
        self.chk_estoque.setChecked("estoque" in permissoes)
        self.chk_relatorios.setChecked("relatorios" in permissoes)
        self.chk_config.setChecked("configuracoes" in permissoes)

        # ========================================================
        # A BLINDAGEM DO ADMIN: Compara o ID clicado com o ID logado
        # ========================================================
        if self.usuario_selecionado_id == self.cliente_dados.get('usuario_id'):
            # É O CHEFE! Trava tudo que é perigoso.
            self.input_senha.setEnabled(False)
            self.input_senha.setPlaceholderText("Altere a senha do Admin na Aba Conta")
            
            self.chk_catalogo.setEnabled(False)
            self.chk_estoque.setEnabled(False)
            self.chk_relatorios.setEnabled(False)
            self.chk_config.setEnabled(False)
            
            # Força o visual de "Tenho todas as permissões"
            self.chk_catalogo.setChecked(True)
            self.chk_estoque.setChecked(True)
            self.chk_relatorios.setChecked(True)
            self.chk_config.setChecked(True)
            
            self.btn_excluir.hide() # Imortal!
        else:
            # É FUNCIONÁRIO NORMAL. Libera tudo.
            self.input_senha.setEnabled(True)
            self.input_senha.setPlaceholderText("Deixe em branco para não alterar")
            
            self.chk_catalogo.setEnabled(True)
            self.chk_estoque.setEnabled(True)
            self.chk_relatorios.setEnabled(True)
            self.chk_config.setEnabled(True)
            
            self.btn_excluir.show() # Pode ser demitido!

    def salvar_funcionario(self):
        if not self.input_login.text().strip():
            QMessageBox.warning(self, "Aviso", "O campo Login é obrigatório.")
            return

        # Só barra se for um NOVO usuário (se estiver editando, deixa passar)
        if not self.usuario_selecionado_id: 
            # Na aba de Equipe, ele JÁ É PRO. O limite total é 6 (Admin + 5 contas)
            total_atual = self.tabela.rowCount()
            
            if total_atual >= 6:
                QMessageBox.warning(self, "Limite PRO Atingido", 
                    "Você já cadastrou os 5 usuários extras permitidos no Plano PRO.\n\n"
                    "Para adicionar contas adicionais (R$ 25,00/mês cada), entre em contato com o suporte.")
                return
        
        # --- TRAVA DE SEGURANÇA DA SENHA FORTE ---
        senha_digitada = self.input_senha.text()
        login_digitado = self.input_login.text().strip()
        
        # Se for novo cadastro, ou se for edição e ele resolveu digitar uma senha nova
        if not self.usuario_selecionado_id or senha_digitada:
            if senha_digitada.lower() == login_digitado.lower():
                QMessageBox.warning(self, "Segurança", "A senha não pode ser igual ao login.")
                return
            if len(senha_digitada) < 8 or not re.search(r'[A-Za-z]', senha_digitada) or not re.search(r'\d', senha_digitada):
                QMessageBox.warning(self, "Senha Fraca", "A senha precisa seguir as regras de segurança (Mínimo de 8 caracteres, 1 letra e 1 número).")
                return
        # -----------------------------------------

        # Monta a lista de permissões estritamente com o que você marcou na tela
        permissoes = [] 
        if self.chk_dashboard.isChecked(): permissoes.append("dashboard")
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
        msg = QMessageBox(self)
        msg.setWindowTitle("Confirmar Exclusão")
        msg.setText("Tem certeza que deseja demitir/remover este acesso?")
        
        # Cria os botões na marra e obriga o PySide a mostrá-los com cor!
        btn_sim = msg.addButton("Sim, Excluir", QMessageBox.ActionRole)
        btn_sim.setStyleSheet("background-color: #f44336; color: white; padding: 5px 15px; font-weight: bold; border-radius: 3px;")
        
        btn_nao = msg.addButton("Não, Cancelar", QMessageBox.RejectRole)
        btn_nao.setStyleSheet("background-color: #777; color: white; padding: 5px 15px; font-weight: bold; border-radius: 3px;")
        
        msg.setDefaultButton(btn_nao) # Deixa o Não selecionado por segurança
        
        msg.exec() # Mostra a caixa
        
        # Verifica se o cara clicou no nosso botão vermelho criado na mão
        if msg.clickedButton() == btn_sim and self.usuario_selecionado_id:
            try:
                requests.delete(f"{API_BASE_URL}/equipe/{self.usuario_selecionado_id}")
                self.limpar_formulario()
                self.carregar_equipe()
            except: 
                pass
            
    def toggle_senha_equipe(self):
        if self.input_senha.echoMode() == QLineEdit.Password:
            self.input_senha.setEchoMode(QLineEdit.Normal)
            self.btn_olho_equipe.setText("🔒")
        else:
            self.input_senha.setEchoMode(QLineEdit.Password)
            self.btn_olho_equipe.setText("👁️")