import os
import sys
import json
import subprocess
import shutil
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

    def limpar_restos(self, diretorio_raiz, nome_versao):
        # 1/3 e 3/3 do seu .bat: Limpa a pasta build e arquivos .spec
        pasta_build = os.path.join(diretorio_raiz, "build")
        if os.path.exists(pasta_build):
            shutil.rmtree(pasta_build, ignore_errors=True)
        
        spec_1 = os.path.join(diretorio_raiz, f"VegaStock_{nome_versao}.spec")
        spec_2 = os.path.join(diretorio_raiz, "VegaStock.spec")
        if os.path.exists(spec_1): os.remove(spec_1)
        if os.path.exists(spec_2): os.remove(spec_2)

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
        
        # O BAT do seu tio recriado: Sobrescreve o JSON e também cria o versao.py
        try:
            with open(arquivo_json, "w", encoding="utf-8") as f:
                json.dump({"versao": nova_versao}, f, indent=4)
                
            arquivo_py = os.path.join(diretorio_raiz, "versao.py")
            with open(arquivo_py, "w", encoding="utf-8") as f:
                f.write(f'VERSAO_LOCAL = "{nova_versao}"\n')
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Falha ao salvar arquivos de versão:\n{e}")
            return
            
        # Se você abrir o .exe direto pelo Windows, ele pode não achar o PyInstaller do ambiente virtual.
        # Essa linha garante que ele puxe a ferramenta de dentro da sua pasta venv.
        pyinstaller_exe = os.path.join(diretorio_raiz, "venv", "Scripts", "pyinstaller.exe")
        if not os.path.exists(pyinstaller_exe):
            pyinstaller_exe = "pyinstaller" # Tenta o global caso o venv não esteja lá
            
        # --- AQUI ESTÁ A LÓGICA DO SEU .BAT ---
        nome_final = f"VegaStock_{nova_versao}"
        
        comando = [
            pyinstaller_exe, 
            "--noconfirm", 
            "--onefile",           # Como você usa no seu .bat
            "--windowed", 
            "--name", nome_final,  # VegaStock_v1.0.x
            "--icon", "assets/logo.ico", 
            "--add-data", "assets;assets", 
            "--hidden-import", "dialog_feedback", 
            "app.py"               # O arquivo que você compila no .bat
        ]
        
        self.btn_atualizar.setText("Assando o código...")
        self.btn_atualizar.setEnabled(False)
        QApplication.processEvents() # Destrava a tela para o texto do botão atualizar
        
        try:
            # 1. Limpa o lixo da compilação anterior
            self.limpar_restos(diretorio_raiz, nova_versao)
            
            # 2. O shell=True garante que a janela preta não pule na sua cara do nada
            subprocess.run(comando, shell=True, check=True)
            
            # 3. Limpa os restos da obra (igual seu .bat)
            self.limpar_restos(diretorio_raiz, nova_versao)
            
            QMessageBox.information(self, "Sucesso", f"MONSTRO CRIADO!\n\nO executável da versão {nova_versao} está pronto na pasta dist!")
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