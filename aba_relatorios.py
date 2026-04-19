import requests
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QComboBox, QTableWidget, QTableWidgetItem, QHeaderView, 
                               QFrame, QAbstractItemView)
import os
from PySide6.QtCore import Qt, QThread, Signal, QSize
from PySide6.QtGui import QMovie

API_BASE_URL = "https://vegastock.onrender.com"

class WorkerRelatorios(QThread):
    resultado = Signal(dict)
    erro = Signal(str)

    def __init__(self, cliente_id, url_relatorio, atualizar_filtros):
        super().__init__()
        self.cliente_id = cliente_id
        self.url_relatorio = url_relatorio
        self.atualizar_filtros = atualizar_filtros # Flag para saber se puxa os combos ou não

    def run(self):
        try:
            dados = {"atualizar_filtros": self.atualizar_filtros}
            
            # Puxa os filtros de Categoria e Motivo apenas se a tela pedir
            if self.atualizar_filtros:
                r_cat = requests.get(f"{API_BASE_URL}/categorias/{self.cliente_id}")
                r_mot = requests.get(f"{API_BASE_URL}/motivos/{self.cliente_id}")
                
                dados["categorias"] = r_cat.json() if r_cat.status_code == 200 else []
                # Já filtra só as perdas aqui no porão
                motivos = r_mot.json() if r_mot.status_code == 200 else []
                dados["motivos"] = [m for m in motivos if m.get("tipo") == "PERDA"]

            # Puxa a tabela e os KPIs do relatório
            r_rel = requests.get(self.url_relatorio)
            if r_rel.status_code == 200:
                dados["relatorio"] = r_rel.json()
            else:
                # Se falhar, manda um dicionário vazio para não quebrar a tela
                dados["relatorio"] = {"kpis": {}, "tabela": []}

            self.resultado.emit(dados)
        except Exception:
            self.erro.emit("Falha de conexão.")

