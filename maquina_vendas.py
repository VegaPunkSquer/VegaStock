import sys
import os
import re
import requests
import webbrowser
from PySide6.QtWidgets import (QApplication, QDialog, QVBoxLayout, QLabel, QFrame, 
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
        self.setFixedSize(420, 350)
        
        layout = QVBoxLayout()
        
        # --- O SEU PADRÃO REAL (QFrame com borda e fundo claro) ---
        frame_compra = QFrame()
        frame_compra.setStyleSheet("background-color: #f9f9f9; border: 1px solid #ddd; border-radius: 5px;")
        layout_form = QVBoxLayout(frame_compra)
        
        lbl_cnpj = QLabel("CNPJ do Estabelecimento:")
        lbl_cnpj.setStyleSheet("font-weight: bold; border: none;")
        layout_form.addWidget(lbl_cnpj)
        
        self.input_cnpj = QLineEdit()
        self.input_cnpj.setInputMask("99.999.999/9999-99")
        self.input_cnpj.setStyleSheet("padding: 5px; border: 1px solid #ccc; background-color: #fff;")
        layout_form.addWidget(self.input_cnpj)
        
        lbl_email = QLabel("E-mail do Responsável (Para Nota/Recibo):")
        lbl_email.setStyleSheet("font-weight: bold; border: none; margin-top: 10px;")
        layout_form.addWidget(lbl_email)
        
        self.input_email = QLineEdit()
        self.input_email.setPlaceholderText("contato@restaurante.com.br")
        self.input_email.setStyleSheet("padding: 5px; border: 1px solid #ccc; background-color: #fff;")
        layout_form.addWidget(self.input_email)
        
        lbl_plano = QLabel("Escolha seu Plano:")
        lbl_plano.setStyleSheet("font-weight: bold; border: none; margin-top: 10px;")
        layout_form.addWidget(lbl_plano)
        
        self.combo_plano = QComboBox()
        self.combo_plano.addItem("Básico (Mensal) - R$ 139/mês + R$ 400 Adesão", "BASICO_MENSAL")
        self.combo_plano.addItem("Básico (Semestral) - 6x R$ 99 (R$ 594 total) + Adesão", "BASICO_SEMESTRAL")
        self.combo_plano.addItem("PRO (Mensal) - R$ 289/mês | ZERO Adesão", "PRO_MENSAL")
        self.combo_plano.addItem("PRO (Semestral) - 6x R$ 189 (R$ 1134 total) | ZERO Adesão", "PRO_SEMESTRAL")
        self.combo_plano.setStyleSheet("padding: 5px; border: 1px solid #ccc; background-color: #fff;")
        layout_form.addWidget(self.combo_plano)
        
        layout.addWidget(frame_compra)
        
        # O Botão de Venda
        self.btn_gerar = QPushButton("Ir para o Pagamento Seguro")
        self.btn_gerar.setStyleSheet("background-color: #009EE3; color: white; font-weight: bold; padding: 12px; margin-top: 10px; border-radius: 5px;")
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