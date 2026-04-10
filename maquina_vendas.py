import sys
import hashlib
import random
import string
import re
from datetime import datetime, timedelta
from PySide6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QLabel, 
                               QLineEdit, QPushButton, QMessageBox)
from database import engine, Base, SessionLocal
import models

# Garante que o banco de dados e as tabelas existam
Base.metadata.create_all(bind=engine)

class MaquinaVendas(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Gerador de Licenças B2B")
        self.setFixedSize(350, 250)
        
        layout = QVBoxLayout()
        
        layout.addWidget(QLabel("CNPJ do Cliente (pode usar pontos/barras):"))
        
        self.input_cnpj = QLineEdit()
        self.input_cnpj.setInputMask("99.999.999/9999-99") # Máscara visual nativa do Qt
        layout.addWidget(self.input_cnpj)
        # Permite apertar Enter para gerar
        self.input_cnpj.returnPressed.connect(self.gerar_licenca)
        
        self.btn_gerar = QPushButton("Gerar Licença de 48h")
        self.btn_gerar.setStyleSheet("background-color: #FFD700; color: #000000; font-weight: bold; padding: 8px;")
        self.btn_gerar.clicked.connect(self.gerar_licenca)
        layout.addWidget(self.btn_gerar)
        
        self.lbl_resultado = QLabel("")
        self.lbl_resultado.setStyleSheet("font-size: 12px; font-weight: bold; color: green;")
        layout.addWidget(self.lbl_resultado)
        
        from PySide6.QtWidgets import QHBoxLayout # Adiciona o layout horizontal para alinhar o botão
        layout_copiar = QHBoxLayout()
        
        self.input_token_gerado = QLineEdit()
        self.input_token_gerado.setReadOnly(True)
        self.input_token_gerado.setPlaceholderText("O código da licença aparecerá aqui")
        
        self.btn_copiar = QPushButton("Copiar")
        self.btn_copiar.setStyleSheet("background-color: #000000; color: #FFFFFF; font-weight: bold;")
        self.btn_copiar.clicked.connect(self.copiar_licenca)
        
        layout_copiar.addWidget(self.input_token_gerado)
        layout_copiar.addWidget(self.btn_copiar)
        layout.addLayout(layout_copiar)
        
        self.setLayout(layout)

    def limpar_cnpj(self, cnpj_sujo):
        # Remove tudo que não for número (pontos, barras, traços, espaços)
        return re.sub(r'[^0-9]', '', cnpj_sujo)

    def gerar_licenca(self):
        cnpj_cru = self.input_cnpj.text().strip()
        cnpj_limpo = self.limpar_cnpj(cnpj_cru)
        
        if len(cnpj_limpo) != 14:
            QMessageBox.warning(self, "Erro", "CNPJ inválido. Precisa ter exatamente 14 números.")
            return
            
        # Mistura maiúsculas, minúsculas e números
        caracteres = string.ascii_letters + string.digits
        token_limpo = ''.join(random.choice(caracteres) for _ in range(12))
        expiracao = datetime.utcnow() + timedelta(hours=48)
        
        try:
            db = SessionLocal()
            nova_licenca = models.Licenca(
                token=token_limpo, # <--- CORTAMOS O HASH. Salva exatamente os 12 caracteres gerados.
                usada=False,
                cnpj_esperado=cnpj_limpo,
                data_expiracao=expiracao
            )
            db.add(nova_licenca)
            db.commit()
            db.close()
            
            self.lbl_resultado.setText(f"Salvo no banco! Expira em: {expiracao.strftime('%d/%m/%Y %H:%M')}")
            self.input_token_gerado.setText(token_limpo)
            QMessageBox.information(self, "Sucesso", "Licença gerada com sucesso! Entregue o código ao cliente.")
            
        except Exception as e:
            QMessageBox.critical(self, "Erro Fatal", f"Erro ao salvar no banco: {str(e)}")
            
    def copiar_licenca(self):
        texto = self.input_token_gerado.text()
        if texto:
            QApplication.clipboard().setText(texto)
            self.btn_copiar.setText("Copiado!")
            self.btn_copiar.setStyleSheet("background-color: green; color: white; font-weight: bold;")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    janela = MaquinaVendas()
    janela.show()
    sys.exit(app.exec())