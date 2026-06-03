import os
import sys
import json
import subprocess
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox

class FabricaVegaStock(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Fábrica de Updates")
        self.setFixedSize(300, 150)
        
        layout = QVBoxLayout(self)
        
        lbl = QLabel("Digite a nova versão (ex: 1.0.5):")
        layout.addWidget(lbl)
        
        self.input_versao = QLineEdit()
        layout.addWidget(self.input_versao)
        
        self.btn_atualizar = QPushButton("Atualizar")
        self.btn_atualizar.clicked.connect(self.compilar)
        layout.addWidget(self.btn_atualizar)

    def compilar(self):
        nova_versao = self.input_versao.text().strip()
        if not nova_versao:
            QMessageBox.warning(self, "Aviso", "A versão não pode ficar vazia.")
            return
            
        # Garante o caminho absoluto perfeito, seja rodando como .py ou compilado como .exe
        if getattr(sys, 'frozen', False):
            diretorio_raiz = os.path.dirname(os.path.abspath(sys.executable))
        else:
            diretorio_raiz = os.path.dirname(os.path.abspath(__file__))
            
        arquivo_json = os.path.join(diretorio_raiz, "versao.json")
        caminho_main = os.path.join(diretorio_raiz, "main.py")
        
        # Sobrescreve o JSON com a versão nova
        try:
            with open(arquivo_json, "w", encoding="utf-8") as f:
                json.dump({"versao": nova_versao}, f, indent=4)
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Falha ao salvar JSON:\n{e}")
            return
            
        # Se você abrir o .exe direto pelo Windows, ele pode não achar o PyInstaller do ambiente virtual.
        # Essa linha garante que ele puxe a ferramenta de dentro da sua pasta venv.
        pyinstaller_exe = os.path.join(diretorio_raiz, "venv", "Scripts", "pyinstaller.exe")
        if not os.path.exists(pyinstaller_exe):
            pyinstaller_exe = "pyinstaller" # Tenta o global caso o venv não esteja lá
            
        comando = [
            pyinstaller_exe, 
            "--noconfirm", 
            "--onedir", 
            "--windowed", 
            "--name", "VegaStock", 
            caminho_main
        ]
        
        self.btn_atualizar.setText("Assando o código...")
        self.btn_atualizar.setEnabled(False)
        QApplication.processEvents() # Destrava a tela para o texto do botão atualizar
        
        try:
            # O shell=True garante que a janela do terminal preta não pule na sua cara do nada
            subprocess.run(comando, shell=True, check=True)
            QMessageBox.information(self, "Sucesso", f"O executável da versão {nova_versao} está pronto na pasta dist!")
            self.input_versao.clear()
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"A compilação falhou:\n{e}")
        finally:
            self.btn_atualizar.setText("Atualizar")
            self.btn_atualizar.setEnabled(True)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    janela = FabricaVegaStock()
    janela.show()
    sys.exit(app.exec())