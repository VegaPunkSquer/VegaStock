import os
import sys
import base64
import subprocess
from datetime import datetime
from PySide6.QtWidgets import (QDialog, QFrame, QVBoxLayout, QHBoxLayout, QGroupBox, 
                               QRadioButton, QPushButton, QLabel, QFileDialog, 
                               QMessageBox, QButtonGroup)
from PySide6.QtCore import Qt
from PySide6.QtGui import QTextDocument, QPageLayout, QPageSize
from PySide6.QtPrintSupport import QPrinter

# Importa a sessão e modelos do seu backend
from database import SessionLocal
import models

class DialogGeradorRelatorio(QDialog):
    def __init__(self, cliente_dados, parent=None):
        super().__init__(parent)
        self.cliente_dados = cliente_dados
        self.cliente_id = self.cliente_dados.get("cliente_id") or self.cliente_dados.get("id")
        self.nome_fantasia = self.cliente_dados.get("nome_fantasia", "VEGASTOCK B2B")
        self.logo_url = self.cliente_dados.get("logo_url", "")
        
        self.setWindowTitle("📊 Central de Relatórios Executivos - VegaStock")
        # Aumentamos a janela para dar respiro aos botões
        self.setFixedSize(500, 480) 
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        
        self.init_ui()
        
    def init_ui(self):
        from PySide6.QtWidgets import QComboBox # Importação segura
        layout_principal = QVBoxLayout(self)
        layout_principal.setSpacing(20)
        layout_principal.setContentsMargins(25, 25, 25, 25)
        
        lbl_titulo = QLabel("Selecione os parâmetros para emissão do documento:")
        lbl_titulo.setStyleSheet("font-weight: bold; font-size: 15px; color: #1E293B;")
        layout_principal.addWidget(lbl_titulo)
        
        # --- 1. ORIENTAÇÃO (AGORA É DROPDOWN - IMPOSSÍVEL DE BUGAR) ---
        lbl_or = QLabel("1. Orientação da Página:")
        lbl_or.setStyleSheet("font-weight: bold; font-size: 13px; color: #2563EB;")
        layout_principal.addWidget(lbl_or)
        
        self.combo_orientacao = QComboBox()
        self.combo_orientacao.addItems(["📄 Retrato (Vertical)", "🖥️ Paisagem (Horizontal)"])
        self.combo_orientacao.setStyleSheet("padding: 8px; font-size: 14px; border: 1px solid #CBD5E1; border-radius: 4px; background-color: white;")
        self.combo_orientacao.setCursor(Qt.PointingHandCursor)
        layout_principal.addWidget(self.combo_orientacao)
        
        # --- 2. TIPO DE RELATÓRIO (AGORA É DROPDOWN - IMPOSSÍVEL DE BUGAR) ---
        lbl_tp = QLabel("2. Conteúdo do Relatório:")
        lbl_tp.setStyleSheet("font-weight: bold; font-size: 13px; color: #2563EB; margin-top: 10px;")
        layout_principal.addWidget(lbl_tp)
        
        self.combo_tipo = QComboBox()
        self.combo_tipo.addItems([
            "📑 Relatório Executivo Completo (Todos)",
            "📦 Catálogo Geral de Produtos",
            "📊 Posição do Estoque e Valoração",
            "⚠️ Análise de Desperdícios e Prejuízos"
        ])
        self.combo_tipo.setStyleSheet("padding: 8px; font-size: 14px; border: 1px solid #CBD5E1; border-radius: 4px; background-color: white;")
        self.combo_tipo.setCursor(Qt.PointingHandCursor)
        layout_principal.addWidget(self.combo_tipo)
        
        layout_principal.addStretch()
        
        # --- BOTÃO GERAR ---
        self.btn_gerar = QPushButton("🚀 Gerar Relatório e Abrir PDF")
        self.btn_gerar.setMinimumHeight(50)
        self.btn_gerar.setStyleSheet("""
            QPushButton {
                background-color: #0F172A; color: white; font-weight: bold; font-size: 15px; border-radius: 6px;
            }
            QPushButton:hover { background-color: #1E293B; }
        """)
        self.btn_gerar.setCursor(Qt.PointingHandCursor)
        self.btn_gerar.clicked.connect(self.processar_e_gerar_pdf)
        layout_principal.addWidget(self.btn_gerar)
        
    def converter_logo_base64(self):
        # AQUI É ONDE CORTAMOS A FOTO REDONDA IGUAL A DO APLICATIVO
        if not self.logo_url:
            return ""
        caminho_absoluto = os.path.abspath(self.logo_url)
        if os.path.exists(caminho_absoluto):
            try:
                from PySide6.QtGui import QPixmap, QPainter, QPainterPath
                from PySide6.QtCore import QBuffer, QIODevice, Qt
                
                tamanho = 120
                pixmap_orig = QPixmap(caminho_absoluto)
                if pixmap_orig.isNull(): return ""
                
                pixmap_scaled = pixmap_orig.scaled(tamanho, tamanho, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
                
                final_pixmap = QPixmap(tamanho, tamanho)
                final_pixmap.fill(Qt.transparent)
                
                painter = QPainter(final_pixmap)
                painter.setRenderHint(QPainter.Antialiasing)
                path = QPainterPath()
                path.addEllipse(0, 0, tamanho, tamanho)
                painter.setClipPath(path)
                
                x_offset = (tamanho - pixmap_scaled.width()) // 2
                y_offset = (tamanho - pixmap_scaled.height()) // 2
                painter.drawPixmap(x_offset, y_offset, pixmap_scaled)
                painter.end()

                buffer = QBuffer()
                buffer.open(QIODevice.WriteOnly)
                final_pixmap.save(buffer, "PNG")
                encoded_string = base64.b64encode(buffer.data().data()).decode('utf-8')
                return f"data:image/png;base64,{encoded_string}"
            except Exception as e:
                print(f"Erro ao forçar foto redonda: {e}")
                return ""
        return ""

    def processar_e_gerar_pdf(self):
        diretorio_atual = os.path.dirname(os.path.abspath(__file__))
        pasta_relatorios = os.path.join(diretorio_atual, "relatorios_gerados")
        if not os.path.exists(pasta_relatorios):
            os.makedirs(pasta_relatorios)
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        nome_default = os.path.join(pasta_relatorios, f"Relatorio_VegaStock_{timestamp}.pdf")
        
        caminho_salvar, _ = QFileDialog.getSaveFileName(self, "Salvar Relatório PDF", nome_default, "PDF Files (*.pdf)")
        if not caminho_salvar:
            return
            
        self.btn_gerar.setText("⏳ Compilando Dados no Banco...")
        self.btn_gerar.setEnabled(False)
        
        try:
            html_content = self.construir_html_relatorio()
            
            printer = QPrinter(QPrinter.HighResolution)
            printer.setOutputFormat(QPrinter.PdfFormat)
            printer.setOutputFileName(os.path.abspath(caminho_salvar))
            
            # LÊ DIRETO DO COMBOBOX AGORA
            if "Paisagem" in self.combo_orientacao.currentText():
                printer.setPageOrientation(QPageLayout.Orientation.Landscape)
            else:
                printer.setPageOrientation(QPageLayout.Orientation.Portrait)
                
            printer.setPageSize(QPageSize(QPageSize.A4))
            
            doc = QTextDocument()
            doc.setHtml(html_content)
            doc.print_(printer)
            
            self.accept()
            caminho_final = os.path.abspath(caminho_salvar)
            if os.name == 'nt':
                os.startfile(caminho_final)
            else:
                subprocess.Popen(['open' if sys.platform == 'darwin' else 'xdg-open', caminho_final])
                
        except Exception as e:
            QMessageBox.critical(self, "Erro na Emissão", f"Falha ao gerar o arquivo PDF:\n{str(e)}")
            self.btn_gerar.setText("🚀 Gerar Relatório e Abrir PDF")
            self.btn_gerar.setEnabled(True)
            
    def construir_html_relatorio(self):
        import requests
        API_URL = "https://vegap-vega-stock.hf.space"
        
        # 1. PUXANDO DADOS REAIS DA API (Substitui o SessionLocal incorreto)
        produtos = []
        try:
            r = requests.get(f"{API_URL}/produtos/{self.cliente_id}", timeout=5)
            if r.status_code == 200: produtos = r.json()
        except: pass

        movs = []
        try:
            r = requests.get(f"{API_URL}/movimentacoes/{self.cliente_id}", timeout=5)
            if r.status_code == 200: movs = r.json()
        except: pass

        logo_base64 = self.converter_logo_base64()
        tag_img_logo = f'<p align="center" style="margin-bottom: 5px;"><img src="{logo_base64}"></p>' if logo_base64 else ''
        
        data_atual = datetime.now().strftime("%d/%m/%Y às %H:%M")
        
        opcao_selecionada = self.combo_tipo.currentText()
        if "Catálogo" in opcao_selecionada: tipo_str = "CATÁLOGO DE PRODUTOS"
        elif "Estoque" in opcao_selecionada: tipo_str = "POSIÇÃO DO ESTOQUE E VALORAÇÃO"
        elif "Desperdícios" in opcao_selecionada: tipo_str = "ANÁLISE DE DESPERDÍCIOS E PREJUÍZOS"
        else: tipo_str = "GERAL COMPLETO DE OPERAÇÕES"
            
        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; color: #1E293B; }}
                h3 {{ color: #0F172A; font-size: 15px; border-left: 4px solid #2563EB; padding-left: 8px; margin-top: 25px; margin-bottom: 10px; }}
                table {{ width: 100%; border-collapse: collapse; margin-bottom: 20px; font-size: 11px; }}
                th {{ background-color: #0F172A; color: white; font-weight: bold; text-align: left; padding: 7px; border: 1px solid #0F172A; }}
                td {{ padding: 7px; border: 1px solid #CBD5E1; }}
                tr:nth-child(even) {{ background-color: #F8FAFC; }}
                .numero {{ text-align: right; }}
                .alerta {{ color: #DC2626; font-weight: bold; }}
            </style>
        </head>
        <body>
            <div style="text-align: center; margin-bottom: 20px;">
                {tag_img_logo}
                <h2 style="color: #0F172A; margin: 0; font-size: 18px;">RELATÓRIO {tipo_str} — {self.nome_fantasia.upper()}</h2>
                <p style="color: #64748B; font-size: 12px; margin-top: 5px; font-weight: bold;">Emitido pelo Sistema em: {data_atual}</p>
            </div>
            <hr style="border: 1px solid #0F172A; margin-bottom: 20px;">
        """
        
        is_completo = "Completo" in opcao_selecionada
        is_catalogo = "Catálogo" in opcao_selecionada or is_completo
        is_estoque = "Estoque" in opcao_selecionada or is_completo
        is_prejuizo = "Desperdícios" in opcao_selecionada or is_completo

        # --- MÓDULO 1: CATÁLOGO ---
        if is_catalogo:
            html += "<h3>📦 Catálogo de Produtos Cadastrados</h3>"
            html += "<table><tr><th>ID</th><th>Nome do Produto</th><th>Unidade</th><th class='numero'>Estoque Mínimo</th><th class='numero'>Custo Médio (R$)</th></tr>"
            if not produtos:
                html += "<tr><td colspan='5' style='text-align:center;'>Nenhum produto cadastrado no catálogo.</td></tr>"
            else:
                for p in produtos:
                    pid = p.get('id', '')
                    nome = p.get('nome', 'Sem Nome')
                    unid = p.get('unidade_medida', 'UN')
                    est_min = float(p.get('estoque_minimo', 0.0))
                    custo = float(p.get('custo_medio', 0.0))
                    html += f"<tr><td>{pid}</td><td><b>{nome}</b></td><td>{unid}</td><td class='numero'>{est_min:.2f}</td><td class='numero'>R$ {custo:.2f}</td></tr>"
            html += "</table>"
            
        # --- MÓDULO 2: ESTOQUE ---
        if is_estoque:
            html += "<h3>📊 Posição do Estoque Atual e Valoração</h3>"
            html += "<table><tr><th>Produto</th><th>Unidade</th><th class='numero'>Qtd. Atual</th><th class='numero'>Custo Unitário (R$)</th><th class='numero'>Valoração Total (R$)</th><th>Status</th></tr>"
            total_financeiro_estoque = 0.0
            if not produtos:
                html += "<tr><td colspan='6' style='text-align:center;'>Nenhum dado de estoque disponível.</td></tr>"
            else:
                for p in produtos:
                    qtd = float(p.get('quantidade_atual', 0.0))
                    custo = float(p.get('custo_medio', 0.0))
                    est_min = float(p.get('estoque_minimo', 0.0))
                    val_total = qtd * custo
                    total_financeiro_estoque += val_total
                    status_str = '<span class="alerta">⚠️ ABAIXO DO MÍNIMO</span>' if qtd <= est_min else '✅ Normal'
                    html += f"<tr><td><b>{p.get('nome', '')}</b></td><td>{p.get('unidade_medida', '')}</td><td class='numero'><b>{qtd:.2f}</b></td><td class='numero'>R$ {custo:.2f}</td><td class='numero'><b>R$ {val_total:.2f}</b></td><td>{status_str}</td></tr>"
                html += f"<tr style='background-color: #E2E8F0; font-weight: bold;'><td colspan='4' style='text-align: right;'>TOTAL FINANCEIRO EM ESTOQUE:</td><td class='numero' style='color: #0F172A;'>R$ {total_financeiro_estoque:.2f}</td><td></td></tr>"
            html += "</table>"

        # --- MÓDULO 3: PREJUÍZO ---
        if is_prejuizo:
            html += "<h3>⚠️ Análise de Desperdícios e Quebras de Estoque</h3>"
            html += "<table><tr><th>Data/Hora</th><th>Produto</th><th>Motivo da Baixa</th><th class='numero'>Qtd. Perdida</th><th class='numero'>Custo Unitário</th><th class='numero'>Prejuízo Total (R$)</th></tr>"
            
            prejuizos = [m for m in movs if "saida" in str(m.get("tipo_movimento", "")).lower() and m.get("motivo_baixa_id")]
            total_prejuizo = 0.0
            
            if not prejuizos:
                html += "<tr><td colspan='6' style='text-align:center;'>Nenhum registro de desperdício ou avaria encontrado no histórico.</td></tr>"
            else:
                for m in prejuizos:
                    # Relaciona as tabelas cruzando os IDs
                    pid = m.get("produto_id")
                    prod_relacionado = next((p for p in produtos if p.get("id") == pid), {})
                    
                    nome_prod = m.get("produto_nome", prod_relacionado.get("nome", "Produto Removido"))
                    desc_motivo = m.get("motivo_descricao", "Motivo Interno")
                    
                    qtd = float(m.get("quantidade", 0.0))
                    custo_base = float(m.get("custo_unitario") or prod_relacionado.get("custo_medio") or 0.0)
                    perda_financeira = qtd * custo_base
                    total_prejuizo += perda_financeira
                    
                    data_str = m.get("data_hora", "--/--").replace("T", " ")[:16]
                    html += f"<tr><td>{data_str}</td><td><b>{nome_prod}</b></td><td>{desc_motivo}</td><td class='numero'>{qtd:.2f}</td><td class='numero'>R$ {custo_base:.2f}</td><td class='numero alerta'>R$ {perda_financeira:.2f}</td></tr>"
                html += f"<tr style='background-color: #FEE2E2; font-weight: bold;'><td colspan='5' style='text-align: right; color: #DC2626;'>TOTAL ACUMULADO DE PREJUÍZOS / PERDAS:</td><td class='numero alerta'>R$ {total_prejuizo:.2f}</td></tr>"
            html += "</table>"
            
        html += "</body></html>"
        return html