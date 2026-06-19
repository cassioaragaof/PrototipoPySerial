from PyQt6.QtWidgets import QWidget, QVBoxLayout, QGridLayout, QLabel, QGroupBox, QHBoxLayout, QSizePolicy, QTabWidget
from PyQt6.QtGui import QPainter, QColor, QPen, QFont
from PyQt6.QtCore import Qt, QRectF, QTimer
from PyQt6.QtWebEngineWidgets import QWebEngineView

from painel_analise import PainelAnaliseDados

# =======================================================
# CÓDIGO DO MAPA
# =======================================================
HTML_MAPA = """
<!DOCTYPE html>
<html>
<head>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <style>
        body { margin:0; padding:0; background-color: #121212; }
        #map { width: 100%; height: 100vh; }
    </style>
</head>
<body>
    <div id="map"></div>
    <script>
        var map = L.map('map', {zoomControl: false}).setView([-19.747, -47.939], 17);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            maxZoom: 19, attribution: '© OpenStreetMap'
        }).addTo(map);
        var polyline = L.polyline([], {color: '#00ffcc', weight: 4, opacity: 0.9}).addTo(map);
        var marker = L.circleMarker([-19.747, -47.939], {
            color: '#121212', fillColor: '#00ffcc', fillOpacity: 1, radius: 8, weight: 2
        }).addTo(map);

        function updatePosition(lat, lon) {
            var novaPosicao = new L.LatLng(lat, lon);
            marker.setLatLng(novaPosicao);
            polyline.addLatLng(novaPosicao);
            map.panTo(novaPosicao, {animate: true, duration: 0.5}); 
        }
    </script>
</body>
</html>
"""

class PainelConexao(QWidget):
    def __init__(self):
        super().__init__()
        self.setFixedHeight(45)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        self.lbl_status = QLabel()
        self.lbl_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_status.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        layout.addWidget(self.lbl_status)

        self.frames_animacao = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
        self.frame_atual = 0
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.animar)
        self.set_conectado(False) 

    def set_conectado(self, conectado):
        if conectado:
            self.timer.stop() 
            self.lbl_status.setText("📶 SINAL FORTE - CONECTADO")
            self.setStyleSheet("QWidget { background-color: rgba(0, 255, 204, 0.8); color: #000; border-radius: 6px; }")
        else:
            self.setStyleSheet("QWidget { background-color: rgba(255, 68, 68, 0.8); color: white; border-radius: 6px; }")
            if not self.timer.isActive():
                self.timer.start(100) 

    def animar(self):
        frame = self.frames_animacao[self.frame_atual]
        self.lbl_status.setText(f"{frame} CONEXÃO PERDIDA - BUSCANDO SINAL...")
        self.frame_atual = (self.frame_atual + 1) % len(self.frames_animacao)

# =======================================================
# RELÓGIOS (Gauges Consertados com Interpolação Matemática Segura)
# =======================================================
class GaugeCircular(QWidget):
    def __init__(self, titulo, valor_maximo, cor_anel, unidade=""):
        super().__init__()
        self.titulo = titulo
        self.valor_maximo = valor_maximo
        self.valor_atual = 0.0
        self.valor_alvo = 0.0
        self.cor_base = QColor(cor_anel)
        self.unidade = unidade
        
        self.setMinimumSize(160, 160)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        # Usando um Timer simples e 100% fiável para a animação
        self.timer_animacao = QTimer()
        self.timer_animacao.timeout.connect(self._suavizar_movimento)
        self.timer_animacao.start(30) # 30 FPS

    def set_valor(self, valor):
        # Apenas dizemos ao sistema onde queremos que o ponteiro chegue
        self.valor_alvo = min(float(valor), self.valor_maximo)

    def _suavizar_movimento(self):
        # Este é o segredo matemático para evitar congelamentos (Interpolação Linear)
        if abs(self.valor_alvo - self.valor_atual) > 0.5:
            self.valor_atual += (self.valor_alvo - self.valor_atual) * 0.15
            self.update()
        elif self.valor_atual != self.valor_alvo:
            self.valor_atual = self.valor_alvo
            self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing) 
        
        tamanho = min(self.width(), self.height())
        margem = 15
        rect = QRectF((self.width() - tamanho)/2 + margem, (self.height() - tamanho)/2 + margem, tamanho - margem*2, tamanho - margem*2)
        
        caneta_fundo = QPen(QColor("#2a2a2a"), 12)
        caneta_fundo.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(caneta_fundo)
        painter.drawArc(rect, 225 * 16, -270 * 16) 
        
        angulo_span = -int((self.valor_atual / self.valor_maximo) * 270 * 16)
        
        cor_glow = QColor(self.cor_base)
        cor_glow.setAlpha(40) 
        caneta_glow = QPen(cor_glow, 22) 
        caneta_glow.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(caneta_glow)
        painter.drawArc(rect, 225 * 16, angulo_span)

        caneta_ativa = QPen(self.cor_base, 10)
        caneta_ativa.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(caneta_ativa)
        painter.drawArc(rect, 225 * 16, angulo_span)
        
        painter.setPen(QColor("#ffffff"))
        painter.setFont(QFont("Segoe UI", 26, QFont.Weight.Bold))
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, f"{int(self.valor_atual)}")
        
        painter.setFont(QFont("Segoe UI", 10))
        painter.setPen(QColor("#a1a1aa"))
        rect_titulo = QRectF(rect.x(), rect.bottom() - 25, rect.width(), 20)
        painter.drawText(rect_titulo, Qt.AlignmentFlag.AlignCenter, f"{self.titulo} {self.unidade}")
        painter.end()

