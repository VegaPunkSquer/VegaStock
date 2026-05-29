from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt
import requests
from PySide6.QtWidgets import QListWidget, QListWidgetItem, QLineEdit, QPushButton, QHBoxLayout, QVBoxLayout, QLabel, QWidget
from PySide6.QtCore import QTimer, QThread, Signal
import os

API_BASE_URL = "https://vegap-vega-stock.hf.space"

class AbaSobre(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignTop)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(15)

        # Título principal
        lbl_titulo = QLabel("VegaStock — Sistema de Estoque B2B")
        lbl_titulo.setStyleSheet("font-size: 20px; font-weight: bold;")
        layout.addWidget(lbl_titulo)

        # Informações gerais do software
        lbl_info = QLabel(
            "<b>Versão:</b> 1.0.0<br>"
            "<b>Descrição:</b> Sistema desktop inteligente para gestão de estoque em restaurantes, "
            "cafeterias e indústrias alimentícias, equipado com controle multitenant e relatórios "
            "avançados de desperdício."
            "<br>Feito pela Vega Tech em Parceria com a Mais Soluções Integradas!<br>"
        )
        lbl_info.setStyleSheet("font-size: 13px; color: #333333; line-height: 140%;")
        layout.addWidget(lbl_info)

        layout.addSpacing(10)

        # Título da seção de suporte
        lbl_suporte = QLabel("Canais de Suporte Técnico")
        lbl_suporte.setStyleSheet("font-size: 15px; font-weight: bold;")
        layout.addWidget(lbl_suporte)

        # Estrutura de contatos com links autênticos para e-mail e WhatsApp (2 seções)
        texto_suporte = (
            "<table cellspacing='15' cellpadding='0' style='font-size: 13px; color: #000000;'>"
            "  <tr>"
            "    <td style='font-weight: bold; font-size: 14px;'>🚀 Vega Tech Solutions</td>"
            "    <td style='font-weight: bold; font-size: 14px;'>🤝 Mais Soluções Integradas</td>"
            "  </tr>"
            "  <tr>"
            "    <td>"
            "      📧 <b>E-mail:</b> <a href='mailto:sergio.renan.ms@gmail.com' style='color: #009EE3;'>suporte@vegastock.com.br</a><br><br>"
            "      💬 <b>WhatsApp:</b> <a href='https://wa.me/5512981194607' style='color: #25D366;'>🟢 (12) 98119-4607</a>"
            "    </td>"
            "    <td>"
            "      📧 <b>E-mail:</b> <a href='mailto:maissolucoesintegradas@gmail.com' style='color: #009EE3;'>suporte@associado.com.br</a><br><br>"
            "      💬 <b>WhatsApp:</b> <a href='https://wa.me/558396622804' style='color: #25D366;'>🟢 (83) 99662-2804</a>"
            "    </td>"
            "  </tr>"
            "</table>"
        )

        lbl_contatos = QLabel(texto_suporte)
        lbl_contatos.setOpenExternalLinks(True)
        layout.addWidget(lbl_contatos)

        layout.addStretch()

        # Rodapé
        lbl_rodape = QLabel("© 2026 VegaStock. Todos os direitos reservados.")
        lbl_rodape.setStyleSheet("color: #888888; font-size: 10px;")
        layout.addWidget(lbl_rodape, alignment=Qt.AlignHCenter)
        
        # ========================================================
        # ESTRUTURA NATIVA DO CHAT DE SUPORTE INTERNO
        # ========================================================
        lbl_suporte = QLabel("💬 Central de Atendimento VegaStock")
        lbl_suporte.setStyleSheet("font-size: 15px; font-weight: bold; color: #2C3E50; margin-top: 15px; margin-bottom: 5px;")
        layout_principal = self.layout()
        layout_principal.addWidget(lbl_suporte)

        # Lista nativa com fundo de chat e sem bordas genéricas esticadas
        self.lista_chat = QListWidget()
        self.lista_chat.setStyleSheet("QListWidget { border: 1px solid #DCDCDC; border-radius: 6px; background-color: #F4F6F7; padding: 8px; }")
        layout_principal.addWidget(self.lista_chat)

        # Barra inferior de digitação e envio
        layout_envio = QHBoxLayout()
        self.input_mensagem = QLineEdit()
        self.input_mensagem.setPlaceholderText("Digite sua dúvida aqui...")
        self.input_mensagem.returnPressed.connect(self.enviar_mensagem_suporte) # Envia ao apertar Enter
        
        self.btn_enviar_chat = QPushButton("Enviar ✈️")
        self.btn_enviar_chat.clicked.connect(self.enviar_mensagem_suporte)
        
        layout_envio.addWidget(self.input_mensagem, stretch=8)
        layout_envio.addWidget(self.btn_enviar_chat, stretch=2)
        layout_principal.addLayout(layout_envio)

        # Timer nativo para atualizar as mensagens em segundo plano a cada 5 segundos
        self.timer_chat = QTimer(self)
        self.timer_chat.timeout.connect(self.atualizar_chat_suporte)
        self.timer_chat.start(5000) # 5000 milissegundos = 5 segundos

        # Carrega o histórico imediatamente ao abrir a aba
        QTimer.singleShot(500, self.atualizar_chat_suporte)
        
