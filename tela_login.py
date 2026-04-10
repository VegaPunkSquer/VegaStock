import requests
from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox
from PySide6.QtCore import Qt

API_BASE_URL = "http://127.0.0.1:8000"

class TelaLogin(QDialog):
    def __init__(self):
        super().__init__()
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
        lbl_assinatura = QLabel("Desenvolvido por Vega | v1.0.0")
        lbl_assinatura.setAlignment(Qt.AlignCenter)
        lbl_assinatura.setStyleSheet("color: #888; font-size: 10px; margin-top: 10px; border: none;")
        layout.addWidget(lbl_assinatura)

    def fazer_login(self):
        login = self.input_login.text()
        senha = self.input_senha.text()

        if not login or not senha:
            QMessageBox.warning(self, "Erro", "Preencha usuário e senha.")
            return

        try:
            # Bate na rota nova que criamos na Parte 2
            response = requests.post(f"{API_BASE_URL}/login", json={"login": login, "senha": senha})
            if response.status_code == 200:
                self.cliente_dados = response.json()
                self.accept() # Fecha com sucesso
            else:
                try:
                    erro = response.json().get("detail", "Erro desconhecido")
                except:
                    # Se a API der Erro 500 e não mandar JSON, cai aqui em vez de quebrar o App
                    erro = f"Erro interno de comunicação com o servidor (Status {response.status_code})."
                QMessageBox.warning(self, "Acesso Negado", erro)
        except requests.exceptions.ConnectionError:
            QMessageBox.critical(self, "Erro Fatal", "Não foi possível conectar à API.")

    def abrir_cadastro(self):
        self.ir_para_cadastro = True
        self.reject() # Fecha a tela de login avisando o app.py para abrir o Cadastro
        
    def abrir_recuperacao(self):
        self.ir_para_recuperacao = True
        self.reject()