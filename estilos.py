# Paleta da Empresa: Fundo Branco, Textos e Bordas Pretas, Destaques em Amarelo
ESTILO_GLOBAL = """
QWidget {
    background-color: #FFFFFF;
    color: #000000;
    font-family: Arial, sans-serif;
}
QLineEdit {
    border: 1px solid #000000;
    padding: 6px;
    border-radius: 4px;
}
QPushButton {
    background-color: #000000;
    color: #FFFFFF;
    font-weight: bold;
    padding: 8px;
    border-radius: 4px;
}
QPushButton:hover {
    background-color: #333333;
}
/* Botões de Ação Principal (Entrar, Salvar, Confirmar) */
QPushButton#btn_destaque {
    background-color: #FFD700; /* Amarelo Padrão */
    color: #000000;
}
QPushButton#btn_destaque:hover {
    background-color: #E6C200;
}
QLabel#titulo {
    font-size: 18px;
    font-weight: bold;
}
"""