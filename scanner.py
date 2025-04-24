from binance.client import Client
import pandas as pd
from ta.trend import EMAIndicator
from ta.momentum import RSIIndicator
import json
from alerts import send_email_alert, send_telegram_alert, send_ntfy_alert


CONFIG_FILE = "config.json"

class Scanner:
    def __init__(self):
        self.client = self.load_binance_client()

    def load_binance_client(self):
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
        return Client(config["api_key"], config["api_secret"])

    def scan(self, pairs, interval, ema_fast, ema_slow):
        prices = []
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

                cross = (df['ema_fast'].iloc[-1] > df['ema_slow'].iloc[-1]) and (df['ema_fast'].iloc[-2] <= df['ema_slow'].iloc[-2])
                rsi_high = df['rsi'].iloc[-1] > 70
                vol_avg = df['volume'][:-1].mean()
                vol_spike = df['volume'].iloc[-1] > vol_avg * 3
                candle_size = abs(df['close'].iloc[-1] - df['open'].iloc[-1])
                body_avg = abs(df['close'] - df['open']).mean()
                big_candle = candle_size > body_avg * 2

                current_price = df['close'].iloc[-1]
                prices.append(current_price)

                print(f"📈 Precio actual: {current_price:.4f} USDT")
                print(f"📊 EMA cross: {cross} | RSI>70: {rsi_high} | Volumen x3: {vol_spike} | Velón: {big_candle}")
                
                # 🧪 Fuerza de señal para prueba
                ###cross = rsi_high = vol_spike = big_candle = True

                if cross and rsi_high and vol_spike and big_candle:
                    print(f"⚠️ ALERTA DETECTADA en {pair}!")
                    message = f"⚠️ Alerta en {pair} - RSI: {df['rsi'].iloc[-1]:.2f}"
                    send_email_alert("⚠️ Alerta de Trading Detectada", message)
                    send_telegram_alert(message)
                    send_ntfy_alert(config.get("ntfy_topic", ""), "Alerta de Trading Detectada", message)  # <- SIN emojis en el título

            except Exception as e:
                print(f"❌ Error al procesar {pair}: {e}")
                prices.append(None)

        print("✅ Escaneo completado.\n")
        return prices

