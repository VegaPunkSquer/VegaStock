import requests
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QComboBox, QTableWidget, QTableWidgetItem, QHeaderView, 
                               QFrame, QAbstractItemView)
from PySide6.QtCore import Qt

API_BASE_URL = "https://vegastock.onrender.com"

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
        self.tabela.setColumnCount(6)
        self.tabela.setHorizontalHeaderLabels(["Produto", "Categoria", "Qtd Perdida", "Motivo da Baixa", "Prejuízo (R$)", "Data"])
        self.tabela.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabela.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tabela.setEditTriggers(QAbstractItemView.NoEditTriggers)
        
        # Pinta o cabeçalho para dar um ar mais "Relatório"
        self.tabela.setStyleSheet("QHeaderView::section { background-color: #f0f0f0; font-weight: bold; }")

        layout_principal.addWidget(self.tabela)

    # --- FUNÇÕES ---

    def showEvent(self, event):
        super().showEvent(event)
        self.carregar_filtros()
        self.carregar_relatorio()

    def carregar_filtros(self):
        # Desliga os gatilhos pra não recarregar a tabela 10x enquanto monta os filtros
        self.combo_cat.blockSignals(True)
        self.combo_motivo.blockSignals(True)
        
        # Limpa mantendo o item "Todos" no topo
        while self.combo_cat.count() > 1: self.combo_cat.removeItem(1)
        while self.combo_motivo.count() > 1: self.combo_motivo.removeItem(1)

        try:
            # Puxa Categorias
            resp_cat = requests.get(f"{API_BASE_URL}/categorias/{self.cliente_dados['cliente_id']}")
            if resp_cat.status_code == 200:
                for cat in resp_cat.json():
                    self.combo_cat.addItem(cat["nome"], cat["id"])
            
            # Puxa Motivos
            resp_mot = requests.get(f"{API_BASE_URL}/motivos/{self.cliente_dados['cliente_id']}")
            if resp_mot.status_code == 200:
                for mot in resp_mot.json():
                    if mot["tipo"] == "PERDA": # Só mostra motivos de perda nos filtros!
                        self.combo_motivo.addItem(mot["descricao"], mot["id"])
        except: pass

        self.combo_cat.blockSignals(False)
        self.combo_motivo.blockSignals(False)

    def carregar_relatorio(self):
        # 1. Pega os valores dos filtros
        txt_tempo = self.combo_tempo.currentText()
        dias = 30
        if txt_tempo == "Últimos 7 Dias": dias = 7
        elif txt_tempo == "Hoje": dias = 1

        cat_id = self.combo_cat.currentData()
        motivo_id = self.combo_motivo.currentData()

        # 2. Monta a URL com os filtros opcionais
        url = f"{API_BASE_URL}/relatorios/desperdicio/{self.cliente_dados['cliente_id']}?dias={dias}"
        if cat_id: url += f"&categoria_id={cat_id}"
        if motivo_id: url += f"&motivo_id={motivo_id}"

        # 3. Busca na API e Preenche a Tela
        try:
            resp = requests.get(url)
            if resp.status_code == 200:
                dados = resp.json()
                
                # Atualiza os Cartões (KPIs)
                kpis = dados["kpis"]
                self.val_prejuizo.setText(f"R$ {kpis['total_prejuizo']:.2f}".replace('.', ','))
                self.sub_prejuizo.setText("Somatório das perdas")

                self.val_vilao.setText(kpis["top_produto"])
                self.sub_vilao.setText(f"Custou R$ {kpis['top_produto_valor']:.2f}")

                self.val_motivo.setText(kpis["top_motivo"])
                self.sub_motivo.setText(f"Custou R$ {kpis['top_motivo_valor']:.2f}")

                # Atualiza a Tabela
                tabela_dados = dados["tabela"]
                self.tabela.setRowCount(0)
                for i, linha in enumerate(tabela_dados):
                    self.tabela.insertRow(i)
                    self.tabela.setItem(i, 0, QTableWidgetItem(linha["produto"]))
                    self.tabela.setItem(i, 1, QTableWidgetItem(linha["categoria"]))
                    self.tabela.setItem(i, 2, QTableWidgetItem(f"{linha['quantidade_perdida']} {linha['unidade']}"))
                    self.tabela.setItem(i, 3, QTableWidgetItem(linha["motivo"]))
                    
                    # Formata o dinheiro e pinta de vermelho
                    item_valor = QTableWidgetItem(f"R$ {linha['custo_total_perdido_rs']:.2f}")
                    item_valor.setForeground(Qt.darkRed)
                    self.tabela.setItem(i, 4, item_valor)
                    
                    self.tabela.setItem(i, 5, QTableWidgetItem(linha["data"]))
        except:
            pass # Se o servidor não responder, simplesmente não atualiza (ou poderiamos por um aviso)