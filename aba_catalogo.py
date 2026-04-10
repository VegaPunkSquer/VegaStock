import requests
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
                               QComboBox, QSpinBox, QPushButton, QTableWidget, QTableWidgetItem,
                               QHeaderView, QMessageBox, QGroupBox, QFormLayout, QAbstractItemView, QInputDialog)
from PySide6.QtCore import Qt

API_BASE_URL = "http://127.0.0.1:8000"

class AbaCatalogo(QWidget):
    def __init__(self, cliente_dados):
        super().__init__()
        self.cliente_dados = cliente_dados
        layout_principal = QVBoxLayout(self)

        lbl_titulo = QLabel("Catálogo de Produtos")
        lbl_titulo.setStyleSheet("font-size: 24px; font-weight: bold; color: #333; margin-bottom: 10px;")
        layout_principal.addWidget(lbl_titulo)

        # =================================================================
        # 1. SUBSTITUA O QGROUPBOX DO CADASTRO (CSS AGRESSIVO) E COMBO_UNIDADE
        # =================================================================
        group_cadastro = QGroupBox("Cadastrar Novo Produto")
        # CSS conserta o texto cortado criando uma margem real no topo
        group_cadastro.setStyleSheet("QGroupBox { font-weight: bold; padding-top: 25px; margin-top: 15px; } QGroupBox::title { top: -10px; left: 10px; }")
        layout_form = QFormLayout()

        self.input_nome = QLineEdit()
        self.input_nome.setPlaceholderText("Ex: Tomate Carmem")

        self.combo_categoria = QComboBox()
        self.combo_categoria.setPlaceholderText("Selecione a Categoria...")

        self.combo_unidade = QComboBox()
        # Gatilho: Quando ele muda a opção, o PySide roda essa função
        self.combo_unidade.activated.connect(self.verificar_nova_unidade)

        self.spin_alerta = QSpinBox()
        self.spin_alerta.setRange(0, 9999)
        self.spin_alerta.setSpecialValueText("Usar Regra Geral")
        
        # Trava PRO para o Limite Individual
        if self.cliente_dados.get('status_assinatura') != "PRO":
            self.spin_alerta.setEnabled(False)
            self.spin_alerta.setToolTip("Assine o plano PRO para definir alertas individuais.")

        self.btn_salvar = QPushButton("Cadastrar Produto")
        self.btn_salvar.setStyleSheet("background-color: #000; color: #fff; font-weight: bold; padding: 8px;")
        self.btn_salvar.clicked.connect(self.cadastrar_produto)

        layout_form.addRow("Nome do Produto:", self.input_nome)
        layout_form.addRow("Categoria:", self.combo_categoria)
        layout_form.addRow("Unidade de Medida:", self.combo_unidade)
        layout_form.addRow("Avisar estoque baixo em (PRO):", self.spin_alerta)

        group_cadastro.setLayout(layout_form)
        layout_principal.addWidget(group_cadastro)
        layout_principal.addWidget(self.btn_salvar)

        # ==========================================
        # 2. TABELA DE PRODUTOS CADASTRADOS
        # ==========================================
        self.tabela = QTableWidget()
        self.tabela.setColumnCount(5)
        self.tabela.setHorizontalHeaderLabels(["ID", "Nome", "ID Cat.", "Unidade", "Alerta Mínimo"])
        self.tabela.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabela.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tabela.setEditTriggers(QAbstractItemView.NoEditTriggers)
        
        # Oculta a coluna de ID real para ficar mais limpo
        self.tabela.setColumnHidden(0, True)
        self.tabela.setColumnHidden(2, True) # Oculta o ID da categoria
        
        layout_principal.addWidget(self.tabela)

        self.btn_excluir = QPushButton("Excluir Produto Selecionado")
        self.btn_excluir.setStyleSheet("color: red; font-weight: bold; border: 1px solid red; padding: 6px;")
        self.btn_excluir.clicked.connect(self.excluir_produto)
        layout_principal.addWidget(self.btn_excluir)

        # Carrega os dados na tela
        self.carregar_categorias()
        self.carregar_produtos()
        self.carregar_unidades()

    # --- FUNÇÕES DE LÓGICA ---

    def carregar_categorias(self):
        self.combo_categoria.clear()
        try:
            resp = requests.get(f"{API_BASE_URL}/categorias/{self.cliente_dados['cliente_id']}")
            if resp.status_code == 200:
                for cat in resp.json():
                    # Adiciona o nome, mas esconde o ID no 'userData' do item
                    self.combo_categoria.addItem(cat["nome"], cat["id"])
        except:
            pass

    def carregar_produtos(self):
        self.tabela.setRowCount(0)
        try:
            resp = requests.get(f"{API_BASE_URL}/produtos", params={"cliente_id": self.cliente_dados['cliente_id']})
            if resp.status_code == 200:
                produtos = resp.json()
                for i, prod in enumerate(produtos):
                    self.tabela.insertRow(i)
                    
                    self.tabela.setItem(i, 0, QTableWidgetItem(str(prod["id"])))
                    self.tabela.setItem(i, 1, QTableWidgetItem(prod["nome"]))
                    self.tabela.setItem(i, 2, QTableWidgetItem(str(prod["categoria_id"])))
                    self.tabela.setItem(i, 3, QTableWidgetItem(prod["unidade_medida"]))
                    
                    alerta = str(prod["estoque_minimo"]) if prod["estoque_minimo"] > 0 else "Geral"
                    self.tabela.setItem(i, 4, QTableWidgetItem(alerta))
        except:
            pass

    def cadastrar_produto(self):
        nome = self.input_nome.text().strip()
        cat_id = self.combo_categoria.currentData()
        unidade = self.combo_unidade.currentText()
        alerta = float(self.spin_alerta.value())

        # TRAVA ANTI-FANTASMA (NOVO)
        if unidade == "+ Adicionar Nova...":
            QMessageBox.warning(self, "Aviso", "Selecione uma unidade de medida válida.")
            return

        dados = {
            "cliente_id": self.cliente_dados['cliente_id'],
            "nome": nome,
            "categoria_id": cat_id,
            "unidade_medida": unidade,
            "estoque_minimo": alerta
        }

        try:
            resp = requests.post(f"{API_BASE_URL}/produtos", json=dados)
            if resp.status_code == 200:
                self.input_nome.clear()
                self.spin_alerta.setValue(0)
                self.carregar_produtos()
                QMessageBox.information(self, "Sucesso", "Produto cadastrado!")
        except Exception as e:
            QMessageBox.critical(self, "Erro", "Não foi possível conectar à API.")

    def excluir_produto(self):
        linha = self.tabela.currentRow()
        if linha < 0:
            return

        produto_id = self.tabela.item(linha, 0).text()
        
        try:
            requests.delete(f"{API_BASE_URL}/produtos/{produto_id}")
            self.carregar_produtos()
        except:
            QMessageBox.critical(self, "Erro", "Falha ao excluir produto.")
            
    def showEvent(self, event):
        # Evento nativo do PySide: Dispara sozinho toda vez que a aba aparece na tela
        super().showEvent(event)
        self.carregar_categorias()
        self.carregar_produtos()
        self.carregar_unidades()
        
    def carregar_unidades(self):
        # Desliga temporariamente o gatilho para não acionar um loop infinito
        self.combo_unidade.blockSignals(True) 
        self.combo_unidade.clear()
        
        try:
            resp = requests.get(f"{API_BASE_URL}/unidades/{self.cliente_dados['cliente_id']}")
            if resp.status_code == 200:
                for uni in resp.json():
                    self.combo_unidade.addItem(uni["nome"].upper(), uni["nome"]) # (Texto exibido, Valor real salvo)
        except:
            pass
            
        # Adiciona a opção mágica no final
        self.combo_unidade.addItem("+ Adicionar Nova...")
        self.combo_unidade.blockSignals(False) # Liga o gatilho de novo

    def verificar_nova_unidade(self, index):
        texto_selecionado = self.combo_unidade.itemText(index)
        
        if texto_selecionado == "+ Adicionar Nova...":
            nova_unidade, ok = QInputDialog.getText(self, "Nova Unidade", "Digite a nova unidade (Ex: Saco, Fardo):")
            
            if ok and nova_unidade.strip():
                dados = {"cliente_id": self.cliente_dados['cliente_id'], "nome": nova_unidade.strip()}
                resp = requests.post(f"{API_BASE_URL}/unidades", json=dados)
                
                if resp.status_code == 200:
                    self.carregar_unidades() 
                    index_novo = self.combo_unidade.findText(nova_unidade.strip().upper())
                    if index_novo >= 0:
                        self.combo_unidade.setCurrentIndex(index_novo)
                else:
                    QMessageBox.warning(self, "Aviso", "Esta unidade já existe!")
                    self.carregar_unidades() 
            else:
                self.carregar_unidades()