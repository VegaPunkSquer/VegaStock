# 📦 VegaStock (B2B SaaS Restaurant Ecosystem)

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688.svg)](https://fastapi.tiangolo.com)
[![PySide6](https://img.shields.io/badge/PySide6-Qt6-41CD52.svg)](https://wiki.qt.io/Qt_for_Python)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-336791.svg)](https://www.postgresql.org)
[![Alembic](https://img.shields.io/badge/Alembic-Migrations-8A2BE2.svg)](https://alembic.alchemy.org)

O **VegaStock** é um ecossistema B2B de alta performance projetado especificamente para a gestão inteligente, controle de estoque rigoroso e automação de PDV (Ponto de Venda) para o setor de restaurantes. O sistema opera em arquitetura distribuída, unindo um cliente desktop nativo ultra otimizado em hardware, um aplicativo móvel cross-platform para gerenciamento ágil e uma API de retaguarda Cloud-Native. 

> 🚀 **Milestone:** Produto homologado e em operação real de mercado, sustentando transações, controle de inventário e emissão de dados de clientes em produção.

---

## 📸 Demonstração do Ecossistema

<!-- DICA: Capture pequenos GIFs ou imagens do seu app rodando e substitua os links abaixo -->
<table>
  <tr>
    <td width="50%" align="center"><b>Dashboard, Análise de Métricas & Operação de Estoque</b></td>
    <td width="50%" align="center"><b>Máquina de Vendas / PDV Interativo</b></td>
  </tr>
  <tr>
    <td><img src=".github/assets/dashboard_demo.gif" alt="Dashboard VegaStock" width="100%"></td>
    <td><img src=".github/assets/pdv_demo.gif" alt="PDV VegaStock" width="100%"></td>
  </tr>
</table>

---

## 🏗️ Destaques da Engenharia de Software & Arquitetura

O ecossistema foi desenvolvido aplicando rigorosamente padrões de projeto corporativos (`SOLID`, `Clean Code` e arquitetura baseada em componentes), destacando-se pelos seguintes módulos:

### ⚡ Retaguarda Cloud & Persistência Resiliente
*   **Engine Assíncrona (FastAPI):** API REST robusta construída em Python, conteinerizada via `Dockerfile` e preparada para deploys escaláveis, gerenciando esquemas de dados complexos através de contratos estritos (`Pydantic/Schemas`).
*   **Persistência Segura (PostgreSQL + SQLAlchemy):** Camada de dados configurada com estratégias de otimização de conexão, incluindo *pool pre-ping* ativo para detecção automática de quedas e reestabelecimento invisível de sessões para o cliente final.
*   **Evolução de Banco com Alembic:** Gerenciamento rigoroso de alterações estruturais através de migrações automáticas (`auto_alembic.py`), garantindo atualizações de esquema em produção sem perda de dados ou necessidade de interrupção do banco.

### 💻 Cliente Desktop Nativo (PySide6 / Qt)
*   **Interface Componentizada e Responsiva:** Interface rica construída com widgets nativos estáveis, garantindo excelente tempo de resposta de interface, renderização ágil e recursos de acessibilidade nativos (como ajuste dinâmico de tamanho de fontes).
*   **Ciclo de Automação de Ciclo de Vida:**
    *   `tela_login.py`: Sistema integrado de verificação automática de novas versões antes da inicialização do fluxo principal.
    *   `atualizador.py`: Script autônomo de atualização que baixa, substitui binários locais e reinicializa a aplicação sem fricção para o usuário.
    *   `limpador.py`: Rotina automática de sanitização e manutenção corretiva de memória local e cache local do banco de dados.

### 🛡️ Recursos Avançados de Operação (B2B SaaS)
*   **Módulo de Suporte & Chat Interno:** Sistema de mensageria em tempo real embutido diretamente na aplicação (`models.py`), permitindo comunicação direta do cliente operacional com a administração do SaaS para suporte técnico rápido.
*   **Módulo Automático de Feedback:** Diálogos inteligentes disparados dinamicamente com base em eventos da jornada do usuário para coleta e auditoria de experiência e bugs em produção.

---

## 📂 Estrutura do Repositório (Módulos Core)

A árvore de arquivos reflete uma separação estrita de responsabilidades, isolando a interface nativa cliente das regras críticas de persistência e segurança de dados:

├── alembic/                  # Versionamento estrutural e histórico de migrações do banco
├── assets/                   # Recursos de identidade visual e mídia da aplicação
├── mobile/                   # Subprojeto móvel do ecossistema (vegastock-mobile)
├── aba_*.py                  # Componentes modulares e abas da interface em PySide6
├── app.py / main.py          # Inicialização da aplicação e rotinas de gerência de memória
├── database.py / models.py   # Camada ORM, pools de conexão ativa e mapeamento de tabelas
├── schemas.py                # Contratos estritos de validação e payloads de APIs (Pydantic)
└── requirements.txt          # Dependências limpas e otimizadas do ambiente externo

## 🔒 Propriedade Intelectual e Licença Comercial

O **VegaStock** é um software proprietário de código fechado (*Closed-Source B2B SaaS*). Todo o código-fonte, arquitetura, design de interface e scripts de automação contidos neste repositório são protegidos por direitos autorais. 

*   **Uso Comercial:** Estritamente proibida a reprodução, distribuição, modificação ou engenharia reversa para fins comerciais ou de exploração de terceiros sem autorização expressa do desenvolvedor proprietário.
*   **Finalidade do Repositório:** Este repositório tem o propósito exclusivo de exibir o portfólio de engenharia de software, qualidade de código, padrões de projeto e maturidade arquitetural do desenvolvedor para avaliações técnicas e processos seletivos.

---
Developed with ⚡ by Vega. All rights reserved.