class TelaDashboard(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Telemetria 2027 - Baja SAE")
        self.resize(1200, 700)
        self.setStyleSheet("background-color: #0d0d0d; color: white;") 

        layout_raiz = QVBoxLayout(self)

        self.painel_status = PainelConexao()
        layout_raiz.addWidget(self.painel_status)

        self.abas = QTabWidget()
        self.abas.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #2a2a2a; background: #0d0d0d; border-radius: 8px; }
            QTabBar::tab { background: #1a1a1a; color: #777; padding: 12px 30px; font-weight: bold; font-size: 14px; margin-right: 2px; border-top-left-radius: 6px; border-top-right-radius: 6px;}
            QTabBar::tab:selected { background: #2a2a2a; color: #00ffcc; border-bottom: 3px solid #00ffcc; }
            QTabBar::tab:hover { background: #222; }
        """)

        self.aba_live = QWidget()
        layout_live = QHBoxLayout(self.aba_live)

        container_esquerdo = QWidget()
        container_esquerdo.setMinimumWidth(380) 
        container_esquerdo.setMaximumWidth(480) 
        painel_esquerdo = QVBoxLayout(container_esquerdo)
        
        grade_gauges = QGridLayout()
        grade_gauges.setSpacing(15)
        self.gauge_vel = GaugeCircular("VELOCIDADE", 120, "#00ffcc", "km/h")
        self.gauge_rpm = GaugeCircular("MOTOR", 7000, "#ffaa00", "RPM")
        self.gauge_comb = GaugeCircular("COMBUSTÍVEL", 100, "#ff4444", "%")
        
        grade_gauges.addWidget(self.gauge_vel, 0, 0)
        grade_gauges.addWidget(self.gauge_rpm, 0, 1)
        grade_gauges.addWidget(self.gauge_comb, 1, 0, 1, 2, Qt.AlignmentFlag.AlignCenter) 
        painel_esquerdo.addLayout(grade_gauges)

        box_mapa = QGroupBox("📍 RASTREAMENTO VIA SATÉLITE")
        box_mapa.setStyleSheet("QGroupBox { border: 1px solid #2a2a2a; border-radius: 8px; color: #a1a1aa; font-weight: bold; margin-top: 15px; } QGroupBox::title { subcontrol-origin: margin; left: 15px; padding: 0 5px; }")
        layout_mapa = QVBoxLayout()
        self.navegador_mapa = QWebEngineView()
        self.navegador_mapa.setHtml(HTML_MAPA)
        layout_mapa.addWidget(self.navegador_mapa)
        box_mapa.setLayout(layout_mapa)

        layout_live.addWidget(container_esquerdo) 
        layout_live.addWidget(box_mapa, stretch=1) 

        self.painel_estatistico = PainelAnaliseDados()

        self.abas.addTab(self.aba_live, "⏱️ TELEMETRIA AO VIVO")
        self.abas.addTab(self.painel_estatistico, "📈 ANÁLISE DE ENGENHARIA")

        layout_raiz.addWidget(self.abas)

    def atualizar_valores(self, tensao, combustivel, vel, temp, rpm, lat, lon):
        try:
            self.gauge_vel.set_valor(vel)
            self.gauge_rpm.set_valor(rpm)
            self.gauge_comb.set_valor(combustivel)

            latitude = float(lat)
            longitude = float(lon)
            comando_js = f"updatePosition({latitude}, {longitude});"
            self.navegador_mapa.page().runJavaScript(comando_js)

            self.painel_estatistico.processar_novos_dados(tensao, combustivel, vel, temp, rpm)
        except ValueError:
            pass