# ==================================================
# VEGASTOCK PRO - DARK THEME (Premium SaaS)
# ==================================================

ESTILO_GLOBAL = """
/* Fundo Geral e Texto Padrão */
QWidget {
    background-color: #121215;
    color: #E0E0E0;
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 14px;
}

/* Janela Principal */
QMainWindow {
    background-color: #121215;
}

/* Títulos e Textos de Destaque */
QLabel#titulo {
    font-size: 26px;
    font-weight: bold;
    color: #FFFFFF;
    margin-bottom: 10px;
}

QLabel#subtitulo {
    font-size: 16px;
    color: #A0A0B0;
}

/* Inputs de Texto (Elegantes e Flat) */
QLineEdit {
    background-color: #1A1A20;
    border: 1px solid #33333E;
    padding: 10px 15px;
    border-radius: 6px;
    color: #FFFFFF;
    font-size: 14px;
}
QLineEdit:focus {
    border: 1px solid #FFD700;
    background-color: #1E1E25;
}

/* Botões Padrão (Dark) */
QPushButton {
    background-color: #24242C;
    border: 1px solid #33333E;
    color: #FFFFFF;
    font-weight: bold;
    padding: 10px 20px;
    border-radius: 6px;
}
QPushButton:hover {
    background-color: #2D2D38;
    border: 1px solid #444455;
}
QPushButton:pressed {
    background-color: #1A1A20;
}

/* Botões de Ação Principal (O Amarelo VegaTech) */
QPushButton#btn_destaque {
    background-color: #FFD700;
    color: #121215;
    border: none;
    font-weight: bold;
    font-size: 15px;
}
QPushButton#btn_destaque:hover {
    background-color: #F4C400;
}
QPushButton#btn_destaque:pressed {
    background-color: #D9AE00;
}

/* Botões de Perigo (Excluir/Sair) */
QPushButton#btn_perigo {
    background-color: #2A1515;
    color: #FF5555;
    border: 1px solid #4A2020;
}
QPushButton#btn_perigo:hover {
    background-color: #FF5555;
    color: #FFFFFF;
}

/* Tabelas (Estoque, Relatórios) */
QTableWidget {
    background-color: #1A1A20;
    alternate-background-color: #1E1E25;
    border: 1px solid #2C2C35;
    border-radius: 6px;
    gridline-color: #2C2C35;
    selection-background-color: #FFD700;
    selection-color: #121215;
}
QHeaderView::section {
    background-color: #24242C;
    color: #A0A0B0;
    padding: 10px;
    border: none;
    border-bottom: 1px solid #2C2C35;
    font-weight: bold;
}

/* Barra de Rolagem (Discreta estilo Mac/Web) */
QScrollBar:vertical {
    border: none;
    background: #121215;
    width: 8px;
    margin: 0px 0px 0px 0px;
}
QScrollBar::handle:vertical {
    background: #33333E;
    min-height: 20px;
    border-radius: 4px;
}
QScrollBar::handle:vertical:hover {
    background: #FFD700;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

/* Menus Laterais (Abas Estilo Dashboard) */
QListWidget {
    background-color: #15151A;
    border: none;
    border-right: 1px solid #2C2C35;
    outline: none;
}
QListWidget::item {
    padding: 15px 20px;
    color: #A0A0B0;
    border-left: 4px solid transparent;
}
QListWidget::item:selected {
    background-color: #1E1E25;
    color: #FFD700;
    border-left: 4px solid #FFD700;
    font-weight: bold;
}
QListWidget::item:hover:!selected {
    background-color: #1A1A20;
    color: #FFFFFF;
}

/* Combobox (Filtros e Seleções) */
QComboBox {
    background-color: #1A1A20;
    border: 1px solid #33333E;
    border-radius: 6px;
    padding: 8px 15px;
    color: #FFFFFF;
}
QComboBox::drop-down {
    border: none;
}
QComboBox QAbstractItemView {
    background-color: #1A1A20;
    color: #FFFFFF;
    selection-background-color: #FFD700;
    selection-color: #121215;
    border: 1px solid #33333E;
}
"""