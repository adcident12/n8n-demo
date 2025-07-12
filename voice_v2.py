import speech_recognition as sr
from gtts import gTTS
from playsound import playsound
import tempfile
import os
import requests
from requests.adapters import HTTPAdapter, Retry
import time
import threading
import logging
from typing import Optional, Dict, Any
import json
import uuid
import functools
import weakref

# ตั้งค่า logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_webhook_url() -> str:
    """โหลด Webhook URL จาก environment variable หรือไฟล์ .env"""
    url = os.environ.get("WEBHOOK_URL_VOICE")
    if url:
        return url
    # รองรับ .env แบบง่าย
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.exists(env_path):
        with open(env_path, encoding="utf-8") as f:
            for line in f:
                if line.strip().startswith("WEBHOOK_URL_VOICE="):
                    return line.strip().split("=", 1)[1]
    # fallback: ใช้ค่า default (ถ้ามี)
    return "https://a611-27-55-89-186.ngrok-free.app/webhook/dd446900-af8a-4726-abc6-033a0db60b10"

class VoiceAssistant:
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url
        self.activated = False
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.session = requests.Session()  # ใช้ session เพื่อประสิทธิภาพที่ดีขึ้น
        self.temp_files = []  # เก็บไฟล์ temp เพื่อลบในภายหลัง
        self.session_id = str(uuid.uuid4())  # สร้าง unique session ID
        
        # ตั้งค่า session และ retry mechanism
        retries = Retry(total=3, backoff_factor=0.1, status_forcelist=[500, 502, 503, 504])
        self.session.mount('http://', HTTPAdapter(max_retries=retries))
        self.session.mount('https://', HTTPAdapter(max_retries=retries))
        
        # Cache สำหรับเสียงที่แปลงแล้ว
        self._speech_cache = {}  # ใช้ dict ปกติแทน weakref
        
        # ใช้ threading.Lock สำหรับ thread safety
        self._lock = threading.Lock()
        
        # ตั้งค่า microphone
        self._setup_microphone()
        
        # คำสั่งควบคุม
        self.control_phrases = {
            "activate": ["สวัสดีบอท", "เฮลโล่บอท", "บอทฟัง"],
            "deactivate": ["ปิดการทำงาน", "หยุดฟัง", "บอทหยุด"],
            "exit": ["ปิดระบบ", "ออกจากระบบ", "บายบอท"]
        }
        
    def _setup_microphone(self):
        """ตั้งค่าไมโครโฟน"""
        try:
            with self.microphone as source:
                logger.info("🎙️ กำลังปรับตั้งไมโครโฟน...")
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
                logger.info("✅ ตั้งค่าไมโครโฟนเสร็จสิ้น")
        except Exception as e:
            logger.error(f"❌ ไม่สามารถตั้งค่าไมโครโฟนได้: {e}")
            
    @functools.lru_cache(maxsize=128)
    def _generate_speech_file(self, text: str, lang: str) -> str:
        """สร้างไฟล์เสียงแบบ cache"""
        tts = gTTS(text=text, lang=lang, slow=False)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
            temp_filename = fp.name
            tts.save(temp_filename)
            return temp_filename

    def speak(self, text: str, lang: str = 'th') -> bool:
        """แปลงข้อความเป็นเสียงพูด"""
        try:
            print(f"🗣️ BOT: {text}")
            logger.info(f"Speaking: {text}")
            
            # ใช้ cache ถ้ามีข้อความเดิม
            cache_key = f"{text}_{lang}"
            temp_filename = self._speech_cache.get(cache_key)
            
            if not temp_filename or not os.path.exists(temp_filename):
                temp_filename = self._generate_speech_file(text, lang)
                self._speech_cache[cache_key] = temp_filename
                self.temp_files.append(temp_filename)
            
            playsound(temp_filename)
            return True
            
        except Exception as e:
            logger.error(f"❌ เกิดข้อผิดพลาดในการพูด: {e}")
            return False

    def _cleanup_temp_file(self, filename: str):
        """ลบไฟล์ temp แบบปลอดภัย"""
        try:
            with self._lock:
                if os.path.exists(filename):
                    os.remove(filename)
                    if filename in self.temp_files:
                        self.temp_files.remove(filename)
        except Exception as e:
            logger.error(f"ไม่สามารถลบไฟล์ temp: {e}")

    def listen(self, timeout: int = 5, phrase_time_limit: int = 10, max_retry: int = 2) -> str:
        """ฟังเสียงและแปลงเป็นข้อความ พร้อม retry และแจ้งเตือนสถานะ"""
        already_prompted = False
        for attempt in range(max_retry + 1):
            try:
                with self.microphone as source:
                    if not self.activated:
                        print("🕓 รอฟังคำสั่งเปิดใช้งาน...")
                        if not already_prompted:
                            self.speak("กรุณาพูดคำสั่งเพื่อเริ่มต้น", lang="th")
                            already_prompted = True
                    else:
                        print("🎤 กำลังฟัง...")
                        if not already_prompted:
                            self.speak("กรุณาพูดคำสั่งของคุณ", lang="th")
                            already_prompted = True
                    audio = self.recognizer.listen(
                        source,
                        timeout=timeout,
                        phrase_time_limit=phrase_time_limit
                    )
                # แปลงเสียงเป็นข้อความ
                text = self.recognizer.recognize_google(audio, language='th-TH')
                logger.info(f"Recognized: {text}")
                print(f"👤 YOU: {text}")
                return text.strip().lower()
            except sr.WaitTimeoutError:
                logger.info("⏳ ไม่ได้ยินเสียงพูดในเวลาที่กำหนด")
                if attempt == max_retry:
                    if self.activated:
                        self.speak("ไม่ได้ยินเสียง กรุณาพูดใหม่อีกครั้ง", lang="th")
                continue
            except sr.UnknownValueError:
                logger.info("😕 ไม่เข้าใจเสียงพูด")
                if attempt == max_retry:
                    self.speak("ขออภัย ไม่เข้าใจเสียงพูด กรุณาพูดใหม่อีกครั้ง", lang="th")
                continue
            except sr.RequestError as e:
                logger.error(f"🚨 ไม่สามารถเชื่อมต่อบริการ: {e}")
                self.speak("ไม่สามารถเชื่อมต่อบริการแปลงเสียง กรุณาตรวจสอบอินเทอร์เน็ต", lang="th")
                return ""
            except Exception as e:
                logger.error(f"เกิดข้อผิดพลาดในการฟัง: {e}")
                if attempt == max_retry:
                    self.speak("เกิดข้อผิดพลาดในการฟัง กรุณาลองใหม่", lang="th")
                continue
        return ""

    def send_to_ai(self, text: str, timeout: int = 30) -> str:
        """ส่งข้อความไปยัง AI พร้อมแจ้งเตือนระหว่างรอและตัดข้อความว่าง"""
        text = text.strip()
        if not text:
            return "ไม่ได้รับข้อความ กรุณาพูดใหม่อีกครั้ง"
        try:
            self.speak("กำลังประมวลผล กรุณารอสักครู่...", lang="th")
            payload = {
                "text": text,
                "session_id": self.session_id,
                "timestamp": time.time(),
                "language": "th"
            }
            headers = {
                'Content-Type': 'application/json',
                'User-Agent': 'VoiceAssistant/1.0',
                'Connection': 'keep-alive'
            }
            with self._lock:
                response = self.session.post(
                    self.webhook_url,
                    json=payload,
                    headers=headers,
                    timeout=timeout
                )
                response.raise_for_status()
            result = response.json()
            logger.info(f"AI Response: {result}")
            # รองรับหลายรูปแบบ response
            if isinstance(result, dict):
                for key in ("reply", "response", "message", "text"):
                    if key in result and result[key]:
                        return str(result[key]).strip()
                return str(result)
            elif isinstance(result, str):
                return result.strip()
            else:
                return "ไม่สามารถประมวลผลข้อมูลที่ได้กลับมา"
        except requests.exceptions.Timeout:
            logger.error("AI request timeout")
            return "ขออภัย ระบบใช้เวลานานเกินไป กรุณาลองใหม่อีกครั้ง"
        except requests.exceptions.ConnectionError:
            logger.error("AI connection error")
            return "ไม่สามารถเชื่อมต่อกับระบบประมวลผลได้ กรุณาตรวจสอบการเชื่อมต่อ"
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP Error: {e}")
            return f"เกิดข้อผิดพลาดจากเซิร์ฟเวอร์: {e}"
        except Exception as e:
            logger.error(f"❌ เกิดข้อผิดพลาดขณะติดต่อ AI: {e}")
            return "เกิดข้อผิดพลาดในการเชื่อมต่อกับระบบประมวลผล"

    def check_control_phrases(self, text: str) -> Optional[str]:
        """ตรวจสอบคำสั่งควบคุมแบบยืดหยุ่น"""
        text_lower = text.lower()
        for action, phrases in self.control_phrases.items():
            for phrase in phrases:
                if phrase.lower() in text_lower:
                    return action
        return None
    
    def cleanup(self):
        """ทำความสะอาดทรัพยากรแบบปลอดภัย"""
        logger.info("กำลังทำความสะอาดทรัพยากร...")
        
        # ล้าง cache
        self._speech_cache.clear()
        self._generate_speech_file.cache_clear()
        
        with self._lock:
            # ปิด session
            self.session.close()
            
            # ลบไฟล์ temp ที่เหลือ
            for temp_file in list(self.temp_files):  # ใช้ list copy เพื่อป้องกัน race condition
                try:
                    if os.path.exists(temp_file):
                        os.remove(temp_file)
                        self.temp_files.remove(temp_file)
                except Exception as e:
                    logger.error(f"ไม่สามารถลบไฟล์ temp: {e}")
        
        logger.info("ทำความสะอาดเสร็จสิ้น")
    
    def run(self):
        """เริ่มต้นระบบ"""
        logger.info("🚀 เริ่มต้นระบบ Voice Assistant")
        logger.info(f"🆔 Session ID: {self.session_id}")
        self.speak("สวัสดีค่ะ ระบบพร้อมทำงาน กรุณาพูด 'สวัสดีบอท' เพื่อเริ่มใช้งาน")
        consecutive_errors = 0
        max_consecutive_errors = 5
        try:
            while True:
                text = self.listen()
                if not text:
                    consecutive_errors += 1
                    if consecutive_errors >= max_consecutive_errors:
                        logger.warning("เกิดข้อผิดพลาดต่อเนื่อง กำลังรีเซ็ตระบบ...")
                        self._setup_microphone()
                        consecutive_errors = 0
                    continue
                consecutive_errors = 0  # รีเซ็ตตัวนับเมื่อฟังได้สำเร็จ
                # ตรวจสอบคำสั่งควบคุม
                control_action = self.check_control_phrases(text)
                if control_action == "activate" and not self.activated:
                    self.activated = True
                    self.speak("พร้อมรับคำสั่งค่ะ")
                    logger.info("ระบบเปิดใช้งาน")
                elif control_action == "deactivate" and self.activated:
                    self.activated = False
                    self.speak("ระบบจะหยุดรับคำสั่งชั่วคราวค่ะ หากต้องการเปิดใช้งานอีกครั้ง ให้พูด 'สวัสดีบอท'")
                    logger.info("ระบบหยุดชั่วคราว")
                elif control_action == "exit":
                    self.speak("ขอบคุณที่ใช้งานค่ะ ระบบจะปิดตัวลงแล้ว")
                    logger.info("ออกจากระบบ")
                    break
                elif self.activated:
                    # ประมวลผลคำสั่งปกติ
                    reply = self.send_to_ai(text)
                    self.speak(reply)
                elif not self.activated:
                    logger.debug("ระบบยังไม่เปิดใช้งาน")
        except KeyboardInterrupt:
            logger.info("ได้รับสัญญาณหยุดจากผู้ใช้")
            self.speak("ระบบจะปิดตัวลงแล้ว")
        except Exception as e:
            logger.error(f"เกิดข้อผิดพลาดในระบบหลัก: {e}")
            self.speak("เกิดข้อผิดพลาดในระบบ กำลังปิดตัวลง")
        finally:
            self.cleanup()

def main():
    """ฟังก์ชันหลัก"""
    WEBHOOK_URL = load_webhook_url()
    
    # สร้างและเริ่มต้น Voice Assistant
    assistant = VoiceAssistant(WEBHOOK_URL)
    assistant.run()

if __name__ == "__main__":
    main()