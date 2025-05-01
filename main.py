from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QPushButton, QCheckBox,
    QHBoxLayout, QSpinBox, QComboBox, QTabWidget, QLineEdit, QGridLayout, QMessageBox, QMessageBox, QDialog, QTextEdit
)

from PyQt5.QtCore import QTimer
import sys, json, os
from scanner import Scanner
from alerts import send_telegram_alert
from alerts import send_ntfy_alert  # asegúrate de tener esto arriba

CONFIG_FILE = "config.json"

class MainApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Trading Alerts Bot")
        self.setGeometry(100, 100, 700, 600)

        self.tabs = QTabWidget()
        self.tab_monitor = QWidget()
        self.tab_config = QWidget()

        self.tabs.addTab(self.tab_monitor, "Monitor")
        self.tabs.addTab(self.tab_config, "Configuración")

        self.layout = QVBoxLayout(self)
        self.layout.addWidget(self.tabs)
        self.setLayout(self.layout)

        self.init_monitor_tab()
        self.init_config_tab()
        self.load_config()

        self.timer = QTimer()
        self.timer.timeout.connect(self.scan)

        self.scanner = Scanner()
        
        

    def init_monitor_tab(self):
        layout = QVBoxLayout()
        grid = QGridLayout()

        self.pair_inputs = []
        self.price_labels = []
        self.ema_labels = []
        self.rsi_labels = []
        self.vol_labels = []
        self.candle_labels = []
        self.info_buttons = []

        for i in range(5):
            pair_input = QLineEdit()
            pair_input.setPlaceholderText("Ej: TRUMPUSDT")

            price_label = QLabel("-")
            ema_label = QPushButton("EMA")
            rsi_label = QPushButton("RSI")
            vol_label = QPushButton("Volumen")
            candle_label = QPushButton("Velón")
            info_button = QPushButton("Info")

            for btn in [ema_label, rsi_label, vol_label, candle_label]:
                btn.setEnabled(False)

            info_button.clicked.connect(lambda _, row=i: self.show_info_popup(row))

            self.pair_inputs.append(pair_input)
            self.price_labels.append(price_label)
            self.ema_labels.append(ema_label)
            self.rsi_labels.append(rsi_label)
            self.vol_labels.append(vol_label)
            self.candle_labels.append(candle_label)
            self.info_buttons.append(info_button)

            grid.addWidget(pair_input, i, 0)
            grid.addWidget(price_label, i, 1)
            grid.addWidget(ema_label, i, 2)
            grid.addWidget(rsi_label, i, 3)
            grid.addWidget(vol_label, i, 4)
            grid.addWidget(candle_label, i, 5)
            grid.addWidget(info_button, i, 6)

        layout.addLayout(grid)

        # Declaración y configuración de widgets de control (añadidos aquí)
        self.interval_combo = QComboBox()
        self.interval_combo.addItems(["15m", "30m", "1h"])

        self.ema_fast_input = QSpinBox()
        self.ema_fast_input.setValue(5)

        self.ema_slow_input = QSpinBox()
        self.ema_slow_input.setValue(15)

        self.scan_time_input = QSpinBox()
        self.scan_time_input.setValue(300)

        self.start_button = QPushButton("Iniciar escaneo")
        self.stop_button = QPushButton("Detener escaneo")

        self.start_button.clicked.connect(self.start_scanning)
        self.stop_button.clicked.connect(self.stop_scanning)

        # Añadir los controles al layout
        layout.addWidget(QLabel("Intervalo:"))
        layout.addWidget(self.interval_combo)
        layout.addWidget(QLabel("EMA rápida:"))
        layout.addWidget(self.ema_fast_input)
        layout.addWidget(QLabel("EMA lenta:"))
        layout.addWidget(self.ema_slow_input)
        layout.addWidget(QLabel("Tiempo de escaneo (segundos):"))
        layout.addWidget(self.scan_time_input)
        layout.addWidget(self.start_button)
        layout.addWidget(self.stop_button)

        self.tab_monitor.setLayout(layout)

        # Guarda los últimos resultados para el popup
        self.last_signals = [{} for _ in range(5)]
        
        

    def init_config_tab(self):
        layout = QVBoxLayout()

        self.api_key_input = QLineEdit()
        self.api_key_input.setEchoMode(QLineEdit.Password)
        self.api_secret_input = QLineEdit()
        self.api_secret_input.setEchoMode(QLineEdit.Password)

        self.telegram_token_input = QLineEdit()
        self.telegram_token_input.setEchoMode(QLineEdit.Password)

        self.telegram_chat_id_input = QLineEdit()
        self.telegram_chat_id_input.setEchoMode(QLineEdit.Password)

        self.smtp_server_input = QLineEdit()
        self.smtp_port_input = QLineEdit()
        self.email_input = QLineEdit()
        self.email_pass_input = QLineEdit()
        self.email_pass_input.setEchoMode(QLineEdit.Password)
        self.email_to_input = QLineEdit()
        self.ntfy_topic_input = QLineEdit()
        
        self.email_checkbox = QCheckBox("Enviar alertas por Email")
        self.telegram_checkbox = QCheckBox("Enviar alertas por Telegram")
        self.ntfy_checkbox = QCheckBox("Enviar alertas por NTFY")

        self.save_config_btn = QPushButton("Guardar configuración")
        self.save_config_btn.clicked.connect(self.save_config)

        layout.addWidget(QLabel("Binance API Key:"))
        layout.addWidget(self.api_key_input)
        layout.addWidget(QLabel("Binance API Secret:"))
        layout.addWidget(self.api_secret_input)
        layout.addWidget(QLabel("Telegram Token:"))
        layout.addWidget(self.telegram_token_input)
        layout.addWidget(QLabel("Telegram Chat ID:"))
        layout.addWidget(self.telegram_chat_id_input)

        layout.addWidget(QLabel("SMTP Server:"))
        layout.addWidget(self.smtp_server_input)
        layout.addWidget(QLabel("SMTP Port:"))
        layout.addWidget(self.smtp_port_input)
        layout.addWidget(QLabel("Email:"))
        layout.addWidget(self.email_input)
        layout.addWidget(QLabel("Contraseña Email:"))
        layout.addWidget(self.email_pass_input)
        layout.addWidget(QLabel("Enviar alertas a:"))
        layout.addWidget(self.email_to_input)
        
        layout.addWidget(QLabel("NTFY Topic:"))
        layout.addWidget(self.ntfy_topic_input)
        
        layout.addWidget(self.email_checkbox)
        layout.addWidget(self.telegram_checkbox)
        layout.addWidget(self.ntfy_checkbox)

        layout.addWidget(self.save_config_btn)
        self.tab_config.setLayout(layout)

    def save_config(self):
        config = {
            "api_key": self.api_key_input.text(),
            "api_secret": self.api_secret_input.text(),
            "telegram_token": self.telegram_token_input.text(),
            "telegram_chat_id": self.telegram_chat_id_input.text(),
            "smtp_server": self.smtp_server_input.text(),
            "smtp_port": self.smtp_port_input.text(),
            "email": self.email_input.text(),
            "email_password": self.email_pass_input.text(),
            "email_to": self.email_to_input.text(),
            "pairs": [inp.text().strip().upper() for inp in self.pair_inputs],
            "interval": self.interval_combo.currentText(),
            "ema_fast": self.ema_fast_input.value(),
            "ema_slow": self.ema_slow_input.value(),
            "scan_time": self.scan_time_input.value(),
            "ntfy_topic": self.ntfy_topic_input.text(),
            "enable_email": self.email_checkbox.isChecked(),
            "enable_telegram": self.telegram_checkbox.isChecked(),
            "enable_ntfy": self.ntfy_checkbox.isChecked()
        }
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=4)
        print("Configuración guardada.")
        try:
            send_telegram_alert("✅ Configuración guardada correctamente desde la interfaz.")
        except Exception as e:
            print("Error al enviar mensaje de prueba a Telegram:", e)
            
        # 🧪 Enviar push de prueba por NTFY
        try:
            send_ntfy_alert(config.get("ntfy_topic", ""), "Configuracion Guardada", "Configuracion guardada desde la interfaz.")
        except Exception as e:
            print("Error al enviar notificación NTFY:", e)    

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
                self.api_key_input.setText(config.get("api_key", ""))
                self.api_secret_input.setText(config.get("api_secret", ""))
                self.telegram_token_input.setText(config.get("telegram_token", ""))
                self.telegram_chat_id_input.setText(config.get("telegram_chat_id", ""))
                self.smtp_server_input.setText(config.get("smtp_server", "smtp.gmail.com"))
                self.smtp_port_input.setText(config.get("smtp_port", "465"))
                self.email_input.setText(config.get("email", ""))
                self.email_pass_input.setText(config.get("email_password", ""))
                self.email_to_input.setText(config.get("email_to", ""))
                self.ntfy_topic_input.setText(config.get("ntfy_topic", ""))
                self.email_checkbox.setChecked(config.get("enable_email", True))
                self.telegram_checkbox.setChecked(config.get("enable_telegram", True))
                self.ntfy_checkbox.setChecked(config.get("enable_ntfy", True))

                pairs = config.get("pairs", [])
                for i, pair in enumerate(pairs):
                    if i < len(self.pair_inputs):
                        self.pair_inputs[i].setText(pair)

                self.interval_combo.setCurrentText(config.get("interval", "15m"))
                self.ema_fast_input.setValue(config.get("ema_fast", 5))
                self.ema_slow_input.setValue(config.get("ema_slow", 15))
                self.scan_time_input.setValue(config.get("scan_time", 300))
                

    def show_info_popup(self, row):
        data = self.last_signals[row]
        if not data:
            QMessageBox.information(self, "Sin datos", "No hay información para este par aún.")
            return

        msg = (
            f"📊 Detalles de {data.get('pair', 'Par desconocido')}\n\n"
            f"Precio actual: {data.get('price')}\n"
            f"EMA rápida: {data.get('ema_fast')}\n"
            f"EMA lenta: {data.get('ema_slow')}\n"
            f"RSI: {data.get('rsi'):.2f}\n"
            f"Volumen: {data.get('volume'):.2f} (Promedio: {data.get('vol_avg'):.2f})\n"
            f"Velón: {'✅' if data.get('big_candle') else '❌'}"
        )

        dlg = QDialog(self)
        dlg.setWindowTitle(f"Detalles: {data.get('pair')}")
        layout = QVBoxLayout()
        txt = QTextEdit(msg)
        txt.setReadOnly(True)
        layout.addWidget(txt)
        dlg.setLayout(layout)
        dlg.exec_()

    
    
    def start_scanning(self):
        if not self.api_key_input.text().strip() or not self.api_secret_input.text().strip():
            QMessageBox.warning(self, "Falta configuración", "Debes introducir la API Key y Secret de Binance.")
            return
        if not any(inp.text().strip() for inp in self.pair_inputs):
            QMessageBox.warning(self, "Sin pares", "Debes ingresar al menos un par de trading.")
            return
        try:
            self.scan()
            interval = self.scan_time_input.value() * 1000
            self.timer.start(interval)
            self.start_button.setStyleSheet("background-color: lightgreen")
            print("Escaneo iniciado.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Ocurrió un error: {str(e)}")
            print(f"Error al iniciar escaneo: {e}")

    def stop_scanning(self):
        self.timer.stop()
        self.start_button.setStyleSheet("")
        print("Escaneo detenido.")

    def scan(self):
        pairs = [inp.text().strip().upper() for inp in self.pair_inputs if inp.text().strip()]
        interval = self.interval_combo.currentText()
        ema_fast = self.ema_fast_input.value()
        ema_slow = self.ema_slow_input.value()

        results = self.scanner.scan(pairs, interval, ema_fast, ema_slow)

        for i, res in enumerate(results):
            if i < len(self.price_labels):
                self.price_labels[i].setText(f"{res.get('price', '-'): .4f} USDT" if res.get("price") else "-")

                self.ema_labels[i].setStyleSheet("background-color: lightgreen" if res.get("cross") else "")
                self.rsi_labels[i].setStyleSheet("background-color: lightgreen" if res.get("rsi_high") else "")
                self.vol_labels[i].setStyleSheet("background-color: lightgreen" if res.get("vol_spike") else "")
                self.candle_labels[i].setStyleSheet("background-color: lightgreen" if res.get("big_candle") else "")

                self.last_signals[i] = res  # guardamos todo para la ventana Info

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainApp()
    window.show()
    sys.exit(app.exec_())
