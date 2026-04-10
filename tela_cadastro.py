import requests
import os
import re
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                               QLineEdit, QPushButton, QMessageBox, QFileDialog)

API_BASE_URL = "http://127.0.0.1:8000"

class TelaCadastro(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SaaS Restaurante - Novo Cadastro")
        self.setFixedSize(350, 550)

        layout = QVBoxLayout()

        lbl_titulo = QLabel("Criar Conta (Requer Licença)")
        lbl_titulo.setObjectName("titulo") # Puxa o estilo global
        layout.addWidget(lbl_titulo)

        self.input_licenca = QLineEdit()
        self.input_licenca.setPlaceholderText("Código da Licença (12 dígitos)")
        layout.addWidget(self.input_licenca)

        self.input_cnpj = QLineEdit()
        self.input_cnpj.setInputMask("99.999.999/9999-99")
        layout.addWidget(self.input_cnpj)

        self.input_nome = QLineEdit()
        self.input_nome.setPlaceholderText("Nome Fantasia")
        layout.addWidget(self.input_nome)
        
        # --- INÍCIO: UPLOAD DE LOGO ---
        self.caminho_logo_absoluto = "" # Guarda o caminho do arquivo
        
        layout_logo = QHBoxLayout()
        self.btn_logo = QPushButton("Selecionar Logo...")
        self.btn_logo.clicked.connect(self.selecionar_logo)
        self.lbl_caminho_logo = QLabel("Nenhuma imagem selecionada")
        self.lbl_caminho_logo.setStyleSheet("color: gray; font-size: 10px;")
        
        layout_logo.addWidget(self.btn_logo)
        layout_logo.addWidget(self.lbl_caminho_logo)
        layout.addLayout(layout_logo)
        # --- FIM: UPLOAD DE LOGO ---

        self.input_login = QLineEdit()
        self.input_login.setPlaceholderText("Criar Usuário Admin")
        layout.addWidget(self.input_login)

        self.input_senha = QLineEdit()
        self.input_senha.setPlaceholderText("Criar Senha")
        self.input_senha.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.input_senha)
        
        # --- INÍCIO: FEEDBACK VISUAL DA SENHA ---
        # Dispara a validação a cada tecla que o usuário digita
        self.input_senha.textChanged.connect(self.validar_senha_tempo_real)

        self.lbl_regra_tamanho = QLabel("❌ Mínimo de 8 caracteres")
        self.lbl_regra_letra = QLabel("❌ Pelo menos 1 letra")
        self.lbl_regra_numero = QLabel("❌ Pelo menos 1 número")
        
        estilo_invalido = "color: gray; font-size: 11px;"
        self.lbl_regra_tamanho.setStyleSheet(estilo_invalido)
        self.lbl_regra_letra.setStyleSheet(estilo_invalido)
        self.lbl_regra_numero.setStyleSheet(estilo_invalido)
        
        layout.addWidget(self.lbl_regra_tamanho)
        layout.addWidget(self.lbl_regra_letra)
        layout.addWidget(self.lbl_regra_numero)
        # --- FIM: FEEDBACK VISUAL DA SENHA ---

        self.btn_cadastrar = QPushButton("Finalizar Cadastro")
        self.btn_cadastrar.setObjectName("btn_destaque") # Amarelo
        self.btn_cadastrar.clicked.connect(self.fazer_cadastro)
        layout.addWidget(self.btn_cadastrar)

        self.btn_voltar = QPushButton("Voltar para o Login")
        self.btn_voltar.clicked.connect(self.reject)
        layout.addWidget(self.btn_voltar)

        self.setLayout(layout)
        
    def selecionar_logo(self):
        # Abre a raiz do projeto de forma dinâmica usando caminhos absolutos
        diretorio_inicial = os.path.abspath(".")
        caminho, _ = QFileDialog.getOpenFileName(self, "Selecionar Logo da Empresa", diretorio_inicial, "Imagens (*.png *.jpg *.jpeg)")
        
        if caminho:
            self.caminho_logo_absoluto = os.path.abspath(caminho)
            nome_arquivo = os.path.basename(self.caminho_logo_absoluto)
            self.lbl_caminho_logo.setText(nome_arquivo) # Mostra só o nome pra não poluir a tela
            self.lbl_caminho_logo.setStyleSheet("color: green; font-size: 10px; font-weight: bold;")

    def validar_senha_tempo_real(self, texto):
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

    def fazer_cadastro(self):
        licenca = self.input_licenca.text().strip()
        cnpj_cru = self.input_cnpj.text().strip()
        cnpj = re.sub(r'[^0-9]', '', cnpj_cru) # Tira os pontos da máscara para enviar só número pra API
        nome = self.input_nome.text().strip()
        login = self.input_login.text().strip()
        senha = self.input_senha.text()

        if not all([licenca, cnpj, nome, login, senha]):
            QMessageBox.warning(self, "Erro", "Preencha todos os campos.")
            return

        # Validação de Senha (min 8 chars, 1 letra, 1 numero)
        if len(senha) < 8 or not re.search(r'[A-Za-z]', senha) or not re.search(r'\d', senha):
            QMessageBox.warning(self, "Senha Fraca", "A senha precisa ter no mínimo 8 caracteres, contendo letras e números.")
            return

        dados = {
            "token_licenca": licenca,
            "cnpj": cnpj,
            "nome_fantasia": nome,
            "login": login,
            "senha": senha,
            "logo_url": self.caminho_logo_absoluto # Envia o caminho absoluto da imagem selecionada
        }

        try:
            # Dispara os dados para a API
            response = requests.post(f"{API_BASE_URL}/cadastrar", json=dados)
            if response.status_code == 200:
                QMessageBox.information(self, "Sucesso", "Cadastro realizado! Faça login para entrar.")
                self.accept() # Fecha a tela de cadastro
            else:
                erro = response.json().get("detail", "Erro desconhecido")
                QMessageBox.warning(self, "Erro no Cadastro", erro)
        except requests.exceptions.ConnectionError:
            QMessageBox.critical(self, "Erro Fatal", "Não foi possível conectar à API.")