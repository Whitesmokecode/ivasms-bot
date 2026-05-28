import asyncio
import re
import logging
import aiohttp
from bs4 import BeautifulSoup
from telegram import Bot

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# YOUR CREDENTIALS
TELEGRAM_BOT_TOKEN = "8299925576:AAHeRtYSZ1n4HQk35ZmU9L5qB1wzVHxozfU"
TELEGRAM_GROUP_CHAT_ID = -1003962610348
IVASMS_EMAIL = "fikolamiobileye22@gmail.com"
IVASMS_PASSWORD = "O674674fv#"

bot = Bot(token=TELEGRAM_BOT_TOKEN)
session = None
last_messages = set()

async def login():
    global session
    try:
        session = aiohttp.ClientSession()
        
        # Get login page
        async with session.get("https://ivasms.com/login") as resp:
            html = await resp.text()
            soup = BeautifulSoup(html, 'html.parser')
            csrf = soup.find('input', {'name': '_token'})
            csrf_token = csrf.get('value') if csrf else ""
        
        # Login
        data = {
            'email': IVASMS_EMAIL,
            'password': IVASMS_PASSWORD,
            '_token': csrf_token
        }
        
        async with session.post("https://ivasms.com/login", data=data, allow_redirects=True) as resp:
            if "dashboard" in str(resp.url):
                logger.info("Login successful!")
                await bot.send_message(
                    chat_id=TELEGRAM_GROUP_CHAT_ID,
                    text="✅ IVASMS Bot Connected!\nWaiting for OTPs..."
                )
                return True
            else:
                logger.error("Login failed - wrong credentials")
                return False
    except Exception as e:
        logger.error(f"Login error: {e}")
        return False

async def check_otp():
    global session, last_messages
    try:
        async with session.get("https://ivasms.com/messages") as resp:
            html = await resp.text()
            soup = BeautifulSoup(html, 'html.parser')
            
            rows = soup.find_all('tr')
            for row in rows:
                cols = row.find_all('td')
                if len(cols) >= 2:
                        sender = cols[0].get_text(strip=True)
                        msg = cols[1].get_text(strip=True)
                        time = cols[2].get_text(strip=True) if len(cols) > 2 else ""
                        
                        if sender and msg:
                            msg_id = f"{sender}_{time}"
                            if msg_id not in last_messages:
                                last_messages.add(msg_id)
                                
                                # Find OTP
                                otp_match = re.search(r'\b(\d{4,6})\b', msg)
                                if otp_match:
                                    otp = otp_match.group(1)
                                    text = f"🔐 *NEW OTP*\n📱 From: {sender}\n🔢 Code: `{otp}`\n📝 {msg}"
                                else:
                                    text = f"📨 *New SMS*\n📱 From: {sender}\n📝 {msg}"
                                
                                await bot.send_message(
                                    chat_id=TELEGRAM_GROUP_CHAT_ID,
                                    text=text,
                                    parse_mode='Markdown'
                                )
                                logger.info(f"Sent: {sender} - {otp if otp_match else 'no OTP'}")
    except Exception as e:
        logger.error(f"Check error: {e}")

async def main():
    global session
    if await login():
        while True:
            try:
                await check_otp()
                await asyncio.sleep(5)
            except Exception as e:
                logger.error(f"Loop error: {e}")
                await asyncio.sleep(10)
                # Try to re-login
                await login()
    else:
        await bot.send_message(
            chat_id=TELEGRAM_GROUP_CHAT_ID,
            text="❌ Login failed! Check your IVASMS credentials."
        )

if __name__ == "__main__":
    asyncio.run(main())
