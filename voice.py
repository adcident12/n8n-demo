import speech_recognition as sr
from gtts import gTTS
from playsound import playsound
import tempfile
import os
import requests
import time
import threading
import logging
from typing import Optional, Dict, Any
import json
import uuid

# ตั้งค่า logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class VoiceAssistant:
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url
        self.activated = False
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.session = requests.Session()  # ใช้ session เพื่อประสิทธิภาพที่ดีขึ้น
        self.temp_files = []  # เก็บไฟล์ temp เพื่อลบในภายหลัง
        self.session_id = str(uuid.uuid4())  # สร้าง unique session ID
        
        # ตั้งค่า microphone
        self._setup_microphone()
        
        # คำสั่งควบคุม
        self.activation_phrases = ["สวัสดีบอท", "เฮลโล่บอท", "บอทฟัง"]
        self.deactivation_phrases = ["ปิดการทำงาน", "หยุดฟัง", "บอทหยุด"]
        self.exit_phrases = ["ปิดระบบ", "ออกจากระบบ", "บายบอท"]
        
    def _setup_microphone(self):
        """ตั้งค่าไมโครโฟน"""
        try:
            with self.microphone as source:
                logger.info("🎙️ กำลังปรับตั้งไมโครโฟน...")
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
                logger.info("✅ ตั้งค่าไมโครโฟนเสร็จสิ้น")
        except Exception as e:
            logger.error(f"❌ ไม่สามารถตั้งค่าไมโครโฟนได้: {e}")
            
    def speak(self, text: str, lang: str = 'th') -> bool:
        """แปลงข้อความเป็นเสียงพูด"""
        try:
            print(f"🗣️ BOT: {text}")
            logger.info(f"Speaking: {text}")
            
            # สร้างไฟล์เสียง
            tts = gTTS(text=text, lang=lang, slow=False)
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
                temp_filename = fp.name
                tts.save(temp_filename)
                self.temp_files.append(temp_filename)
            
            # เล่นเสียง
            playsound(temp_filename)
            
            # ลบไฟล์ temp (ใน thread แยก)
            threading.Thread(target=self._cleanup_temp_file, args=(temp_filename,), daemon=True).start()
            
            return True
            
        except Exception as e:
            logger.error(f"❌ เกิดข้อผิดพลาดในการพูด: {e}")
            print(f"❌ ไม่สามารถพูดได้: {e}")
            return False
    
    def _cleanup_temp_file(self, filename: str):
        """ลบไฟล์ temp หลังเล่นเสียงเสร็จ"""
        try:
            time.sleep(0.5)  # รอให้เล่นเสียงเสร็จ
            if os.path.exists(filename):
                os.remove(filename)
                if filename in self.temp_files:
                    self.temp_files.remove(filename)
        except Exception as e:
            logger.error(f"ไม่สามารถลบไฟล์ temp: {e}")
    
    def listen(self, timeout: int = 5, phrase_time_limit: int = 10) -> str:
        """ฟังเสียงและแปลงเป็นข้อความ"""
        try:
            with self.microphone as source:
                if not self.activated:
                    print("🕓 รอฟังคำสั่งเปิดใช้งาน...")
                else:
                    print("🎤 กำลังฟัง...")
                    
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
            if self.activated:
                logger.debug("Timeout - ไม่มีเสียงพูด")
            return ""
        except sr.UnknownValueError:
            if self.activated:
                print("😕 ไม่เข้าใจเสียงพูด")
                logger.warning("ไม่สามารถรับรู้เสียงพูดได้")
            return ""
        except sr.RequestError as e:
            logger.error(f"🚨 ไม่สามารถเชื่อมต่อบริการ: {e}")
            print(f"🚨 ไม่สามารถเชื่อมต่อบริการ: {e}")
            return ""
        except Exception as e:
            logger.error(f"เกิดข้อผิดพลาดในการฟัง: {e}")
            return ""
    
    def send_to_ai(self, text: str, timeout: int = 30) -> str:
        """ส่งข้อความไปยัง AI และรับคำตอบ"""
        try:
            logger.info(f"Sending to AI: {text}")
            
            # เพิ่ม headers
            headers = {
                'Content-Type': 'application/json',
                'User-Agent': 'VoiceAssistant/1.0'
            }
            
            payload = {
                "text": text,
                "session_id": self.session_id,
                "timestamp": time.time(),
                "language": "th"
            }
            
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
                if "reply" in result:
                    return result["reply"]
                elif "response" in result:
                    return result["response"]
                elif "message" in result:
                    return result["message"]
                else:
                    return str(result)
            elif isinstance(result, str):
                return result
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
        """ตรวจสอบคำสั่งควบคุม"""
        text_lower = text.lower()
        
        # ตรวจสอบคำสั่งเปิดใช้งาน
        for phrase in self.activation_phrases:
            if phrase.lower() in text_lower:
                return "activate"
        
        # ตรวจสอบคำสั่งหยุดชั่วคราว
        for phrase in self.deactivation_phrases:
            if phrase.lower() in text_lower:
                return "deactivate"
        
        # ตรวจสอบคำสั่งออกจากระบบ
        for phrase in self.exit_phrases:
            if phrase.lower() in text_lower:
                return "exit"
        
        return None
    
    def cleanup(self):
        """ทำความสะอาดทรัพยากร"""
        logger.info("กำลังทำความสะอาดทรัพยากร...")
        
        # ปิด session
        self.session.close()
        
        # ลบไฟล์ temp ที่เหลือ
        for temp_file in self.temp_files:
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
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
                    self.speak("โปรดรอสักครู่ ระบบกำลังประมวลผลคำสั่งของคุณ")
                    logger.info(f"➡️ ส่งไปยัง AI: {text} (Session: {self.session_id})")
                    
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
    WEBHOOK_URL = "" # กำหนด URL ของ Webhook จาก n8n ที่นี่
    
    # ตรวจสอบว่า URL ถูกต้อง
    if not WEBHOOK_URL.startswith(('http://', 'https://')):
        logger.error("WEBHOOK_URL ไม่ถูกต้อง")
        print("❌ กรุณาตั้งค่า WEBHOOK_URL ให้ถูกต้อง")
        return
    
    # สร้างและเริ่มต้น Voice Assistant
    assistant = VoiceAssistant(WEBHOOK_URL)
    assistant.run()

if __name__ == "__main__":
    main()