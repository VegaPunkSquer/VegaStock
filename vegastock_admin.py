import sys
import requests
from PySide6.QtCore import QTimer, Qt, QThread, Signal, QDate
from PySide6.QtWidgets import (QApplication, QLabel, QMainWindow, QWidget, QHBoxLayout, 
                               QVBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView, 
                               QGroupBox, QFormLayout, QLineEdit, QComboBox, QDateEdit, 
                               QPushButton, QMessageBox, QListWidget, QAbstractItemView, QTabWidget)

class WorkerListarFeedbacks(QThread):
    resultado = Signal(list)
    erro = Signal(str)

    def run(self):
        headers = {"token-master": TOKEN_MASTER}
        try:
            response = requests.get(f"{API_BASE_URL}/admin/feedbacks", headers=headers)
            if response.status_code == 200:
                self.resultado.emit(response.json())
            else:
                self.erro.emit(f"Erro {response.status_code}")
        except Exception as e:
            self.erro.emit(str(e))

from PySide6.QtWidgets import QListWidget  # Garanta que este widget nativo está importado

class WorkerListarConversasAtivas(QThread):
    resultado = Signal(list)

    def run(self):
        headers = {"token-master": TOKEN_MASTER}
        try:
            response = requests.get(f"{API_BASE_URL}/admin/suporte/conversas_actives", headers=headers)
            if response.status_code == 200:
                self.resultado.emit(response.json())
        except:
            pass

class WorkerEnviarAdminChat(QThread):
    sucesso = Signal()

    def __init__(self, cliente_id, texto):
        super().__init__()
        self.cliente_id = cliente_id
        self.texto = texto

    def run(self):
        payload = {
            "cliente_id": self.cliente_id,
            "remetente": "ADMIN",
            "texto": self.texto
        }
        try:
            requests.post(f"{API_BASE_URL}/suporte/enviar", json=payload)
            self.sucesso.emit()
        except:
            pass

# URL exata do seu Space no Hugging Face
API_BASE_URL = "https://vegap-vega-sotck.hf.space"
# Defina aqui o mesmo token master que você colocou no Config Secret do Hugging Face
TOKEN_MASTER = "VegaChaveMestre123"

class WorkerAdicionarWhitelist(QThread):
    sucesso = Signal(str)
    erro = Signal(str)

    def __init__(self, cnpj, plano, data_fim):
        super().__init__()
        self.cnpj = cnpj
        self.plano = plano
        self.data_fim = data_fim

    def run(self):
        payload = {
            "cnpj": self.cnpj,
            "plano": self.plano,
            "data_fim": self.data_fim
        }
        headers = {
            "token-master": TOKEN_MASTER
        }
        try:
            response = requests.post(f"{API_BASE_URL}/admin/whitelist", json=payload, headers=headers)
            if response.status_code == 200:
                self.sucesso.emit(response.json().get("mensagem", "CNPJ liberado com sucesso!"))
            else:
                try:
                    msg_erro = response.json().get("detail", "Erro desconhecido.")
                except:
                    msg_erro = f"Erro {response.status_code}"
                self.erro.emit(msg_erro)
        except Exception as e:
            self.erro.emit(f"Falha de conexão com a API: {str(e)}")

