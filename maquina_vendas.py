import sys
import os
import re
import requests
import webbrowser
from PySide6.QtWidgets import (QApplication, QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                               QLineEdit, QPushButton, QMessageBox, QFrame, QRadioButton, QButtonGroup)
from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QIcon

API_BASE_URL = "https://vegap-vega-stock.hf.space"
class MaquinaVendas(QDialog):
    def __init__(self, tela_cadastro_pai=None):
        super().__init__(tela_cadastro_pai)
        self.tela_cadastro_pai = tela_cadastro_pai
        self.cnpj_limpo_atual = ""
        
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        caminho_icone = os.path.join(BASE_DIR, "assets", 'logo.ico')
        
        self.setWindowIcon(QIcon(caminho_icone))
        self.setWindowTitle("VegaStock - Comprar Licença")
        self.setFixedSize(850, 520) # Tamanho exato para caber os 4 cartões confortavelmente
        
        # TEMA ESCURO (Igual ao seu Upgrade PRO)
        self.setStyleSheet("background-color: #1a1a1f; color: white; font-family: Arial;")
        
        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(20, 20, 20, 20)
        
        lbl_titulo = QLabel("VegaStock - Comprar Licença B2B")
        lbl_titulo.setStyleSheet("font-size: 20px; font-weight: bold; border: none; margin-bottom: 10px;")
        layout_principal.addWidget(lbl_titulo, alignment=Qt.AlignCenter)
        
        # --- DADOS DO CLIENTE (Lado a Lado para ficar limpo) ---
        layout_dados = QHBoxLayout()
        layout_dados.setSpacing(20)
        
        layout_cnpj = QVBoxLayout()
        lbl_cnpj = QLabel("CNPJ do Estabelecimento:")
        lbl_cnpj.setStyleSheet("color: #aaa; font-weight: bold; border: none;")
        self.input_cnpj = QLineEdit()
        self.input_cnpj.setInputMask("99.999.999/9999-99")
        self.input_cnpj.setStyleSheet("background-color: #2b2b36; border: 1px solid #333; border-radius: 5px; padding: 10px; color: white; font-size: 14px;")
        layout_cnpj.addWidget(lbl_cnpj)
        layout_cnpj.addWidget(self.input_cnpj)
        
        layout_email = QVBoxLayout()
        lbl_email = QLabel("E-mail do Responsável:")
        lbl_email.setStyleSheet("color: #aaa; font-weight: bold; border: none;")
        self.input_email = QLineEdit()
        self.input_email.setPlaceholderText("contato@restaurante.com.br")
        self.input_email.setStyleSheet("background-color: #2b2b36; border: 1px solid #333; border-radius: 5px; padding: 10px; color: white; font-size: 14px;")
        layout_email.addWidget(lbl_email)
        layout_email.addWidget(self.input_email)
        
        layout_dados.addLayout(layout_cnpj)
        layout_dados.addLayout(layout_email)
        layout_principal.addLayout(layout_dados)
        
        layout_principal.addSpacing(15)
        
        lbl_planos = QLabel("Escolha seu Plano:")
        lbl_planos.setStyleSheet("font-size: 16px; font-weight: bold; border: none;")
        layout_principal.addWidget(lbl_planos)

        # --- OS CARTÕES DE PLANOS (A estética que você criou) ---
        layout_cards = QHBoxLayout()
        layout_cards.setSpacing(15)
        
        self.grupo_planos = QButtonGroup(self)
        self.chaves_api = []
        
        # Dados: (Chave API, Título, Total, Subtexto, Info Extra, Destaque)
        planos_info = [
            ("BASICO_MENSAL", "Básico Mensal", "R$ 139,00", "+ R$ 400 Adesão", "2 Contas", False),
            ("BASICO_SEMESTRAL", "Básico Semestral", "R$ 594,00", "+ R$ 400 Adesão", "2 Contas (R$ 99/mês)", False),
            ("PRO_MENSAL", "PRO Mensal", "R$ 289,00", "ZERO Adesão", "6 Contas", False),
            ("PRO_SEMESTRAL", "PRO Semestral\n⭐️ MELHOR PREÇO", "R$ 1.134,00", "ZERO Adesão", "6 Contas (R$ 189/mês)", True)
        ]
        
        for i, (chave, titulo, total, subtexto, extra, destaque) in enumerate(planos_info):
            frame = QFrame()
            borda = "2px solid #5c85d6" if destaque else "1px solid #333"
            bg_color = "#2b2b36" if destaque else "#25252c"
            
            frame.setStyleSheet(f"""
                QFrame {{
                    background-color: {bg_color};
                    border: {borda};
                    border-radius: 12px;
                }}
            """)
            
            card_layout = QVBoxLayout(frame)
            card_layout.setContentsMargins(15, 20, 15, 20)
            card_layout.setSpacing(10)
            
            rb = QRadioButton(titulo)
            rb.setStyleSheet("""
                QRadioButton { 
                    background: transparent;  /* <--- A MÁGICA ESTÁ AQUI */
                    font-size: 14px; 
                    font-weight: bold; 
                    border: none; 
                    padding-bottom: 5px; 
                }
                QRadioButton::indicator { 
                    width: 14px; height: 14px; border-radius: 8px; 
                    border: 2px solid #aaa; background-color: transparent; 
                }
                QRadioButton::indicator:checked { 
                    border: 2px solid #FFD700; background-color: #FFD700; 
                }
            """)
            if i == 0: rb.setChecked(True)
            self.grupo_planos.addButton(rb, i)
            card_layout.addWidget(rb, alignment=Qt.AlignHCenter)
            
            lbl_sub = QLabel("Valor do pacote:")
            lbl_sub.setStyleSheet("color: #aaa; font-size: 11px; border: none;")
            card_layout.addWidget(lbl_sub, alignment=Qt.AlignHCenter)
            
            lbl_total = QLabel(total)
            lbl_total.setStyleSheet("font-size: 20px; font-weight: bold; border: none;")
            card_layout.addWidget(lbl_total, alignment=Qt.AlignHCenter)
            
            lbl_mes = QLabel(subtexto)
            lbl_mes.setStyleSheet("color: #FFD700; font-size: 11px; font-weight: bold; border: none; margin-top: 5px;")
            card_layout.addWidget(lbl_mes, alignment=Qt.AlignHCenter)
            
            lbl_eco = QLabel(extra)
            lbl_eco.setStyleSheet("color: #4CAF50; font-size: 11px; font-weight: bold; border: none;")
            card_layout.addWidget(lbl_eco, alignment=Qt.AlignHCenter)
                
            layout_cards.addWidget(frame)
            self.chaves_api.append(chave)
            
        layout_principal.addLayout(layout_cards)
        layout_principal.addSpacing(15)
        
        # --- BOTÃO DE PAGAR ---
        self.btn_gerar = QPushButton("GERAR PAGAMENTO SEGURO")
        self.btn_gerar.setStyleSheet("background-color: #009EE3; color: white; font-weight: bold; padding: 15px; font-size: 14px; border-radius: 5px;")
        self.btn_gerar.clicked.connect(self.iniciar_compra)
        layout_principal.addWidget(self.btn_gerar)
        
        self.lbl_status = QLabel("")
        self.lbl_status.setStyleSheet("font-size: 14px; font-weight: bold; color: #FFD700; border: none;")
        layout_principal.addWidget(self.lbl_status, alignment=Qt.AlignCenter)

        # O radar
        self.timer_pagamento = QTimer(self)
        self.timer_pagamento.timeout.connect(self.checar_pagamento)

    def iniciar_compra(self):
        cnpj_cru = self.input_cnpj.text().strip()
        self.cnpj_limpo_atual = re.sub(r'[^0-9]', '', cnpj_cru)
        email = self.input_email.text().strip()
        
        id_selecionado = self.grupo_planos.checkedId()
        plano_escolhido = self.chaves_api[id_selecionado]
        
        if len(self.cnpj_limpo_atual) != 14 or not email:
            QMessageBox.warning(self, "Erro", "Preencha o CNPJ corretamente e informe um E-mail válido.")
            return
            
        self.btn_gerar.setEnabled(False)
        self.btn_gerar.setText("⏳ GERANDO COBRANÇA NO ASAAS...")
        self.btn_gerar.setStyleSheet("background-color: #555; color: white; font-weight: bold; padding: 15px; font-size: 14px; border-radius: 5px;")
        
        dados = {
            "cnpj": self.cnpj_limpo_atual,
            "email": email,
            "plano": plano_escolhido
        }
        
        try:
            resp = requests.post(f"{API_BASE_URL}/comprar_licenca", json=dados)
            if resp.status_code == 200:
                link = resp.json().get("link_pagamento")
                webbrowser.open(link)
                
                self.lbl_status.setText("⏳ Aguardando pagamento no Pix/Cartão (verifique o navegador)...")
                self.btn_gerar.setText("⏳ AGUARDANDO CONFIRMAÇÃO...")
                
                self.timer_pagamento.start(5000)
            else:
                QMessageBox.critical(self, "Erro", f"Não foi possível gerar a cobrança.\nDetalhe: {resp.text}")
                self.btn_gerar.setEnabled(True)
                self.btn_gerar.setText("GERAR PAGAMENTO SEGURO")
                self.btn_gerar.setStyleSheet("background-color: #009EE3; color: white; font-weight: bold; padding: 15px; font-size: 14px; border-radius: 5px;")
        except Exception:
            QMessageBox.critical(self, "Erro", "Sem conexão com o servidor.")
            self.btn_gerar.setEnabled(True)
            self.btn_gerar.setText("GERAR PAGAMENTO SEGURO")
            self.btn_gerar.setStyleSheet("background-color: #009EE3; color: white; font-weight: bold; padding: 15px; font-size: 14px; border-radius: 5px;")

    def checar_pagamento(self):
        try:
            resp = requests.get(f"{API_BASE_URL}/checar_licenca_nova/{self.cnpj_limpo_atual}")
            if resp.status_code == 200:
                dados = resp.json()
                if dados.get("pago"):
                    self.timer_pagamento.stop() 
                    token = dados.get("token")
                    
                    self.lbl_status.setStyleSheet("font-size: 14px; font-weight: bold; color: #4CAF50; border: none;")
                    self.lbl_status.setText("✅ Pagamento Confirmado!")
                    
                    if self.tela_cadastro_pai:
                        self.tela_cadastro_pai.input_licenca.setText(token)
                        self.tela_cadastro_pai.input_cnpj.setText(self.input_cnpj.text())
                        
                    QMessageBox.information(self, "Sucesso!", f"Pagamento recebido!\nA sua licença foi gerada: {token}")
                    self.accept()
        except:
            pass

if __name__ == "__main__":
    app = QApplication(sys.argv)
    janela = MaquinaVendas()
    janela.show()
    sys.exit(app.exec())