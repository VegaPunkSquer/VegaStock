import os
import requests
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QLineEdit, QPushButton, QMessageBox, QFileDialog, QFrame)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap  # <--- Injetado aqui para o QR Code ser desenhado na tela!

API_BASE_URL = "https://vegap-vega-stock.hf.space"
class AbaConta(QWidget):
    def __init__(self, cliente_dados, main_window):
        super().__init__()
        self.cliente_dados = cliente_dados
        self.main_window = main_window # Referência para podermos atualizar a logo no menu lateral
        
        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(20, 20, 20, 20)
        layout_principal.setSpacing(20)

        # Título da Aba
        lbl_titulo = QLabel("Configurações da Conta")
        lbl_titulo.setStyleSheet("font-size: 24px; font-weight: bold; color: #333;")
        layout_principal.addWidget(lbl_titulo, alignment=Qt.AlignCenter)

        # --- BLOCO 1: INFORMAÇÕES E LOGO ---
        self.caminho_logo_temporario = self.cliente_dados.get('logo_url', '')
        
        frame_info = QFrame()
        frame_info.setStyleSheet("background-color: #f9f9f9; border: 1px solid #ddd; border-radius: 5px;")
        layout_info = QVBoxLayout(frame_info)
        layout_info.setContentsMargins(15, 15, 15, 15)
        
        lbl_info_titulo = QLabel("Dados do Estabelecimento")
        lbl_info_titulo.setStyleSheet("font-weight: bold; font-size: 16px; border: none;")
        layout_info.addWidget(lbl_info_titulo)

        lbl_cnpj = QLabel(f"CNPJ: {self.cliente_dados.get('cnpj')}")
        lbl_cnpj.setStyleSheet("color: #555; border: none; padding-top: 5px;")
        layout_info.addWidget(lbl_cnpj)

        self.input_nome_fantasia = QLineEdit(self.cliente_dados.get('nome_fantasia', ''))
        self.input_nome_fantasia.setPlaceholderText("Nome Fantasia")
        self.input_nome_fantasia.setFixedWidth(300)
        self.input_nome_fantasia.setStyleSheet("padding: 8px; border: 1px solid #ccc; border-radius: 3px;")
        layout_info.addWidget(self.input_nome_fantasia)

        layout_botoes_perfil = QHBoxLayout()
        
        btn_alterar_logo = QPushButton("Selecionar Nova Logo")
        btn_alterar_logo.setFixedWidth(150)
        btn_alterar_logo.setStyleSheet("background-color: #000; color: #fff; font-weight: bold; padding: 8px; border-radius: 3px;")
        btn_alterar_logo.clicked.connect(self.alterar_logo)
        layout_botoes_perfil.addWidget(btn_alterar_logo)
        
        btn_salvar_perfil = QPushButton("Salvar Alterações")
        btn_salvar_perfil.setFixedWidth(150)
        btn_salvar_perfil.setStyleSheet("background-color: #FFD700; color: #000; font-weight: bold; padding: 8px; border-radius: 3px;")
        btn_salvar_perfil.clicked.connect(self.salvar_perfil)
        layout_botoes_perfil.addWidget(btn_salvar_perfil)
        
        layout_botoes_perfil.addStretch()
        layout_info.addLayout(layout_botoes_perfil)
        
        self.lbl_status_logo = QLabel("Nenhuma imagem nova selecionada.")
        self.lbl_status_logo.setStyleSheet("color: gray; font-size: 10px; border: none;")
        layout_info.addWidget(self.lbl_status_logo)
        
        layout_principal.addWidget(frame_info)

        # --- CONTROLE DE ACESSIBILIDADE COM MEMÓRIA SALVA ---
        from PySide6.QtWidgets import QComboBox
        from PySide6.QtCore import QSettings
        
        frame_acessibilidade = QFrame()
        frame_acessibilidade.setStyleSheet("background-color: #ffffff; border: 1px solid #ddd; border-radius: 8px; padding: 15px;")
        layout_acessibilidade = QVBoxLayout(frame_acessibilidade)
        
        lbl_titulo_ace = QLabel("👁️ Acessibilidade e Visual")
        lbl_titulo_ace.setStyleSheet("font-size: 16px; font-weight: bold; color: #333; border: none;")
        layout_acessibilidade.addWidget(lbl_titulo_ace)
        
        layout_combo = QHBoxLayout()
        lbl_zoom = QLabel("Tamanho do Texto:")
        lbl_zoom.setStyleSheet("font-size: 13px; color: #555; border: none;")
        
        self.combo_zoom = QComboBox()
        self.combo_zoom.addItems(["Padrão (Pequeno)", "Médio (+25%)", "Grande (+50%)"])
        self.combo_zoom.setStyleSheet("padding: 5px; min-width: 150px; color: #333;")
        
        # Recupera a configuração salva localmente na máquina
        config = QSettings("VegaStock", "Preferencias")
        indice_salvo = int(config.value("escala_fonte_index", 0))
        self.combo_zoom.setCurrentIndex(indice_salvo)
        
        self.combo_zoom.currentIndexChanged.connect(self.mudar_escala_aplicativo)
        
        layout_combo.addWidget(lbl_zoom)
        layout_combo.addWidget(self.combo_zoom)
        layout_combo.addStretch()
        layout_acessibilidade.addLayout(layout_combo)
        
        layout_principal.addWidget(frame_acessibilidade)
        # ----------------------------------------------------

        # Bloco 2: Alterar Senha
        frame_senha = QFrame()
        frame_senha.setStyleSheet("background-color: #f9f9f9; border: 1px solid #ddd; border-radius: 5px;")
        layout_senha = QVBoxLayout(frame_senha)
        layout_senha.setContentsMargins(15, 15, 15, 15)

        lbl_senha_titulo = QLabel("Segurança: Alterar Senha de Admin")
        lbl_senha_titulo.setStyleSheet("font-weight: bold; font-size: 16px; border: none;")
        layout_senha.addWidget(lbl_senha_titulo)

        # Estilo padrão para os botões de olhinho da aba conta
        estilo_olho = "padding: 7px; background-color: #eee; border: 1px solid #ccc; border-radius: 3px;"

        # 1. Campo Senha Atual com Olhinho
        self.input_senha_atual = QLineEdit()
        self.input_senha_atual.setPlaceholderText("Senha Atual")
        self.input_senha_atual.setEchoMode(QLineEdit.Password)
        self.input_senha_atual.setStyleSheet("padding: 8px; border: 1px solid #ccc; border-radius: 3px;")
        
        layout_sa = QHBoxLayout()
        layout_sa.addWidget(self.input_senha_atual)
        self.btn_olho_sa = QPushButton("👁️")
        self.btn_olho_sa.setFixedWidth(35)
        self.btn_olho_sa.setStyleSheet(estilo_olho)
        self.btn_olho_sa.clicked.connect(lambda: self.toggle_campo_senha(self.input_senha_atual, self.btn_olho_sa))
        layout_sa.addWidget(self.btn_olho_sa)
        layout_sa.addStretch()
        layout_senha.addLayout(layout_sa)

        # 2. Campo Nova Senha com Olhinho
        self.input_nova_senha = QLineEdit()
        self.input_nova_senha.setPlaceholderText("Nova Senha")
        self.input_nova_senha.setEchoMode(QLineEdit.Password)
        self.input_nova_senha.setStyleSheet("padding: 8px; border: 1px solid #ccc; border-radius: 3px;")
        
        layout_ns = QHBoxLayout()
        layout_ns.addWidget(self.input_nova_senha)
        self.btn_olho_ns = QPushButton("👁️")
        self.btn_olho_ns.setFixedWidth(35)
        self.btn_olho_ns.setStyleSheet(estilo_olho)
        self.btn_olho_ns.clicked.connect(lambda: self.toggle_campo_senha(self.input_nova_senha, self.btn_olho_ns))
        layout_ns.addWidget(self.btn_olho_ns)
        layout_ns.addStretch()
        layout_senha.addLayout(layout_ns)

        # 3. Campo Confirmar Senha com Olhinho
        self.input_confirma_senha = QLineEdit()
        self.input_confirma_senha.setPlaceholderText("Confirmar Nova Senha")
        self.input_confirma_senha.setEchoMode(QLineEdit.Password)
        self.input_confirma_senha.setStyleSheet("padding: 8px; border: 1px solid #ccc; border-radius: 3px;")
        
        layout_cs = QHBoxLayout()
        layout_cs.addWidget(self.input_confirma_senha)
        self.btn_olho_cs = QPushButton("👁️")
        self.btn_olho_cs.setFixedWidth(35)
        self.btn_olho_cs.setStyleSheet(estilo_olho)
        self.btn_olho_cs.clicked.connect(lambda: self.toggle_campo_senha(self.input_confirma_senha, self.btn_olho_cs))
        layout_cs.addWidget(self.btn_olho_cs)
        layout_cs.addStretch()
        layout_senha.addLayout(layout_cs)

        btn_salvar_senha = QPushButton("Atualizar Senha")
        btn_salvar_senha.setFixedWidth(150)
        btn_salvar_senha.setStyleSheet("background-color: #FFD700; color: #000; font-weight: bold; padding: 8px; border-radius: 3px;")
        # NOVO CAMPO: Login para funcionários
        self.input_novo_login = QLineEdit()
        self.input_novo_login.setPlaceholderText("Novo Login (Deixe em branco para manter)")
        self.input_novo_login.setFixedWidth(300)
        self.input_novo_login.setStyleSheet("padding: 8px; border: 1px solid #ccc; border-radius: 3px;")
        layout_senha.insertWidget(1, self.input_novo_login) # Coloca logo abaixo do título

        btn_salvar_senha.clicked.connect(self.alterar_senha)
        layout_senha.addWidget(btn_salvar_senha)

        layout_principal.addWidget(frame_senha)
        # --- BLOCO 3: ACESSO MOBILE (PIN OPERACIONAL) ---
        frame_mobile = QFrame()
        frame_mobile.setStyleSheet("background-color: #f9f9f9; border: 1px solid #ddd; border-radius: 5px;")
        layout_mobile = QVBoxLayout(frame_mobile)
        layout_mobile.setContentsMargins(15, 15, 15, 15)

        lbl_mobile_tit = QLabel("Acesso Mobile (Aplicativo do Estoque)")
        lbl_mobile_tit.setStyleSheet("font-weight: bold; font-size: 16px; border: none;")
        layout_mobile.addWidget(lbl_mobile_tit)

        layout_pin = QHBoxLayout()
        self.input_nome_operador = QLineEdit()
        self.input_nome_operador.setPlaceholderText("Nome do Operador (Ex: João)")
        self.input_nome_operador.setStyleSheet("padding: 8px; border: 1px solid #ccc; border-radius: 3px;")
        
        self.input_pin = QLineEdit()
        self.input_pin.setPlaceholderText("PIN de 4 dígitos (Ex: 1234)")
        self.input_pin.setEchoMode(QLineEdit.Password)
        self.input_pin.setMaxLength(4)
        self.input_pin.setStyleSheet("padding: 8px; border: 1px solid #ccc; border-radius: 3px;")
        
        # Botão de olhinho para o PIN do mobile
        self.btn_olho_pin = QPushButton("👁️")
        self.btn_olho_pin.setFixedWidth(35)
        self.btn_olho_pin.setStyleSheet("padding: 7px; background-color: #eee; border: 1px solid #ccc; border-radius: 3px;")
        self.btn_olho_pin.clicked.connect(lambda: self.toggle_campo_senha(self.input_pin, self.btn_olho_pin))
        
        btn_salvar_pin = QPushButton("Salvar PIN Operacional")
        btn_salvar_pin.setStyleSheet("background-color: #000; color: #fff; font-weight: bold; padding: 8px; border-radius: 3px;")
        btn_salvar_pin.clicked.connect(self.salvar_pin_mobile)

        layout_pin.addWidget(self.input_nome_operador)
        layout_pin.addWidget(self.input_pin)
        layout_pin.addWidget(self.btn_olho_pin) # Injetado entre o PIN e o Salvar
        layout_pin.addWidget(btn_salvar_pin)
        
        # Injetando o botão mestre de pareamento logo abaixo do bloco de salvar o PIN
        self.btn_parear_mobile = QPushButton("📱 Parear Dispositivo Mobile")
        self.btn_parear_mobile.setStyleSheet("padding: 10px; background-color: #2196F3; color: white; font-weight: bold; border-radius: 4px; margin-top: 10px;")
        self.btn_parear_mobile.clicked.connect(self.abrir_popup_qrcode)
        layout_pin.addWidget(self.btn_parear_mobile)

        layout_mobile.addLayout(layout_pin)
        layout_principal.addWidget(frame_mobile)

        layout_principal.addStretch() # Agora sim empurra tudo pra cima!
        
        # Puxa o PIN atual da nuvem
        self.carregar_pin_atual() # Empurra tudo para cima

        # ==========================================
        # TRAVA DE HIERARQUIA (O PPOREEEEM GIGANTE)
        # ==========================================
        if str(self.cliente_dados.get("nivel_acesso", "Normal")).lower() != "admin":
            frame_info.hide() 
            frame_mobile.hide() # <--- ADICIONE ESTA LINHA PARA ESCONDER O ACESSO MOBILE
            lbl_senha_titulo.setText("Segurança: Alterar Minhas Credenciais")
            self.input_senha_atual.hide() 
            btn_salvar_senha.setText("Atualizar Minha Conta")
        else:
            self.input_novo_login.hide()

    def alterar_logo(self):
        arquivo, _ = QFileDialog.getOpenFileName(self, "Selecionar Nova Logo", "", "Imagens (*.png *.jpg *.jpeg)")
        if arquivo:
            caminho_corrigido = os.path.abspath(arquivo).replace("\\", "/")
            self.caminho_logo_temporario = caminho_corrigido
            nome_arquivo = os.path.basename(caminho_corrigido)
            self.lbl_status_logo.setText(f"Imagem pronta para salvar: {nome_arquivo}")
            self.lbl_status_logo.setStyleSheet("color: green; font-size: 10px; font-weight: bold; border: none;")

    def salvar_perfil(self):
        novo_nome = self.input_nome_fantasia.text().strip()
        
        if not novo_nome:
            QMessageBox.warning(self, "Erro", "O Nome Fantasia não pode ficar vazio.")
            return
            
        dados = {
            "cliente_id": self.cliente_dados['cliente_id'],
            "nome_fantasia": novo_nome,
            "logo_url": self.caminho_logo_temporario
        }
        
        try:
            response = requests.put(f"{API_BASE_URL}/atualizar_perfil", json=dados)
            if response.status_code == 200:
                QMessageBox.information(self, "Sucesso", "Perfil atualizado!")
                self.cliente_dados['nome_fantasia'] = novo_nome
                self.cliente_dados['logo_url'] = self.caminho_logo_temporario
                
                # O Chute duplo na tela principal para atualizar na mesma hora
                self.main_window.atualizar_nome_restaurante(novo_nome)
                self.main_window.carregar_logo_redondo(self.caminho_logo_temporario)
                
                self.lbl_status_logo.setText("Nenhuma imagem nova selecionada.")
                self.lbl_status_logo.setStyleSheet("color: gray; font-size: 10px; border: none;")
            else:
                QMessageBox.warning(self, "Erro", response.json().get("detail", "Erro ao atualizar."))
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Sem conexão com a API.\n{e}")

    def alterar_senha(self):
        nivel_acesso = self.cliente_dados.get("nivel_acesso", "Normal")
        nova = self.input_nova_senha.text()
        confirma = self.input_confirma_senha.text()

        if nova != confirma:
            QMessageBox.warning(self, "Aviso", "A nova senha e a confirmação não batem.")
            return

        # ==========================================
        # ROTA 1: SE FOR ADMIN (Mantém a sua lógica intacta)
        # ==========================================
        if str(nivel_acesso).lower() == "admin":
            atual = self.input_senha_atual.text()
            if not all([atual, nova, confirma]):
                QMessageBox.warning(self, "Aviso", "Preencha todos os campos de senha.")
                return

            dados = {
                "cliente_id": self.cliente_dados['cliente_id'],
                "senha_atual": atual,
                "nova_senha": nova
            }

            try:
                response = requests.put(f"{API_BASE_URL}/atualizar_senha", json=dados)
                if response.status_code == 200:
                    QMessageBox.information(self, "Sucesso", "Senha atualizada com sucesso!")
                    self.input_senha_atual.clear()
                    self.input_nova_senha.clear()
                    self.input_confirma_senha.clear()
                else:
                    QMessageBox.warning(self, "Erro", response.json().get("detail", "Erro ao atualizar."))
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Sem conexão com a API.\n{e}")

        # ==========================================
        # ROTA 2: SE FOR FUNCIONÁRIO (Usa a nova rota)
        # ==========================================
        else:
            novo_log = self.input_novo_login.text().strip()
            
            if not novo_log and not nova:
                QMessageBox.warning(self, "Aviso", "Preencha o login ou a senha para atualizar.")
                return
                
            dados_func = {
                "usuario_id": self.cliente_dados.get("usuario_id"),
                "novo_login": novo_log,
                "nova_senha": nova
            }
            
            try:
                response = requests.put(f"{API_BASE_URL}/atualizar_conta_funcionario", json=dados_func)
                if response.status_code == 200:
                    QMessageBox.information(self, "Sucesso", "Conta atualizada! No próximo acesso, use suas novas credenciais.")
                    self.input_novo_login.clear()
                    self.input_nova_senha.clear()
                    self.input_confirma_senha.clear()
                else:
                    QMessageBox.warning(self, "Erro", response.json().get("detail", "Erro ao atualizar."))
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Sem conexão com a API.\n{e}")
                
    def carregar_pin_atual(self):
        try:
            resp = requests.get(f"{API_BASE_URL}/operador/{self.cliente_dados['cliente_id']}")
            if resp.status_code == 200:
                dados = resp.json()
                self.input_nome_operador.setText(dados.get("nome", ""))
                self.input_pin.setText(dados.get("pin", ""))
        except: pass

    def salvar_pin_mobile(self):
        nome = self.input_nome_operador.text().strip()
        pin = self.input_pin.text().strip()
        if not nome or len(pin) != 4 or not pin.isdigit():
            QMessageBox.warning(self, "Aviso", "Preencha o nome e um PIN numérico de exatos 4 dígitos.")
            return
            
        dados = {"cliente_id": self.cliente_dados['cliente_id'], "nome": nome, "pin": pin}
        try:
            resp = requests.post(f"{API_BASE_URL}/operador", json=dados)
            if resp.status_code == 200:
                QMessageBox.information(self, "Sucesso", "PIN do Mobile configurado com sucesso!")
        except Exception as e:
            QMessageBox.critical(self, "Erro", "Erro ao salvar PIN."),
            
    def toggle_campo_senha(self, campo_input, botao_clicado):
        if campo_input.echoMode() == QLineEdit.Password:
            campo_input.setEchoMode(QLineEdit.Normal)
            botao_clicado.setText("🔒")
        else:
            campo_input.setEchoMode(QLineEdit.Password)
            botao_clicado.setText("👁️")
            
    def abrir_popup_qrcode(self):
        # Importações explícitas locais para garantir autonomia total da janela
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton
        from PySide6.QtCore import Qt
        from PySide6.QtGui import QPixmap
        import requests
        
        # Cria a janela de Pop-up nativa
        dialog = QDialog(self)
        dialog.setWindowTitle("Pareamento do Mobile")
        dialog.setFixedSize(320, 380)
        dialog.setStyleSheet("background-color: #ffffff;")
        
        layout_popup = QVBoxLayout(dialog)
        layout_popup.setContentsMargins(20, 20, 20, 20)
        layout_popup.setSpacing(15)
        
        lbl_info = QLabel("Abra o app no celular e escaneie o código abaixo para vincular este estabelecimento:")
        lbl_info.setWordWrap(True)
        lbl_info.setStyleSheet("font-size: 13px; color: #333; font-weight: bold;")
        lbl_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout_popup.addWidget(lbl_info)
        
        # Puxa o ID de forma totalmente segura
        cliente_id = str(self.cliente_dados.get('cliente_id') or self.cliente_dados.get('id') or '1')
        
        # Trocado para o QRServer (Garante entrega imediata e estável sem 404)
        url_qrcode = f"https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={cliente_id}"
        
        lbl_qr = QLabel()
        lbl_qr.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_qr.setFixedSize(200, 200)
        lbl_qr.setStyleSheet("border: 1px dashed #ccc; background-color: #fafafa;")
        
        try:
            # Faz o download da imagem direto para a memória do PySide
            resposta = requests.get(url_qrcode, timeout=5)
            if resposta.status_code == 200:
                pixmap = QPixmap()
                pixmap.loadFromData(resposta.content)
                lbl_qr.setPixmap(pixmap)
                lbl_qr.setStyleSheet("border: none; background-color: transparent;")
            else:
                lbl_qr.setText(f"Erro API: {resposta.status_code}")
        except Exception as e:
            lbl_qr.setText("Sem conexão com a internet")
            print(f"Erro ao gerar QR Code: {e}")
            
        layout_popup.addWidget(lbl_qr, alignment=Qt.AlignmentFlag.AlignCenter)
        
        btn_fechar = QPushButton("Concluído")
        btn_fechar.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_fechar.setStyleSheet("padding: 10px; background-color: #333; color: white; font-weight: bold; border-radius: 4px;")
        btn_fechar.clicked.connect(dialog.accept)
        layout_popup.addWidget(btn_fechar)
        
        dialog.exec()
        
    def mudar_escala_aplicativo(self, indice):
        from PySide6.QtWidgets import QApplication
        from PySide6.QtCore import QSettings
        
        app_instance = QApplication.instance()
        if not app_instance:
            return
            
        # Grava a escolha no registro local para o app lembrar quando reabrir
        config = QSettings("VegaStock", "Preferencias")
        config.setValue("escala_fonte_index", indice)
            
        fatores = {0: 1.0, 1: 1.25, 2: 1.5}
        fator = fatores.get(indice, 1.0)
        
        # O SEU LOOP VOLTOU: Varre as telas abertas e aplica o zoom na hora!
        for widget in app_instance.allWidgets():
            if widget.inherits("QLabel") or widget.inherits("QPushButton") or widget.inherits("QLineEdit") or widget.inherits("QComboBox"):
                fonte = widget.font()
                if not hasattr(widget, "_tam_original"):
                    widget._tam_original = fonte.pointSize() if fonte.pointSize() > 0 else 10
                
                fonte.setPointSize(int(widget._tam_original * fator))
                widget.setFont(fonte)
                
                # Redimensiona as caixas fixas para o texto não ficar claustrofóbico
                if widget.maximumHeight() < 16777215 or widget.minimumHeight() > 0:
                    if not hasattr(widget, "_alt_original"):
                        widget._alt_original = widget.height() if widget.height() > 0 else 35
                    widget.setFixedHeight(int(widget._alt_original * (1.0 + (fator - 1.0) * 0.6)))
            
    def refresh_ui(self):
        """Atualiza os textos da tela com os novos dados sincronizados."""
        # Se você tiver um label de CNPJ, atualize ele aqui. 
        # Exemplo: self.lbl_cnpj_valor.setText(self.cliente_dados.get('cnpj', 'Não informado'))
        pass