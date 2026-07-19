import requests
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, 
                               QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, 
                               QMessageBox, QGroupBox, QFormLayout, QRadioButton, 
                               QButtonGroup, QDoubleSpinBox, QAbstractItemView)
import os
from PySide6.QtCore import Qt, QThread, Signal, QSize, QUrl
from PySide6.QtGui import QMovie
from PySide6.QtMultimedia import QSoundEffect

API_BASE_URL = "https://vegap-vega-stock.hf.space"
class WorkerEstoque(QThread):
    resultado = Signal(dict)
    erro = Signal(str)
    alerta_ui = Signal(str) # <--- SINAL DE COMUNICAÇÃO DE RETRY

    def __init__(self, cliente_id, dias, limit, offset, atualizar_combos=True):
        super().__init__()
        self.cliente_id = cliente_id
        self.dias = dias
        self.limit = limit
        self.offset = offset
        self.atualizar_combos = atualizar_combos

    def run(self):
        import time
        max_tentativas = 3
        
        for tentativa in range(1, max_tentativas + 1):
            try:
                dados = {"atualizar_combos": self.atualizar_combos}
                
                if self.atualizar_combos:
                    r_prod = requests.get(f"{API_BASE_URL}/produtos", params={"cliente_id": self.cliente_id}, timeout=8)
                    r_mot = requests.get(f"{API_BASE_URL}/motivos/{self.cliente_id}", timeout=8)
                    r_cat = requests.get(f"{API_BASE_URL}/categorias/{self.cliente_id}", timeout=8)
                    
                    dados["produtos"] = r_prod.json() if r_prod.status_code == 200 else []
                    dados["motivos"] = r_mot.json() if r_mot.status_code == 200 else []
                    dados["categorias"] = r_cat.json() if r_cat.status_code == 200 else []

                r_hist = requests.get(f"{API_BASE_URL}/movimentacoes/paginado/{self.cliente_id}", params={"dias": self.dias, "limit": self.limit, "offset": self.offset}, timeout=10)

                # Se for sucesso absoluto, emite e mata o loop
                if r_hist.status_code == 200:
                    json_hist = r_hist.json()
                    dados["historico"] = json_hist.get("movimentacoes", [])
                    dados["total"] = json_hist.get("total", 0)
                    self.resultado.emit(dados)
                    return 
                    
                # Se o Hugging Face estiver capengando (HTML gigante, 500, 503)
                elif r_hist.status_code in [500, 502, 503, 504]:
                    if tentativa < max_tentativas:
                        self.alerta_ui.emit(f"Servidor instável. Tentando reconectar ({tentativa}/{max_tentativas})...")
                        time.sleep(3) # Pausa segura dentro do Porão
                        continue
                    else:
                        self.erro.emit(f"Nuvem inacessível no momento. Tente novamente em instantes.")
                        return
                else:
                    self.erro.emit(f"Erro na API Paginada: {r_hist.status_code}")
                    return

            except Exception as e:
                if tentativa < max_tentativas:
                    self.alerta_ui.emit(f"Falha na rede. Tentando reconectar ({tentativa}/{max_tentativas})...")
                    time.sleep(3)
                    continue
                else:
                    self.erro.emit(f"Falha de conexão física: {str(e)}")
                    return