# ========================================================
# WORKERS EM THREAD PARA GERENCIAMENTO DO CHAT
# ========================================================

class WorkerBuscarChat(QThread):
    mensagens_recebidas = Signal(list)

    def __init__(self, cliente_id):
        super().__init__()
        self.cliente_id = cliente_id

    def run(self):
        try:
            response = requests.get(f"{API_BASE_URL}/suporte/historico/{self.cliente_id}")
            if response.status_code == 200:
                self.mensagens_recebidas.emit(response.json())
        except:
            pass

class WorkerEnviarChat(QThread):
    sucesso = Signal()

    def __init__(self, cliente_id, texto):
        super().__init__()
        self.cliente_id = cliente_id
        self.texto = texto

    def run(self):
        payload = {
            "cliente_id": self.cliente_id,
            "remetente": "CLIENTE",
            "texto": self.texto
        }
        try:
            requests.post(f"{API_BASE_URL}/suporte/enviar", json=payload)
            self.sucesso.emit()
        except:
            pass

# Injeta os métodos de controle dentro da classe AbaSobre existente
def atualizar_chat_suporte(self):
    # Captura de forma segura os dados do cliente logado no app principal
    if hasattr(self.window(), 'cliente_dados') and self.window().cliente_dados:
        cliente_id = self.window().cliente_dados.get("cliente_id") or self.window().cliente_dados.get("id")
        if cliente_id:
            self.worker_buscar = WorkerBuscarChat(cliente_id)
            self.worker_buscar.mensagens_recebidas.connect(self.renderizar_mensagens)
            self.worker_buscar.start()

def renderizar_mensagens(self, lista_msg):
    if not hasattr(self, '_cache_qtd_mensagens'):
        self._cache_qtd_mensagens = 0
        
    if len(lista_msg) == self._cache_qtd_mensagens:
        return
        
    self._cache_qtd_mensagens = len(lista_msg)
    self.lista_chat.clear()
    
    for msg in lista_msg:
        item = QListWidgetItem(self.lista_chat)
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(5, 5, 5, 5)
        
        lbl = QLabel()
        lbl.setWordWrap(True)
        lbl.setMaximumWidth(480)  # Impede que o balão estique bizarramente em monitores UltraWide
        
        if msg["remetente"] == "CLIENTE":
            lbl.setText(f"<b>Você:</b><br>{msg['texto']}")
            lbl.setStyleSheet("background-color: #DCF8C6; border: 1px solid #C7E5A9; border-radius: 8px; padding: 10px; font-size: 13px; color: #222222;")
            layout.addStretch()  # Empurra o balão do cliente para a direita
            layout.addWidget(lbl)
        else:
            lbl.setText(f"<b>Suporte VegaStock:</b><br>{msg['texto']}")
            lbl.setStyleSheet("background-color: #FFFFFF; border: 1px solid #E2E2E2; border-radius: 8px; padding: 10px; font-size: 13px; color: #222222;")
            layout.addWidget(lbl)
            layout.addStretch()  # Empurra o balão do admin para a esquerda
            
        container.setLayout(layout)
        item.setSizeHint(container.sizeHint())
        self.lista_chat.setItemWidget(item, container)
    
    # [O Aviso da Montanha] Estilizado como um belo banner de alerta do sistema
    if lista_msg and lista_msg[-1]["remetente"] == "CLIENTE":
        item_sys = QListWidgetItem(self.lista_chat)
        container_sys = QWidget()
        layout_sys = QHBoxLayout(container_sys)
        layout_sys.setContentsMargins(5, 8, 5, 5)
        
        lbl_sys = QLabel("⚠️ <b>SISTEMA:</b> Mensagem entregue ao suporte! Não é necessário aguardar nesta tela. Você pode continuar usando o VegaStock normalmente; assim que o desenvolvedor responder, seu histórico atualizará.")
        lbl_sys.setWordWrap(True)
        lbl_sys.setStyleSheet("background-color: #FFF3CD; border: 1px solid #FFEEBA; border-radius: 6px; padding: 12px; font-size: 12px; color: #856404;")
        
        layout_sys.addWidget(lbl_sys)
        container_sys.setLayout(layout_sys)
        item_sys.setSizeHint(container_sys.sizeHint())
        self.lista_chat.setItemWidget(item_sys, container_sys)
    
    self.lista_chat.scrollToBottom()

def enviar_mensagem_suporte(self):
    texto = self.input_mensagem.text().strip()
    if not texto:
        return
        
    if hasattr(self.window(), 'cliente_dados') and self.window().cliente_dados:
        cliente_id = self.window().cliente_dados.get("cliente_id") or self.window().cliente_dados.get("id")
        if cliente_id:
            self.btn_enviar_chat.setEnabled(False)
            self.input_mensagem.clear()
            
            self.worker_enviar = WorkerEnviarChat(cliente_id, texto)
            self.worker_enviar.sucesso.connect(lambda: [self.btn_enviar_chat.setEnabled(True), self.atualizar_chat_suporte()])
            self.worker_enviar.start()

# Vincula dinamicamente os métodos à classe principal
AbaSobre.atualizar_chat_suporte = atualizar_chat_suporte
AbaSobre.renderizar_mensagens = renderizar_mensagens
AbaSobre.enviar_mensagem_suporte = enviar_mensagem_suporte