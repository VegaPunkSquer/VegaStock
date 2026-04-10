import re
import requests
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox

API_BASE_URL = "https://vegastock.onrender.com"

class TelaRecuperacao(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowIcon(QIcon("logo.ico"))
        self.setWindowTitle("VegaStock - Sistema de Estoque - Recuperar Senha")
        self.setFixedSize(300, 350)

        layout = QVBoxLayout()

        lbl_titulo = QLabel("Recuperação de Acesso")
        lbl_titulo.setObjectName("titulo")
        layout.addWidget(lbl_titulo)

        self.input_cnpj = QLineEdit()
        self.input_cnpj.setPlaceholderText("CNPJ da Empresa")
        self.input_cnpj.setInputMask("99.999.999/9999-99")
        layout.addWidget(self.input_cnpj)

        self.input_licenca = QLineEdit()
        self.input_licenca.setPlaceholderText("Token da Licença Original")
        layout.addWidget(self.input_licenca)

        self.input_nova_senha = QLineEdit()
        self.input_nova_senha.setPlaceholderText("Nova Senha")
        self.input_nova_senha.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.input_nova_senha)

        self.input_confirma_senha = QLineEdit()
        self.input_confirma_senha.setPlaceholderText("Confirmar Nova Senha")
        self.input_confirma_senha.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.input_confirma_senha)
        
        # Oculta os campos de senha no início
        self.input_nova_senha.hide()
        self.input_confirma_senha.hide()

        # Botão passo 1: Verificar
        self.btn_verificar = QPushButton("Verificar Credenciais")
        self.btn_verificar.setObjectName("btn_destaque")
        self.btn_verificar.clicked.connect(self.verificar_credenciais)
        layout.addWidget(self.btn_verificar)

        # Botão passo 2: Salvar (Oculto no início)
        self.btn_salvar = QPushButton("Atualizar Senha")
        self.btn_salvar.setObjectName("btn_destaque")
        self.btn_salvar.clicked.connect(self.enviar_recuperacao)
        self.btn_salvar.hide()
        layout.addWidget(self.btn_salvar)

        self.btn_voltar = QPushButton("Voltar")
        self.btn_voltar.clicked.connect(self.reject)
        layout.addWidget(self.btn_voltar)

        self.setLayout(layout)
        
    def verificar_credenciais(self):
        cnpj_cru = self.input_cnpj.text().strip()
        cnpj_limpo = re.sub(r'[^0-9]', '', cnpj_cru)
        licenca = self.input_licenca.text().strip()

        if not all([cnpj_limpo, licenca]):
            QMessageBox.warning(self, "Erro", "Preencha CNPJ e Token.")
            return

        dados = {"cnpj": cnpj_limpo, "token_licenca": licenca}
        
        try:
            response = requests.post(f"{API_BASE_URL}/verificar_licenca", json=dados)
            if response.status_code == 200:
                # Trava os campos de cima para não mudarem mais
                self.input_cnpj.setReadOnly(True)
                self.input_licenca.setReadOnly(True)
                
                # Esconde o botão verificar e mostra o resto
                self.btn_verificar.hide()
                self.input_nova_senha.show()
                self.input_confirma_senha.show()
                self.btn_salvar.show()
                
                QMessageBox.information(self, "Sucesso", "Credenciais válidas. Digite sua nova senha.")
            else:
                erro = response.json().get("detail", "Erro desconhecido")
                QMessageBox.warning(self, "Acesso Negado", erro)
        except requests.exceptions.ConnectionError:
            QMessageBox.critical(self, "Erro Fatal", "Não foi possível conectar à API.")

    def enviar_recuperacao(self):
        cnpj_cru = self.input_cnpj.text().strip()
        cnpj_limpo = re.sub(r'[^0-9]', '', cnpj_cru)
        licenca = self.input_licenca.text().strip()
        nova_senha = self.input_nova_senha.text()
        confirma = self.input_confirma_senha.text()

        if not all([cnpj_limpo, licenca, nova_senha, confirma]):
            QMessageBox.warning(self, "Erro", "Preencha todos os campos.")
            return

        if nova_senha != confirma:
            QMessageBox.warning(self, "Erro", "As senhas não coincidem.")
            return

        if len(nova_senha) < 8 or not re.search(r'[A-Za-z]', nova_senha) or not re.search(r'\d', nova_senha):
            QMessageBox.warning(self, "Senha Fraca", "A senha precisa ter no mínimo 8 caracteres, com letras e números.")
            return

        dados = {
            "cnpj": cnpj_limpo,
            "token_licenca": licenca,
            "nova_senha": nova_senha
        }

        try:
            response = requests.post(f"{API_BASE_URL}/recuperar_senha", json=dados)
            if response.status_code == 200:
                QMessageBox.information(self, "Sucesso", "Senha atualizada! Faça o login.")
                self.accept()
            else:
                erro = response.json().get("detail", "Erro desconhecido")
                QMessageBox.warning(self, "Erro", erro)
        except requests.exceptions.ConnectionError:
            QMessageBox.critical(self, "Erro Fatal", "Não foi possível conectar à API.")