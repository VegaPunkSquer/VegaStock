import os
import requests
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QLineEdit, QPushButton, QMessageBox, QFileDialog, QFrame)
from PySide6.QtCore import Qt

API_BASE_URL = "http://127.0.0.1:8000"

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
        layout_principal.addWidget(lbl_titulo)

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

        # --- BLOCO 2: ALTERAÇÃO DE SENHA ---
        frame_senha = QFrame()
        frame_senha.setStyleSheet("background-color: #f9f9f9; border: 1px solid #ddd; border-radius: 5px;")
        layout_senha = QVBoxLayout(frame_senha)
        layout_senha.setContentsMargins(15, 15, 15, 15)

        lbl_senha_titulo = QLabel("Segurança: Alterar Senha de Admin")
        lbl_senha_titulo.setStyleSheet("font-weight: bold; font-size: 16px; border: none;")
        layout_senha.addWidget(lbl_senha_titulo)

        # Campos de Senha
        self.input_senha_atual = QLineEdit()
        self.input_senha_atual.setPlaceholderText("Senha Atual")
        self.input_senha_atual.setEchoMode(QLineEdit.Password)
        self.input_senha_atual.setFixedWidth(300)
        self.input_senha_atual.setStyleSheet("padding: 8px; border: 1px solid #ccc; border-radius: 3px;")
        layout_senha.addWidget(self.input_senha_atual)

        self.input_nova_senha = QLineEdit()
        self.input_nova_senha.setPlaceholderText("Nova Senha")
        self.input_nova_senha.setEchoMode(QLineEdit.Password)
        self.input_nova_senha.setFixedWidth(300)
        self.input_nova_senha.setStyleSheet("padding: 8px; border: 1px solid #ccc; border-radius: 3px;")
        layout_senha.addWidget(self.input_nova_senha)

        self.input_confirma_senha = QLineEdit()
        self.input_confirma_senha.setPlaceholderText("Confirmar Nova Senha")
        self.input_confirma_senha.setEchoMode(QLineEdit.Password)
        self.input_confirma_senha.setFixedWidth(300)
        self.input_confirma_senha.setStyleSheet("padding: 8px; border: 1px solid #ccc; border-radius: 3px;")
        layout_senha.addWidget(self.input_confirma_senha)

        btn_salvar_senha = QPushButton("Atualizar Senha")
        btn_salvar_senha.setFixedWidth(150)
        btn_salvar_senha.setStyleSheet("background-color: #FFD700; color: #000; font-weight: bold; padding: 8px; border-radius: 3px;")
        btn_salvar_senha.clicked.connect(self.alterar_senha)
        layout_senha.addWidget(btn_salvar_senha)

        layout_principal.addWidget(frame_senha)
        layout_principal.addStretch() # Empurra tudo para cima

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
        atual = self.input_senha_atual.text()
        nova = self.input_nova_senha.text()
        confirma = self.input_confirma_senha.text()

        if not all([atual, nova, confirma]):
            QMessageBox.warning(self, "Aviso", "Preencha todos os campos de senha.")
            return

        if nova != confirma:
            QMessageBox.warning(self, "Aviso", "A nova senha e a confirmação não batem.")
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