import requests
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, 
                               QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, 
                               QMessageBox, QGroupBox, QFormLayout, QRadioButton, 
                               QButtonGroup, QDoubleSpinBox, QAbstractItemView)
from PySide6.QtCore import Qt

API_BASE_URL = "http://127.0.0.1:8000"

class AbaEstoque(QWidget):
    def __init__(self, cliente_dados):
        super().__init__()
        self.cliente_dados = cliente_dados
        layout_principal = QVBoxLayout(self)

        lbl_titulo = QLabel("Operação de Estoque")
        lbl_titulo.setStyleSheet("font-size: 24px; font-weight: bold; color: #333; margin-bottom: 10px;")
        layout_principal.addWidget(lbl_titulo)

        # ==========================================
        # 1. FORMULÁRIO DE MOVIMENTAÇÃO (O TOPO)
        # ==========================================
        group_mov = QGroupBox("Registrar Nova Movimentação")
        group_mov.setStyleSheet("QGroupBox { font-weight: bold; padding-top: 25px; margin-top: 15px; } QGroupBox::title { top: -10px; left: 10px; }")
        layout_form = QFormLayout()

        # --- Botões de Ação (Entrada / Saída) ---
        layout_radios = QHBoxLayout()
        
        self.btn_entrada = QPushButton("ENTRADA (Compra)")
        self.btn_saida = QPushButton("SAÍDA (Consumo/Perda)")
        
        # Transforma o botão normal em um botão que "trava" clicado (estilo interruptor)
        self.btn_entrada.setCheckable(True)
        self.btn_saida.setCheckable(True)
        self.btn_entrada.setChecked(True) # Padrão

        # CSS Avançado para os botões
        estilo_btn = """
            QPushButton {
                font-weight: bold; font-size: 14px; padding: 12px;
                border: 2px solid #ccc; border-radius: 5px;
                background-color: #f8f8f8; color: #777;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
            QPushButton:checked#btn_entrada {
                background-color: #e8f5e9; border: 2px solid #4CAF50; color: #2E7D32;
            }
            QPushButton:checked#btn_saida {
                background-color: #ffebee; border: 2px solid #f44336; color: #C62828;
            }
        """
        self.btn_entrada.setObjectName("btn_entrada")
        self.btn_saida.setObjectName("btn_saida")
        self.btn_entrada.setStyleSheet(estilo_btn)
        self.btn_saida.setStyleSheet(estilo_btn)
        
        layout_radios.addWidget(self.btn_entrada)
        layout_radios.addWidget(self.btn_saida)
        
        self.grupo_radios = QButtonGroup()
        self.grupo_radios.addButton(self.btn_entrada)
        self.grupo_radios.addButton(self.btn_saida)
        self.grupo_radios.buttonClicked.connect(self.alternar_modo)

        # --- Campos do Formulário ---
        self.combo_produto = QComboBox()
        self.combo_produto.setPlaceholderText("Selecione o Produto...")
        self.combo_produto.currentIndexChanged.connect(self.ajustar_decimais)

        # O SpinBox é perfeito: evita que digitem letras e já formata os números
        self.spin_qtd = QDoubleSpinBox()
        self.spin_qtd.setRange(0.001, 99999.999)
        self.spin_qtd.setDecimals(3) 

        self.spin_custo = QDoubleSpinBox()
        self.spin_custo.setRange(0.01, 99999.99)
        self.spin_custo.setPrefix("R$ ")
        self.spin_custo.setDecimals(2)

        self.combo_motivo = QComboBox()
        self.combo_motivo.setPlaceholderText("Selecione o Motivo da Saída...")

        # Montando o Formulário
        layout_form.addRow(layout_radios)
        layout_form.addRow("Produto:", self.combo_produto)
        layout_form.addRow("Quantidade:", self.spin_qtd)
        layout_form.addRow("Custo Unitário Pago:", self.spin_custo)
        layout_form.addRow("Motivo da Baixa:", self.combo_motivo)

        self.btn_registrar = QPushButton("REGISTRAR MOVIMENTAÇÃO")
        self.btn_registrar.setStyleSheet("background-color: #000; color: #fff; font-size: 16px; font-weight: bold; padding: 12px;")
        self.btn_registrar.clicked.connect(self.registrar_movimentacao)

        group_mov.setLayout(layout_form)
        layout_principal.addWidget(group_mov)
        layout_principal.addWidget(self.btn_registrar)

        # ==========================================
        # 2. HISTÓRICO DE MOVIMENTAÇÕES (A BASE)
        # ==========================================
        layout_filtro = QHBoxLayout()
        lbl_historico = QLabel("Últimas Movimentações")
        lbl_historico.setStyleSheet("font-size: 16px; font-weight: bold;")
        
        self.combo_filtro = QComboBox()
        self.combo_filtro.addItems(["Hoje", "Últimos 7 Dias", "Últimos 30 Dias"])
        self.combo_filtro.currentIndexChanged.connect(self.carregar_historico)
        
        layout_filtro.addWidget(lbl_historico)
        layout_filtro.addStretch()
        layout_filtro.addWidget(QLabel("Filtrar por:"))
        layout_filtro.addWidget(self.combo_filtro)
        layout_principal.addLayout(layout_filtro)

        # Tabela
        self.tabela = QTableWidget()
        self.tabela.setColumnCount(7)
        self.tabela.setHorizontalHeaderLabels(["ID", "Data/Hora", "Tipo", "Produto", "Qtd", "Custo (R$)", "Motivo"])
        self.tabela.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabela.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tabela.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tabela.setColumnHidden(0, True) # Esconde o ID
        
        layout_principal.addWidget(self.tabela)

        # Prepara a tela inicial
        self.alternar_modo()

    # --- FUNÇÕES DA INTERFACE ---

    def showEvent(self, event):
        super().showEvent(event)
        self.carregar_produtos()
        self.carregar_motivos()
        self.carregar_historico()

    def alternar_modo(self):
        # Mágica da Interface: Esconde ou Mostra dependendo do botão
        if self.btn_entrada.isChecked():
            self.spin_custo.show()
            self.combo_motivo.hide()
            # Pega o label associado ao widget no form layout e esconde/mostra
            self.spin_custo.parentWidget().layout().labelForField(self.spin_custo).show()
            self.combo_motivo.parentWidget().layout().labelForField(self.combo_motivo).hide()
        else:
            self.spin_custo.hide()
            self.combo_motivo.show()
            self.spin_custo.parentWidget().layout().labelForField(self.spin_custo).hide()
            self.combo_motivo.parentWidget().layout().labelForField(self.combo_motivo).show()

    def ajustar_decimais(self):
        # Trava Anti-Idiota das Unidades
        dados_produto = self.combo_produto.currentData()
        if not dados_produto: return
        
        unidade = dados_produto.get("unidade", "").lower()
        
        if unidade in ["kg", "litro", "gramas", "ml"]:
            self.spin_qtd.setDecimals(3)
        else:
            # Trava em números inteiros (0 casas decimais)
            self.spin_qtd.setDecimals(0)

    # --- FUNÇÕES DE LÓGICA E API ---

    def carregar_produtos(self):
        self.combo_produto.blockSignals(True)
        self.combo_produto.clear()
        try:
            resp = requests.get(f"{API_BASE_URL}/produtos", params={"cliente_id": self.cliente_dados['cliente_id']})
            if resp.status_code == 200:
                for prod in resp.json():
                    # Guarda um dicionário invisível no item com o ID e a Unidade
                    self.combo_produto.addItem(f"{prod['nome']} ({prod['unidade_medida']})", {"id": prod["id"], "unidade": prod["unidade_medida"]})
        except: pass
        self.combo_produto.blockSignals(False)
        self.ajustar_decimais() # Roda uma vez para o primeiro item

    def carregar_motivos(self):
        self.combo_motivo.clear()
        try:
            resp = requests.get(f"{API_BASE_URL}/motivos/{self.cliente_dados['cliente_id']}")
            if resp.status_code == 200:
                for mot in resp.json():
                    self.combo_motivo.addItem(mot["descricao"], mot["id"])
        except: pass

    def registrar_movimentacao(self):
        dados_produto = self.combo_produto.currentData()
        if not dados_produto:
            QMessageBox.warning(self, "Aviso", "Cadastre produtos no Catálogo primeiro!")
            return

        tipo = "ENTRADA" if self.btn_entrada.isChecked() else "SAIDA"
        
        payload = {
            "cliente_id": self.cliente_dados['cliente_id'],
            "produto_id": dados_produto["id"],
            "tipo_movimento": tipo,
            "quantidade": self.spin_qtd.value()
        }

        if tipo == "ENTRADA":
            payload["custo_unitario"] = self.spin_custo.value()
        else:
            motivo_id = self.combo_motivo.currentData()
            if not motivo_id:
                QMessageBox.warning(self, "Aviso", "Selecione o motivo da saída!")
                return
            payload["motivo_baixa_id"] = motivo_id

        try:
            resp = requests.post(f"{API_BASE_URL}/movimentacao", json=payload)
            if resp.status_code == 200:
                self.spin_qtd.setValue(0)
                self.spin_custo.setValue(0)
                self.carregar_historico() # Dá F5 na tabela
                QMessageBox.information(self, "Sucesso", "Movimentação registrada com sucesso!")
            else:
                QMessageBox.warning(self, "Erro", resp.json().get("detail", "Erro ao registrar."))
        except Exception as e:
            QMessageBox.critical(self, "Erro", "Falha de conexão com o servidor.")

    def carregar_historico(self):
        self.tabela.setRowCount(0)
        
        # Traduz o combobox para os dias do banco
        filtro_txt = self.combo_filtro.currentText()
        if filtro_txt == "Hoje": dias = 1
        elif filtro_txt == "Últimos 7 Dias": dias = 7
        else: dias = 30
        
        try:
            resp = requests.get(f"{API_BASE_URL}/movimentacoes/{self.cliente_dados['cliente_id']}?dias={dias}")
            if resp.status_code == 200:
                movs = resp.json()
                for i, mov in enumerate(movs):
                    self.tabela.insertRow(i)
                    self.tabela.setItem(i, 0, QTableWidgetItem(str(mov["id"])))
                    self.tabela.setItem(i, 1, QTableWidgetItem(mov["data"]))
                    
                    # Formata a coluna Tipo com cor
                    item_tipo = QTableWidgetItem(mov["tipo"])
                    if mov["tipo"] == "ENTRADA":
                        item_tipo.setForeground(Qt.darkGreen)
                    else:
                        item_tipo.setForeground(Qt.red)
                    self.tabela.setItem(i, 2, item_tipo)
                    
                    self.tabela.setItem(i, 3, QTableWidgetItem(mov["produto"]))
                    self.tabela.setItem(i, 4, QTableWidgetItem(f"{mov['quantidade']} {mov['unidade']}"))
                    
                    custo_str = f"R$ {mov['custo']:.2f}" if mov['custo'] else "-"
                    self.tabela.setItem(i, 5, QTableWidgetItem(custo_str))
                    self.tabela.setItem(i, 6, QTableWidgetItem(mov["motivo"]))
        except: pass