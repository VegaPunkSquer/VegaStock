from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt

API_BASE_URL = "https://vegap-vega-stock.hf.space"

class AbaSobre(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignTop)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(15)

        # Título principal
        lbl_titulo = QLabel("VegaStock — Sistema de Estoque B2B")
        lbl_titulo.setStyleSheet("font-size: 20px; font-weight: bold;")
        layout.addWidget(lbl_titulo)

        # Informações gerais do software
        lbl_info = QLabel(
            "<b>Versão:</b> 1.0.0<br>"
            "<b>Descrição:</b> Sistema desktop inteligente para gestão de estoque em restaurantes, "
            "cafeterias e indústrias alimentícias, equipado com controle multitenant e relatórios "
            "avançados de desperdício."
            "<br>Feito pela Vega Tech em Parceria com a Mais Soluções Integradas!<br>"
        )
        lbl_info.setStyleSheet("font-size: 13px; color: #333333; line-height: 140%;")
        layout.addWidget(lbl_info)

        layout.addSpacing(10)

        # Título da seção de suporte
        lbl_suporte = QLabel("Canais de Suporte Técnico")
        lbl_suporte.setStyleSheet("font-size: 15px; font-weight: bold;")
        layout.addWidget(lbl_suporte)

        # Estrutura de contatos com links autênticos para e-mail e WhatsApp (2 seções)
        texto_suporte = (
            "<table cellspacing='15' cellpadding='0' style='font-size: 13px; color: #000000;'>"
            "  <tr>"
            "    <td style='font-weight: bold; font-size: 14px;'>🚀 Vega Tech Solutions</td>"
            "    <td style='font-weight: bold; font-size: 14px;'>🤝 Mais Soluções Integradas</td>"
            "  </tr>"
            "  <tr>"
            "    <td>"
            "      📧 <b>E-mail:</b> <a href='mailto:sergio.renan.ms@gmail.com' style='color: #009EE3;'>suporte@vegastock.com.br</a><br><br>"
            "      💬 <b>WhatsApp:</b> <a href='https://wa.me/5512981194607' style='color: #25D366;'>🟢 (12) 98119-4607</a>"
            "    </td>"
            "    <td>"
            "      📧 <b>E-mail:</b> <a href='mailto:maissolucoesintegradas@gmail.com' style='color: #009EE3;'>suporte@associado.com.br</a><br><br>"
            "      💬 <b>WhatsApp:</b> <a href='https://wa.me/558396622804' style='color: #25D366;'>🟢 (83) 99662-2804</a>"
            "    </td>"
            "  </tr>"
            "</table>"
        )

        lbl_contatos = QLabel(texto_suporte)
        lbl_contatos.setOpenExternalLinks(True)
        layout.addWidget(lbl_contatos)

        layout.addStretch()

        # Rodapé
        lbl_rodape = QLabel("© 2026 VegaStock. Todos os direitos reservados.")
        lbl_rodape.setStyleSheet("color: #888888; font-size: 10px;")
        layout.addWidget(lbl_rodape, alignment=Qt.AlignHCenter)