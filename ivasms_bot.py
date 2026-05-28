import asyncio
import re
import logging
from datetime import datetime
import aiohttp
from bs4 import BeautifulSoup
from telegram import Bot

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# YOUR TELEGRAM CREDENTIALS
TELEGRAM_BOT_TOKEN = "8299925576:AAHeRtYSZ1n4HQk35ZmU9L5qB1wzVHxozfU"
TELEGRAM_GROUP_CHAT_ID = -1003962610348

# YOUR COOKIES FROM BROWSER
COOKIES = {
    "cf_clearance": "UeSnF6ZTJlcDIs6qTN0IURJb7jndSiv8_2nk1aV1S2k-1779931963-1.2.1.1-e5WWgu5hCay2B0FrlgLxUGxxVFQiJp0MAKaloPYtmE_t7SDHPvEEoH6Fy3I6Fe9GZ_Y5tvKWuu.a5e9uEmm4MSql4645cuuiHWsT4LkmEiNgNEhYh7elYJSYfIxtSeI801RowfXsMy3nPQvCqU8cTiYQSh1I3KA7.t9futYnC5hrrvTFVAMnoLql84fUsfOW7AK_fTdxJ0skgiPgSqGKnO4YMsaZiWqN9DjShKTo8z.DoJyBD63OYf_zK4q5yHME47wawsz3RrBf5h6dhoTcu9.R.TE_scMaW5nv_c8KKlO.uMtICBSTIoVasoU0VQJPs6kuKmieeXL_jO986dE.bctcCI6wLzEYxF2x9X.aSZvtYaXaAxN1BwtQTmhSMfvHR7JwIq8U0wRDzmpvmUs6PlTOweEziVQYVJz710tn.jk",
    "XSRF-TOKEN": "eyJpdiI6IkwzTzZmSTh6TENweG5PMER1UjdRU2c9PSIsInZhbHVlIjoiZGRYWloyR29JU3dBemlFUGRnb0FvajVXdnh4aVJZT1lGanZDOEVsQ1hrcStSRmwyWWcvcDhiMVREOGJnbFRQR0VHNEFuTVljb3g3VHYrT2FTN3Q1WTA4aEx4OFBFM2Fpdk1KUW4vL01PZUtWVzJGbytqaS9iSXY4dVp2OU9EdUQiLCJtYWMiOiI5NDBhZThmNjMyYjA5M2FjYWVjYmQyNzFmMWY2ZWZlOTc1Mjg0YTc5MmU0ZjViMjA1YjBhYjQ1YWZmYzhiOTc1IiwidGFnIjoiIn0%3D",
    "ivas_sms_session": "eyJpdiI6InZNdUg5eVBIVzBSUGZuWUhBVkhVYnc9PSIsInZhbHVlIjoiMzZkN3BEQzNJYncySE02UlBQanZQTUk3ekExQkZvZ2xaeFFGaE1GUGVqcWdXd0k5TFdMd0NQc0dKaU1HOWllVVBMYjcvS3B0allmdUcvb0ZxUkY3bks1YjBlQVJnUzJYZms2TFlaVnd6cjQxZWxWNmQzWHJzSFUzRG9Uc0k2Z28iLCJtYWMiOiI1MWFkNTRkZGNmOTRjYjUxZDg2MWNkM2IwYjQwNzY0YWY0OTQ4YTk0YmEzM2M0MWQ0NjE2OGVkZjI5MmI3YTI3IiwidGFnIjoiIn0%3D"
}

bot = Bot(token=TELEGRAM_BOT_TOKEN)
session = None
last_messages = set()

async def create_session():
    global session
    # Create cookie jar and add cookies
    cookie_jar = aiohttp.CookieJar()
    for name, value in COOKIES.items():
        cookie_jar.update_cookies({name: value})
    
    session = aiohttp.ClientSession(cookie_jar=cookie_jar)
    return session

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
