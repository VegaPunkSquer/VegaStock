import os
import sys
import requests
import subprocess
from PySide6.QtWidgets import QMessageBox, QProgressDialog, QApplication
from PySide6.QtCore import Qt

# Variáveis injetadas automaticamente pela Nave-Mãe
PRODUTO_ID_NO_MASTER = 3
NOME_EXECUTAVEL_ATUAL = "VegaStock.exe"
API_MASTER_URL = "https://vegap-masterapp.hf.space"

import json

if getattr(sys, 'frozen', False):
    diretorio_raiz = sys._MEIPASS
else:
    diretorio_raiz = os.path.dirname(os.path.abspath(__file__))

caminho_manifesto = os.path.join(diretorio_raiz, "vega_manifesto.json")

try:
    with open(caminho_manifesto, "r", encoding="utf-8") as f:
        VERSAO_LOCAL = json.load(f).get("versao_atual", "v1.0.0")
except Exception:
    VERSAO_LOCAL = "v1.0.8"

def checar_e_atualizar(parent_widget=None):
    if not getattr(sys, 'frozen', False):
        return False

    try:
        resp = requests.get(f"{API_MASTER_URL}/master/atualizacao/{PRODUTO_ID_NO_MASTER}", timeout=5)
        if resp.status_code == 200:
            dados = resp.json()
            versao_nuvem = dados.get("versao_atual")
            link_download = dados.get("link_download")
            notas = dados.get("notas_atualizacao", "").strip() # <--- Captura as Notas da Nuvem!

            if versao_nuvem and versao_nuvem != VERSAO_LOCAL and link_download:
                msg = QMessageBox(parent_widget)
                msg.setIcon(QMessageBox.Information)
                msg.setWindowTitle("Atualização de Estabilidade")
                msg.setText(f"Uma nova versão ({versao_nuvem}) está disponível!")
                msg.setInformativeText("O sistema baixará a atualização e reiniciará automaticamente. Deseja prosseguir?")
                msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
                msg.setDefaultButton(QMessageBox.Yes)

                if msg.exec() == QMessageBox.Yes:
                    _baixar_e_instalar(link_download, notas, parent_widget) # Passa as notas pro download
                    return True
    except Exception as e:
        print(f"Aviso silencioso: Falha ao checar atualização - {e}")
        pass
    return False

def _baixar_e_instalar(url, notas_texto, parent_widget):
    exe_atual = os.path.abspath(sys.executable)
    diretorio_base = os.path.dirname(exe_atual)
    exe_novo = os.path.join(diretorio_base, "update_temporario.exe")
    bat_path = os.path.join(diretorio_base, "updater.bat")
    
    # --- NOVO: GERADOR DE RELEASE NOTES NO COMPUTADOR DO CLIENTE ---
    if notas_texto:
        caminho_notas = os.path.join(diretorio_base, "release_notes.txt")
        try:
            with open(caminho_notas, "w", encoding="utf-8") as f:
                f.write(notas_texto)
        except Exception:
            pass
    # -------------------------------------------------------------

    progresso = QProgressDialog("Baixando atualização...", "Cancelar", 0, 100, parent_widget)
    progresso.setWindowTitle("Atualizando")
    progresso.setWindowModality(Qt.WindowModal)
    progresso.setAutoClose(True)
    progresso.setMinimumDuration(0)
    progresso.show()
    QApplication.processEvents()

    try:
        resposta = requests.get(url, stream=True, timeout=15)
        resposta.raise_for_status()
        tamanho_total = int(resposta.headers.get('content-length', 0))
        tamanho_baixado = 0

        with open(exe_novo, 'wb') as arquivo:
            for chunk in resposta.iter_content(chunk_size=8192):
                QApplication.processEvents()
                if progresso.wasCanceled():
                    arquivo.close()
                    if os.path.exists(exe_novo): os.remove(exe_novo)
                    return 

                arquivo.write(chunk)
                tamanho_baixado += len(chunk)
                if tamanho_total > 0:
                    progresso.setValue(int((tamanho_baixado / tamanho_total) * 100))

        nome_exe_original = os.path.basename(exe_atual)
        
        conteudo_bat = f"""@echo off\ntimeout /t 2 /nobreak > NUL\ndel /F /Q "{exe_atual}"\nren "{exe_novo}" "{nome_exe_original}"\nexplorer.exe "{exe_atual}"\ndel "%~f0"\n"""
        with open(bat_path, "w", encoding="mbcs") as f:
            f.write(conteudo_bat)

        CREATE_NO_WINDOW = 0x08000000
        DETACHED_PROCESS = 0x00000008
        subprocess.Popen([bat_path], creationflags=CREATE_NO_WINDOW | DETACHED_PROCESS)

        os._exit(0)

    except Exception as e:
        progresso.cancel()
        if os.path.exists(exe_novo): os.remove(exe_novo)
        QMessageBox.critical(parent_widget, "Erro", f"Falha ao baixar a atualização.\n{e}")
