import sys
import os
import requests
import ctypes
from datetime import datetime
from PySide6.QtWidgets import (QApplication, QMainWindow, QMessageBox, QWidget, QVBoxLayout, 
                               QLabel, QHBoxLayout, QStackedWidget,QListWidget, QPushButton, QFrame, QSizePolicy, QGridLayout) # ADICIONADO QFrame
from PySide6.QtGui import QPixmap, QPainter, QPainterPath, QColor, QBrush, QIcon
from PySide6.QtCore import Qt, QSize
import estilos
from tela_login import TelaLogin
from tela_cadastro import TelaCadastro
from tela_recuperacao import TelaRecuperacao

from aba_dashboard import AbaDashboard
from aba_catalogo import AbaCatalogo
from aba_estoque import AbaEstoque
from aba_relatorios import AbaRelatorios
from aba_equipe import AbaEquipe
from aba_conta import AbaConta
from aba_configuracoes import AbaConfiguracoes

myappid = 'vegasotck.versao1' # Pode ser qualquer string única
ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

class MainWindow(QMainWindow):
    def __init__(self, cliente_dados):
        super().__init__()
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        caminho_icone = os.path.join(BASE_DIR, 'logo.ico')
        
        self.setWindowIcon(QIcon(caminho_icone))
        self.cliente_dados = cliente_dados
        self.setWindowTitle(f"VegaStock - Gerenciamento de Estoque - {self.cliente_dados['nome_fantasia']}")
        self.resize(900, 600)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        # --- INÍCIO DO LAYOUT GRID DEFINITIVO ---
        layout_principal = QGridLayout(central_widget)
        layout_principal.setContentsMargins(15, 15, 15, 15)
        layout_principal.setSpacing(15)

        # ==========================================
        # 1. TOPO ESQUERDA: LOGO (Linha 0, Coluna 0)
        # ==========================================
        self.frame_logo = QFrame()
        self.frame_logo.setFixedSize(220, 180) # Trava o tamanho do quadro do logo
        self.frame_logo.setStyleSheet("border-bottom: 2px solid #ccc; background-color: #f9f9f9;") # Linha separadora embaixo
        layout_logo = QVBoxLayout(self.frame_logo)
        
        self.lbl_logo = QLabel()
        self.lbl_logo.setAlignment(Qt.AlignCenter)
        self.lbl_logo.setStyleSheet("border: none; background-color: transparent;")
        self.carregar_logo_redondo(self.cliente_dados.get('logo_url', ''))
        layout_logo.addWidget(self.lbl_logo)
        
        layout_principal.addWidget(self.frame_logo, 0, 0)

        # ==========================================
        # 2. TOPO DIREITA: NOME (Linha 0, Coluna 1)
        # ==========================================
        self.frame_nome = QFrame()
        self.frame_nome.setFixedHeight(180) # Mesma altura exata do logo
        self.frame_nome.setStyleSheet("background-color: transparent; border-bottom: 2px solid #ccc;") # Linha separadora embaixo
        layout_nome = QVBoxLayout(self.frame_nome)
        layout_nome.setContentsMargins(0, 0, 0, 0)
        
        nome_fantasia = self.cliente_dados.get('nome_fantasia', 'RESTAURANTE')
        self.lbl_nome = QLabel(nome_fantasia.upper())
        self.lbl_nome.setAlignment(Qt.AlignCenter) # Centralizado X e Y
        self.lbl_nome.setStyleSheet("font-size: 48px; font-weight: bold; color: #333; border: none;") # Fonte maior
        layout_nome.addWidget(self.lbl_nome)
        
        layout_principal.addWidget(self.frame_nome, 0, 1)

        # ==========================================
        # 3. BAIXO ESQUERDA: MENU (Linha 1, Coluna 0)
        # ==========================================
        self.frame_menu = QFrame()
        self.frame_menu.setFixedWidth(220)
        self.frame_menu.setStyleSheet("border: none; background-color: transparent;")
        self.layout_abas = QVBoxLayout(self.frame_menu)
        self.layout_abas.setContentsMargins(0, 10, 0, 0) # Remove margens laterais
        self.layout_abas.setSpacing(0) # Sem espaço entre os botões para parecerem blocos

        self.nomes_abas = [
            "DASHBOARD", "CATÁLOGO DE PRODUTOS", "OPERAÇÃO DE ESTOQUE",
            "ANÁLISE DE DESPERDÍCIO", "EQUIPE E PERMISSÕES 🔒", "MINHA CONTA", "CONFIGURAÇÕES"
        ]
        
        estilo_btn = """
            QPushButton {
                background-color: 
                #EAEAEA; border: 1px solid #CCCCCC;
                text-align: center; padding-left: 15px; font-weight: bold; font-size: 12px; color: #333;
                border-radius: 5px; /* Cantos arredondados de volta */
            }
            QPushButton:hover { background-color: #DCDCDC; }
           
            QPushButton:checked { background-color: #FFD700; border: 1px solid #E6C200; color: #000; }
        """
        
        # --- BOTÃO LOGOFF ---
        self.btn_logoff = QPushButton("🚪 TROCAR CONTA")
        self.btn_logoff.setStyleSheet("""
            QPushButton {
                background-color: transparent; color: #f44336; padding: 12px;
                border: 1px solid #f44336; border-radius: 5px; font-weight: bold; font-size: 14px;
            }
            QPushButton:hover { background-color: #f44336; color: white; }
        """)
        self.btn_logoff.clicked.connect(self.fazer_logoff)
        
        # Coloque o botão no layout do seu menu lateral. 
        # (Se o seu layout lateral se chamar 'layout_menu' ou 'layout_botoes', use o nome dele aqui)
        self.layout_abas.addWidget(self.btn_logoff)
        
        # --- MAPA DE PERMISSÕES (NOVO) ---
        # Relaciona o nome do botão com a palavra salva no banco de dados
        mapa_permissoes = {
            "DASHBOARD": "dashboard",
            "CATÁLOGO DE PRODUTOS": "catalogo",
            "OPERAÇÃO DE ESTOQUE": "estoque",
            "ANÁLISE DE DESPERDÍCIO": "relatorios",
            "EQUIPE E PERMISSÕES 🔒": "admin", # Apenas Admin/Dono
            "MINHA CONTA": "livre",           # Todos veem
            "CONFIGURAÇÕES": "configuracoes"
        }

        # Descobre quem é o cara logado
        cargo_usuario = self.cliente_dados.get("cargo", "Admin")
        permissoes_usuario = self.cliente_dados.get("permissoes", [])

        self.botoes_abas = []
        for i, nome in enumerate(self.nomes_abas):
            btn = QPushButton(nome)
            btn.setCheckable(True)
            btn.setAutoExclusive(True)
            btn.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding) 
            btn.setStyleSheet(estilo_btn)
            btn.clicked.connect(lambda _, idx=i: self.mudar_aba(idx))
            
            # Lógica do PRO dinâmica (que já funcionava)
            if "🔒" in nome:
                if self.cliente_dados.get('status_assinatura') == "PRO":
                    btn.setText(nome.replace(" 🔒", ""))
                else:
                    estilo_bloqueado = """
                        QPushButton {
                            background-color: #fafafa; color: #aaa; border: 1px solid #e0e0e0;
                            text-align: center; padding-left: 15px; font-weight: bold; font-size: 12px; border-radius: 5px;
                        }
                        QPushButton:checked { background-color: #e0e0e0; color: #555; border: 1px solid #ccc; }
                    """
                    btn.setStyleSheet(estilo_bloqueado)
                    
            # ==========================================
            # O GRAN FINALE: TRAVA DE VISIBILIDADE
            # ==========================================
            chave = mapa_permissoes.get(nome, "livre")

            # Se NÃO for o dono (Admin) e a aba não for "livre"
            if self.cliente_dados.get("nivel_acesso") != "Admin" and chave != "livre":
                # Esconde se for aba de Admin ou se ele não tiver a permissão na carteira
                if chave == "admin" or chave not in permissoes_usuario:
                    btn.hide() # O botão fica invisível e intocável!

            self.layout_abas.addWidget(btn)
            self.botoes_abas.append(btn)

        self.botoes_abas[0].setChecked(True)
        
        # --- BOTÃO DE SINCRONIZAR NO MENU ---
        self.btn_sync = QPushButton(" 🔄 SINCRONIZAR DADOS")
        self.btn_sync.setStyleSheet("background-color: #2b2b36; color: #FFD700; text-align: center; padding: 15px; border: 1px solid #444; font-weight: bold; border-radius: 5px; margin-top: 20px;")
        self.btn_sync.clicked.connect(self.sincronizar_dados_nuvem)
        self.layout_abas.addWidget(self.btn_sync) # <--- AQUI ESTÁ O NOME CERTO!
        
        layout_principal.addWidget(self.frame_menu, 1, 0)

        # ==========================================
        # 4. BAIXO DIREITA: CONTEÚDO E RODAPÉ (Linha 1, Coluna 1)
        # ==========================================
        self.frame_conteudo = QFrame()
        self.frame_conteudo.setStyleSheet("border: none; background-color: #ffffff;")
        layout_dir = QVBoxLayout(self.frame_conteudo)
        layout_dir.setContentsMargins(20, 20, 0, 0)
        
        self.area_central = QStackedWidget()
        self.area_central.setStyleSheet("border: none;")
        
        self.aba_dash = AbaDashboard(self.cliente_dados)
        self.aba_cat = AbaCatalogo(self.cliente_dados)
        self.aba_est = AbaEstoque(self.cliente_dados)
        self.aba_rel = AbaRelatorios(self.cliente_dados)
        self.aba_eqp = AbaEquipe(self.cliente_dados)
        self.aba_cnt = AbaConta(self.cliente_dados, self)
        self.aba_cfg = AbaConfiguracoes(self.cliente_dados)

        self.area_central.addWidget(self.aba_dash)
        self.area_central.addWidget(self.aba_cat)
        self.area_central.addWidget(self.aba_est)
        self.area_central.addWidget(self.aba_rel)
        self.area_central.addWidget(self.aba_eqp)
        self.area_central.addWidget(self.aba_cnt)
        self.area_central.addWidget(self.aba_cfg)
        
        layout_dir.addWidget(self.area_central)

        # Rodapé
        layout_rodape = QHBoxLayout()
        layout_rodape.addStretch()
        user = self.cliente_dados.get('login_usuario', 'ADMIN')
        lbl_user = QLabel(f"USUÁRIO: {user.upper()}")
        lbl_user.setStyleSheet("font-weight: normal; color: #000; font-size: 12px;")
        layout_rodape.addWidget(lbl_user)
        layout_dir.addLayout(layout_rodape)

        layout_principal.addWidget(self.frame_conteudo, 1, 1)
        
        # ========================================================
        # O CADEADO DE INICIALIZAÇÃO: 
        # Chama a função que tranca tudo logo que o app abre!
        # ========================================================
        self.atualizar_bloqueios_interface()
        
    def mudar_aba(self, index):
        self.area_central.setCurrentIndex(index)

    def carregar_logo_redondo(self, caminho_logo):
        tamanho = 180
        pixmap = QPixmap()
        carregou = False
        
        # Trata o caminho para o PySide não engasgar com as barras do Windows
        if caminho_logo:
            caminho_corrigido = os.path.normpath(caminho_logo).replace("\\", "/")
            if os.path.exists(caminho_corrigido):
                carregou = pixmap.load(caminho_corrigido) # Força o carregamento real
        
        if carregou:
            pixmap = pixmap.scaled(tamanho, tamanho, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
        else:
            # Placeholder circular
            pixmap = QPixmap(tamanho, tamanho)
            pixmap.fill(Qt.transparent)
            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setBrush(QBrush(QColor("#f0f0f0")))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(0, 0, tamanho, tamanho)
            
            painter.setPen(QColor("#FFD700"))
            font = painter.font()
            font.setPointSize(48)
            font.setBold(True)
            painter.setFont(font)
            painter.drawText(pixmap.rect(), Qt.AlignCenter, "L")
            painter.end()

        # Aplica a máscara circular
        final_pixmap = QPixmap(tamanho, tamanho)
        final_pixmap.fill(Qt.transparent)
        
        painter = QPainter(final_pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        path = QPainterPath()
        path.addEllipse(0, 0, tamanho, tamanho)
        painter.setClipPath(path)
        
        x_offset = (tamanho - pixmap.width()) // 2
        y_offset = (tamanho - pixmap.height()) // 2
        painter.drawPixmap(x_offset, y_offset, pixmap)
        painter.end()
        
        self.lbl_logo.setPixmap(final_pixmap)
        self.lbl_logo.repaint() # Chute na tela: força a atualização na mesma hora
        
    def atualizar_nome_restaurante(self, novo_nome):
        self.lbl_nome.setText(novo_nome.upper())
        self.lbl_nome.repaint() # Chute na tela para o nome
        
    def sincronizar_dados_nuvem(self):
        try:
            url = f"https://vegastock.onrender.com/config/{self.cliente_dados['cliente_id']}"
            resp = requests.get(url, timeout=10)
            
            if resp.status_code == 200:
                dados_nuvem = resp.json()
                
                # Atualiza os dados de plano no dicionário global
                self.cliente_dados['status_assinatura'] = dados_nuvem.get('status_assinatura', self.cliente_dados.get('status_assinatura'))
                self.cliente_dados['plano'] = dados_nuvem.get('plano', self.cliente_dados.get('plano', 'BÁSICO'))
                self.cliente_dados['limite_contas'] = dados_nuvem.get('limite_contas', self.cliente_dados.get('limite_contas', 2))
                self.cliente_dados['cnpj'] = dados_nuvem.get('cnpj', self.cliente_dados.get('cnpj')) # <--- PEGA O CNPJ DA NUVEM
                
                # ATUALIZA TODAS AS ABAS:
                self.aba_cfg.cliente_dados = self.cliente_dados
                self.aba_eqp.cliente_dados = self.cliente_dados
                self.aba_cnt.cliente_dados = self.cliente_dados
                
                # Se a aba equipe tiver uma função de recarregar, chame-a aqui
                if hasattr(self.aba_eqp, 'carregar_equipe'):
                    self.aba_eqp.carregar_equipe()
                
                # =======================================================
                # O CHOQUE VISUAL: Força o texto na tela a mudar na hora!
                # =======================================================
                plano_bonito = self.cliente_dados.get('plano', 'BÁSICO').replace('_', ' ').upper()
                self.aba_cfg.lbl_plano_info.setText(f"💎 PLANO ATUAL: {plano_bonito}")
                
                # Se for PRO, muda a cor pra dourado/laranja, se não, volta pro cinza
                cor = "#d84315" if "PRO" in plano_bonito else "#777"
                self.aba_cfg.lbl_plano_info.setStyleSheet(f"font-size: 14px; font-weight: bold; color: {cor}; margin-bottom: 10px;")
                # =======================================================
                
                # CHAMA O REFRESH DA INTERFACE (Libera o menu lateral)
                self.atualizar_bloqueios_interface()
                
                QMessageBox.information(self, "Sucesso", "Dados sincronizados! O modo PRO foi ativado.")
            else:
                QMessageBox.warning(self, "Erro", f"A API recusou: Erro {resp.status_code}")
                
        except Exception as e:
            QMessageBox.critical(self, "Falha de Conexão", f"O erro foi: {str(e)}")
            
    def fazer_logoff(self):
        msg = QMessageBox(self)
        msg.setWindowTitle("Trocar de Conta")
        msg.setText("Deseja encerrar a sessão atual e voltar para a tela de Login?")
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg.setDefaultButton(QMessageBox.No)
        resposta = msg.exec()
        
        if resposta == QMessageBox.Yes:
            import os, sys
            # Reinicia o aplicativo inteiro do zero, limpando a memória
            os.execl(sys.executable, sys.executable, *sys.argv)
            
    def atualizar_bloqueios_interface(self):
        """Varre os botões e aplica as travas de permissão e plano PRO."""
        status_assinatura = self.cliente_dados.get('status_assinatura', 'BÁSICO')
        is_pro = status_assinatura == "PRO"
        
        # Pega a lista de permissões (se vier None/Null do banco, vira lista vazia [])
        permissoes_usuario = self.cliente_dados.get('permissoes') or []
        
        # Pega o cargo (se vier None/Null do banco, vira texto vazio "")
        cargo_bruto = self.cliente_dados.get('cargo') or ""
        cargo = cargo_bruto.upper()

        # Mapa para ligar o texto do botão à chave da permissão
        mapa = {
            "DASHBOARD": "dashboard",
            "CATÁLOGO DE PRODUTOS": "catalogo",
            "OPERAÇÃO DE ESTOQUE": "estoque",
            "ANÁLISE DE DESPERDÍCIO": "relatorios",
            "EQUIPE E PERMISSÕES": "admin", 
            "CONFIGURAÇÕES": "configuracoes"
        }

        for btn in self.botoes_abas:
            texto_botao = btn.text().replace(" 🔒", "").strip().upper()
            chave = mapa.get(texto_botao, "livre")

            # REGRA 1: Se for ADMIN, libera TUDO.
            if cargo == "ADMIN":
                btn.show()
                btn.setEnabled(True)
                continue

            # REGRA 2: Se for aba de EQUIPE, só o Admin vê (já tratado acima, mas por garantia:)
            if chave == "admin":
                btn.hide()
                continue

            # REGRA 3: Checagem de permissões para funcionários normais
            if chave != "livre" and chave not in permissoes_usuario:
                btn.hide() # Esconde o que ele não pode ver
            else:
                btn.show() # Mostra o que ele pode ver

def iniciar_app():
    app = QApplication(sys.argv)
    
    # Injeta a paleta de cores da empresa do seu tio no aplicativo inteiro
    app.setStyleSheet(estilos.ESTILO_GLOBAL)

    # Loop de Navegação (Roteador do PySide)
    while True:
        tela_login = TelaLogin()
        resultado_login = tela_login.exec()

        if resultado_login == TelaLogin.Accepted:
            # Login deu certo! Abre a tela principal e quebra o loop
            janela_principal = MainWindow(tela_login.cliente_dados)
            janela_principal.show()
            sys.exit(app.exec())
        
        elif tela_login.ir_para_cadastro:
            # Clicou no botão "Cadastrar-se"
            tela_cadastro = TelaCadastro()
            tela_cadastro.exec()
            # Ao fechar o cadastro (sucesso ou "Voltar"), o loop reinicia e abre o Login de novo
            
        elif tela_login.ir_para_recuperacao:
            tela_rec = TelaRecuperacao()
            tela_rec.exec()
            # Ao fechar, o loop reinicia e volta para o Login
        
        else:
            # Usuário clicou no "X" vermelho da janela, fecha tudo.
            break

    sys.exit()

if __name__ == "__main__":
    iniciar_app()