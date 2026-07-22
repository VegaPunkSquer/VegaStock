import os
import sys
import requests
import subprocess
from PySide6.QtWidgets import QMessageBox, QProgressDialog, QApplication
from PySide6.QtCore import Qt
import json

if getattr(sys, 'frozen', False):
    diretorio_raiz = sys._MEIPASS
else:
    diretorio_raiz = os.path.dirname(os.path.abspath(__file__))

caminho_manifesto = os.path.join(diretorio_raiz, "vega_manifesto.json")

# AQUI ESTÁ AS VARIÁVEIS GLOBAIS QUE O ABA_SOBRE.PY PRECISA PARA NÃO CRASHAR:
try:
    with open(caminho_manifesto, "r", encoding="utf-8") as f:
        manifesto_data = json.load(f)
        PRODUTO_ID_NO_MASTER = manifesto_data.get("produto_id_master")
        NOME_DO_APP = manifesto_data.get("nome", "App VegaTech")
        VERSAO_LOCAL = manifesto_data.get("versao_atual", "v1.0.0")
except Exception:
    PRODUTO_ID_NO_MASTER = None
    NOME_DO_APP = "App VegaTech"
    VERSAO_LOCAL = "v1.0.0"

API_MASTER_URL = "https://vegap-masterapp.hf.space"

def checar_e_atualizar(parent_widget=None):
    if not getattr(sys, 'frozen', False):
        return False

    if not PRODUTO_ID_NO_MASTER:
        msg = QMessageBox(parent_widget)
        msg.setWindowTitle("Falha de Integridade")
        msg.setText("Arquivo vega_manifesto.json ausente, corrompido ou inválido.")
        msg.setInformativeText("Por medida de segurança, as atualizações deste aplicativo foram bloqueadas. Contate o suporte.")
        msg.setIcon(QMessageBox.Critical)
        msg.exec()
        return False

    try:
        resp = requests.get(f"{API_MASTER_URL}/master/atualizacao/{PRODUTO_ID_NO_MASTER}", timeout=5)
        if resp.status_code == 200:
            dados = resp.json()
            versao_nuvem = dados.get("versao_atual")
            link_download = dados.get("link_download")
            notas = dados.get("notas_atualizacao", "Sem notas disponíveis.").strip()
            
            if versao_nuvem and versao_nuvem != VERSAO_LOCAL and link_download:
                msg = QMessageBox(parent_widget)
                msg.setWindowTitle(f"Atualização Disponível: {NOME_DO_APP}")
                msg.setText(f"Uma nova versão ({versao_nuvem}) está disponível!\n\nO que há de novo:\n\n{notas}\n\nDeseja baixar e atualizar agora?")
                msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
                
                if msg.exec() == QMessageBox.Yes:
                    _baixar_e_instalar(link_download, parent_widget)
                    return True
    except Exception as e:
        print(f"Erro silencioso de rede: {e}")
    return False

def _baixar_e_instalar(url, parent_widget):
    exe_atual = os.path.abspath(sys.executable)
    diretorio_base = os.path.dirname(exe_atual)
    exe_novo = os.path.join(diretorio_base, "update_temporario.exe")
    bat_path = os.path.join(diretorio_base, "updater.bat")

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

        subprocess.Popen([bat_path], creationflags=0x08000000 | 0x00000008)
        os._exit(0)
    except Exception as e:
        progresso.cancel()
        if os.path.exists(exe_novo): os.remove(exe_novo)
        QMessageBox.critical(parent_widget, "Erro", f"Falha no download: {e}")