class JanelaAdmin(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("VegaStock — Painel de Controle Operacional Admin")
        self.resize(800, 450)

        # Instancia o gerenciador de abas nativo como o coração da janela
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        # CONTAINER DA ABA 1: Controle de Whitelist (Seu código antigo envelopado aqui)
        container_acessos = QWidget()
        layout_principal = QHBoxLayout(container_acessos)
        layout_principal.setContentsMargins(15, 15, 15, 15)
        layout_principal.setSpacing(15)

        # ========================================================
        # ESQUERDA: Tabela de Monitoramento de Clientes Autorizados
        # ========================================================
        self.tabela_clientes = QTableWidget()
        self.tabela_clientes.setColumnCount(3)
        self.tabela_clientes.setHorizontalHeaderLabels(["CNPJ Liberado", "Plano Selecionado", "Até Quando Livre"])
        self.tabela_clientes.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabela_clientes.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tabela_clientes.setSelectionBehavior(QAbstractItemView.SelectRows)
        layout_principal.addWidget(self.tabela_clientes, stretch=6)

        # ========================================================
        # DIREITA: Formulário de Pré-Autorização de Testes (Whitelist)
        # ========================================================
        grupo_whitelist = QGroupBox("Autorizar Novo CNPJ para Testes")
        layout_form = QFormLayout(grupo_whitelist)
        layout_form.setSpacing(10)

        self.input_cnpj = QLineEdit()
        self.input_cnpj.setPlaceholderText("Apenas números")
        # Máscara padrão nativa para evitar erros de digitação do CNPJ
        self.input_cnpj.setInputMask("99.999.999/9999-99")

        self.combo_plano = QComboBox()
        self.combo_plano.addItems(["BÁSICO", "PRO"])

        self.date_final = QDateEdit()
        self.date_final.setCalendarPopup(True)  # Abre o calendário nativo padrão ao clicar
        self.date_final.setMinimumDate(QDate.currentDate())  # Não deixa escolher data retroativa
        self.date_final.setDate(QDate.currentDate().addDays(7))  # Sugere 7 dias a partir de hoje por padrão

        self.btn_enviar = QPushButton("Liberar Acesso Gratuito")
        self.btn_enviar.clicked.connect(self.executar_liberacao_cnpj)

        layout_form.addRow("CNPJ do Cliente:", self.input_cnpj)
        layout_form.addRow("Plano de Teste:", self.combo_plano)
        layout_form.addRow("Livre Até:", self.date_final)
        layout_form.addRow("", self.btn_enviar)

        layout_principal.addWidget(grupo_whitelist, stretch=4)
        self.tabs.addTab(container_acessos, "🔑 Pré-Autorizar Testes")

        # CONTAINER DA ABA 2: Central de Feedback dos Clientes ( Analytics )
        container_feedbacks = QWidget()
        layout_feedbacks = QVBoxLayout(container_feedbacks)
        layout_feedbacks.setContentsMargins(15, 15, 15, 15)
        layout_feedbacks.setSpacing(10)

        # Tabelão padrão para listar os textões e notas
        self.tabela_feedbacks = QTableWidget()
        self.tabela_feedbacks.setColumnCount(4)
        self.tabela_feedbacks.setHorizontalHeaderLabels(["Empresa / Cliente", "Nota (Estrelas)", "Comentário / Sugestão", "Data de Envio"])
        self.tabela_feedbacks.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabela_feedbacks.setEditTriggers(QAbstractItemView.NoEditTriggers)
        layout_feedbacks.addWidget(self.tabela_feedbacks)

        self.btn_atualizar_feedbacks = QPushButton("🔄 Atualizar Mural de Feedbacks")
        self.btn_atualizar_feedbacks.clicked.connect(self.carregar_feedbacks_nuvem)
        layout_feedbacks.addWidget(self.btn_atualizar_feedbacks)

        self.tabs.addTab(container_feedbacks, "⭐ Satisfação & Sugestões")
        
        # CONTAINER DA ABA 3: Central de Atendimento em Tempo Real
        container_suporte = QWidget()
        layout_suporte_master = QHBoxLayout(container_suporte)
        layout_suporte_master.setContentsMargins(15, 15, 15, 15)
        layout_suporte_master.setSpacing(15)

        # Esquerda: Lista nativa de conversas/CNPJs ativos
        self.lista_clientes_ativos = QListWidget()
        self.lista_clientes_ativos.setFixedWidth(220)
        self.lista_clientes_ativos.itemClicked.connect(self.selecionar_cliente_conversa)
        layout_suporte_master.addWidget(self.lista_clientes_ativos)

        # Direita: Painel vertical do chat selecionado
        painel_chat_direito = QWidget()
        layout_chat_direito = QVBoxLayout(painel_chat_direito)
        layout_chat_direito.setContentsMargins(0, 0, 0, 0)
        layout_chat_direito.setSpacing(10)

        self.lbl_cliente_atual = QLabel("<b>Selecione um cliente para iniciar o atendimento</b>")
        self.lista_mensagens_admin = QListWidget()
        
        # Barra de digitação inferior
        layout_input_admin = QHBoxLayout()
        self.input_msg_admin = QLineEdit()
        self.input_msg_admin.setPlaceholderText("Digite a resposta mestre aqui...")
        self.input_msg_admin.returnPressed.connect(self.enviar_resposta_admin)
        self.input_msg_admin.setEnabled(False)
        
        self.btn_enviar_admin = QPushButton("Responder ✈️")
        self.btn_enviar_admin.clicked.connect(self.enviar_resposta_admin)
        self.btn_enviar_admin.setEnabled(False)

        layout_input_admin.addWidget(self.input_msg_admin, stretch=8)
        layout_input_admin.addWidget(self.btn_enviar_admin, stretch=2)

        layout_chat_direito.addWidget(self.lbl_cliente_atual)
        layout_chat_direito.addWidget(self.lista_mensagens_admin)
        layout_chat_direito.addLayout(layout_input_admin)
        layout_suporte_master.addWidget(painel_chat_direito)

        self.tabs.addTab(container_suporte, "💬 Central de Atendimento")

        # Variáveis de controle de estado interno
        self.cliente_id_selecionado = None
        self.historico_cache_tamanho = 0

        # Timer nativo para atualizar a lista de conversas e o chat a cada 4 segundos
        self.timer_admin_suporte = QTimer(self)
        self.timer_admin_suporte.timeout.connect(self.atualizar_central_suporte)
        self.timer_admin_suporte.start(4000)

        # Dispara a primeira busca imediata de conversas
        QTimer.singleShot(1000, self.atualizar_central_suporte)

        # Puxa os dados da nuvem automaticamente logo na inicialização para você ver o painel vivo
        self.carregar_feedbacks_nuvem()

    def executar_liberacao_cnpj(self):
        cnpj_cru = self.input_cnpj.text().strip()
        # Remove a máscara nativa deixando apenas os números puros
        cnpj_limpo = "".join(filter(str.isdigit, cnpj_cru))
        plano = self.combo_plano.currentText()
        # Converte a data selecionada para string no formato ISO (AAAA-MM-DD) para enviar à API
        data_fim = self.date_final.date().toString("yyyy-MM-dd")

        if len(cnpj_limpo) != 14:
            QMessageBox.warning(self, "Aviso", "Por favor, digite um CNPJ válido with 14 dígitos.")
            return

        self.btn_enviar.setEnabled(False)
        self.btn_enviar.setText("⏳ Enviando para o Space...")

        # Dispara o Worker em segundo plano para não congelar a interface
        self.worker = WorkerAdicionarWhitelist(cnpj_limpo, plano, data_fim)
        self.worker.sucesso.connect(self.sucesso_whitelist)
        self.worker.erro.connect(self.erro_whitelist)
        self.worker.start()

    def sucesso_whitelist(self, mensagem):
        self.btn_enviar.setEnabled(True)
        self.btn_enviar.setText("Liberar Acesso Gratuito")
        
        # Alimenta a tabela local temporariamente para feedback visual imediato
        linha = self.tabela_clientes.rowCount()
        self.tabela_clientes.insertRow(linha)
        self.tabela_clientes.setItem(linha, 0, QTableWidgetItem(self.input_cnpj.text()))
        self.tabela_clientes.setItem(linha, 1, QTableWidgetItem(self.combo_plano.currentText()))
        self.tabela_clientes.setItem(linha, 2, QTableWidgetItem(self.date_final.date().toString("dd/MM/yyyy")))

        QMessageBox.information(self, "Sucesso Master", mensagem)
        self.input_cnpj.clear()

    def erro_whitelist(self, mensagem):
        self.btn_enviar.setEnabled(True)
        self.btn_enviar.setText("Liberar Acesso Gratuito")
        QMessageBox.critical(self, "Falha de Operação", mensagem)
        
    def carregar_feedbacks_nuvem(self):
        self.btn_atualizar_feedbacks.setEnabled(False)
        self.btn_atualizar_feedbacks.setText("⏳ Buscando avaliações na Neon...")
        
        self.worker_fb = WorkerListarFeedbacks()
        self.worker_fb.resultado.connect(self.sucesso_feedbacks)
        self.worker_fb.erro.connect(self.erro_feedbacks)
        self.worker_fb.start()

    def sucesso_feedbacks(self, lista_feedbacks):
        self.btn_atualizar_feedbacks.setEnabled(True)
        self.btn_atualizar_feedbacks.setText("🔄 Atualizar Mural de Feedbacks")
        self.tabela_feedbacks.setRowCount(0)

        for i, fb in enumerate(lista_feedbacks):
            self.tabela_feedbacks.insertRow(i)
            
            # Formata a nota visualmente para ficar fácil de bater o olho
            estrelas_vistas = "⭐" * fb["estrelas"]
            
            # Trata a data para o padrão BR
            data_crua = fb["data_envio"].split("T")[0]
            data_br = "/".join(data_crua.split("-")[::-1])

            self.tabela_feedbacks.setItem(i, 0, QTableWidgetItem(str(fb["nome_fantasia"])))
            self.tabela_feedbacks.setItem(i, 1, QTableWidgetItem(estrelas_vistas))
            self.tabela_feedbacks.setItem(i, 2, QTableWidgetItem(str(fb["comentario"] or "Sem comentários adicionais.")))
            self.tabela_feedbacks.setItem(i, 3, QTableWidgetItem(data_br))

    def erro_feedbacks(self, mensagem):
        self.btn_atualizar_feedbacks.setEnabled(True)
        self.btn_atualizar_feedbacks.setText("🔄 Atualizar Mural de Feedbacks")
        QMessageBox.warning(self, "Aviso de Coleta", f"Não foi possível atualizar os feedbacks: {mensagem}")
        
    def atualizar_central_suporte(self):
        # Busca a lista de conversas ativas na nuvem
        self.worker_ativas = WorkerListarConversasAtivas()
        self.worker_ativas.resultado.connect(self.atualizar_lista_clientes_ativos)
        self.worker_ativas.start()

        # Se já tiver um cliente selecionado na tela, atualiza o chat dele em tempo real
        if self.cliente_id_selecionado:
            from aba_sobre import WorkerBuscarChat # Reaproveita o worker que criamos na aba sobre
            self.worker_recuperar = WorkerBuscarChat(self.cliente_id_selecionado)
            self.worker_recuperar.mensagens_recebidas.connect(self.renderizar_mensagens_admin)
            self.worker_recuperar.start()

    def atualizar_lista_clientes_ativos(self, lista_conversas):
        # Evita reconstruir a lista se nada mudou para não quebrar a seleção do usuário
        if len(lista_conversas) == self.lista_clientes_ativos.count():
            return
            
        self.lista_clientes_ativos.clear()
        for conv in lista_conversas:
            texto_exibido = f"{conv['nome_fantasia']}\n└ {conv['ultima_mensagem'][:20]}..."
            item = QTableWidgetItem(texto_exibido)
            # Guarda o ID do cliente escondido dentro do item da lista nativa
            item.setData(Qt.UserRole, conv["cliente_id"])
            item.setData(Qt.ToolTipRole, conv["nome_fantasia"])
            self.lista_clientes_ativos.addItem(texto_exibido)

    def selecionar_cliente_conversa(self, item):
        # Recupera o ID do cliente correspondente à linha clicada
        linha_index = self.lista_clientes_ativos.row(item)
        lista_itens = [self.lista_clientes_ativos.item(i) for i in range(self.lista_clientes_ativos.count())]
        # Gambiarra limpa para pegar o ID correto do item clicado
        # Como o PySide6 ListWidget armazena objetos, buscamos o metadado
        self.cliente_id_selecionado = item.data(Qt.UserRole) or (linha_index + 1) # Fallback seguro
        
        # Como o clique foi explícito, força o reset do cache para renderizar na hora
        self.historico_cache_tamanho = 0
        nome_cliente = item.text().split('\n')[0]
        self.lbl_cliente_atual.setText(f"<b>Atendendo: {nome_cliente}</b>")
        
        self.input_msg_admin.setEnabled(True)
        self.btn_enviar_admin.setEnabled(True)
        self.lista_mensagens_admin.clear()
        self.atualizar_central_suporte()

    def renderizar_mensagens_admin(self, lista_msg):
        if len(lista_msg) == self.historico_cache_tamanho:
            return
            
        self.historico_cache_tamanho = len(lista_msg)
        self.lista_mensagens_admin.clear()
        
        for msg in lista_msg:
            remetente = "CLIENTE" if msg["remetente"] == "CLIENTE" else "Você (Admin)"
            self.lista_mensagens_admin.addItem(f"[{remetente}]: {msg['texto']}")
            
        self.lista_mensagens_admin.scrollToBottom()

    def enviar_resposta_admin(self):
        texto = self.input_msg_admin.text().strip()
        if not texto or not self.cliente_id_selecionado:
            return
            
        self.btn_enviar_admin.setEnabled(False)
        self.input_msg_admin.clear()
        
        self.worker_envio_admin = WorkerEnviarAdminChat(self.cliente_id_selecionado, texto)
        # Reativa os botões e força a atualização assim que a mensagem subir
        self.worker_envio_admin.sucesso.connect(lambda: [self.btn_enviar_admin.setEnabled(True), self.atualizar_central_suporte()])
        self.worker_envio_admin.start()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    janela = JanelaAdmin()
    janela.show()
    sys.exit(app.exec())