import pandas as pd
import numpy as np
import pyqtgraph as pg
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, 
                             QTableWidgetItem, QHeaderView, QPushButton, QLabel, 
                             QMessageBox, QComboBox, QCheckBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
import os

# Ativa o Anti-Aliasing globalmente para suavizar as bordas das curvas
pg.setConfigOptions(antialias=True) 

class PainelAnaliseDados(QWidget):
    def __init__(self):
        super().__init__()
        self.layout_principal = QVBoxLayout(self)
        self.setStyleSheet("background-color: #0d0d0d; color: white;")

        self.historico = {
            "Tempo": [], "Tensão (V)": [], "Combustível (%)": [],
            "Velocidade (km/h)": [], "Temperatura (°C)": [], "RPM": []
        }
        self.leituras_totais = 0

        self.lbl_titulo = QLabel("📊 Processamento de Sinal e Estatística Descritiva")
        self.lbl_titulo.setStyleSheet("font-size: 20px; font-weight: bold; color: #ffffff; margin-bottom: 10px;")
        self.lbl_titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout_principal.addWidget(self.lbl_titulo)

        self.tabela_stats = QTableWidget(5, 6) 
        self.tabela_stats.setHorizontalHeaderLabels(["Métrica", "Tensão", "Combustível", "Velocidade", "Temperatura", "RPM"])
        self.tabela_stats.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tabela_stats.setMaximumHeight(180)
        self.tabela_stats.setStyleSheet("""
            QTableWidget { background-color: #121212; gridline-color: #2a2a2a; font-size: 13px; border: 1px solid #2a2a2a; border-radius: 5px; }
            QHeaderView::section { background-color: #1a1a1a; color: #a1a1aa; font-weight: bold; padding: 6px; border: 1px solid #2a2a2a; }
            QTableWidget::item { padding: 5px; }
        """)
        self.layout_principal.addWidget(self.tabela_stats)

        layout_controles = QHBoxLayout()
        layout_controles.setContentsMargins(0, 10, 0, 10)
        
        lbl_seletor = QLabel("Variável Alvo:")
        lbl_seletor.setStyleSheet("font-weight: bold; font-size: 14px; color: #a1a1aa;")
        
        self.combo_variaveis = QComboBox()
        self.combo_variaveis.addItems(["Velocidade (km/h)", "RPM", "Temperatura (°C)", "Tensão (V)", "Combustível (%)"])
        self.combo_variaveis.setStyleSheet("background-color: #1a1a1a; border: 1px solid #333; border-radius: 4px; color: white; padding: 5px 15px; font-weight: bold;")
        self.combo_variaveis.currentTextChanged.connect(self.atualizar_grafico)
        
        self.cb_filtro = QCheckBox("Aplicar Filtro de Média Móvel (Curva Suave)")
        self.cb_filtro.setStyleSheet("font-weight: bold; font-size: 13px; color: #ffaa00;")
        self.cb_filtro.stateChanged.connect(self.atualizar_grafico)

        self.lbl_anomalias = QLabel("⚠️ Detetado (Z-Score > 3): 0")
        self.lbl_anomalias.setStyleSheet("font-weight: bold; font-size: 14px; color: #ff4444; background-color: #2a0000; padding: 5px 10px; border-radius: 4px;")

        layout_controles.addWidget(lbl_seletor)
        layout_controles.addWidget(self.combo_variaveis)
        layout_controles.addSpacing(25)
        layout_controles.addWidget(self.cb_filtro)
        layout_controles.addStretch()
        layout_controles.addWidget(self.lbl_anomalias)
        self.layout_principal.addLayout(layout_controles)

        self.grafico = pg.PlotWidget()
        self.grafico.setBackground('#121212') 
        self.grafico.showGrid(x=True, y=True, alpha=0.15)
        
        estilo_eixos = {'color': '#a1a1aa', 'font-size': '12pt'}
        self.grafico.setLabel('bottom', 'Leitura Temporal', **estilo_eixos)
        self.grafico.setLabel('left', 'Velocidade (km/h)', **estilo_eixos)
        
        caneta_eixo = pg.mkPen(color='#3f3f46', width=1)
        self.grafico.getAxis('bottom').setPen(caneta_eixo)
        self.grafico.getAxis('left').setPen(caneta_eixo)
        
        self.layout_principal.addWidget(self.grafico, stretch=1)

        self.btn_exportar = QPushButton("💾 Exportar para CSV")
        self.btn_exportar.setStyleSheet("""
            QPushButton { background-color: #00ffcc; color: #000000; font-weight: bold; padding: 12px; border-radius: 6px; margin-top: 5px; font-size: 14px; }
            QPushButton:hover { background-color: #00cca3; }
        """)
        self.btn_exportar.clicked.connect(self.exportar_csv)
        self.layout_principal.addWidget(self.btn_exportar)

        metricas = ["Média (Mean)", "Pico Máximo", "Mínimo", "Desvio Padrão", "Variância"]
        for i, met in enumerate(metricas):
            item = QTableWidgetItem(met)
            item.setBackground(QColor("#1a1a1a"))
            item.setForeground(QColor("#a1a1aa"))
            self.tabela_stats.setItem(i, 0, item)

    def processar_novos_dados(self, tensao, comb, vel, temp, rpm):
        try:
            v_tensao = float(tensao)
            v_comb = float(comb)
            v_vel = float(vel)
            v_temp = float(temp)
            v_rpm = float(rpm)

            self.leituras_totais += 1
            self.historico["Tempo"].append(self.leituras_totais)
            self.historico["Tensão (V)"].append(v_tensao)
            self.historico["Combustível (%)"].append(v_comb)
            self.historico["Velocidade (km/h)"].append(v_vel)
            self.historico["Temperatura (°C)"].append(v_temp)
            self.historico["RPM"].append(v_rpm)

            if self.leituras_totais % 20 == 0:
                self.calcular_estatisticas()
            
            # Gráfico super fluido (atualiza frequentemente)
            if self.leituras_totais % 2 == 0:
                self.atualizar_grafico()

        except ValueError as e:
            print(f"⚠️ AVISO: Dados corrompidos pelo rádio/cabo ignorados. Detalhe: {e}")

    def atualizar_grafico(self):
        try:
            if self.leituras_totais < 2:
                return

            variavel_atual = self.combo_variaveis.currentText()
            self.grafico.setLabel('left', variavel_atual)
            
            PONTOS_VISIVEIS = 150 

            # Garante formato seguro de listas nativas
            x_lista = list(self.historico["Tempo"][-PONTOS_VISIVEIS:])
            y_lista = list(self.historico[variavel_atual][-PONTOS_VISIVEIS:])

            # ==========================================
            # Z-SCORE (Deteção Matemática de Erros)
            # ==========================================
            if len(y_lista) > 2:
                desvio_atual = np.std(y_lista)
                if desvio_atual > 0:
                    media_atual = np.mean(y_lista)
                    z_scores = np.abs((np.array(y_lista) - media_atual) / desvio_atual)
                    anomalias = np.sum(z_scores > 3.0)
                    self.lbl_anomalias.setText(f"⚠️ Detetado (Z-Score > 3): {anomalias}")
                else:
                    self.lbl_anomalias.setText("⚠️ Detetado (Z-Score > 3): 0")

            # ==========================================
            # ESTILO VISUAL & FILTROS
            # ==========================================
            if self.cb_filtro.isChecked() and len(y_lista) > 5:
                y_final = pd.Series(y_lista).rolling(window=10, min_periods=1).mean().tolist()
                cor_linha = (255, 170, 0) # Laranja
                cor_fundo = (255, 170, 0, 40)
            else:
                y_final = y_lista
                cor_linha = (0, 255, 204) # Ciano
                cor_fundo = (0, 255, 204, 30)

            # ==========================================
            # RENDERIZAÇÃO BLINDADA (Evita a invisibilidade)
            # ==========================================
            self.grafico.clear() # Limpa o frame com a cor antiga
            
            # Cria e desenha instantaneamente a linha nova por cima
            self.grafico.plot(
                x=x_lista,
                y=y_final,
                pen=pg.mkPen(color=cor_linha, width=2.5),
                fillLevel=0,
                brush=pg.mkBrush(cor_fundo)
            )

        except Exception as e:
            print(f"Erro Crítico na Renderização: {e}")

    def calcular_estatisticas(self):
        try:
            df = pd.DataFrame(self.historico)
            variaveis = ["Tensão (V)", "Combustível (%)", "Velocidade (km/h)", "Temperatura (°C)", "RPM"]

            for col_idx, var in enumerate(variaveis):
                array_numpy = df[var].to_numpy() 
                media = np.mean(array_numpy)
                maximo = np.max(array_numpy)
                minimo = np.min(array_numpy)
                desvio = np.std(array_numpy)
                variancia = np.var(array_numpy)

                valores = [f"{media:.2f}", f"{maximo:.2f}", f"{minimo:.2f}", f"{desvio:.2f}", f"{variancia:.2f}"]
                
                for row_idx, val in enumerate(valores):
                    item = QTableWidgetItem(val)
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    if row_idx % 2 == 0:
                        item.setBackground(QColor("#1a1a1a"))
                    else:
                        item.setBackground(QColor("#121212"))
                    self.tabela_stats.setItem(row_idx, col_idx + 1, item)
        except Exception as e:
            print(f"Erro Estatístico: {e}")

    def exportar_csv(self):
        if self.leituras_totais > 0:
            df = pd.DataFrame(self.historico)
            nome_arquivo = "log_enduro_baja.csv"
            df.to_csv(nome_arquivo, index=False)
            QMessageBox.information(self, "Sucesso", f"Dados exportados com sucesso!\nFicheiro: {os.path.abspath(nome_arquivo)}")
        else:
            QMessageBox.warning(self, "Aviso", "Não há dados suficientes para exportar.")