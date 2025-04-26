from binance.client import Client
import pandas as pd
from ta.trend import EMAIndicator
from ta.momentum import RSIIndicator
import json
from alerts import send_email_alert, send_telegram_alert, send_ntfy_alert

CONFIG_FILE = "config.json"


class AlertStateTracker:
    def __init__(self):
        self.last_alerts = {}  # {'TRUMPUSDT': 3, 'GALAUSDT': 2, ...}

    def should_send_alert(self, pair, current_score):
        last = self.last_alerts.get(pair)
        if last != current_score and current_score >= 3:
            self.last_alerts[pair] = current_score
            return True
        return False


class Scanner:
    def __init__(self):
        self.client = self.load_binance_client()
        self.alert_tracker = AlertStateTracker()

    def load_binance_client(self):
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
        return Client(config["api_key"], config["api_secret"])

    def scan(self, pairs, interval, ema_fast, ema_slow):
        results = []
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)

        for pair in pairs:
            print(f"🔍 Buscando señales en {pair}...")
            try:
                klines = self.client.futures_klines(symbol=pair, interval=interval, limit=50)
                df = pd.DataFrame(klines, columns=[
                    'timestamp', 'open', 'high', 'low', 'close', 'volume',
                    'close_time', 'quote_asset_volume', 'num_trades',
                    'taker_buy_base_volume', 'taker_buy_quote_volume', 'ignore'
                ])
                df['close'] = df['close'].astype(float)
                df['open'] = df['open'].astype(float)
                df['volume'] = df['volume'].astype(float)

                df['ema_fast'] = EMAIndicator(df['close'], window=ema_fast).ema_indicator()
                df['ema_slow'] = EMAIndicator(df['close'], window=ema_slow).ema_indicator()
                df['rsi'] = RSIIndicator(df['close'], window=6).rsi()

                #cross = (df['ema_fast'].iloc[-1] > df['ema_slow'].iloc[-1]) and (df['ema_fast'].iloc[-2] <= df['ema_slow'].iloc[-2])
                cross = df['ema_fast'].iloc[-1] > df['ema_slow'].iloc[-1]
                rsi_high = df['rsi'].iloc[-1] > 70
                vol_avg = df['volume'][:-1].mean()
                vol_spike = df['volume'].iloc[-1] > vol_avg * 3
                candle_size = abs(df['close'].iloc[-1] - df['open'].iloc[-1])
                body_avg = abs(df['close'] - df['open']).mean()
                big_candle = candle_size > body_avg * 2

                current_price = df['close'].iloc[-1]
                print(f"📈 Precio actual: {current_price:.4f} USDT")
                print(f"📊 EMA: {cross} | RSI>70: {rsi_high} | Volumen x3: {vol_spike} | Velón: {big_candle}")

                conditions_met = []
                if cross: conditions_met.append("EMA")
                if rsi_high: conditions_met.append("RSI")
                if vol_spike: conditions_met.append("Volumen")
                if big_candle: conditions_met.append("Velón")
                true_conditions = len(conditions_met)

                if self.alert_tracker.should_send_alert(pair, true_conditions):
                    if true_conditions == 4:
                        print(f"🔥 SEÑAL COMPLETA en {pair}!")
                        message = (
                            f"🔥 Señal completa en {pair}!\n"
                            f"💰 Precio: {current_price:.4f} USDT\n"
                            f"Condiciones cumplidas: EMA, RSI, Volumen, Velón"
                        )
                        send_email_alert("🔥 Señal de Trading Detectada", message)
                        send_telegram_alert(message)
                        send_ntfy_alert(config.get("ntfy_topic", ""), "Señal Completa", message)
                    else:
                        print(f"⚠️ ALERTA PARCIAL: {true_conditions}/4 condiciones en {pair}")
                        message = (
                            f"📢 Señal parcial en {pair}\n"
                            f"💰 Precio: {current_price:.4f} USDT\n"
                            f"✅ Condiciones: {', '.join(conditions_met)}"
                        )
                        send_email_alert("📈 Posible Spike Detectado", message)
                        send_telegram_alert(message)
                        send_ntfy_alert(config.get("ntfy_topic", ""), "Spike Potencial", message)

                results.append({
                    "pair": pair,
                    "price": current_price,
                    "cross": cross,
                    "rsi_high": rsi_high,
                    "vol_spike": vol_spike,
                    "big_candle": big_candle,
                    "rsi": df['rsi'].iloc[-1],
                    "ema_fast": df['ema_fast'].iloc[-1],
                    "ema_slow": df['ema_slow'].iloc[-1],
                    "volume": df['volume'].iloc[-1],
                    "vol_avg": vol_avg
                })

            except Exception as e:
                print(f"❌ Error al procesar {pair}: {e}")
                results.append({
                    "pair": pair,
                    "price": None,
                    "cross": False,
                    "rsi_high": False,
                    "vol_spike": False,
                    "big_candle": False,
                    "rsi": 0,
                    "ema_fast": 0,
                    "ema_slow": 0,
                    "volume": 0,
                    "vol_avg": 0
                })

        print("✅ Escaneo completado.\n")
        return results





