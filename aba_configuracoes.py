import webbrowser
import requests
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QLineEdit, QPushButton, QMessageBox, QFrame, 
                               QListWidget, QListWidgetItem, QCheckBox, QInputDialog, QDialog, QRadioButton, QButtonGroup)
from PySide6.QtCore import Qt, QTimer, QThread, Signal

API_BASE_URL = "https://vegastock.onrender.com"

class WorkerConfiguracoes(QThread):
    resultado = Signal(dict)
    erro = Signal(str)

    def __init__(self, cliente_id):
        super().__init__()
        self.cliente_id = cliente_id

    def run(self):
        try:
            # Puxa as 3 listas na mesma viagem
            r_cat = requests.get(f"{API_BASE_URL}/categorias/{self.cliente_id}")
            r_mot = requests.get(f"{API_BASE_URL}/motivos/{self.cliente_id}")
            r_uni = requests.get(f"{API_BASE_URL}/unidades/{self.cliente_id}")
            
            self.resultado.emit({
                "categorias": r_cat.json() if r_cat.status_code == 200 else [],
                "motivos": r_mot.json() if r_mot.status_code == 200 else [],
                "unidades": r_uni.json() if r_uni.status_code == 200 else []
            })
        except Exception:
            self.erro.emit("Falha")

class DialogUpgradePRO(QDialog):
    def __init__(self, cliente_id):
        super().__init__()
        self.setWindowTitle("VegaStock - Sistema de Estoque - Upgrade de conta PRO")
        self.setFixedSize(780, 420)
        self.cliente_id = cliente_id
        
        # Tema Escuro Global da Janela
        self.setStyleSheet("background-color: #1a1a1f; color: white; font-family: Arial;")

        layout = QVBoxLayout(self)
        
        lbl_titulo = QLabel("VegaStock - Sistema de Estoque - Upgrade PRO")
        lbl_titulo.setStyleSheet("font-size: 20px; font-weight: bold; border: none; margin-bottom: 10px;")
        layout.addWidget(lbl_titulo, alignment=Qt.AlignCenter)

        # Layout horizontal para os 4 cartões
        layout_cards = QHBoxLayout()
        layout_cards.setSpacing(15)
        
        self.grupo_planos = QButtonGroup(self)
        
        # Dados: (Chave API, Título, Total, Por Mês, Economia, Destaque)
        planos_info = [
            ("PRO_MENSAL", "PRO Mensal", "R$ 289,00", "R$ 289,00 /mês", "", False),
            ("PRO_SEMESTRAL", "PRO Semestral\n⭐️ MELHOR PREÇO", "R$ 1.134,00", "R$ 189,00 /mês", "Economize R$ 600,00", True)
        ]
        
        self.chaves_api = []
        
        for i, (chave, titulo, total, por_mes, economia, destaque) in enumerate(planos_info):
            frame = QFrame()
            
            borda = "2px solid #5c85d6" if destaque else "1px solid #333"
            bg_color = "#2b2b36" if destaque else "#25252c"
            
            frame.setStyleSheet(f"""
                QFrame {{ background-color: {bg_color}; border: {borda}; border-radius: 12px; }}
            """)
            
            card_layout = QVBoxLayout(frame)
            card_layout.setContentsMargins(15, 20, 15, 20)
            card_layout.setSpacing(10)
            
            rb = QRadioButton(titulo)
            rb.setStyleSheet("""
                QRadioButton { background: transparent; font-size: 15px; font-weight: bold; border: none; padding-bottom: 5px; }
                QRadioButton::indicator { width: 14px; height: 14px; border-radius: 8px; border: 2px solid #aaa; background-color: transparent; }
                QRadioButton::indicator:checked { border: 2px solid #FFD700; background-color: #FFD700; }
            """)
            if i == 0: rb.setChecked(True)
            self.grupo_planos.addButton(rb, i)
            card_layout.addWidget(rb, alignment=Qt.AlignHCenter)
            
            lbl_sub = QLabel("Total do pacote:")
            lbl_sub.setStyleSheet("color: #aaa; font-size: 11px; border: none; background: transparent;")
            card_layout.addWidget(lbl_sub, alignment=Qt.AlignHCenter)
            
            lbl_total = QLabel(total)
            lbl_total.setStyleSheet("font-size: 22px; font-weight: bold; border: none; background: transparent;")
            card_layout.addWidget(lbl_total, alignment=Qt.AlignHCenter)
            
            lbl_mes = QLabel(por_mes)
            lbl_mes.setStyleSheet("color: #aaa; font-size: 12px; border: none; margin-top: 15px; background: transparent;")
            card_layout.addWidget(lbl_mes, alignment=Qt.AlignHCenter)
            
            if economia:
                lbl_eco = QLabel(economia)
                lbl_eco.setStyleSheet("color: #4CAF50; font-size: 11px; font-weight: bold; border: none; background: transparent;")
                card_layout.addWidget(lbl_eco, alignment=Qt.AlignHCenter)
            else:
                lbl_vazio = QLabel()
                lbl_vazio.setStyleSheet("border: none; background: transparent;")
                card_layout.addWidget(lbl_vazio)
                
            layout_cards.addWidget(frame)
            self.chaves_api.append(chave)
            
        layout.addLayout(layout_cards)
        layout.addSpacing(15)

        self.btn_pagar = QPushButton("GERAR PAGAMENTO SEGURO")
        self.btn_pagar.setStyleSheet("background-color: #009EE3; color: white; font-weight: bold; padding: 15px; font-size: 14px; border-radius: 5px;")
        self.btn_pagar.clicked.connect(self.abrir_pagamento)
        layout.addWidget(self.btn_pagar)
        
        # O Radar que vai verificar o PIX
        self.timer_pagamento = QTimer(self)
        self.timer_pagamento.timeout.connect(self.checar_se_ficou_pro)

    def abrir_pagamento(self):
        id_selecionado = self.grupo_planos.checkedId()
        plano_txt = self.chaves_api[id_selecionado] # "MENSAL", "ANUAL", etc.
        
        confirmar = QMessageBox.question(self, "Confirmar Upgrade", 
            f"Deseja fazer o upgrade para o PRO ({plano_txt}) agora?\n\nO Asaas atualizará sua assinatura e a diferença será cobrada na sua próxima fatura.",
            QMessageBox.Yes | QMessageBox.No)
            
        if confirmar == QMessageBox.Yes:
            self.btn_pagar.setText("⏳ PROCESSANDO UPGRADE...")
            self.btn_pagar.setEnabled(False)
            try:
                # Dispara a ordem pro seu backend
                resp = requests.post(f"{API_BASE_URL}/fazer_upgrade", 
                                     json={"cliente_id": self.cliente_id, "novo_plano": f"PRO_{plano_txt}"})
                
                if resp.status_code == 200:
                    QMessageBox.information(self, "Sucesso!", "Upgrade realizado com sucesso! O sistema foi destrancado.\nPor favor, feche e abra a tela para atualizar.")
                    self.accept()
                else:
                    QMessageBox.warning(self, "Erro no Asaas", f"Recusado: {resp.text}")
                    self.btn_pagar.setText("GERAR PAGAMENTO SEGURO")
                    self.btn_pagar.setEnabled(True)
            except Exception as e:
                QMessageBox.critical(self, "Erro de Conexão", f"Servidor inacessível.\n{e}")
                self.btn_pagar.setText("GERAR PAGAMENTO SEGURO")
                self.btn_pagar.setEnabled(True)
            
    def checar_se_ficou_pro(self):
        try:
            resp = requests.get(f"{API_BASE_URL}/status_assinatura/{self.cliente_id}")
            if resp.status_code == 200 and resp.json().get("status") == "PRO":
                self.timer_pagamento.stop() # Desliga o radar
                QMessageBox.information(self, "PAGAMENTO APROVADO!", "A mágica aconteceu! Bem-vindo à Elite. O sistema foi destrancado.")
                self.accept() # Fecha a janela sozinha
        except:
            pass # Se a API engasgar, fica quieto e tenta de novo no próximo pulso

    def processar_pagamento(self):
        try:
            resp = requests.put(f"{API_BASE_URL}/ativar_pro_automatizado", json={"cliente_id": self.cliente_id})
            if resp.status_code == 200:
                QMessageBox.information(self, "SUCESSO!", "Pagamento aprovado! Suas funções PRO foram liberadas.")
                self.accept()
        except:
            QMessageBox.critical(self, "Erro", "Erro ao processar transação via API.")

