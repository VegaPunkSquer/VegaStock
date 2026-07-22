FROM python:3.10-slim

# Cria um usuário comum para o Hugging Face não reclamar de permissão
RUN useradd -m -u 1000 user
USER user
ENV PATH="/home/user/.local/bin:$PATH"

WORKDIR /app

# Copia o seu requirements real e instala as dependências no servidor deles
COPY --chown=user ./requirements.txt requirements.txt
RUN pip install --no-cache-dir --upgrade -r requirements.txt

# Copia o resto dos seus arquivos do VegaStock
COPY --chown=user . /app

# Inicializa o SEU main.py na porta obrigatória 7860
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860"]