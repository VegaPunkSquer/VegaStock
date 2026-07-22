# Paleta da Empresa: Light Premium (SaaS Design)
ESTILO_GLOBAL = """
/* Fundo Geral e Tipografia */
QWidget {
    background-color: #F8FAFC;
    color: #0F172A;
    font-family: 'Segoe UI', -apple-system, sans-serif;
}

/* Títulos */
QLabel#titulo {
    font-size: 22px;
    font-weight: 800;
    color: #0F172A;
}

/* Inputs, SpinBoxes e Comboboxes */
QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox {
    background-color: #FFFFFF;
    border: 1px solid #CBD5E1;
    border-radius: 6px;
    padding: 4px 12px;
    min-height: 28px;
    color: #0F172A;
    selection-background-color: #FFD700;
    selection-color: #000000;
}
QLineEdit:hover, QComboBox:hover, QSpinBox:hover, QDoubleSpinBox:hover {
    border: 1px solid #94A3B8;
}
QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus {
    border: 2px solid #FFD700;
    background-color: #FFFFFF;
}
QComboBox::drop-down {
    border: none;
    width: 20px;
}

/* Botões Padrão */
QPushButton {
    background-color: #0F172A;
    color: #F8FAFC;
    border: none;
    border-radius: 6px;
    padding: 8px 16px;
    font-weight: 600;
}
QPushButton:hover {
    background-color: #1E293B;
}
QPushButton:pressed {
    background-color: #000000;
}

/* Botão de Destaque */
QPushButton#btn_destaque {
    background-color: #FFD700;
    color: #000000;
    font-weight: 700;
}
QPushButton#btn_destaque:hover {
    background-color: #FACC15;
}
QPushButton#btn_destaque:pressed {
    background-color: #EAB308;
}

/* DESIGN 1: TABELAS CLEAN (Sem grade dura do Excel) */
QTableWidget {
    background-color: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 8px;
    gridline-color: transparent; 
}
QTableWidget::item {
    border-bottom: 1px solid #F1F5F9; /* Linhas horizontais super suaves */
    padding: 5px;
}
QTableWidget::item:selected {
    background-color: #FEF08A;
    color: #0F172A;
}
QHeaderView::section {
    background-color: #F8FAFC;
    color: #64748B;
    font-weight: 700;
    border: none;
    border-bottom: 2px solid #E2E8F0;
    padding: 10px;
}

/* DESIGN 2: BARRAS DE ROLAGEM MINIMALISTAS (Scrollbars) */
QScrollBar:vertical {
    border: none;
    background: transparent;
    width: 6px;
    margin: 0px;
}
QScrollBar::handle:vertical {
    background: #CBD5E1;
    border-radius: 3px;
    min-height: 20px;
}
QScrollBar::handle:vertical:hover {
    background: #94A3B8;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}
"""