import sys
import os
import requests
from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QComboBox, QLineEdit, QPushButton, QMessageBox
from PySide6.QtCore import Qt, QThread, Signal

class WorkerFeedback(QThread):
    sucesso = Signal(str)
    erro = Signal(str)

    def __init__(self, api_url, cliente_id, estrelas, comentario):
        super().__init__()
        self.api_url = api_url
        self.cliente_id = cliente_id
        self.estrelas = estrelas
        self.comentario = comentario

    def run(self):
        payload = {
            "cliente_id": self.cliente_id,
            "estrelas": self.estrelas,
            "comentario": self.comentario
        }
        try:
            response = requests.post(f"{self.api_url}/feedback", json=payload)
            if response.status_code == 200:
                self.sucesso.emit(response.json().get("mensagem", "Feedback enviado com sucesso!"))
            else:
                self.erro.emit(f"Erro {response.status_code}")
        except Exception as e:
            self.erro.emit(str(e))

class DialogFeedback(QDialog):
    def __init__(self, api_url, cliente_id, plano_atual, parent=None):
        super().__init__(parent)
        self.api_url = api_url
        self.cliente_id = cliente_id
        
        self.setWindowTitle("Sua opinião importa!")
        self.setFixedSize(380, 240)
        
        # Layout nativo e literal padrão
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)
        
        lbl_convite = QLabel(
            f"<b>Gostando do VegaStock {plano_atual}?</b><br><br>"
            "Notamos que seu período de testes está chegando na reta final.<br>"
            "Deixe uma nota e sua sugestão para continuarmos evoluindo!"
        )
        lbl_convite.setAlignment(Qt.AlignCenter)
        lbl_convite.setWordWrap(True)
        layout.addWidget(lbl_convite)
        
        # Seletor nativo de estrelas
        self.combo_estrelas = QComboBox()
        self.combo_estrelas.addItems([
            "5 Estrelas ⭐⭐⭐⭐⭐", 
            "4 Estrelas ⭐⭐⭐⭐", 
            "3 Estrelas ⭐⭐⭐", 
            "2 Estrelas ⭐⭐", 
            "1 Estrela ⭐"
        ])
        layout.addWidget(self.combo_estrelas)
        
        self.input_comentario = QLineEdit()
        self.input_comentario.setPlaceholderText("O que podemos melhorar no app? (Opcional)")
        layout.addWidget(self.input_comentario)
        
        self.btn_enviar = QPushButton("Enviar Avaliação")
        self.btn_enviar.clicked.connect(self.enviar_feedback)
        layout.addWidget(self.btn_enviar)

    def enviar_feedback(self):
        texto_estrela = self.combo_estrelas.currentText()
        estrelas = int(texto_estrela.split()[0])
        comentario = self.input_comentario.text().strip()
        
        self.btn_enviar.setEnabled(False)
        self.btn_enviar.setText("⏳ Enviando avaliação...")
        
        self.worker = WorkerFeedback(self.api_url, self.cliente_id, estrelas, comentario)
        self.worker.sucesso.connect(self.sucesso_envio)
        self.worker.erro.connect(self.erro_envio)
        self.worker.start()

    def sucesso_envio(self, mensagem):
        QMessageBox.information(self, "Obrigado!", mensagem)
        self.accept()

    def erro_envio(self, mensaje):
        self.btn_enviar.setEnabled(True)
        self.btn_enviar.setText("Enviar Avaliação")
        QMessageBox.warning(self, "Aviso", f"Não foi possível processar: {mensaje}")
        self.reject()