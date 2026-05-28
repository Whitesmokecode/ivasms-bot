import asyncio
import re
import logging
import os
import threading
from datetime import datetime
from typing import Dict, List, Optional
import aiohttp
from bs4 import BeautifulSoup
from telegram import Bot
from flask import Flask

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

flask_app = Flask('')

@flask_app.route('/')
def home():
    return "IVASMS Bot is running!"

def run_flask():
    flask_app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

threading.Thread(target=run_flask, daemon=True).start()

# ========== YOUR CREDENTIALS (HARDCODED) ==========
TELEGRAM_BOT_TOKEN = "8299925576:AAHeRtYSZ1n4HQk35ZmU9L5qB1wzVHxozfU"
TELEGRAM_GROUP_CHAT_ID = -1003962610348
IVASMS_EMAIL = "fikolamiobileye22@gmail.com"
IVASMS_PASSWORD = "O674674fv#"
CHECK_INTERVAL = 3
# ==================================================

class IVASMSBridge:
    def __init__(self):
        self.session = None
        self.last_messages = {}
        self.bot = Bot(token=TELEGRAM_BOT_TOKEN)
        self.is_logged_in = False
        
    async def create_session(self):
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        self.session = aiohttp.ClientSession(headers=headers)
    
    async def login(self) -> bool:
        try:
            await self.create_session()
            async with self.session.get("https://ivasms.com/login", ssl=False) as response:
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                csrf_token = None
                token_input = soup.find('input', {'name': '_token'})
                if token_input:
                    csrf_token = token_input.get('value')
                if not csrf_token:
                    return False
            
            login_data = {'email': IVASMS_EMAIL, 'password': IVASMS_PASSWORD, '_token': csrf_token}
            async with self.session.post("https://ivasms.com/login", data=login_data, ssl=False, allow_redirects=True) as response:
                if "dashboard" in response.url.path:
                    self.is_logged_in = True
                    await self.bot.send_message(chat_id=TELEGRAM_GROUP_CHAT_ID, 
                        text=f"🟢 IVASMS Bot Connected\n📧 Account: {IVASMS_EMAIL}\n⏱️ Checking every {CHECK_INTERVAL} seconds",
                        parse_mode='Markdown')
                    return True
            return False
        except Exception as e:
            logger.error(f"Login error: {e}")
            return False
    
    async def get_messages(self):
        if not self.is_logged_in:
            return []
        try:
            async with self.session.get("https://ivasms.com/messages", ssl=False) as response:
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                messages = []
                rows = soup.find_all('tr')
                for row in rows:
                    cols = row.find_all('td')
                    if len(cols) >= 2:
                        sender = cols[0].get_text(strip=True)
                        msg_text = cols[1].get_text(strip=True)
                        time = cols[2].get_text(strip=True) if len(cols) > 2 else ""
                        otp_match = re.search(r'\b(\d{4,6})\b', msg_text)
                        otp = otp_match.group(1) if otp_match else None
                        if sender and msg_text:
                            messages.append({
                                'sender': sender,
                                'message': msg_text,
                                'otp': otp,
                                'time': time,
                                'full_text': f"🔐 NEW OTP\n\n📱 From: {sender}\n🔢 OTP: {otp}\n📝 {msg_text}\n🕐 {time}\n\n👉 {otp} 👈"
                            })
                return messages
        except Exception as e:
            return []
    
    async def check_and_forward(self):
        while True:
            try:
                if not self.is_logged_in:
                    await self.login()
                messages = await self.get_messages()
                for msg in messages:
                    msg_id = f"{msg['sender']}_{msg['time']}"
                    if msg_id not in self.last_messages:
                        self.last_messages[msg_id] = msg['full_text']
                        await self.bot.send_message(chat_id=TELEGRAM_GROUP_CHAT_ID, text=msg['full_text'], parse_mode='Markdown')
                        logger.info(f"Forwarded OTP from {msg['sender']}")
                await asyncio.sleep(CHECK_INTERVAL)
            except Exception as e:
                logger.error(f"Error: {e}")
                await asyncio.sleep(10)

async def main():
    bridge = IVASMSBridge()
    await bridge.check_and_forward()

if __name__ == "__main__":
    asyncio.run(main())