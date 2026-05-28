import os
import requests
import time
import re
from bs4 import BeautifulSoup

# Telegram credentials
BOT_TOKEN = "8299925576:AAHeRtYSZ1n4HQk35ZmU9L5qB1wzVHxozfU"
CHAT_ID = "-1003962610348"

# WolfSMS credentials
WOLF_URL = "http://213.32.24.208/ints/agent/SMSDashboard"
WOLF_USER = "Victor"
WOLF_PASS = "212009"

session = requests.Session()
last_otps = set()

def send_telegram(text):
    """Send message to Telegram group"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try:
        requests.post(url, json={
            'chat_id': CHAT_ID, 
            'text': text,
            'parse_mode': 'Markdown'
        })
    except Exception as e:
        print(f"Telegram error: {e}")

def login_wolf():
    """Login to WolfSMS dashboard"""
    try:
        # Try different login endpoints
        login_endpoints = [
            f"{WOLF_URL}/login",
            f"{WOLF_URL}/api/login",
            f"{WOLF_URL}/auth/login"
        ]
        
        for endpoint in login_endpoints:
            try:
                response = session.post(endpoint, data={
                    'username': WOLF_USER,
                    'password': WOLF_PASS
                }, timeout=10)
                
                if response.status_code == 200 and 'dashboard' in response.text.lower():
                    print(f"Logged in via {endpoint}")
                    return True
            except:
                continue
        
        # Try simple GET with auth
        response = session.get(WOLF_URL, timeout=10)
        if response.status_code == 200:
            print("Connected without explicit login")
            return True
            
        return False
    except Exception as e:
        print(f"Login error: {e}")
        return False

def get_messages():
    """Fetch messages from WolfSMS"""
    messages = []
    try:
        # Try different message endpoints
        msg_endpoints = [
            f"{WOLF_URL}/messages",
            f"{WOLF_URL}/api/messages",
            f"{WOLF_URL}/get_messages",
            f"{WOLF_URL}/sms"
        ]
        
        for endpoint in msg_endpoints:
            try:
                response = session.get(endpoint, timeout=10)
                if response.status_code == 200:
                    html = response.text
                    
                    # Parse HTML for messages
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Look for tables containing messages
                    tables = soup.find_all('table')
                    for table in tables:
                        rows = table.find_all('tr')
                        for row in rows:
                            cols = row.find_all('td')
                            if len(cols) >= 2:
                                sender = cols[0].get_text(strip=True)
                                message = cols[1].get_text(strip=True)
                                if sender and message and len(message) > 2:
                                    otp = re.search(r'\b\d{4,6}\b', message)
                                    messages.append({
                                        'sender': sender,
                                        'message': message,
                                        'otp': otp.group(0) if otp else None
                                    })
                    
                    # Also try JSON response
                    if not messages and html.strip().startswith('['):
                        try:
                            import json
                            data = json.loads(html)
                            for item in data:
                                sender = item.get('sender') or item.get('from') or item.get('number')
                                message = item.get('message') or item.get('text') or item.get('body')
                                if sender and message:
                                    otp = re.search(r'\b\d{4,6}\b', message)
                                    messages.append({
                                        'sender': sender,
                                        'message': message,
                                        'otp': otp.group(0) if otp else None
                                    })
                        except:
                            pass
                    
                    if messages:
                        return messages
            except:
                continue
        
        return messages
    except Exception as e:
        print(f"Get messages error: {e}")
        return []

def main():
    print("🟢 Starting WolfSMS Bot on Railway...")
    
    # Send startup message
    send_telegram("✅ *WolfSMS Bot Connected!*\n\n📱 Panel: WolfSMS Test Account\n👤 User: Victor\n⏱️ Monitoring OTPs...\n\n_Will forward any OTPs received_", "Markdown")
    
    # Login to WolfSMS
    if login_wolf():
        print("✅ Logged into WolfSMS")
        send_telegram("✅ Successfully connected to WolfSMS dashboard")
    else:
        print("⚠️ Login may not be needed - will try to fetch messages directly")
    
    # Main monitoring loop
    while True:
        try:
            messages = get_messages()
            
            for msg in messages:
                msg_id = f"{msg['sender']}_{msg['message'][:30]}"
                if msg_id not in last_otps:
                    last_otps.add(msg_id)
                    
                    if msg['otp']:
                        text = f"🔐 *NEW OTP from WolfSMS*\n\n📱 Sender: `{msg['sender']}`\n🔢 OTP Code: `{msg['otp']}`\n💬 Message: {msg['message']}"
                    else:
                        text = f"📨 *New SMS from WolfSMS*\n\n📱 Sender: `{msg['sender']}`\n💬 {msg['message']}"
                    
                    send_telegram(text)
                    print(f"Forwarded: {msg['sender']} - OTP: {msg['otp']}")
            
            # Keep last 100 messages in memory
            if len(last_otps) > 100:
                last_otps = set(list(last_otps)[-100:])
            
            time.sleep(5)  # Check every 5 seconds
            
        except Exception as e:
            print(f"Loop error: {e}")
            time.sleep(10)

if __name__ == "__main__":
    main()async def check_otp():
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
                    time = cols[2].get_text(strip=True) if len(cols) > 2 else datetime.now().strftime("%H:%M:%S")
                    
                    if sender and msg:
                        msg_id = f"{sender}_{time}"
                        if msg_id not in last_messages:
                            last_messages.add(msg_id)
                            
                            otp_match = re.search(r'\b(\d{4,6})\b', msg)
                            if otp_match:
                                otp = otp_match.group(1)
                                text = f"🔐 *NEW OTP*\n📱 From: {sender}\n🔢 Code: `{otp}`\n📝 {msg}\n🕐 {time}"
                            else:
                                text = f"📨 *New SMS*\n📱 From: {sender}\n📝 {msg}\n🕐 {time}"
                            
                            await bot.send_message(
                                chat_id=TELEGRAM_GROUP_CHAT_ID,
                                text=text,
                                parse_mode='Markdown'
                            )
                            logger.info(f"Sent: {sender} - OTP: {otp if otp_match else 'No OTP'}")
    except Exception as e:
        logger.error(f"Check error: {e}")

async def main():
    global session
    await create_session()
    
    # Test if cookies work
    try:
        async with session.get("https://ivasms.com/dashboard") as resp:
            html = await resp.text()
            if "login" not in html.lower() and "dashboard" in html.lower():
                await bot.send_message(
                    chat_id=TELEGRAM_GROUP_CHAT_ID,
                    text="✅ IVASMS Bot Connected with Cookies!\n🍪 Cloudflare bypassed successfully!\n⏱️ Waiting for OTPs..."
                )
                logger.info("Cookie authentication successful!")
            else:
                await bot.send_message(
                    chat_id=TELEGRAM_GROUP_CHAT_ID,
                    text="❌ Cookies expired or invalid. Need fresh cookies."
                )
                return
    except Exception as e:
        await bot.send_message(
            chat_id=TELEGRAM_GROUP_CHAT_ID,
            text=f"❌ Connection error: {str(e)[:100]}"
        )
        return
    
    # Main monitoring loop
    while True:
        try:
            await check_otp()
            await asyncio.sleep(5)
        except Exception as e:
            logger.error(f"Loop error: {e}")
            await asyncio.sleep(10)

if __name__ == "__main__":
    asyncio.run(main())            '_token': csrf_token
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