class AbaConfiguracoes(QWidget):
    def __init__(self, cliente_dados):
        super().__init__()
        self.cliente_dados = cliente_dados
        
        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(20, 20, 20, 20)
        layout_principal.setSpacing(15)

        lbl_titulo = QLabel("Configurações do Sistema")
        lbl_titulo.setStyleSheet("font-size: 24px; font-weight: bold; color: #333;")
        layout_principal.addWidget(lbl_titulo, alignment=Qt.AlignCenter)

        # --- NOVO: MOSTRAR O PLANO ATUAL ---
        # Blinda contra dados nulos vindo do banco
        plano_banco = self.cliente_dados.get('plano')
        plano_atual = (plano_banco if plano_banco else 'BÁSICO').replace('_', ' ').upper()
        cor_plano = "#d84315" if "PRO" in plano_atual else "#777"
        
        self.lbl_plano_info = QLabel(f"💎 PLANO ATUAL: {plano_atual}")
        self.lbl_plano_info.setStyleSheet(f"font-size: 14px; font-weight: bold; color: {cor_plano}; margin-bottom: 10px;")
        layout_principal.addWidget(self.lbl_plano_info, alignment=Qt.AlignCenter)

        # ==========================================
        # 1. NOTIFICAÇÕES (Global e PRO)
        # ==========================================
        frame_notif = QFrame()
        frame_notif.setStyleSheet("background-color: #f0f8ff; border: 1px solid #b0c4de; border-radius: 5px;")
        layout_notif = QVBoxLayout(frame_notif) # Mudamos para Vertical para caber a lista PRO

        # Linha 1: Toggles Gerais
        layout_linha1 = QHBoxLayout()
        self.btn_toggle_notif = QPushButton("Notificações LIGADAS")
        self.btn_toggle_notif.setCheckable(True)
        self.btn_toggle_notif.setChecked(self.cliente_dados.get('receber_notificacoes', True))
        self.btn_toggle_notif.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 6px;")
        # LIGA O MOTOR DE REPINTURA (NOVO)
        self.btn_toggle_notif.toggled.connect(self.atualizar_visual_btn_notif)
        self.atualizar_visual_btn_notif(self.btn_toggle_notif.isChecked()) # Roda uma vez para pintar certo ao abrir
        layout_linha1.addWidget(self.btn_toggle_notif)
        
        self.chk_som = QCheckBox("Emitir aviso sonoro")
        self.chk_som.setChecked(True)
        layout_linha1.addWidget(self.chk_som)
        
        layout_linha1.addStretch()
        layout_notif.addLayout(layout_linha1)

        # Linha 2: Limite Global
        layout_linha2 = QHBoxLayout()
        
        lbl_avisar = QLabel("Avisar quando o estoque for menor que:")
        lbl_avisar.setStyleSheet("color: #333; border: none;") # Força cor escura
        layout_linha2.addWidget(lbl_avisar)
        
        self.input_limite_global = QLineEdit(str(self.cliente_dados.get('limite_global', 5.0)))
        self.input_limite_global.setFixedWidth(50)
        self.input_limite_global.setStyleSheet("color: #000; background-color: #fff; border: 1px solid #ccc; padding: 4px;")
        layout_linha2.addWidget(self.input_limite_global)
        
        lbl_unidades = QLabel("unidades (Geral)")
        lbl_unidades.setStyleSheet("color: #333; border: none;") # Força cor escura
        layout_linha2.addWidget(lbl_unidades)
        
        btn_salvar_global = QPushButton("Salvar Regra Geral")
        btn_salvar_global.setStyleSheet("background-color: #000; color: #fff; font-weight: bold; padding: 6px 12px; border-radius: 4px;")
        btn_salvar_global.clicked.connect(self.salvar_config_global)
        layout_linha2.addWidget(btn_salvar_global)
        
        layout_linha2.addStretch()
        layout_notif.addLayout(layout_linha2)

        # Linha 3: Ativador PRO
        self.btn_toggle_pro = QPushButton("Habilitar limites individuais por Produto (PRO 👑)")
        self.btn_toggle_pro.setCheckable(True)
        self.btn_toggle_pro.setStyleSheet("background-color: #FFD700; color: #000; padding: 8px; font-weight: bold; border: 1px solid #E6C200; border-radius: 4px;")
        self.btn_toggle_pro.clicked.connect(self.verificar_assinatura_pro)
        layout_notif.addWidget(self.btn_toggle_pro)

        # Área PRO: Lista de produtos (Escondida por padrão)
        self.area_lista_pro = QFrame()
        self.area_lista_pro.setStyleSheet("background-color: #ffffff; border-top: 1px dashed #ccc;")
        self.layout_lista_pro = QVBoxLayout(self.area_lista_pro)
        self.area_lista_pro.hide()
        layout_notif.addWidget(self.area_lista_pro)

        layout_principal.addWidget(frame_notif)

        # ==========================================
        # 2. A PALAVRA MESTRA DE USO (Trava de Segurança)
        # ==========================================
        frame_uso = QFrame()
        frame_uso.setStyleSheet("background-color: #fff3e0; border: 1px solid #ffcc80; border-radius: 5px;")
        layout_uso = QHBoxLayout(frame_uso)
        layout_uso.setContentsMargins(15, 15, 15, 15)

        lbl_uso = QLabel("Palavra padrão para Saída Normal (Uso da Cozinha):")
        lbl_uso.setStyleSheet("font-weight: bold; font-size: 13px; border: none; color: #d84315;")
        layout_uso.addWidget(lbl_uso)

        self.input_uso = QLineEdit()
        self.input_uso.setPlaceholderText("Ex: Uso Interno")
        self.input_uso.setStyleSheet("padding: 6px; border: 1px solid #ccc; background-color: #fff;")
        layout_uso.addWidget(self.input_uso)

        self.btn_salvar_uso = QPushButton("Salvar")
        self.btn_salvar_uso.setStyleSheet("background-color: #FFD700; color: #000; font-weight: bold; padding: 6px;")
        self.btn_salvar_uso.clicked.connect(self.salvar_motivo_uso)
        layout_uso.addWidget(self.btn_salvar_uso)

        self.btn_editar_uso = QPushButton("Alterar Palavra")
        self.btn_editar_uso.setStyleSheet("background-color: #333; color: #fff; font-weight: bold; padding: 6px;")
        self.btn_editar_uso.clicked.connect(self.abrir_popup_uso)
        self.btn_editar_uso.hide() # Fica escondido até ele salvar a primeira vez
        layout_uso.addWidget(self.btn_editar_uso)

        layout_principal.addWidget(frame_uso)

        # ==========================================
        # 3. PAINÉIS LADO A LADO (Categorias e Perdas)
        # ==========================================
        layout_paineis = QHBoxLayout()
        layout_paineis.setSpacing(20)

        # PAINEL ESQUERDO: CATEGORIAS
        frame_cat = QFrame()
        frame_cat.setStyleSheet("background-color: #f9f9f9; border: 1px solid #ddd; border-radius: 5px;")
        layout_cat = QVBoxLayout(frame_cat)

        lbl_cat_titulo = QLabel("1. Categorias do Cardápio")
        lbl_cat_titulo.setStyleSheet("font-weight: bold; border: none;")
        layout_cat.addWidget(lbl_cat_titulo)

        layout_add_cat = QHBoxLayout()
        self.input_nova_cat = QLineEdit()
        self.input_nova_cat.setPlaceholderText("Ex: Hortifruti")
        layout_add_cat.addWidget(self.input_nova_cat)
        btn_add_cat = QPushButton("Adicionar")
        btn_add_cat.setStyleSheet("background-color: #000; color: #fff; font-weight: bold;")
        btn_add_cat.clicked.connect(self.adicionar_categoria)
        layout_add_cat.addWidget(btn_add_cat)
        layout_cat.addLayout(layout_add_cat)

        self.lista_categorias = QListWidget()
        layout_cat.addWidget(self.lista_categorias)

        btn_del_cat = QPushButton("Excluir Categoria Selecionada")
        btn_del_cat.setStyleSheet("color: red; font-weight: bold; border: 1px solid red;")
        btn_del_cat.clicked.connect(self.deletar_categoria)
        layout_cat.addWidget(btn_del_cat)

        layout_paineis.addWidget(frame_cat)

        # PAINEL DIREITO: MOTIVOS DE PERDA (Dinheiro pro Ralo)
        frame_perda = QFrame()
        frame_perda.setStyleSheet("background-color: #f9f9f9; border: 1px solid #ddd; border-radius: 5px;")
        layout_perda = QVBoxLayout(frame_perda)

        lbl_perda_titulo = QLabel("2. Motivos de Desperdício/Perda")
        lbl_perda_titulo.setStyleSheet("font-weight: bold; border: none;")
        layout_perda.addWidget(lbl_perda_titulo)

        layout_add_perda = QHBoxLayout()
        self.input_nova_perda = QLineEdit()
        self.input_nova_perda.setPlaceholderText("Ex: Passou da validade")
        layout_add_perda.addWidget(self.input_nova_perda)
        btn_add_perda = QPushButton("Adicionar")
        btn_add_perda.setStyleSheet("background-color: #000; color: #fff; font-weight: bold;")
        btn_add_perda.clicked.connect(self.adicionar_motivo_perda)
        layout_add_perda.addWidget(btn_add_perda)
        layout_perda.addLayout(layout_add_perda)

        self.lista_perdas = QListWidget()
        layout_perda.addWidget(self.lista_perdas)

        btn_del_perda = QPushButton("Excluir Motivo Selecionado")
        btn_del_perda.setStyleSheet("color: red; font-weight: bold; border: 1px solid red;")
        btn_del_perda.clicked.connect(self.deletar_motivo)
        layout_perda.addWidget(btn_del_perda)

        layout_paineis.addWidget(frame_perda)
        
        # PAINEL DIREITO 2: UNIDADES DE MEDIDA (NOVO)
        frame_unidade = QFrame()
        frame_unidade.setStyleSheet("background-color: #f9f9f9; border: 1px solid #ddd; border-radius: 5px;")
        layout_unidade = QVBoxLayout(frame_unidade)

        lbl_unidade_titulo = QLabel("3. Unidades de Medida")
        lbl_unidade_titulo.setStyleSheet("font-weight: bold; border: none;")
        layout_unidade.addWidget(lbl_unidade_titulo)

        layout_add_unidade = QHBoxLayout()
        self.input_nova_unidade = QLineEdit()
        self.input_nova_unidade.setPlaceholderText("Ex: Saco")
        layout_add_unidade.addWidget(self.input_nova_unidade)
        
        btn_add_unidade = QPushButton("Adicionar")
        btn_add_unidade.setStyleSheet("background-color: #000; color: #fff; font-weight: bold;")
        btn_add_unidade.clicked.connect(self.adicionar_unidade)
        layout_add_unidade.addWidget(btn_add_unidade)
        layout_unidade.addLayout(layout_add_unidade)

        self.lista_unidades = QListWidget()
        self.lista_unidades.itemDoubleClicked.connect(self.editar_unidade)
        layout_unidade.addWidget(self.lista_unidades)

        btn_del_unidade = QPushButton("Excluir Unidade")
        btn_del_unidade.setStyleSheet("color: red; font-weight: bold; border: 1px solid red;")
        btn_del_unidade.clicked.connect(self.deletar_unidade)
        layout_unidade.addWidget(btn_del_unidade)

        layout_paineis.addWidget(frame_unidade) # Adiciona o 3º painel na tela
        
        layout_principal.addLayout(layout_paineis)
        
        # Assinatura, Info e Botão de Suporte Vega
        layout_app_info = QHBoxLayout()
        lbl_app_dados = QLabel(f"VegaStock v1.0.0 | Cliente: {self.cliente_dados.get('nome_fantasia', '')}")
        lbl_app_dados.setStyleSheet("color: #aaa; font-size: 10px; border: none;")
        
        texto_link = '<a href="https://wa.me/5512981194607" style="color: #aaa; text-decoration: none;">Desenvolvido por Vega | Suporte: (12) 98119-4607</a>'
        lbl_dev = QLabel(texto_link)
        lbl_dev.setOpenExternalLinks(True)
        lbl_dev.setStyleSheet("font-size: 10px; font-weight: bold; border: none;")
        
        layout_app_info.addWidget(lbl_app_dados)
        layout_app_info.addStretch()
        layout_app_info.addWidget(lbl_dev)
        layout_principal.addLayout(layout_app_info)

    # --- FUNÇÕES DE LÓGICA E CONEXÃO COM A API ---
    
    def atualizar_visual_btn_notif(self, checado):
        if checado:
            self.btn_toggle_notif.setText("Notificações LIGADAS")
            self.btn_toggle_notif.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 6px;")
        else:
            self.btn_toggle_notif.setText("Notificações DESLIGADAS")
            self.btn_toggle_notif.setStyleSheet("background-color: #f44336; color: white; font-weight: bold; padding: 6px;")

    def showEvent(self, event):
        super().showEvent(event)
        self.carregar_listas()

    def carregar_listas(self):
        # 1. Avisa que tá carregando nas 3 listas de uma vez
        self.lista_categorias.clear()
        self.lista_perdas.clear()
        self.lista_unidades.clear()
        
        self.lista_categorias.addItem("Carregando...")
        self.lista_perdas.addItem("Carregando...")
        self.lista_unidades.addItem("Carregando...")
        
        # 2. Chama o Trabalhador
        self.worker = WorkerConfiguracoes(self.cliente_dados['cliente_id'])
        self.worker.resultado.connect(self.atualizar_tela)
        self.worker.start()

    def atualizar_tela(self, dados):
        # 3. O trabalhador voltou! Limpa as mensagens e preenche com os dados reais
        self.lista_categorias.clear()
        self.lista_perdas.clear()
        self.lista_unidades.clear()
        
        for cat in dados.get("categorias", []):
            item = QListWidgetItem(cat["nome"])
            item.setData(Qt.UserRole, cat["id"])
            self.lista_categorias.addItem(item)
            
        for mov in dados.get("motivos", []):
            if mov["tipo"] == "USO":
                self.travar_campo_uso(mov["descricao"])
            elif mov["tipo"] == "PERDA":
                item = QListWidgetItem(mov["descricao"])
                item.setData(Qt.UserRole, mov["id"])
                self.lista_perdas.addItem(item)
                
        for uni in dados.get("unidades", []):
            item = QListWidgetItem(uni["nome"].upper())
            item.setData(Qt.UserRole, uni["id"])
            self.lista_unidades.addItem(item)

    def travar_campo_uso(self, palavra):
        self.input_uso.setText(palavra)
        self.input_uso.setReadOnly(True)
        self.input_uso.setStyleSheet("padding: 6px; border: 1px solid #ccc; background-color: #e0e0e0; color: #555;")
        self.btn_salvar_uso.hide()
        self.btn_editar_uso.show()

    def salvar_motivo_uso(self, palavra_fornecida=None):
        # Se veio do popup usa a palavra fornecida, senão pega do QLineEdit
        palavra = palavra_fornecida if palavra_fornecida else self.input_uso.text().strip()
        if not palavra:
            return
            
        dados = {"cliente_id": self.cliente_dados['cliente_id'], "descricao": palavra, "tipo": "USO"}
        try:
            requests.post(f"{API_BASE_URL}/motivo_uso", json=dados)
            self.travar_campo_uso(palavra)
            QMessageBox.information(self, "Sucesso", "Palavra de Uso definida com sucesso!")
        except Exception as e:
            QMessageBox.warning(self, "Erro", "Falha ao salvar a palavra.")

    def abrir_popup_uso(self):
        nova_palavra, ok = QInputDialog.getText(self, "Alterar Palavra", "Digite a nova palavra para Saída Normal:")
        if ok and nova_palavra.strip():
            self.salvar_motivo_uso(nova_palavra.strip())

    def adicionar_categoria(self):
        nome = self.input_nova_cat.text().strip()
        if not nome: return
        dados = {"cliente_id": self.cliente_dados['cliente_id'], "nome": nome}
        try:
            requests.post(f"{API_BASE_URL}/categorias", json=dados)
            self.input_nova_cat.clear()
            self.carregar_listas()
        except:
            pass

    def adicionar_motivo_perda(self):
        descricao = self.input_nova_perda.text().strip()
        if not descricao: return
        dados = {"cliente_id": self.cliente_dados['cliente_id'], "descricao": descricao, "tipo": "PERDA"}
        try:
            requests.post(f"{API_BASE_URL}/motivos", json=dados)
            self.input_nova_perda.clear()
            self.carregar_listas()
        except:
            pass

    def adicionar_unidade(self):
        nome = self.input_nova_unidade.text().strip()
        if not nome: return
        dados = {"cliente_id": self.cliente_dados['cliente_id'], "nome": nome}
        try:
            resp = requests.post(f"{API_BASE_URL}/unidades", json=dados)
            if resp.status_code == 200:
                self.input_nova_unidade.clear()
                self.carregar_listas()
            else:
                QMessageBox.warning(self, "Aviso", resp.json().get("detail", "Erro ao adicionar."))
        except: pass
        
    def editar_unidade(self, item):
        item_id = item.data(Qt.UserRole)
        nome_atual = item.text()
        
        # Abre o popup já com o texto atual preenchido
        novo_nome, ok = QInputDialog.getText(self, "Editar Unidade", "Modifique o nome da unidade:", text=nome_atual)
        
        # Só salva se ele deu OK, se não tá vazio e se ele realmente mudou alguma coisa
        if ok and novo_nome.strip() and novo_nome.strip().upper() != nome_atual.upper():
            dados = {"nome": novo_nome.strip()}
            try:
                resp = requests.put(f"{API_BASE_URL}/unidades/{item_id}", json=dados)
                if resp.status_code == 200:
                    self.carregar_listas() # Dá o F5 na tela
                else:
                    QMessageBox.warning(self, "Erro", resp.json().get("detail", "Erro ao editar."))
            except:
                pass

    def deletar_unidade(self):
        item_selecionado = self.lista_unidades.currentItem()
        if item_selecionado:
            item_id = item_selecionado.data(Qt.UserRole)
            requests.delete(f"{API_BASE_URL}/unidades/{item_id}")
            self.carregar_listas()

    def deletar_categoria(self):
        item_selecionado = self.lista_categorias.currentItem()
        if item_selecionado:
            item_id = item_selecionado.data(Qt.UserRole)
            requests.delete(f"{API_BASE_URL}/categorias/{item_id}")
            self.carregar_listas()

    def deletar_motivo(self):
        item_selecionado = self.lista_perdas.currentItem()
        if item_selecionado:
            item_id = item_selecionado.data(Qt.UserRole)
            requests.delete(f"{API_BASE_URL}/motivos/{item_id}")
            self.carregar_listas()
            
    def salvar_config_global(self):
        try:
            dados = {
                "cliente_id": self.cliente_dados['cliente_id'],
                "receber_notificacoes": self.btn_toggle_notif.isChecked(),
                "limite_global": float(self.input_limite_global.text())
            }
            response = requests.put(f"{API_BASE_URL}/atualizar_config_notificacoes", json=dados)
            if response.status_code == 200:
                QMessageBox.information(self, "Sucesso", "Regra geral de notificação atualizada!")
        except:
            QMessageBox.warning(self, "Erro", "Verifique o valor do limite digitado.")

    def verificar_assinatura_pro(self):
        status = self.cliente_dados.get('status_assinatura', 'Ativo')
        
        if status != "PRO":
            # Desmarca o botão imediatamente, pois ele ainda não é PRO
            self.btn_toggle_pro.setChecked(False) 
            
            # Abre a janela de vendas (Pode ser aberta infinitas vezes agora)
            dialog = DialogUpgradePRO(self.cliente_dados['cliente_id'])
            dialog.exec() 
        else:
            # Se ele JÁ É PRO no banco de dados
            if self.btn_toggle_pro.isChecked():
                self.area_lista_pro.show()
                self.carregar_produtos_pro()
            else:
                self.area_lista_pro.hide()

    def carregar_produtos_pro(self):
        # Limpa o layout antes de carregar
        for i in reversed(range(self.layout_lista_pro.count())): 
            self.layout_lista_pro.itemAt(i).widget().setParent(None)

        try:
            # Busca todos os produtos do cliente
            response = requests.get(f"{API_BASE_URL}/produtos", params={"cliente_id": self.cliente_dados['cliente_id']})
            if response.status_code == 200:
                produtos = response.json()
                for prod in produtos:
                    linha = QHBoxLayout()
                    lbl = QLabel(f"{prod['nome']} ({prod['unidade_medida']}):")
                    lbl.setFixedWidth(150)
                    input_lim = QLineEdit(str(prod.get('estoque_minimo', 0)))
                    input_lim.setFixedWidth(50)
                    
                    btn_save = QPushButton("Salvar")
                    btn_save.setFixedWidth(50)
                    # Conexão direta passando os dados
                    btn_save.clicked.connect(lambda chk, p_id=prod['id'], inp=input_lim: self.salvar_limite_individual(p_id, inp))
                    
                    linha.addWidget(lbl)
                    linha.addWidget(input_lim)
                    linha.addWidget(btn_save)
                    linha.addStretch()
                    
                    widget_linha = QWidget()
                    widget_linha.setLayout(linha)
                    self.layout_lista_pro.addWidget(widget_linha)
        except:
            pass

    def salvar_limite_individual(self, produto_id, input_widget):
        try:
            dados = {
                "produto_id": produto_id,
                "cliente_id": self.cliente_dados['cliente_id'],
                "estoque_minimo": float(input_widget.text())
            }
            requests.put(f"{API_BASE_URL}/atualizar_limite_produto", json=dados)
            input_widget.setStyleSheet("background-color: #c8e6c9;") # Feedback de salvo (verde)
        except:
            QMessageBox.warning(self, "Erro", "Valor inválido.")