class AbaRelatorios(QWidget):
    def __init__(self, cliente_dados):
        super().__init__()
        self.cliente_dados = cliente_dados
        layout_principal = QVBoxLayout(self)

        lbl_titulo = QLabel("Análise de Desperdício (Prejuízo)")
        lbl_titulo.setStyleSheet("font-size: 24px; font-weight: bold; color: #333; margin-bottom: 10px;")
        layout_principal.addWidget(lbl_titulo, alignment=Qt.AlignCenter)

        # ==========================================
        # 1. OS CARTÕES DE IMPACTO (KPIs)
        # ==========================================
        layout_kpis = QHBoxLayout()

        # Função interna para desenhar os cartões
        def criar_cartao(titulo, cor_borda, cor_valor):
            frame = QFrame()
            frame.setStyleSheet(f"""
                QFrame {{
                    background-color: #fff; border-radius: 8px;
                    border-left: 5px solid {cor_borda};
                    border-top: 1px solid #ddd; border-right: 1px solid #ddd; border-bottom: 1px solid #ddd;
                }}
            """)
            layout_frame = QVBoxLayout(frame)
            
            lbl_tit = QLabel(titulo)
            lbl_tit.setStyleSheet("font-size: 14px; color: #666; font-weight: bold; border: none;")
            
            lbl_val = QLabel("Carregando...")
            lbl_val.setStyleSheet(f"font-size: 22px; font-weight: bold; color: {cor_valor}; border: none;")
            
            lbl_sub = QLabel("-")
            lbl_sub.setStyleSheet("font-size: 12px; color: #999; border: none;")
            
            layout_frame.addWidget(lbl_tit)
            layout_frame.addWidget(lbl_val)
            layout_frame.addWidget(lbl_sub)
            
            return frame, lbl_val, lbl_sub

        # Criando os 3 cartões
        self.card_prejuizo, self.val_prejuizo, self.sub_prejuizo = criar_cartao("PREJUÍZO TOTAL", "#d32f2f", "#d32f2f") # Vermelho
        self.card_vilao, self.val_vilao, self.sub_vilao = criar_cartao("PRODUTO MAIS PERDIDO", "#ff9800", "#333") # Laranja
        self.card_motivo, self.val_motivo, self.sub_motivo = criar_cartao("MOTIVO PRINCIPAL", "#f44336", "#333") # Vermelho Claro

        layout_kpis.addWidget(self.card_prejuizo)
        layout_kpis.addWidget(self.card_vilao)
        layout_kpis.addWidget(self.card_motivo)
        layout_principal.addLayout(layout_kpis)

        # ==========================================
        # 2. CONTROLES E FILTROS
        # ==========================================
        layout_filtros = QHBoxLayout()
        layout_filtros.setContentsMargins(0, 15, 0, 10)

        self.combo_tempo = QComboBox()
        self.combo_tempo.addItems(["Últimos 30 Dias", "Últimos 7 Dias", "Hoje"])
        self.combo_tempo.currentIndexChanged.connect(self.carregar_relatorio)

        self.combo_cat = QComboBox()
        self.combo_cat.addItem("Todas as Categorias", None)
        self.combo_cat.currentIndexChanged.connect(self.carregar_relatorio)

        self.combo_motivo = QComboBox()
        self.combo_motivo.addItem("Todos os Motivos", None)
        self.combo_motivo.currentIndexChanged.connect(self.carregar_relatorio)

        layout_filtros.addWidget(QLabel("Período:"))
        layout_filtros.addWidget(self.combo_tempo)
        layout_filtros.addWidget(QLabel("   Categoria:"))
        layout_filtros.addWidget(self.combo_cat)
        layout_filtros.addWidget(QLabel("   Motivo:"))
        layout_filtros.addWidget(self.combo_motivo)
        layout_filtros.addStretch()

        layout_principal.addLayout(layout_filtros)

        # ==========================================
        # 3. A TABELA INVESTIGATIVA (RAIO-X)
        # ==========================================
        self.tabela = QTableWidget()
        self.tabela.setColumnCount(7) # <--- Aumentou pra 7
        self.tabela.setHorizontalHeaderLabels(["Produto", "Categoria", "Qtd Perdida", "Motivo da Baixa", "Prejuízo (R$)", "Responsável", "Data"]) # <--- Nova coluna
        self.tabela.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabela.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tabela.setEditTriggers(QAbstractItemView.NoEditTriggers)
        
        # Pinta o cabeçalho para dar um ar mais "Relatório"
        self.tabela.setStyleSheet("QHeaderView::section { background-color: #f0f0f0; font-weight: bold; }")

        layout_principal.addWidget(self.tabela)

    # --- FUNÇÕES ---

    def showEvent(self, event):
        super().showEvent(event)
        # Ao abrir a aba, avisa o trabalhador para trazer o relatório E preencher os combos
        self.carregar_dados(atualizar_filtros=True)

    def carregar_relatorio(self):
        # Gatilho de quando o usuário muda um combobox. Não recarrega os combos, só a tabela.
        self.carregar_dados(atualizar_filtros=False)

    def carregar_dados(self, atualizar_filtros=True):
        # 1. Congela a tela no modo "Carregando"
        self.val_prejuizo.setText("...")
        self.sub_prejuizo.setText("Calculando...")
        self.val_vilao.setText("...")
        self.sub_vilao.setText("Investigando...")
        self.val_motivo.setText("...")
        self.sub_motivo.setText("Buscando...")

        # 2. O Show do GIF na Tabela
        self.tabela.setRowCount(1)
        lbl_gif = QLabel()
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        caminho_gif = os.path.join(BASE_DIR, 'hourglass.gif')
        
        self.movie = QMovie(caminho_gif)
        self.movie.setScaledSize(QSize(20, 20))
        lbl_gif.setMovie(self.movie)
        lbl_gif.setAlignment(Qt.AlignCenter)
        self.movie.start()
        
        # Coluna 0 é a de Produtos, sem mistério e sem estar oculta!
        self.tabela.setCellWidget(0, 0, lbl_gif) 
        self.tabela.setItem(0, 1, QTableWidgetItem("..."))
        self.tabela.setItem(0, 2, QTableWidgetItem("..."))
        self.tabela.setItem(0, 3, QTableWidgetItem("Puxando relatório dos EUA..."))
        self.tabela.setItem(0, 4, QTableWidgetItem("..."))
        self.tabela.setItem(0, 5, QTableWidgetItem("..."))
        self.tabela.setItem(0, 6, QTableWidgetItem("...")) # <--- Coluna 6 (Data) pulou pra cá

        # 3. Constrói a URL lendo os filtros
        txt_tempo = self.combo_tempo.currentText()
        dias = 30
        if txt_tempo == "Últimos 7 Dias": dias = 7
        elif txt_tempo == "Hoje": dias = 1

        url = f"{API_BASE_URL}/relatorios/desperdicio/{self.cliente_dados['cliente_id']}?dias={dias}"
        
        # Lê categoria e motivo só se eles já existirem no combobox
        if self.combo_cat.count() > 0:
            cat_id = self.combo_cat.currentData()
            if cat_id: url += f"&categoria_id={cat_id}"
            
        if self.combo_motivo.count() > 0:
            motivo_id = self.combo_motivo.currentData()
            if motivo_id: url += f"&motivo_id={motivo_id}"

        # 4. Envia o trabalhador pro porão
        self.worker = WorkerRelatorios(self.cliente_dados['cliente_id'], url, atualizar_filtros)
        self.worker.resultado.connect(self.atualizar_tela)
        self.worker.start()

    def atualizar_tela(self, dados):
        # 1. Preenche os Combos (Só roda na primeira vez)
        if dados.get("atualizar_filtros"):
            self.combo_cat.blockSignals(True)
            self.combo_motivo.blockSignals(True)
            
            while self.combo_cat.count() > 1: self.combo_cat.removeItem(1)
            while self.combo_motivo.count() > 1: self.combo_motivo.removeItem(1)
            
            for cat in dados.get("categorias", []):
                self.combo_cat.addItem(cat["nome"], cat["id"])
            for mot in dados.get("motivos", []):
                self.combo_motivo.addItem(mot["descricao"], mot["id"])
                
            self.combo_cat.blockSignals(False)
            self.combo_motivo.blockSignals(False)

        # 2. Preenche os Cartões (KPIs)
        rel = dados.get("relatorio", {})
        kpis = rel.get("kpis", {"total_prejuizo": 0, "top_produto": "-", "top_produto_valor": 0, "top_motivo": "-", "top_motivo_valor": 0})
        
        self.val_prejuizo.setText(f"R$ {kpis.get('total_prejuizo', 0):.2f}".replace('.', ','))
        self.sub_prejuizo.setText("Somatório das perdas")

        self.val_vilao.setText(kpis.get("top_produto", "-"))
        self.sub_vilao.setText(f"Custou R$ {kpis.get('top_produto_valor', 0):.2f}")

        self.val_motivo.setText(kpis.get("top_motivo", "-"))
        self.sub_motivo.setText(f"Custou R$ {kpis.get('top_motivo_valor', 0):.2f}")

        # 3. Preenche a Tabela (Esmagando o GIF)
        tabela_dados = rel.get("tabela", [])
        self.tabela.setRowCount(0)
        for i, linha in enumerate(tabela_dados):
            self.tabela.insertRow(i)
            self.tabela.setItem(i, 0, QTableWidgetItem(linha["produto"]))
            self.tabela.setItem(i, 1, QTableWidgetItem(linha["categoria"]))
            self.tabela.setItem(i, 2, QTableWidgetItem(f"{linha['quantidade_perdida']} {linha['unidade']}"))
            self.tabela.setItem(i, 3, QTableWidgetItem(linha["motivo"]))
            
            item_valor = QTableWidgetItem(f"R$ {linha['custo_total_perdido_rs']:.2f}")
            item_valor.setForeground(Qt.darkRed)
            self.tabela.setItem(i, 4, item_valor)
            
            # Puxa o nome do responsável e joga na coluna 5
            self.tabela.setItem(i, 5, QTableWidgetItem(linha.get("responsavel", "Desconhecido")))
            self.tabela.setItem(i, 6, QTableWidgetItem(linha["data"])) # A data vai pra última (6)