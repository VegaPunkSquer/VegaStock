import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel, QHBoxLayout, QTabWidget
import estilos
from tela_login import TelaLogin
from tela_cadastro import TelaCadastro

class MainWindow(QMainWindow):
    def __init__(self, cliente_dados):
        super().__init__()
        self.cliente_dados = cliente_dados
        self.setWindowTitle(f"Controle de Estoque - {self.cliente_dados['nome_fantasia']}")
        self.resize(900, 600)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout_principal = QVBoxLayout(central_widget)

        header_layout = QHBoxLayout()
        # Mostrando o Nível de Acesso para confirmar que a API leu os dados certos
        lbl_nome_restaurante = QLabel(f"Restaurante: {self.cliente_dados['nome_fantasia']} | Usuário: {self.cliente_dados['nivel_acesso']}")
        lbl_nome_restaurante.setObjectName("titulo") # Aplica o estilo global
        header_layout.addWidget(lbl_nome_restaurante)
        header_layout.addStretch()
        layout_principal.addLayout(header_layout)

        self.abas = QTabWidget()
        layout_principal.addWidget(self.abas)

        # Abas vazias esperando o Passo 4 e 5
        self.aba_estoque = QWidget()
        self.abas.addTab(self.aba_estoque, "Operação de Estoque")
        self.aba_relatorios = QWidget()
        self.abas.addTab(self.aba_relatorios, "Análise de Desperdício")

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
        
        else:
            # Usuário clicou no "X" vermelho da janela, fecha tudo.
            break

    sys.exit()

if __name__ == "__main__":
    iniciar_app()