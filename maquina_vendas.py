import sys
import os
import re
import requests
import webbrowser
from PySide6.QtWidgets import (QApplication, QDialog, QVBoxLayout, QLabel, 
                               QLineEdit, QPushButton, QMessageBox, QComboBox)
from PySide6.QtCore import QTimer
from PySide6.QtGui import QIcon

API_BASE_URL = "https://vegastock.onrender.com"

class MaquinaVendas(QDialog):
    def __init__(self, tela_cadastro_pai=None):
        super().__init__(tela_cadastro_pai)
        self.tela_cadastro_pai = tela_cadastro_pai # Para preencher a licença lá automaticamente
        self.cnpj_limpo_atual = ""
        
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        caminho_icone = os.path.join(BASE_DIR, 'logo.ico')
        
        self.setWindowIcon(QIcon(caminho_icone))
        self.setWindowTitle("Comprar Licença VegaStock")
        self.setFixedSize(380, 350)
        
        layout = QVBoxLayout()
        
        layout.addWidget(QLabel("CNPJ do Estabelecimento:"))
        self.input_cnpj = QLineEdit()
        self.input_cnpj.setInputMask("99.999.999/9999-99")
        layout.addWidget(self.input_cnpj)
        
        layout.addWidget(QLabel("E-mail do Responsável (Para Nota/Recibo):"))
        self.input_email = QLineEdit()
        self.input_email.setPlaceholderText("contato@restaurante.com.br")
        layout.addWidget(self.input_email)

        layout.addWidget(QLabel("Escolha seu Plano:"))
        self.combo_plano = QComboBox()
        self.combo_plano.addItem("Básico - R$ 139/mês (+ R$ 400 Adesão) | 2 Contas", "BASICO")
        self.combo_plano.addItem("PRO - R$ 289/mês (ZERO Adesão) | 6 Contas", "PRO")
        layout.addWidget(self.combo_plano)
        
        self.btn_gerar = QPushButton("Ir para o Pagamento")
        self.btn_gerar.setStyleSheet("background-color: #2196F3; color: white; font-weight: bold; padding: 10px; margin-top: 10px;")
        self.btn_gerar.clicked.connect(self.iniciar_compra)
        layout.addWidget(self.btn_gerar)
        
        self.lbl_status = QLabel("")
        self.lbl_status.setStyleSheet("font-size: 14px; font-weight: bold; color: #ff9800;")
        layout.addWidget(self.lbl_status)
        
        self.setLayout(layout)

        # O "Relógio" que vai ficar perguntando pra API se já pagou
        self.timer_pagamento = QTimer(self)
        self.timer_pagamento.timeout.connect(self.checar_pagamento)

    def iniciar_compra(self):
        cnpj_cru = self.input_cnpj.text().strip()
        self.cnpj_limpo_atual = re.sub(r'[^0-9]', '', cnpj_cru)
        email = self.input_email.text().strip()
        plano = self.combo_plano.currentData()
        
        if len(self.cnpj_limpo_atual) != 14 or not email:
            QMessageBox.warning(self, "Erro", "Preencha o CNPJ corretamente e informe um E-mail válido.")
            return
            
        self.btn_gerar.setEnabled(False)
        self.btn_gerar.setText("Gerando cobrança...")
        
        dados = {
            "cnpj": self.cnpj_limpo_atual,
            "email": email,
            "plano": plano
        }
        
        try:
            resp = requests.post(f"{API_BASE_URL}/comprar_licenca", json=dados)
            if resp.status_code == 200:
                link = resp.json().get("link_pagamento")
                webbrowser.open(link) # Abre o navegador do cliente!
                
                self.lbl_status.setText("⏳ Aguardando pagamento do Pix/Cartão...")
                self.btn_gerar.setText("Aguardando confirmação...")
                
                # Começa a perguntar pra API a cada 5 segundos (5000 ms)
                self.timer_pagamento.start(5000)
            else:
                QMessageBox.critical(self, "Erro", "Não foi possível gerar a cobrança no Asaas.")
                self.btn_gerar.setEnabled(True)
                self.btn_gerar.setText("Ir para o Pagamento")
        except Exception:
            QMessageBox.critical(self, "Erro", "Sem conexão com o servidor.")
            self.btn_gerar.setEnabled(True)
            self.btn_gerar.setText("Ir para o Pagamento")

    def checar_pagamento(self):
        try:
            resp = requests.get(f"{API_BASE_URL}/checar_licenca_nova/{self.cnpj_limpo_atual}")
            if resp.status_code == 200:
                dados = resp.json()
                if dados.get("pago"):
                    self.timer_pagamento.stop() # Para o relógio
                    token = dados.get("token")
                    
                    self.lbl_status.setStyleSheet("font-size: 14px; font-weight: bold; color: green;")
                    self.lbl_status.setText("✅ Pagamento Confirmado!")
                    
                    # Se abriu por dentro da tela de cadastro, já preenche pra ele!
                    if self.tela_cadastro_pai:
                        self.tela_cadastro_pai.input_licenca.setText(token)
                        self.tela_cadastro_pai.input_cnpj.setText(self.input_cnpj.text())
                        
                    QMessageBox.information(self, "Sucesso!", f"Pagamento recebido!\nA sua licença foi gerada: {token}")
                    self.close() # Fecha a vitrine e deixa ele terminar o cadastro
        except:
            pass # Se der erro de rede na checagem, só ignora e tenta de novo no próximo 5 segundos

if __name__ == "__main__":
    app = QApplication(sys.argv)
    janela = MaquinaVendas()
    janela.show()
    sys.exit(app.exec())