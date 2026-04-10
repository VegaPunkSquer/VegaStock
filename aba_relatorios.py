from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel

class AbaRelatorios(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        
        titulo = QLabel("Relatórios (Em construção)")
        titulo.setObjectName("titulo") # Puxa a fonte e cor do estilos.py
        
        layout.addWidget(titulo)
        self.setLayout(layout)