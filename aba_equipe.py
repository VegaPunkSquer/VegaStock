from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel

class AbaEquipe(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        
        titulo = QLabel("Equipe (Em construção)")
        titulo.setObjectName("titulo") # Puxa a fonte e cor do estilos.py
        
        layout.addWidget(titulo)
        self.setLayout(layout)