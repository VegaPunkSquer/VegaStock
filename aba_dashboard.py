import requests
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QTableWidget, QTableWidgetItem, QHeaderView, 
                               QFrame, QAbstractItemView)
from PySide6.QtCore import Qt

API_BASE_URL = "https://vegastock.onrender.com"

class AbaDashboard(QWidget):
    def __init__(self, cliente_dados):
        super().__init__()
        self.cliente_dados = cliente_dados
        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(20, 20, 20, 20)

        # Cabeçalho Boas-Vindas
        self.lbl_boas_vindas = QLabel(f"Olá, {self.cliente_dados.get('login_usuario', 'usuário')}!")
        self.lbl_boas_vindas.setStyleSheet("font-size: 26px; font-weight: bold; color: #333;")
        layout_principal.addWidget(self.lbl_boas_vindas, alignment=Qt.AlignCenter)
        
        lbl_sub = QLabel("Aqui está o resumo do seu negócio e os alertas mais importantes para o dia.")
        lbl_sub.setStyleSheet("font-size: 14px; color: #777; margin-bottom: 20px;")
        layout_principal.addWidget(lbl_sub)

        # ==========================================
        # 1. CARDS DE RESUMO (O AGORA)
        # ==========================================
        layout_cards = QHBoxLayout()

        def criar_card_dash(titulo, cor_destaque):
            frame = QFrame()
            frame.setFixedHeight(120)
            frame.setStyleSheet(f"""
                QFrame {{
                    background-color: white; border-radius: 10px;
                    border: 1px solid #eee;
                }}
            """)
            l_frame = QVBoxLayout(frame)
            
            t = QLabel(titulo)
            t.setStyleSheet("font-size: 13px; color: #888; font-weight: bold; border: none;")
            
            v = QLabel("---")
            v.setStyleSheet(f"font-size: 28px; font-weight: bold; color: {cor_destaque}; border: none;")
            
            l_frame.addWidget(t)
            l_frame.addWidget(v)
            l_frame.addStretch()
            return frame, v

        self.card_patri, self.val_patri = criar_card_dash("PATRIMÔNIO EM ESTOQUE", "#2E7D32")
        self.card_itens, self.val_itens = criar_card_dash("TOTAL DE ITENS", "#333")
        self.card_alerta, self.val_alerta = criar_card_dash("ALERTAS CRÍTICOS", "#C62828")

        layout_cards.addWidget(self.card_patri)
        layout_cards.addWidget(self.card_itens)
        layout_cards.addWidget(self.card_alerta)
        layout_principal.addLayout(layout_cards)

        # ==========================================
        # 2. SEÇÃO DE REPOSIÇÃO (ALERTA PRO)
        # ==========================================
        lbl_sec_alerta = QLabel("🛒 Itens que precisam de Reposição (Estoque Baixo)")
        lbl_sec_alerta.setStyleSheet("font-size: 18px; font-weight: bold; margin-top: 25px; color: #C62828;")
        layout_principal.addWidget(lbl_sec_alerta)

        self.tabela_compras = QTableWidget()
        self.tabela_compras.setColumnCount(4)
        self.tabela_compras.setHorizontalHeaderLabels(["Produto", "Qtd Atual", "Mínimo Desejado", "Status"])
        self.tabela_compras.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabela_compras.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tabela_compras.setStyleSheet("QTableWidget { background-color: white; border-radius: 5px; }")
        
        layout_principal.addWidget(self.tabela_compras)

        # ==========================================
        # 3. MOVIMENTO DO DIA
        # ==========================================
        self.lbl_mov = QLabel("Movimentação de Hoje: 0 Entradas | 0 Saídas")
        self.lbl_mov.setStyleSheet("font-size: 13px; color: #555; font-style: italic; margin-top: 10px;")
        layout_principal.addWidget(self.lbl_mov)

    def showEvent(self, event):
        super().showEvent(event)
        self.carregar_dados()

    def carregar_dados(self):
        try:
            resp = requests.get(f"{API_BASE_URL}/dashboard/resumo/{self.cliente_dados['cliente_id']}")
            if resp.status_code == 200:
                dados = resp.json()
                
                # Atualiza Cards
                self.val_patri.setText(f"R$ {dados['patrimonio_rs']:.2f}".replace('.', ','))
                self.val_itens.setText(str(dados['total_produtos']))
                self.val_alerta.setText(str(dados['alertas_criticos_qtd']))
                
                # Muda a cor do card de alerta se tiver algo crítico
                if dados['alertas_criticos_qtd'] > 0:
                    self.val_alerta.setStyleSheet("font-size: 28px; font-weight: bold; color: #d32f2f; border: none;")
                else:
                    self.val_alerta.setStyleSheet("font-size: 28px; font-weight: bold; color: #2E7D32; border: none;")

                # Atualiza Tabela de Compras
                self.tabela_compras.setRowCount(0)
                for i, item in enumerate(dados["lista_compras"]):
                    self.tabela_compras.insertRow(i)
                    self.tabela_compras.setItem(i, 0, QTableWidgetItem(item["nome"]))
                    self.tabela_compras.setItem(i, 1, QTableWidgetItem(f"{item['qtd_atual']} {item['unidade']}"))
                    self.tabela_compras.setItem(i, 2, QTableWidgetItem(f"{item['qtd_minima']} {item['unidade']}"))
                    
                    status = QTableWidgetItem("⚠️ REPOR")
                    status.setForeground(Qt.red)
                    status.setTextAlignment(Qt.AlignCenter)
                    self.tabela_compras.setItem(i, 3, status)

                # Atualiza Movimento
                m = dados["movimento_hoje"]
                self.lbl_mov.setText(f"Movimentação de Hoje: {m['entradas']} Entradas | {m['saidas']} Saídas registradas.")
        except:
            pass