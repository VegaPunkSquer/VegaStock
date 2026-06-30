import requests
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
                               QComboBox, QSpinBox, QPushButton, QTableWidget, QTableWidgetItem,
                               QHeaderView, QMessageBox, QGroupBox, QFormLayout, QAbstractItemView, QInputDialog,
                               QStyledItemDelegate)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import QFileDialog
from datetime import datetime
import csv
import os

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
        self.ultimo_diretorio_csv = os.path.dirname(os.path.abspath(__file__)) # Memória da pasta
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
        # Layout horizontal para os botões do formulário
        layout_botoes_form = QHBoxLayout()
        layout_botoes_form.addWidget(self.btn_salvar)
        
        self.btn_importar_csv = QPushButton("📥 Importar Planilha (CSV)")
        self.btn_importar_csv.setStyleSheet("background-color: #2196F3; color: white; font-weight: bold; padding: 8px; border-radius: 4px;")
        self.btn_importar_csv.clicked.connect(self.iniciar_importacao)
        layout_botoes_form.addWidget(self.btn_importar_csv)

        self.btn_exportar_csv = QPushButton("📤 Exportar Catálogo")
        self.btn_exportar_csv.setStyleSheet("background-color: #FF9800; color: white; font-weight: bold; padding: 8px; border-radius: 4px;")
        self.btn_exportar_csv.clicked.connect(self.exportar_csv)
        layout_botoes_form.addWidget(self.btn_exportar_csv)
        
        layout_principal.addLayout(layout_botoes_form)

        # ==========================================
        # 2. TABELA DE PRODUTOS CADASTRADOS
        # ==========================================
        self.tabela = QTableWidget()
        self.tabela.setColumnCount(5)
        self.tabela.setHorizontalHeaderLabels(["ID", "Nome", "Categoria", "Unidade", "Alerta Mínimo"])
        self.tabela.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        # PERMITE edição ao dar dois cliques na célula!
        self.tabela.setSelectionBehavior(QAbstractItemView.SelectItems)
        self.tabela.setEditTriggers(QAbstractItemView.DoubleClicked)
        
        self.tabela.setColumnHidden(0, True)
        # Ocultar a coluna 2 foi removido para a Categoria aparecer
        layout_principal.addWidget(self.tabela)

        # Layout horizontal para agrupar os botões do rodapé
        layout_botoes_rodape = QHBoxLayout()

        self.btn_salvar_edicao = QPushButton("Salvar Edição do Produto")
        self.btn_salvar_edicao.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50; 
                color: white; 
                font-weight: bold; 
                padding: 6px;
                border-radius: 4px;
                border: 1px solid #388E3C;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #2E7D32;
                padding-top: 8px; /* O efeito visual de amassar o botão */
                padding-bottom: 4px;
            }
        """)
        self.btn_salvar_edicao.clicked.connect(self.salvar_edicao)
        self.btn_salvar_edicao.hide()
        # O ALARME: Se alguma célula for alterada, ele roda a função de mostrar o botão
        self.tabela.itemChanged.connect(self.mostrar_botao_salvar)

        self.btn_excluir = QPushButton("Excluir Produto Selecionado")
        self.btn_excluir.setStyleSheet("""
            QPushButton {
                color: red; 
                font-weight: bold; 
                border: 1px solid red; 
                padding: 6px;
                background-color: transparent;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #ffe6e6;
            }
            QPushButton:pressed {
                background-color: red;
                color: white;
                padding-top: 8px; /* Empurra o texto pra baixo simulando o clique */
                padding-bottom: 4px;
            }
        """)
        self.btn_excluir.clicked.connect(self.excluir_produto)
        
        self.btn_resetar = QPushButton("💣 APAGAR TODO O CATÁLOGO")
        self.btn_resetar.setStyleSheet("""
            QPushButton {
                background-color: #000; 
                color: #ff4444; 
                font-weight: bold; 
                border: 2px solid #ff4444; 
                padding: 6px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #220000;
            }
            QPushButton:pressed {
                background-color: #ff4444;
                color: #000;
                padding-top: 8px; /* Empurra o texto pra baixo simulando o clique */
                padding-bottom: 4px;
            }
        """)
        self.btn_resetar.clicked.connect(self.resetar_catalogo)

        layout_botoes_rodape.addWidget(self.btn_salvar_edicao)
        layout_botoes_rodape.addWidget(self.btn_excluir)
        layout_botoes_rodape.addStretch() # Empurra o reset pro canto direito
        layout_botoes_rodape.addWidget(self.btn_resetar)
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
        
        # Mapa de categorias para pegar o nome bonitinho
        mapa_cats = {c['id']: c['nome'] for c in dados.get("categorias", [])}
        
        for i, prod in enumerate(dados["produtos"]):
            self.tabela.insertRow(i)
            self.tabela.setItem(i, 0, QTableWidgetItem(str(prod["id"])))
            self.tabela.setItem(i, 1, QTableWidgetItem(prod["nome"]))
            
            nome_categoria = mapa_cats.get(prod["categoria_id"], "Sem Categoria")
            item_cat = QTableWidgetItem(nome_categoria)
            item_cat.setFlags(item_cat.flags() & ~Qt.ItemIsEditable) # Blinda para não editarem a categoria digitando
            self.tabela.setItem(i, 2, item_cat)
            
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
            
    def resetar_catalogo(self):
        msg = QMessageBox(self)
        msg.setWindowTitle("⚠ ALERTA DE DESTRUIÇÃO ⚠")
        msg.setText("Você está prestes a APAGAR TODOS OS PRODUTOS do catálogo.\n\nEssa ação é IRREVERSÍVEL. Se você tiver produtos no estoque ou histórico financeiro atrelado a eles, o sistema pode apresentar falhas ou ficar com dados órfãos.\n\nTem certeza absoluta que deseja destruir o catálogo inteiro?")
        msg.setIcon(QMessageBox.Critical)
        
        btn_sim = msg.addButton("Sim, Apagar Tudo!", QMessageBox.DestructiveRole)
        btn_sim.setStyleSheet("background-color: red; color: white; font-weight: bold;")
        btn_nao = msg.addButton("Não, pelo amor de Deus, cancele!", QMessageBox.RejectRole)
        msg.setDefaultButton(btn_nao)
        
        msg.exec()

        if msg.clickedButton() == btn_sim:
            linhas = self.tabela.rowCount()
            apagados = 0
            
            # Varre a tabela inteira, pegando os IDs (que estão ocultos na coluna 0) e manda bala
            for i in range(linhas):
                try:
                    produto_id = self.tabela.item(i, 0).text()
                    requests.delete(f"{API_BASE_URL}/produtos/{produto_id}")
                    apagados += 1
                except:
                    pass
            
            # O Dedo Duro: Salva o log usando o caminho absoluto blindado
            base_dir = os.path.dirname(os.path.abspath(__file__))
            caminho_log = os.path.join(base_dir, "log_auditoria_catalogo.txt")
            usuario = self.cliente_dados.get('login_usuario', 'Usuario_Desconhecido')
            agora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            
            try:
                with open(caminho_log, "a", encoding="utf-8") as arquivo_log:
                    arquivo_log.write(f"[{agora}] ALERTA CRITICO: O usuario '{usuario}' deletou TODO o catalogo em massa. Total apagado: {apagados} produtos.\n")
            except:
                pass # Se der erro pra salvar o log, o app não crasha
            
            QMessageBox.information(self, "Devastação Concluída", f"O reset foi finalizado. {apagados} produtos foram deletados.\n\nA auditoria dessa ação foi salva no sistema.")
            self.carregar_dados()

    def iniciar_importacao(self):
        msg = QMessageBox(self)
        msg.setWindowTitle("Importador de Planilha")
        msg.setText("AVISO: O sistema aceita apenas arquivos no formato CSV.\n\nSe a planilha não estiver perfeitamente preenchida, ocorrerão erros no catálogo e você NÃO conseguirá dar entrada no estoque depois.\n\nVocê assume a responsabilidade de importar?")
        msg.setIcon(QMessageBox.Warning)
        
        # Textos curtos para não cortar e CSS blindado
        btn_sim = msg.addButton("Sim", QMessageBox.AcceptRole)
        btn_sim.setStyleSheet("background-color: #4CAF50; color: white; padding: 6px 15px; font-weight: bold; border-radius: 4px; min-width: 60px;")
        
        btn_guia = msg.addButton("Guia", QMessageBox.HelpRole)
        btn_guia.setStyleSheet("background-color: #2196F3; color: white; padding: 6px 15px; font-weight: bold; border-radius: 4px; min-width: 60px;")
        
        btn_nao = msg.addButton("Não", QMessageBox.RejectRole)
        btn_nao.setStyleSheet("background-color: #f44336; color: white; padding: 6px 15px; font-weight: bold; border-radius: 4px; min-width: 60px;")
        
        msg.exec()
        
        if msg.clickedButton() == btn_sim:
            self.confirmar_consentimento_importacao()
        elif msg.clickedButton() == btn_guia:
            self.mostrar_guia_csv()

    def confirmar_consentimento_importacao(self):
        msg_consent = QMessageBox(self)
        msg_consent.setWindowTitle("Termo de Responsabilidade")
        msg_consent.setText("Ao clicar em confirmar, você garante que a planilha está no formato correto.\n\nFicará registrado no sistema a DATA, HORA e o USUÁRIO que realizou esta importação para fins de auditoria.\n\nDeseja continuar?")
        msg_consent.setIcon(QMessageBox.Information)
        
        btn_confirmar = msg_consent.addButton("Confirmar e Importar", QMessageBox.AcceptRole)
        btn_confirmar.setStyleSheet("background-color: #4CAF50; color: white; padding: 6px 15px; font-weight: bold; border-radius: 4px;")
        
        btn_cancelar = msg_consent.addButton("Cancelar", QMessageBox.RejectRole)
        btn_cancelar.setStyleSheet("background-color: #777; color: white; padding: 6px 15px; font-weight: bold; border-radius: 4px;")
        
        msg_consent.exec()
        
        if msg_consent.clickedButton() == btn_confirmar:
            self.processar_csv()

    def mostrar_guia_csv(self):
        guia = QMessageBox(self)
        guia.setWindowTitle("Manual do CSV")
        texto = (
            "A planilha deve ser salva como .CSV separada por vírgulas e ter EXATAMENTE 4 colunas com cabeçalho:\n\n"
            "Coluna 1: Nome do Produto (Ex: Batata Frita)\n"
            "Coluna 2: ID da Categoria (Ex: 3) -> Você deve ver o ID na lista de categorias no seu app.\n"
            "Coluna 3: Unidade de Medida (Ex: kg, litro, caixa)\n"
            "Coluna 4: Alerta de Estoque Mínimo (Ex: 10, ou 0 para regra geral)\n\n"
            "Jamais deixe unidades vazias ou escreva textos na coluna de IDs."
        )
        guia.setText(texto)
        guia.exec()

    def processar_csv(self):
        from PySide6.QtWidgets import QProgressDialog, QApplication
        from PySide6.QtCore import Qt
        
        arquivo, _ = QFileDialog.getOpenFileName(self, "Selecionar CSV do Catálogo", getattr(self, 'ultimo_diretorio_csv', ''), "Arquivos CSV (*.csv)")
        
        if arquivo:
            caminho_absoluto = os.path.abspath(arquivo)
            self.ultimo_diretorio_csv = os.path.dirname(caminho_absoluto) # Salva a pasta escolhida na memória
            try:
                # 1. FAZ A CONTAGEM DE LINHAS PARA A BARRA DE PROGRESSO
                with open(caminho_absoluto, mode='r', newline='', encoding='utf-8') as f:
                    primeira_linha = f.readline()
                    delimitador = ';' if ';' in primeira_linha else ','
                    f.seek(0)
                    # Conta as linhas descontando o cabeçalho
                    total_linhas = sum(1 for _ in csv.reader(f, delimiter=delimitador)) - 1
                
                if total_linhas <= 0:
                    QMessageBox.warning(self, "Vazio", "O arquivo CSV não possui produtos.")
                    return

                # Cria e exibe a Barra de Progresso
                progresso = QProgressDialog("Lendo a mente do usuário e importando...", "Cancelar", 0, total_linhas, self)
                progresso.setWindowTitle("Importação em Andamento")
                progresso.setWindowModality(Qt.WindowModal) # Trava a janela de trás
                progresso.setMinimumDuration(0) # Força a aparecer na hora
                progresso.setValue(0)

                sucesso = 0
                erros = 0
                cats_criadas = 0
                unis_criadas = 0
                
                # MAPEAMENTO DE CATEGORIAS
                mapa_categorias = {}
                for i in range(self.combo_categoria.count()):
                    cat_nome = self.combo_categoria.itemText(i).strip().lower()
                    cat_id = self.combo_categoria.itemData(i)
                    if cat_id:
                        mapa_categorias[cat_nome] = cat_id

                # MAPEAMENTO DE UNIDADES (O segredo do KG, Kg e kg)
                mapa_unidades = {}
                for i in range(self.combo_unidade.count()):
                    uni_nome = self.combo_unidade.itemText(i).strip()
                    if uni_nome and uni_nome.lower() != "selecione...":
                        # Salva a chave em minúsculo, mas o valor é o nome real formatado bonito
                        mapa_unidades[uni_nome.lower()] = uni_nome

                with open(caminho_absoluto, mode='r', newline='', encoding='utf-8') as f:
                    leitor = csv.DictReader(f, delimiter=delimitador)
                    
                    if leitor.fieldnames:
                        leitor.fieldnames = [name.strip('\ufeff').strip().lower() for name in leitor.fieldnames]
                    
                    if not leitor.fieldnames or 'produto' not in leitor.fieldnames or 'unidade' not in leitor.fieldnames or 'categoria' not in leitor.fieldnames:
                        progresso.cancel()
                        QMessageBox.critical(self, "Erro de Estrutura", "Cabeçalho inválido! Verifique as colunas.")
                        return
                    
                    for index, linha in enumerate(leitor):
                        # Se o cara apertar "Cancelar" na barra de progresso, a gente interrompe o loop
                        if progresso.wasCanceled():
                            break
                            
                        # Atualiza a barra visualmente
                        progresso.setValue(index)
                        QApplication.processEvents() # Destrava a tela para a animação fluir
                        
                        nome_prod = linha.get('produto', '').strip()
                        uni_raw = linha.get('unidade', '').strip()
                        cat_raw = linha.get('categoria', '').strip()
                        alerta_raw = linha.get('alerta', '').strip() if 'alerta' in linha else ''
                        
                        if not nome_prod or not uni_raw or not cat_raw:
                            erros += 1
                            continue
                            
                        cat_nome_lower = cat_raw.lower()
                        uni_lower = uni_raw.lower()
                        
                        # TRATA A CATEGORIA (Busca ou Cria)
                        if cat_nome_lower in mapa_categorias:
                            cat_id = mapa_categorias[cat_nome_lower]
                        else:
                            payload_cat = {"cliente_id": self.cliente_dados['cliente_id'], "nome": cat_raw}
                            resp_cat = requests.post(f"{API_BASE_URL}/categorias", json=payload_cat)
                            if resp_cat.status_code == 200:
                                nova_cat = resp_cat.json()
                                cat_id = nova_cat.get("id")
                                mapa_categorias[cat_nome_lower] = cat_id
                                self.combo_categoria.addItem(cat_raw, cat_id)
                                cats_criadas += 1
                            else:
                                erros += 1
                                continue
                                
                        # TRATA A UNIDADE (Busca inteligente ou Cria nova)
                        if uni_lower in mapa_unidades:
                            # Puxa o "KG" bonitão que já existe, ignorando se o cara digitou "Kg"
                            uni_final = mapa_unidades[uni_lower] 
                        else:
                            # Ferrou, não existe. Cria a unidade na API.
                            payload_uni = {"cliente_id": self.cliente_dados['cliente_id'], "nome": uni_raw}
                            resp_uni = requests.post(f"{API_BASE_URL}/unidades", json=payload_uni)
                            if resp_uni.status_code == 200:
                                uni_final = uni_raw
                                mapa_unidades[uni_lower] = uni_final
                                self.combo_unidade.addItem(uni_raw)
                                unis_criadas += 1
                            else:
                                uni_final = uni_raw # Segue a vida e tenta salvar assim mesmo
                        
                        try:
                            alerta = float(alerta_raw) if alerta_raw else 0.0
                        except ValueError:
                            alerta = 0.0

                        dados = {
                            "cliente_id": self.cliente_dados['cliente_id'],
                            "nome": nome_prod,
                            "categoria_id": cat_id,
                            "unidade_medida": uni_final,
                            "estoque_minimo": alerta
                        }
                        
                        resp = requests.post(f"{API_BASE_URL}/produtos", json=dados)
                        if resp.status_code == 200:
                            sucesso += 1
                        else:
                            erros += 1

                # Enche a barra a 100%
                progresso.setValue(total_linhas)
                
                # Gera o relatório do crime no txt
                base_dir = os.path.dirname(os.path.abspath(__file__))
                caminho_log = os.path.join(base_dir, "log_auditoria_catalogo.txt")
                usuario = self.cliente_dados.get('login_usuario', 'Usuario_Desconhecido')
                agora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                
                try:
                    with open(caminho_log, "a", encoding="utf-8") as arquivo_log:
                        arquivo_log.write(f"[{agora}] IMPORTACAO CSV: Usuario '{usuario}'. Produtos: {sucesso}. Erros: {erros}. Novas Categorias: {cats_criadas}. Novas Unidades: {unis_criadas}.\n")
                except:
                    pass
                                
                mensagem_final = f"Carga finalizada!\n\nProdutos importados com sucesso: {sucesso}"
                if cats_criadas > 0:
                    mensagem_final += f"\nCategorias novas criadas: {cats_criadas}"
                if unis_criadas > 0:
                    mensagem_final += f"\nUnidades de medida novas criadas: {unis_criadas}"
                if erros > 0:
                    mensagem_final += f"\nLinhas ignoradas ou com erro: {erros}"
                    
                QMessageBox.information(self, "Fim da Importação", mensagem_final)
                self.carregar_dados() # Atualiza a tabela pra revelar a mágica
                
            except Exception as e:
                QMessageBox.critical(self, "Falha Crítica", f"Ocorreu um erro ao processar o arquivo:\n{e}")

    def mostrar_guia_csv(self):
        guia = QMessageBox(self)
        guia.setWindowTitle("Manual do CSV")
        texto = (
            "A planilha deve ser salva no formato .CSV e conter EXATAMENTE estes nomes no cabeçalho das colunas:\n\n"
            "• 'produto' : Nome do item (Ex: Açúcar Refinado)\n"
            "• 'unidade' : Unidade de medida (Ex: kg, litro, uni)\n"
            "• 'categoria' : Nome da categoria (Ex: Despensa). Se a categoria não existir no app, ela será CRIADA automaticamente!\n"
            "• 'alerta' : [OPCIONAL] Quantidade mínima de segurança. Se vazio ou zerado, usa a Regra Geral."
        )
        guia.setText(texto)
        
        btn_voltar = guia.addButton("Voltar para Importação", QMessageBox.AcceptRole)
        btn_voltar.setStyleSheet("background-color: #2196F3; color: white; padding: 6px 15px; font-weight: bold; border-radius: 4px;")
        
        guia.exec()
        
        self.iniciar_importacao()

    def processar_csv(self):
        from PySide6.QtWidgets import QProgressDialog, QApplication
        from PySide6.QtCore import Qt
        
        arquivo, _ = QFileDialog.getOpenFileName(self, "Selecionar CSV do Catálogo", "", "Arquivos CSV (*.csv)")
        
        if arquivo:
            caminho_absoluto = os.path.abspath(arquivo)
            try:
                # 1. FAZ A CONTAGEM DE LINHAS
                with open(caminho_absoluto, mode='r', newline='', encoding='utf-8') as f:
                    primeira_linha = f.readline()
                    delimitador = ';' if ';' in primeira_linha else ','
                    f.seek(0)
                    total_linhas = sum(1 for _ in csv.reader(f, delimiter=delimitador)) - 1
                
                if total_linhas <= 0:
                    QMessageBox.warning(self, "Vazio", "O arquivo CSV não possui produtos.")
                    return

                # 2. PUXA OS DADOS FRESCOS DIRETO DO BANCO (Ignora a tela desatualizada)
                r_cat = requests.get(f"{API_BASE_URL}/categorias/{self.cliente_dados['cliente_id']}")
                r_uni = requests.get(f"{API_BASE_URL}/unidades/{self.cliente_dados['cliente_id']}")
                
                categorias_frescas = r_cat.json() if r_cat.status_code == 200 else []
                unidades_frescas = r_uni.json() if r_uni.status_code == 200 else []
                
                mapa_categorias = {c['nome'].strip().lower(): c['id'] for c in categorias_frescas}
                mapa_unidades = {u['nome'].strip().lower(): u['nome'] for u in unidades_frescas}

                # 3. CRIA E FORÇA A BARRA DE PROGRESSO A APARECER
                progresso = QProgressDialog("Lendo a planilha e inserindo no sistema...", "Cancelar", 0, total_linhas, self)
                progresso.setWindowTitle("Importação em Andamento")
                progresso.setWindowModality(Qt.WindowModal)
                progresso.setMinimumDuration(0)
                progresso.setValue(0)
                progresso.show() # <-- FORÇA A TELA DA BARRA A ABRIR

                sucesso = 0
                erros = 0
                cats_criadas = 0
                unis_criadas = 0
                erros_detalhes = []

                with open(caminho_absoluto, mode='r', newline='', encoding='utf-8') as f:
                    leitor = csv.DictReader(f, delimiter=delimitador)
                    
                    if leitor.fieldnames:
                        leitor.fieldnames = [name.strip('\ufeff').strip().lower() for name in leitor.fieldnames]
                    
                    if not leitor.fieldnames or 'produto' not in leitor.fieldnames or 'unidade' not in leitor.fieldnames or 'categoria' not in leitor.fieldnames:
                        progresso.cancel()
                        QMessageBox.critical(self, "Erro de Estrutura", "Cabeçalho inválido! Verifique as colunas.")
                        return
                    
                    for index, linha in enumerate(leitor):
                        if progresso.wasCanceled():
                            break
                            
                        progresso.setValue(index)
                        QApplication.processEvents()
                        
                        nome_prod = linha.get('produto', '').strip()
                        uni_raw = linha.get('unidade', '').strip()
                        cat_raw = linha.get('categoria', '').strip()
                        alerta_raw = linha.get('alerta', '').strip() if 'alerta' in linha else ''
                        
                        if not nome_prod or not uni_raw or not cat_raw:
                            erros += 1
                            continue
                            
                        cat_nome_lower = cat_raw.lower()
                        uni_lower = uni_raw.lower()
                        
                        # TRATA CATEGORIA
                        if cat_nome_lower in mapa_categorias:
                            cat_id = mapa_categorias[cat_nome_lower]
                        else:
                            payload_cat = {"cliente_id": self.cliente_dados['cliente_id'], "nome": cat_raw}
                            resp_cat = requests.post(f"{API_BASE_URL}/categorias", json=payload_cat)
                            if resp_cat.status_code == 200:
                                cat_id = resp_cat.json().get("id")
                                mapa_categorias[cat_nome_lower] = cat_id
                                cats_criadas += 1
                            else:
                                erros += 1
                                erros_detalhes.append(f"Erro ao criar categoria: {cat_raw}")
                                continue
                                
                        # TRATA UNIDADE
                        if uni_lower in mapa_unidades:
                            uni_final = mapa_unidades[uni_lower] 
                        else:
                            payload_uni = {"cliente_id": self.cliente_dados['cliente_id'], "nome": uni_raw}
                            resp_uni = requests.post(f"{API_BASE_URL}/unidades", json=payload_uni)
                            if resp_uni.status_code == 200:
                                uni_final = uni_raw
                                mapa_unidades[uni_lower] = uni_final
                                unis_criadas += 1
                            else:
                                uni_final = uni_raw 
                                erros_detalhes.append(f"Erro na unidade: {uni_raw}")
                        
                        try:
                            alerta = float(alerta_raw.replace(',', '.')) if alerta_raw else 0.0
                        except ValueError:
                            alerta = 0.0

                        dados = {
                            "cliente_id": self.cliente_dados['cliente_id'],
                            "nome": nome_prod,
                            "categoria_id": cat_id,
                            "unidade_medida": uni_final,
                            "estoque_minimo": alerta
                        }
                        
                        resp = requests.post(f"{API_BASE_URL}/produtos", json=dados)
                        if resp.status_code == 200:
                            sucesso += 1
                        else:
                            erros += 1

                progresso.setValue(total_linhas)
                
                base_dir = os.path.dirname(os.path.abspath(__file__))
                caminho_log = os.path.join(base_dir, "log_auditoria_catalogo.txt")
                usuario = self.cliente_dados.get('login_usuario', 'Usuario_Desconhecido')
                agora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                
                try:
                    with open(caminho_log, "a", encoding="utf-8") as arquivo_log:
                        arquivo_log.write(f"[{agora}] IMPORTACAO CSV: Usuario '{usuario}'. Sucesso: {sucesso}. Erros: {erros}. Cat criadas: {cats_criadas}. Uni criadas: {unis_criadas}.\n")
                except:
                    pass
                                
                mensagem_final = f"Carga finalizada!\n\nProdutos importados com sucesso: {sucesso}"
                if cats_criadas > 0:
                    mensagem_final += f"\nCategorias novas: {cats_criadas}"
                if unis_criadas > 0:
                    mensagem_final += f"\nUnidades novas: {unis_criadas}"
                if erros > 0:
                    mensagem_final += f"\nErros/Ignorados: {erros}"
                    if erros_detalhes:
                        mensagem_final += f"\nEx: {erros_detalhes[0]}"
                    
                QMessageBox.information(self, "Fim da Importação", mensagem_final)
                self.carregar_dados() # Chama direto, sem argumentos!
                
            except Exception as e:
                QMessageBox.critical(self, "Falha Crítica", f"Ocorreu um erro ao processar o arquivo:\n{e}")

    def exportar_csv(self):
        pasta_base = getattr(self, 'ultimo_diretorio_csv', os.path.dirname(os.path.abspath(__file__)))
        caminho_sugerido = os.path.join(pasta_base, "exportacao_catalogo.csv")
        
        caminho_salvar, _ = QFileDialog.getSaveFileName(
            self, 
            "Salvar Catálogo como CSV", 
            caminho_sugerido, 
            "Arquivos CSV (*.csv)"
        )
        
        if caminho_salvar:
            self.ultimo_diretorio_csv = os.path.dirname(os.path.abspath(caminho_salvar)) # Salva a pasta escolhida na memória
            try:
                with open(caminho_salvar, mode='w', newline='', encoding='utf-8-sig') as f:
                    writer = csv.writer(f, delimiter=';') 
                    
                    # Trocamos "id_produto" por um simples "nº" visual
                    writer.writerow(['nº', 'produto', 'categoria', 'unidade', 'alerta'])
                    
                    linhas = self.tabela.rowCount()
                    for i in range(linhas):
                        # Gera um número sequencial (1, 2, 3...) igualzinho o usuário vê na tela do app
                        numero_visual = str(i + 1)
                        nome = self.tabela.item(i, 1).text() if self.tabela.item(i, 1) else ""
                        cat = self.tabela.item(i, 2).text() if self.tabela.item(i, 2) else ""
                        un = self.tabela.item(i, 3).text() if self.tabela.item(i, 3) else ""
                        alerta = self.tabela.item(i, 4).text() if self.tabela.item(i, 4) else "0.0"
                        
                        writer.writerow([numero_visual, nome, cat, un, alerta])
                        
                QMessageBox.information(self, "Exportação Concluída", f"O catálogo foi salvo com sucesso em:\n{caminho_salvar}")
                
            except Exception as e:
                QMessageBox.critical(self, "Falha na Exportação", f"Ocorreu um erro ao tentar salvar o arquivo:\n{e}")