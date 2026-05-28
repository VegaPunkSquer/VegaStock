import requests
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
                               QComboBox, QSpinBox, QPushButton, QTableWidget, QTableWidgetItem,
                               QHeaderView, QMessageBox, QGroupBox, QFormLayout, QAbstractItemView, QInputDialog,
                               QStyledItemDelegate)
from PySide6.QtCore import Qt, QThread, Signal

API_BASE_URL = "https://vegap-vega-stock.hf.space"

class WorkerCatalogo(QThread):
    resultado = Signal(dict)
    erro = Signal(str)

    def __init__(self, cliente_id):
        super().__init__()
        self.cliente_id = cliente_id

    def run(self):
        try:
            # Faz as 3 buscas de uma vez
            r_cat = requests.get(f"{API_BASE_URL}/categorias/{self.cliente_id}")
            r_prod = requests.get(f"{API_BASE_URL}/produtos", params={"cliente_id": self.cliente_id})
            r_uni = requests.get(f"{API_BASE_URL}/unidades/{self.cliente_id}")

            # Empacota tudo num dicionário
            dados = {
                "categorias": r_cat.json() if r_cat.status_code == 200 else [],
                "produtos": r_prod.json() if r_prod.status_code == 200 else [],
                "unidades": r_uni.json() if r_uni.status_code == 200 else []
            }
            self.resultado.emit(dados)
        except Exception as e:
            self.erro.emit("Falha de conexão.")
            
class UnidadeDelegate(QStyledItemDelegate):
    def __init__(self, unidades, parent=None):
        super().__init__(parent)
        self.unidades = unidades

    def createEditor(self, parent, option, index):
        # Quando der duplo clique, cria o ComboBox
        combo = QComboBox(parent)
        combo.addItems(self.unidades)
        return combo

    def setEditorData(self, editor, index):
        # Puxa o texto que estava na célula pro ComboBox
        texto_atual = index.model().data(index, Qt.EditRole)
        if texto_atual:
            editor.setCurrentText(texto_atual)

    def setModelData(self, editor, model, index):
        # Quando terminar de editar, salva o texto escolhido de volta na célula
        model.setData(index, editor.currentText(), Qt.EditRole)

