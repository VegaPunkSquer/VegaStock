from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel

class AbaCatalogo(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        
        titulo = QLabel("Catálogo (Em construção)")
        titulo.setObjectName("titulo") # Puxa a fonte e cor do estilos.py
        
        layout.addWidget(titulo)
        self.setLayout(layout)