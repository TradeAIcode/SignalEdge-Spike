import json
import smtplib
from email.mime.text import MIMEText
import requests

CONFIG_FILE = "config.json"

def load_config():
    with open(CONFIG_FILE, "r") as f:
        return json.load(f)

def send_telegram_alert(message):
    try:
        config = load_config()
        token = config.get("telegram_token")
        chat_id = config.get("telegram_chat_id")
        if token and chat_id:
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            data = {"chat_id": chat_id, "text": message}
            response = requests.post(url, data=data)
            if response.status_code == 200:
                print("✅ Telegram enviado.")
            else:
                print(f"⚠️ Error Telegram: {response.status_code} - {response.text}")
        else:
            print("⚠️ Telegram no configurado.")
    except Exception as e:
        print("❌ Error en Telegram:", e)

def send_email_alert(subject, message):
    try:
        config = load_config()
        smtp_server = config.get("smtp_server")
        smtp_port = config.get("smtp_port")
        email = config.get("email")
        password = config.get("email_password")
        to_email = config.get("email_to")

        if all([smtp_server, smtp_port, email, password, to_email]):
            msg = MIMEText(message)
            msg["Subject"] = subject
            msg["From"] = email
            msg["To"] = to_email
            with smtplib.SMTP_SSL(smtp_server, int(smtp_port)) as server:
                server.login(email, password)
                server.sendmail(email, to_email, msg.as_string())
            print("✅ Correo enviado.")
        else:
            print("⚠️ Faltan datos de configuración de correo.")
    except Exception as e:
        print("❌ Error en correo:", e)

def send_ntfy_alert(topic, title, message):
    try:
        if not topic:
            print("⚠️ Topic NTFY no especificado.")
            return
        url = f"https://ntfy.sh/{topic}"
        headers = {"Title": title}
        response = requests.post(url, data=message.encode("utf-8"), headers=headers)
        if response.status_code == 200:
            print(f"✅ NTFY enviado a '{topic}'.")
        else:
            print(f"⚠️ Error NTFY: {response.status_code} - {response.text}")
    except Exception as e:
        print("❌ Error al enviar notificación NTFY:", e)
