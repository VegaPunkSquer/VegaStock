import os
import sys
import requests
import subprocess
from PySide6.QtWidgets import QMessageBox, QProgressDialog
from PySide6.QtCore import Qt

# A tatuagem de nascença do seu App! Lembre de mudar aqui ANTES de compilar o novo .exe
try:
    from versao import VERSAO_LOCAL
except ImportError:
    VERSAO_LOCAL = "v1.0.0"

# O radar automático apontado para o seu repositório no GitHub
GITHUB_API_URL = "https://api.github.com/repos/VegaPunkSquer/VegaStock/releases/latest"

def checar_e_atualizar(parent_widget=None):
    if not getattr(sys, 'frozen', False):
        return False # Ignora se estiver rodando no VS Code

    try:
        resp = requests.get(GITHUB_API_URL, timeout=5)
        if resp.status_code == 200:
            dados = resp.json()
            
            # O GitHub entrega o nome da tag (ex: "v1.0.1") e a lista de arquivos anexados (assets)
            versao_remota = dados.get("tag_name")
            assets = dados.get("assets", [])
            
            # Pega o link do primeiro arquivo .exe anexado na release
            link_download = None
            if assets:
                link_download = assets[0].get("browser_download_url")

            # Se a versão for diferente e existir um arquivo para baixar...
            if versao_remota and versao_remota != VERSAO_LOCAL and link_download:
                msg = QMessageBox(parent_widget)
                msg.setIcon(QMessageBox.Information)
                msg.setWindowTitle("Atualização de Estabilidade")
                msg.setText(f"Uma nova versão ({versao_remota}) está disponível!")
                msg.setInformativeText("O sistema baixará a atualização e reiniciará automaticamente. Deseja prosseguir?")
                msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
                msg.setDefaultButton(QMessageBox.Yes)

                if msg.exec() == QMessageBox.Yes:
                    _baixar_e_instalar(link_download, parent_widget)
                    return True # Sinaliza para o app fechar
                    
    except Exception as e:
        print(f"Aviso silencioso: Falha ao checar atualização no GitHub - {e}")
        pass

    return False

def _baixar_e_instalar(url, parent_widget):
    # Pega o caminho absoluto de onde o .exe atual está rodando
    exe_atual = os.path.abspath(sys.executable)
    diretorio_base = os.path.dirname(exe_atual)
    exe_novo = os.path.join(diretorio_base, "update_temporario.exe")
    bat_path = os.path.join(diretorio_base, "updater.bat")

    # Diálogo de Progresso Nativo
    progresso = QProgressDialog("Baixando atualização de estabilidade...", "Cancelar", 0, 100, parent_widget)
    progresso.setWindowTitle("Atualizando")
    progresso.setWindowModality(Qt.WindowModal)
    progresso.setAutoClose(True)
    progresso.show()

    # Faz o download dividindo em pedaços (chunks) para não estourar a memória
    try:
        resposta = requests.get(url, stream=True, timeout=10)
        resposta.raise_for_status()
        tamanho_total = int(resposta.headers.get('content-length', 0))
        tamanho_baixado = 0

        with open(exe_novo, 'wb') as arquivo:
            for chunk in resposta.iter_content(chunk_size=8192):
                if progresso.wasCanceled():
                    arquivo.close()
                    os.remove(exe_novo)
                    return # O usuário cancelou o download

                arquivo.write(chunk)
                tamanho_baixado += len(chunk)
                if tamanho_total > 0:
                    porcentagem = int((tamanho_baixado / tamanho_total) * 100)
                    progresso.setValue(porcentagem)

        # Download concluído! Hora de criar o script "kamikaze"
        nome_exe_original = os.path.basename(exe_atual)
        
        # O script espera 2 segs, deleta o velho, renomeia o novo, executa e se auto-destrói
        conteudo_bat = f"""@echo off
timeout /t 2 /nobreak > NUL
del "{exe_atual}"
ren "{exe_novo}" "{nome_exe_original}"
start "" "{exe_atual}"
del "%~f0"
"""
        with open(bat_path, "w", encoding="utf-8") as f:
            f.write(conteudo_bat)

        # Roda o .bat em segundo plano, sem abrir janela preta chata
        CREATE_NO_WINDOW = 0x08000000
        subprocess.Popen([bat_path], creationflags=CREATE_NO_WINDOW)

        # Mata o aplicativo atual imediatamente para liberar o arquivo .exe
        os._exit(0)

    except Exception as e:
        progresso.cancel()
        QMessageBox.critical(parent_widget, "Erro", f"Falha ao baixar a atualização.\n{e}")