class AbaEstoque(QWidget):
    def __init__(self, cliente_dados):
        super().__init__()
        self.cliente_dados = cliente_dados
        layout_principal = QVBoxLayout(self)

        lbl_titulo = QLabel("Operação de Estoque")
        lbl_titulo.setStyleSheet("font-size: 24px; font-weight: bold; color: #333; margin-bottom: 10px;")
        layout_principal.addWidget(lbl_titulo, alignment=Qt.AlignCenter)

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
        self.combo_produto.setPlaceholderText("Selecione ou digite para pesquisar...")
        
        # MÁGICA DA PESQUISA: Permite digitar, mas bloqueia cadastro de novos itens por aqui
        self.combo_produto.setEditable(True)
        self.combo_produto.setInsertPolicy(QComboBox.NoInsert)
        
        # Configura o autocompletar para buscar em qualquer parte do texto (MatchContains)
        from PySide6.QtWidgets import QCompleter  # Importação local segura
        completer = self.combo_produto.completer()
        completer.setCompletionMode(QCompleter.PopupCompletion)  # Corrigido para QCompleter!
        completer.setFilterMode(Qt.MatchContains)
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        
        self.combo_produto.currentIndexChanged.connect(self.ajustar_decimais)

        # O SpinBox é perfeito: evita que digitem letras e já formata os números
        self.spin_qtd = QDoubleSpinBox()
        self.spin_qtd.setRange(0.000, 99999.999)
        self.spin_qtd.setDecimals(3) 
        self.spin_qtd.setValue(0.00)

        self.spin_custo = QDoubleSpinBox()
        self.spin_custo.setRange(0.00, 99999.99)
        self.spin_custo.setPrefix("R$ ")
        self.spin_custo.setDecimals(2)
        self.spin_custo.setValue(0.00)

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
        self.combo_filtro.addItems(["Tudo (Todo o Histórico)", "Hoje", "Últimos 7 Dias", "Últimos 30 Dias"])
        self.combo_filtro.currentIndexChanged.connect(self.carregar_historico)
        
        # --- NOVO COMBO DE FILTRO POR CATEGORIA ---
        self.combo_cat_filtro = QComboBox()
        self.combo_cat_filtro.addItem("Todas as Categorias", None)
        self.combo_cat_filtro.currentIndexChanged.connect(self.carregar_historico)
        
        # --- O BOTÃO ENTRA EXATAMENTE AQUI ---
        self.btn_atualizar = QPushButton("Atualizar Tabela")
        self.btn_atualizar.setCursor(Qt.PointingHandCursor) # Deixa a mãozinha ao passar o mouse
        self.btn_atualizar.setStyleSheet("background-color: #2196F3; color: white; font-weight: bold; padding: 8px; border-radius: 5px; border: 1px solid #0d47a1;")
        self.btn_atualizar.clicked.connect(lambda: self.carregar_dados(atualizar_combos=False))
        
        layout_filtro.addWidget(lbl_historico)
        layout_filtro.addStretch()
        layout_filtro.addWidget(QLabel("Período:"))
        layout_filtro.addWidget(self.combo_filtro)
        layout_filtro.addWidget(QLabel("Categoria:"))
        layout_filtro.addWidget(self.combo_cat_filtro)
        layout_filtro.addWidget(self.btn_atualizar) # O botão é injetado na tela aqui
        layout_principal.addLayout(layout_filtro)

        # ==========================================
        # PAGINAÇÃO (NO TOPO) E TABELA
        # ==========================================
        self.limite_atual = 30
        self.offset_atual = 0
        self.total_movs = 0
        
        layout_paginacao = QHBoxLayout()
        layout_paginacao.setContentsMargins(0, 15, 0, 5)
        
        layout_paginacao.addWidget(QLabel("Mostrar:"))
        self.combo_limite = QComboBox()
        self.combo_limite.addItems(["10", "30", "50", "100"])
        self.combo_limite.blockSignals(True) 
        self.combo_limite.setCurrentText("30")
        self.combo_limite.blockSignals(False)
        self.combo_limite.currentIndexChanged.connect(self.mudar_limite)
        layout_paginacao.addWidget(self.combo_limite)
        
        layout_paginacao.addStretch()
        
        self.btn_anterior = QPushButton("◀ Anterior")
        self.btn_anterior.setStyleSheet("font-weight: bold; padding: 5px 15px; border-radius: 4px; background-color: #eee;")
        self.btn_anterior.clicked.connect(lambda: self.mudar_pagina(-1))
        
        self.lbl_pagina = QLabel("Página 1")
        self.lbl_pagina.setStyleSheet("font-weight: bold; color: #555;")
        
        self.btn_proxima = QPushButton("Próxima ▶")
        self.btn_proxima.setStyleSheet("font-weight: bold; padding: 5px 15px; border-radius: 4px; background-color: #eee;")
        self.btn_proxima.clicked.connect(lambda: self.mudar_pagina(1))
        
        layout_paginacao.addWidget(self.btn_anterior)
        layout_paginacao.addWidget(self.lbl_pagina)
        layout_paginacao.addWidget(self.btn_proxima)
        
        layout_principal.addLayout(layout_paginacao)

        # Tabela
        self.tabela = QTableWidget()
        self.tabela.setColumnCount(8)
        self.tabela.setHorizontalHeaderLabels(["ID", "Data/Hora", "Tipo", "Produto", "Qtd", "Custo (R$)", "Responsável", "Motivo"])
        self.tabela.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabela.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tabela.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tabela.setColumnHidden(0, True) # Esconde o ID
        
        layout_principal.addWidget(self.tabela)
        
        # --- BOTÃO NUCLEAR: ZERAR ESTOQUE E HISTÓRICO (SÓ APARECE PARA O ADMIN) ---
        self.btn_zerar_estoque = QPushButton("⚠️ Zerar Histórico e Saldo")
        self.btn_zerar_estoque.setCursor(Qt.PointingHandCursor)
        self.btn_zerar_estoque.setStyleSheet("background-color: #d32f2f; color: white; font-weight: bold; padding: 8px; border-radius: 5px;")
        self.btn_zerar_estoque.clicked.connect(self.confirmar_reset_estoque)
        
        # Se o usuário logado NÃO FOR ADMIN, o botão nem aparece na tela!
        if self.cliente_dados.get("nivel_acesso") != "Admin":
            self.btn_zerar_estoque.hide()
            
        # (Adicione self.btn_zerar_estoque ao seu layout, por exemplo junto com o botão self.btn_atualizar)
        layout_filtro.addWidget(self.btn_zerar_estoque)

        # Prepara a tela inicial
        self.alternar_modo()

    # --- FUNÇÕES DA INTERFACE ---

    def showEvent(self, event):
        super().showEvent(event)
        # Quando abre a aba, carrega os combos e a tabela
        self.carregar_dados(atualizar_combos=True)

    def alternar_modo(self):
        if self.btn_entrada.isChecked():
            self.spin_custo.show()
            self.combo_motivo.hide()
            self.spin_custo.parentWidget().layout().labelForField(self.spin_custo).show()
            self.combo_motivo.parentWidget().layout().labelForField(self.combo_motivo).hide()
        else:
            self.spin_custo.hide()
            self.combo_motivo.show()
            self.spin_custo.parentWidget().layout().labelForField(self.spin_custo).hide()
            self.combo_motivo.parentWidget().layout().labelForField(self.combo_motivo).show()

    def ajustar_decimais(self):
        dados_produto = self.combo_produto.currentData()
        if not dados_produto: return
        unidade = dados_produto.get("unidade", "").lower()
        if unidade in ["kg", "litro", "gramas", "ml"]:
            self.spin_qtd.setDecimals(3)
        else:
            self.spin_qtd.setDecimals(0)

    def mudar_limite(self):
        self.limite_atual = int(self.combo_limite.currentText())
        self.offset_atual = 0 # Volta pra página 1 sempre que o limite muda
        self.carregar_dados(atualizar_combos=False)
        
    def mudar_pagina(self, direcao):
        novo_offset = self.offset_atual + (direcao * self.limite_atual)
        if 0 <= novo_offset < self.total_movs:
            self.offset_atual = novo_offset
            self.carregar_dados(atualizar_combos=False)

    def carregar_historico(self):
        # Se mudar o filtro (Hoje, 7 dias, etc), a paginação zera e volta pro começo!
        self.offset_atual = 0
        self.carregar_dados(atualizar_combos=False)

    def carregar_dados(self, atualizar_combos=True):
        self.atualizando_combos = atualizar_combos
        
        if atualizar_combos:
            self.combo_produto.blockSignals(True)
            self.combo_produto.clear()
            self.combo_produto.addItem("Carregando...")
            self.combo_produto.blockSignals(False)
            
            self.combo_motivo.clear()
            self.combo_motivo.addItem("Carregando...")

        self.tabela.setRowCount(0)
        self.lbl_pagina.setText("Carregando...")
        self.btn_anterior.setEnabled(False)
        self.btn_proxima.setEnabled(False)

        filtro_txt = self.combo_filtro.currentText()
        if filtro_txt == "Hoje": dias = 1
        elif filtro_txt == "Últimos 7 Dias": dias = 7
        elif filtro_txt == "Últimos 30 Dias": dias = 30
        else: dias = 0  # 0 representa "Tudo", sem corte de data

        self.worker = WorkerEstoque(self.cliente_dados['cliente_id'], dias, getattr(self, 'limite_atual', 30), getattr(self, 'offset_atual', 0), atualizar_combos)
        self.worker.resultado.connect(self.atualizar_tela)
        self.worker.erro.connect(self.mostrar_erro)
        # O GANCHO VISUAL: O trabalhador fala e o Label do meio da tela atualiza na hora!
        self.worker.alerta_ui.connect(lambda msg: self.lbl_pagina.setText(msg))
        self.worker.start()

    def atualizar_tela(self, dados):
        if self.atualizando_combos and "produtos" in dados:
            self.combo_produto.blockSignals(True)
            self.combo_produto.clear()
            for prod in dados["produtos"]:
                # Mostra o saldo físico na própria caixinha de seleção!
                qtd_atual = float(prod.get('quantidade_atual', 0.0))
                self.combo_produto.addItem(
                    f"{prod['nome']} — [Saldo: {qtd_atual} {prod['unidade_medida']}]", 
                    {"id": prod["id"], "unidade": prod["unidade_medida"]}
                )
            self.combo_produto.blockSignals(False)
            self.ajustar_decimais()

            self.combo_motivo.clear()
            for mot in dados["motivos"]:
                self.combo_motivo.addItem(mot["descricao"], mot["id"])
                
            # Preenche também o nosso novo filtro de categorias da tabela!
            self.combo_cat_filtro.blockSignals(True)
            while self.combo_cat_filtro.count() > 1: self.combo_cat_filtro.removeItem(1)
            for cat in dados.get("categorias", []):
                self.combo_cat_filtro.addItem(cat["nome"], cat["id"])
            self.combo_cat_filtro.blockSignals(False)

        # Matemática da Paginação
        import math
        self.total_movs = dados.get("total", 0)
        pagina_atual = (self.offset_atual // self.limite_atual) + 1
        total_paginas = math.ceil(self.total_movs / self.limite_atual) if self.total_movs > 0 else 1
        
        self.lbl_pagina.setText(f"Página {pagina_atual} de {total_paginas} (Total: {self.total_movs})")
        self.btn_anterior.setEnabled(self.offset_atual > 0)
        self.btn_proxima.setEnabled((self.offset_atual + self.limite_atual) < self.total_movs)

        self.tabela.setRowCount(0)
        for i, mov in enumerate(dados.get("historico", [])):
            self.tabela.insertRow(i)
            self.tabela.setItem(i, 0, QTableWidgetItem(str(mov["id"])))
            self.tabela.setItem(i, 1, QTableWidgetItem(mov["data"]))
            
            tipo_mov = mov.get("tipo", "")
            tipo_mov_lower = tipo_mov.lower()

            item_tipo = QTableWidgetItem(tipo_mov)
            if tipo_mov_lower == "entrada":
                item_tipo.setForeground(Qt.darkGreen)
            elif tipo_mov_lower == "saida":
                item_tipo.setForeground(Qt.red)
            self.tabela.setItem(i, 2, item_tipo)
            
            self.tabela.setItem(i, 3, QTableWidgetItem(mov["produto"]))
            self.tabela.setItem(i, 4, QTableWidgetItem(f"{mov['quantidade']} {mov['unidade']}"))
            
            custo_str = f"R$ {mov['custo']:.2f}" if mov['custo'] else "-"
            self.tabela.setItem(i, 5, QTableWidgetItem(custo_str))
            
            self.tabela.setItem(i, 6, QTableWidgetItem(mov.get("responsavel", "Desconhecido")))

            texto_motivo = mov.get("motivo", "") if tipo_mov_lower == "saida" else ""
            self.tabela.setItem(i, 7, QTableWidgetItem(texto_motivo))

    def mostrar_erro(self, msg):
        self.lbl_pagina.setText("Erro de Conexão")
        QMessageBox.critical(self, "Falha na Nuvem", f"Ocorreu um erro ao buscar o histórico:\n\n{msg}")

    def registrar_movimentacao(self):
        dados_produto = self.combo_produto.currentData()
        if not dados_produto:
            QMessageBox.warning(self, "Aviso", "Selecione um produto primeiro!")
            return

        # TRAVA 1: Quantidade não pode ser zero
        qtd_digitada = self.spin_qtd.value()
        if qtd_digitada <= 0:
            QMessageBox.warning(self, "Aviso", "A quantidade deve ser maior que zero!")
            return

        tipo = "ENTRADA" if self.btn_entrada.isChecked() else "SAIDA"
        
        # Puxa os valores dos campos
        payload = {
            "cliente_id": self.cliente_dados['cliente_id'],
            "produto_id": dados_produto["id"],
            "tipo_movimento": tipo,
            "quantidade": qtd_digitada
        }

        if tipo == "ENTRADA":
            # TRAVA 2: Entrada não pode ter custo zero
            custo_digitado = self.spin_custo.value()
            if custo_digitado <= 0:
                QMessageBox.warning(self, "Aviso", "O custo da entrada não pode ser zero!")
                return
            payload["custo_unitario"] = custo_digitado
            
        else: # Se for SAÍDA
            motivo_id = self.combo_motivo.currentData()
            # TRAVA 3: Saída OBRIGA a escolher um motivo válido
            if not motivo_id or self.combo_motivo.currentText() == "Selecione o Motivo da Saída...":
                QMessageBox.warning(self, "Aviso", "Selecione o motivo da saída!")
                return
            payload["motivo_baixa_id"] = motivo_id

        # TRAVA ANTI-DUPLICIDADE: Desativa o botão na hora para impedir clique duplo!
        self.btn_registrar.setEnabled(False)
        self.btn_registrar.setText("⏳ Salvando na Nuvem...")

        try:
            resp = requests.post(f"{API_BASE_URL}/movimentacao", json=payload)
            if resp.status_code == 200:
                resultado = resp.json()
                self.spin_qtd.setValue(0)
                self.spin_custo.setValue(0)
                # Dá F5 na tabela e nos combos para garantir dados frescos usando a Thread
                self.carregar_dados(atualizar_combos=True) 
                if resultado.get("alerta"):
                    self.tocar_alerta_sonoro()
                    QMessageBox.warning(self, "Atenção!", "Produto atingiu estoque mínimo!")
                else:
                    QMessageBox.information(self, "Sucesso", "Movimentação registrada com sucesso!")
            else:
                QMessageBox.warning(self, "Erro", resp.json().get("detail", "Erro ao registrar."))
        except Exception:
            QMessageBox.critical(self, "Erro", "Falha de conexão com o servidor.")
        finally:
            # Garante que o botão sempre volte ao normal no final, mesmo se der erro ou alerta
            self.btn_registrar.setEnabled(True)
            self.btn_registrar.setText("REGISTRAR MOVIMENTAÇÃO")
            
    def tocar_alerta_sonoro(self):
        if not hasattr(self, 'player'):
            self.player = QSoundEffect()
        
        # Constrói o caminho absoluto para a pasta assets
        base_dir = os.path.dirname(os.path.abspath(__file__))
        caminho_som = os.path.join(base_dir, "assets", "alerta.wav")
        
        if os.path.exists(caminho_som):
            self.player.setSource(QUrl.fromLocalFile(caminho_som))
            self.player.setVolume(1.0)
            self.player.play()
            
    def confirmar_reset_estoque(self):
        msg = QMessageBox(self)
        msg.setWindowTitle("⚠️ ALERTA DE RISCO CRÍTICO")
        msg.setText("<b>Você está prestes a ZERAR TODO O ESTOQUE e o HISTÓRICO da empresa!</b>")
        msg.setInformativeText("Essa ação é irreversível. Todas as entradas e saídas serão apagadas e os produtos voltarão a ter saldo 0.0.\n\nDeseja realmente continuar?")
        msg.setIcon(QMessageBox.Warning)
        
        btn_sim = msg.addButton("Sim, Zerar Tudo", QMessageBox.ActionRole)
        btn_sim.setStyleSheet("background-color: #d32f2f; color: white; font-weight: bold; padding: 6px 15px;")
        
        btn_nao = msg.addButton("Cancelar", QMessageBox.RejectRole)
        btn_nao.setStyleSheet("background-color: #555; color: white; font-weight: bold; padding: 6px 15px;")
        msg.setDefaultButton(btn_nao)
        
        msg.exec()
        
        if msg.clickedButton() == btn_sim:
            try:
                url = f"{API_BASE_URL}/estoque/resetar/{self.cliente_dados['cliente_id']}?usuario_id={self.cliente_dados['usuario_id']}"
                resp = requests.delete(url)
                if resp.status_code == 200:
                    QMessageBox.information(self, "Sucesso", resp.json().get("mensagem", "Estoque zerado com sucesso!"))
                    self.carregar_dados(atualizar_combos=True) # Atualiza a tabela na hora
                else:
                    QMessageBox.critical(self, "Acesso Negado", resp.json().get("detail", "Erro ao executar ação."))
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Falha na comunicação com o servidor: {e}")