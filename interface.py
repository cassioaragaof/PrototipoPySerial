from PyQt6.QtWidgets import QWidget, QVBoxLayout, QGridLayout, QLabel, QGroupBox, QHBoxLayout, QSizePolicy
from PyQt6.QtGui import QPainter, QColor, QPen, QFont
from PyQt6.QtCore import Qt, QRectF, QTimer
from PyQt6.QtWebEngineWidgets import QWebEngineView

# =======================================================
# CÓDIGO DO MAPA REAL
# =======================================================
HTML_MAPA = """
<!DOCTYPE html>
<html>
<head>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <style>
        body { margin:0; padding:0; }
        #map { width: 100%; height: 100vh; }
    </style>
</head>
<body>
    <div id="map"></div>
    <script>
        var map = L.map('map', {zoomControl: false}).setView([-19.747, -47.939], 17);
        
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            maxZoom: 19,
            attribution: '© OpenStreetMap'
        }).addTo(map);
        
        var polyline = L.polyline([], {color: '#ff0000', weight: 5, opacity: 0.8}).addTo(map);
        
        var marker = L.circleMarker([-19.747, -47.939], {
            color: '#ffffff', 
            fillColor: '#3388ff', 
            fillOpacity: 1, 
            radius: 8,
            weight: 2
        }).addTo(map);

        function updatePosition(lat, lon) {
            var novaPosicao = new L.LatLng(lat, lon);
            marker.setLatLng(novaPosicao);
            polyline.addLatLng(novaPosicao);
            map.panTo(novaPosicao, {animate: true, duration: 0.2});
        }
    </script>
</body>
</html>
"""

# =======================================================
# PAINEL DE CONEXÃO
# =======================================================
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
            self.setStyleSheet("""
                QWidget { background-color: #00ffcc; color: #121212; border-radius: 6px; }
            """)
        else:
            self.setStyleSheet("""
                QWidget { background-color: #ff4444; color: white; border-radius: 6px; }
            """)
            self.timer.start(100) 

    def animar(self):
        frame = self.frames_animacao[self.frame_atual]
        self.lbl_status.setText(f"{frame} CONEXÃO PERDIDA - BUSCANDO SINAL...")
        self.frame_atual = (self.frame_atual + 1) % len(self.frames_animacao)

# =======================================================
# RELÓGIOS (Gauges)
# =======================================================
class GaugeCircular(QWidget):
    def __init__(self, titulo, valor_maximo, cor_anel, unidade=""):
        super().__init__()
        self.titulo = titulo
        self.valor_maximo = valor_maximo
        self.valor_atual = 0
        self.cor_anel = QColor(cor_anel)
        self.unidade = unidade
        
        self.setMinimumSize(140, 140)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def set_valor(self, valor):
        self.valor_atual = min(float(valor), self.valor_maximo)
        self.update() 

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing) 
        
        tamanho = min(self.width(), self.height())
        margem = 10
        rect = QRectF((self.width() - tamanho)/2 + margem, (self.height() - tamanho)/2 + margem, tamanho - margem*2, tamanho - margem*2)
        
        caneta_fundo = QPen(QColor("#333333"), 10)
        caneta_fundo.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(caneta_fundo)
        painter.drawArc(rect, 225 * 16, -270 * 16) 
        
        caneta_ativa = QPen(self.cor_anel, 10)
        caneta_ativa.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(caneta_ativa)
        angulo_span = -int((self.valor_atual / self.valor_maximo) * 270 * 16)
        painter.drawArc(rect, 225 * 16, angulo_span)
        
        painter.setPen(QColor("#ffffff"))
        painter.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, f"{int(self.valor_atual)}")
        
        painter.setFont(QFont("Segoe UI", 9))
        painter.setPen(QColor("#888888"))
        rect_titulo = QRectF(rect.x(), rect.bottom() - 20, rect.width(), 20)
        painter.drawText(rect_titulo, Qt.AlignmentFlag.AlignCenter, f"{self.titulo} {self.unidade}")
        painter.end()

# =======================================================
# TELA PRINCIPAL
# =======================================================
class TelaDashboard(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Telemetria 2027")
        self.resize(1100, 600)
        self.setStyleSheet("background-color: #121212; color: white;")

        layout_principal = QHBoxLayout() 

        # --- CONTAINER ESQUERDO ---
        container_esquerdo = QWidget()
        container_esquerdo.setMinimumWidth(350) 
        container_esquerdo.setMaximumWidth(450) 
        
        painel_esquerdo = QVBoxLayout(container_esquerdo)
        
        # 1. Adiciona a barra de status de conexão no topo
        self.painel_status = PainelConexao()
        painel_esquerdo.addWidget(self.painel_status)

        # 2. Adiciona os Gauges embaixo
        grade_gauges = QGridLayout()
        self.gauge_vel = GaugeCircular("VEL", 120, "#00ffcc", "km/h")
        self.gauge_rpm = GaugeCircular("RPM", 7000, "#ffaa00", "")
        self.gauge_comb = GaugeCircular("TANQUE", 100, "#ff4444", "%")
        
        grade_gauges.addWidget(self.gauge_vel, 0, 0)
        grade_gauges.addWidget(self.gauge_rpm, 0, 1)
        grade_gauges.addWidget(self.gauge_comb, 1, 0, 1, 2, Qt.AlignmentFlag.AlignCenter) 
        
        painel_esquerdo.addLayout(grade_gauges)

        # --- PAINEL DO MAPA ---
        box_mapa = QGroupBox("LOCALIZAÇÃO VIA SATÉLITE")
        box_mapa.setStyleSheet("QGroupBox { border: 2px solid #333; border-radius: 8px; color: #888; font-weight: bold; margin-top: 10px; } QGroupBox::title { subcontrol-origin: margin; left: 10px; }")
        layout_mapa = QVBoxLayout()

        self.navegador_mapa = QWebEngineView()
        self.navegador_mapa.setHtml(HTML_MAPA)

        layout_mapa.addWidget(self.navegador_mapa)
        box_mapa.setLayout(layout_mapa)

        layout_principal.addWidget(container_esquerdo) 
        layout_principal.addWidget(box_mapa, stretch=1) 
        
        self.setLayout(layout_principal)

    def atualizar_valores(self, tensao, combustivel, vel, temp, rpm, lat, lon):
        try:
            self.gauge_vel.set_valor(vel)
            self.gauge_rpm.set_valor(rpm)
            self.gauge_comb.set_valor(combustivel)

            latitude = float(lat)
            longitude = float(lon)
            comando_js = f"updatePosition({latitude}, {longitude});"
            self.navegador_mapa.page().runJavaScript(comando_js)
            
        except ValueError:
            pass