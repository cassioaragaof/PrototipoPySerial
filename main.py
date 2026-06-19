# =======================================================
# CÓDIGO DA TELEMETRIA BAJA 2027 - UFTM
# =======================================================

import sys
import time
import serial
import serial.tools.list_ports
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QThread, pyqtSignal

from interface import TelaDashboard

def buscar_porta_arduino():
    portas = serial.tools.list_ports.comports()
    for porta in portas:
        descricao = porta.description.lower()
        if "arduino" in descricao or "ch340" in descricao or "cp210" in descricao or "usb serial" in descricao:
            return porta.device 
    return None

class LeitorSerial(QThread):
    dados_processados = pyqtSignal(str, str, str, str, str, str, str)
    status_conexao = pyqtSignal(bool) 

    def run(self):
        while True:
            porta = buscar_porta_arduino()
            
            if not porta:
                # Dispara a barra vermelha e a animação de refresh
                self.status_conexao.emit(False) 
                time.sleep(1) 
                continue 
            
            try:
                ser = serial.Serial(porta, 9600, timeout=1)
                self.status_conexao.emit(True) 
                
                while True:
                    try:
                        if ser.in_waiting > 0:
                            # 'errors=ignore' evita o travamento (crash) por lixo gerado por ruído no cabo USB
                            dado = ser.readline().decode('utf-8', errors='ignore').strip()
                            
                            if "," in dado:
                                partes = dado.split(',')
                                if len(partes) == 7:
                                    self.dados_processados.emit(
                                        partes[0], partes[1], partes[2], 
                                        partes[3], partes[4], partes[5], partes[6]
                                    )
                    except OSError:
                        break 
                        
            except serial.SerialException:
                self.status_conexao.emit(False)
                time.sleep(2)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    tela = TelaDashboard()
    thread = LeitorSerial()
    
    # Conecta as engrenagens
    thread.dados_processados.connect(tela.atualizar_valores)
    
    # Conecta o sinal Verdadeiro/Falso na função do painel de status
    thread.status_conexao.connect(tela.painel_status.set_conectado) 
    
    thread.start()
    tela.show()
    sys.exit(app.exec())