class AbaCatalogo(QWidget):
    def __init__(self, cliente_dados):
        super().__init__()
        self.cliente_dados = cliente_dados
        layout_principal = QVBoxLayout(self)

        lbl_titulo = QLabel("Catálogo de Produtos")
        lbl_titulo.setStyleSheet("font-size: 24px; font-weight: bold; color: #333; margin-bottom: 10px;")
        layout_principal.addWidget(lbl_titulo, alignment=Qt.AlignCenter)

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
        self.tabela.setColumnCount(5) # Voltamos para 5 colunas!
        self.tabela.setHorizontalHeaderLabels(["ID", "Nome", "ID Cat.", "Unidade", "Alerta Mínimo"])
        self.tabela.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        # PERMITE edição ao dar dois cliques na célula!
        self.tabela.setSelectionBehavior(QAbstractItemView.SelectItems)
        self.tabela.setEditTriggers(QAbstractItemView.DoubleClicked)
        
        self.tabela.setColumnHidden(0, True)
        self.tabela.setColumnHidden(2, True) 
        layout_principal.addWidget(self.tabela)

        # Layout horizontal para agrupar os botões do rodapé
        layout_botoes_rodape = QHBoxLayout()

        self.btn_salvar_edicao = QPushButton("Salvar Edição do Produto")
        self.btn_salvar_edicao.setStyleSheet("background-color: #2196F3; color: white; font-weight: bold; padding: 6px;")
        self.btn_salvar_edicao.clicked.connect(self.salvar_edicao)
        self.btn_salvar_edicao.hide()
        # O ALARME: Se alguma célula for alterada, ele roda a função de mostrar o botão
        self.tabela.itemChanged.connect(self.mostrar_botao_salvar)

        self.btn_excluir = QPushButton("Excluir Produto Selecionado")
        self.btn_excluir.setStyleSheet("color: red; font-weight: bold; border: 1px solid red; padding: 6px;")
        self.btn_excluir.clicked.connect(self.excluir_produto)
        
        layout_botoes_rodape.addWidget(self.btn_salvar_edicao)
        layout_botoes_rodape.addWidget(self.btn_excluir)
        layout_principal.addLayout(layout_botoes_rodape)

    # --- FUNÇÕES DE LÓGICA ---

    def showEvent(self, event):
        super().showEvent(event)
        self.carregar_dados()

    def carregar_dados(self):
        # Trava a tela e avisa que tá carregando
        self.combo_unidade.blockSignals(True)
        self.combo_categoria.clear()
        self.combo_unidade.clear()
        self.combo_categoria.addItem("Carregando...")
        self.combo_unidade.addItem("Carregando...")
        self.tabela.setRowCount(0)
        self.combo_unidade.blockSignals(False)

        # Manda o trabalhador pro porão
        self.worker = WorkerCatalogo(self.cliente_dados['cliente_id'])
        self.worker.resultado.connect(self.atualizar_tela)
        self.worker.start()

    def atualizar_tela(self, dados):
        # 1. Preenche Categorias
        self.combo_categoria.clear()
        for cat in dados["categorias"]:
            self.combo_categoria.addItem(cat["nome"], cat["id"])

        # 2. Preenche Unidades
        self.combo_unidade.blockSignals(True)
        self.combo_unidade.clear()
        for uni in dados["unidades"]:
            self.combo_unidade.addItem(uni["nome"].upper(), uni["nome"])
        self.combo_unidade.addItem("+ Adicionar Nova...")
        self.combo_unidade.blockSignals(False)

        # 3. Preenche Tabela
        self.tabela.blockSignals(True) # Manda o PySide fechar os olhos
        self.tabela.setRowCount(0)        
        for i, prod in enumerate(dados["produtos"]):
            self.tabela.insertRow(i)
            self.tabela.setItem(i, 0, QTableWidgetItem(str(prod["id"])))
            self.tabela.setItem(i, 1, QTableWidgetItem(prod["nome"]))
            self.tabela.setItem(i, 2, QTableWidgetItem(str(prod["categoria_id"])))
            
            # VOLTOU A SER TEXTO NORMAL!
            self.tabela.setItem(i, 3, QTableWidgetItem(prod["unidade_medida"]))
            
            alerta = str(prod["estoque_minimo"]) if prod["estoque_minimo"] > 0 else "Geral"
            item_alerta = QTableWidgetItem(alerta)
            item_alerta.setFlags(item_alerta.flags() & ~Qt.ItemIsEditable) # <-- BLINDA A CÉLULA
            self.tabela.setItem(i, 4, item_alerta)

        # 4. Aplica o espião na coluna da Unidade (Coluna 3)
        nomes_unidades = [uni["nome"].upper() for uni in dados["unidades"]]
        delegate = UnidadeDelegate(nomes_unidades, self.tabela)
        self.tabela.setItemDelegateForColumn(3, delegate)
        self.tabela.blockSignals(False) # Pode abrir os olhos, terminou!

    def cadastrar_produto(self):
        nome = self.input_nome.text().strip()
        cat_id = self.combo_categoria.currentData()
        unidade = self.combo_unidade.currentText()
        alerta = float(self.spin_alerta.value())

        if unidade == "+ Adicionar Nova..." or not unidade:
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
                self.carregar_dados() # Acorda a Thread pra atualizar a tela
                QMessageBox.information(self, "Sucesso", "Produto cadastrado!")
        except Exception:
            QMessageBox.critical(self, "Erro", "Não foi possível conectar à API.")

    def excluir_produto(self):
        linha = self.tabela.currentRow()
        if linha < 0:
            return

        produto_id = self.tabela.item(linha, 0).text()
        try:
            requests.delete(f"{API_BASE_URL}/produtos/{produto_id}")
            self.carregar_dados() # Acorda a Thread pra atualizar a tela
        except:
            QMessageBox.critical(self, "Erro", "Falha ao excluir produto.")

    def verificar_nova_unidade(self, index):
        texto_selecionado = self.combo_unidade.itemText(index)
        
        if texto_selecionado == "+ Adicionar Nova...":
            nova_unidade, ok = QInputDialog.getText(self, "Nova Unidade", "Digite a nova unidade (Ex: Saco, Fardo):")
            
            if ok and nova_unidade.strip():
                dados = {"cliente_id": self.cliente_dados['cliente_id'], "nome": nova_unidade.strip()}
                resp = requests.post(f"{API_BASE_URL}/unidades", json=dados)
                
                if resp.status_code == 200:
                    self.carregar_dados() # Atualiza tudo com a nova unidade
                else:
                    QMessageBox.warning(self, "Aviso", "Esta unidade já existe!")
                    self.carregar_dados() 
            else:
                self.carregar_dados()
                
    def mostrar_botao_salvar(self, item):
        # Só mostra o botão se a tela já terminou de carregar
        self.btn_salvar_edicao.show()
                
    def salvar_edicao(self):
        linha = self.tabela.currentRow()
        if linha < 0:
            QMessageBox.warning(self, "Aviso", "Selecione uma linha para salvar a edição.")
            return

        # Puxa o que o usuário alterou nas células
        produto_id = int(self.tabela.item(linha, 0).text())
        novo_nome = self.tabela.item(linha, 1).text().strip()
        # Agora ele lê direto a opção que o cara selecionou na listinha da tabela
        nova_unidade = self.tabela.item(linha, 3).text().strip()

        dados_editados = {
            "cliente_id": self.cliente_dados['cliente_id'],
            "nome": novo_nome,
            "unidade_medida": nova_unidade
        }

        # Avisa a Render
        try:
            # Você precisa ter uma rota PUT /produtos/{produto_id} na sua API (main.py)
            resp = requests.put(f"{API_BASE_URL}/produtos/{produto_id}", json=dados_editados)
            if resp.status_code == 200:
                QMessageBox.information(self, "Sucesso", "Produto atualizado com sucesso!")
                self.btn_salvar_edicao.hide() # Esconde o botão de salvar de novo
                self.carregar_dados() # Recarrega para ter certeza
            else:
                # Agora ele vai te mostrar o número do erro e o que a API reclamou!
                QMessageBox.warning(self, "Erro", f"A API recusou: {resp.status_code} - {resp.text}")
                self.btn_salvar_edicao.hide() # Força o botão a sumir pra não ficar te encarando
        except Exception:
            QMessageBox.critical(self, "Erro", "Não foi possível conectar à API.")