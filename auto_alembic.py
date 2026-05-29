import os
import sys
import time
import subprocess
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Define a raiz do projeto de forma dinâmica e absoluta
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODELS_ALVO = os.path.join(BASE_DIR, "models.py")

class MonitorModelsHandler(FileSystemEventHandler):
    def __init__(self):
        super().__init__()
        self.ultima_execucao = 0

    def on_modified(self, event):
        # Ignora se for um diretório
        if event.is_directory:
            return

        # Garante a comparação exata usando caminhos absolutos
        caminho_modificado = os.path.abspath(event.src_path)
        if caminho_modificado != MODELS_ALVO:
            return

        # Evita disparos múltiplos seguidos (trava de segurança de 2 segundos)
        agora = time.time()
        if agora - self.ultima_execucao < 2:
            return
        self.ultima_execucao = agora

        print("\n[Watchdog] 🔄 Alteração detectada no models.py! Preparando o Alembic...")
        
        # Gera uma mensagem de commit automática com o timestamp para ficar limpo
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        mensagem_revisao = f"auto_mod_models_{timestamp}"

        try:
            # Executa o comando dentro do diretório raiz correto
            resultado = subprocess.run(
                ["alembic", "revision", "--autogenerate", "-m", mensagem_revisao],
                cwd=BASE_DIR,
                capture_output=True,
                text=True,
                shell=True  # Essencial para rodar comandos globais/venv no Windows
            )

            if resultado.returncode == 0:
                print(f"[Alembic] ✅ Nova revisão gerada automaticamente: {mensagem_revisao}")
                print(resultado.stdout.strip())
            else:
                print("[Alembic] ❌ Erro ao tentar gerar a revisão:")
                print(resultado.stderr.strip())

        except Exception as e:
            print(f"[Erro Fatal] Não foi possível executar o subprocesso: {str(e)}")

def iniciar_vigilancia():
    print(f"[Status] 👁️  Watchdog ativo! Monitorando alterações em: {MODELS_ALVO}")
    
    event_handler = MonitorModelsHandler()
    observer = Observer()
    # Monitora a pasta raiz, o handler filtra apenas o models.py
    observer.schedule(event_handler, path=BASE_DIR, recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[Status] 🛑 Vigilância encerrada pelo desenvolvedor.")
        observer.stop()
    observer.join()

if __name__ == "__main__":
    iniciar_vigilancia()