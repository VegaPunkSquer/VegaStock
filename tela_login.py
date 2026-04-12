import requests
import os
from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QIcon

API_BASE_URL = "https://vegastock.onrender.com"

class WorkerLogin(QThread):
    # O "telefone" para avisar a tela se deu bom ou ruim
    resultado = Signal(dict)
    erro = Signal(str)

    def __init__(self, login, senha):
        super().__init__()
        self.login = login
        self.senha = senha

    def run(self):
        # Tudo que está aqui dentro roda em paralelo sem travar a tela
        try:
            response = requests.post(f"{API_BASE_URL}/login", json={"login": self.login, "senha": self.senha})
            if response.status_code == 200:
                self.resultado.emit(response.json()) # Liga avisando sucesso
            else:
                try:
                    msg_erro = response.json().get("detail", "Erro desconhecido")
                except:
                    msg_erro = f"Erro interno (Status {response.status_code})."
                self.erro.emit(msg_erro) # Liga avisando erro
        except requests.exceptions.ConnectionError:
            self.erro.emit("Não foi possível conectar à API.")

class TelaLogin(QDialog):
    def __init__(self):
        super().__init__()
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        caminho_icone = os.path.join(BASE_DIR, 'logo.ico')
        
        self.setWindowIcon(QIcon(caminho_icone))
        self.setWindowTitle("VegaStock - Sistema de Estoque - Login")
        self.setFixedSize(300, 250)
        
        # Variáveis para devolver ao app.py
        self.cliente_dados = None
        self.ir_para_cadastro = False
        self.ir_para_recuperacao = False

        layout = QVBoxLayout()

        lbl_titulo = QLabel("Acesso ao Sistema")
        lbl_titulo.setObjectName("titulo") # Puxa o amarelo/negrito do estilo.py
        layout.addWidget(lbl_titulo)

        self.input_login = QLineEdit()
        self.input_login.setPlaceholderText("Usuário")
        layout.addWidget(self.input_login)

        self.input_senha = QLineEdit()
        self.input_senha.setPlaceholderText("Senha")
        self.input_senha.setEchoMode(QLineEdit.Password) # Esconde a senha com ***
        layout.addWidget(self.input_senha)

        self.btn_entrar = QPushButton("Entrar")
        self.btn_entrar.setObjectName("btn_destaque") # Botão Amarelo
        self.btn_entrar.clicked.connect(self.fazer_login)
        layout.addWidget(self.btn_entrar)

        self.btn_cadastrar = QPushButton("Cadastrar-se")
        # Botão preto normal, por isso não tem objectName
        self.btn_cadastrar.clicked.connect(self.abrir_cadastro)
        layout.addWidget(self.btn_cadastrar)
        
        self.btn_esqueci = QPushButton("Esqueci minha senha")
        self.btn_esqueci.setStyleSheet("background-color: transparent; color: gray; text-decoration: underline; border: none;")
        self.btn_esqueci.clicked.connect(self.abrir_recuperacao)
        layout.addWidget(self.btn_esqueci)

        self.setLayout(layout)
        
        # Assinatura Vega
        texto_assinatura = '<a href="https://wa.me/5512981194607" style="color: #aaa; text-decoration: none;">Desenvolvido por Vega | Suporte: (12) 98119-4607</a>'
        lbl_assinatura = QLabel(texto_assinatura)
        lbl_assinatura.setOpenExternalLinks(True) # Permite clicar no link e abrir no navegador
        lbl_assinatura.setAlignment(Qt.AlignCenter)
        lbl_assinatura.setStyleSheet("color: #888; font-size: 10px; margin-top: 10px; border: none;")
        layout.addWidget(lbl_assinatura)

    def fazer_login(self):
        login = self.input_login.text()
        senha = self.input_senha.text()

        if not login or not senha:
            QMessageBox.warning(self, "Erro", "Preencha usuário e senha.")
            return

        # Muda o texto do botão e trava ele para o usuário não clicar 2 vezes
        self.btn_entrar.setText("Conectando...")
        self.btn_entrar.setEnabled(False)

        # Manda o trabalhador pro porão com o login e senha
        self.worker = WorkerLogin(login, senha)
        self.worker.resultado.connect(self.login_sucesso)
        self.worker.erro.connect(self.login_erro)
        self.worker.start() # Dá a ordem de trabalhar

    # Função que atende o telefone de sucesso
    def login_sucesso(self, dados):
        self.cliente_dados = dados
        self.accept()

    # Função que atende o telefone de erro
    def login_erro(self, mensagem):
        # Destrava o botão e volta ao normal
        self.btn_entrar.setText("Entrar")
        self.btn_entrar.setEnabled(True)
        QMessageBox.warning(self, "Acesso Negado", mensagem)

    def abrir_cadastro(self):
        self.ir_para_cadastro = True
        self.reject() # Fecha a tela de login avisando o app.py para abrir o Cadastro
        
    def abrir_recuperacao(self):
        self.ir_para_recuperacao = True
        self.reject()