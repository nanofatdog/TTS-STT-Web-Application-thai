# TTS-STT-Web-Application-thai
เว็บแอปพลิเคชันสำหรับแปลงข้อความเป็นเสียง (TTS) และแปลงเสียงเป็นข้อความ (STT) พร้อมระบบดาวน์โหลดไฟล์เสียง
![image](https://github.com/nanofatdog/TTS-STT-Web-Application-thai/blob/main/images/tts.png)
![image](https://github.com/nanofatdog/TTS-STT-Web-Application-thai/blob/main/images/stt.png)
## คุณสมบัติหลัก
### Text-to-Speech (TTS)
  - สนับสนุนเสียงภาษาไทยและภาษาอังกฤษ
  - ปรับความเร็วเสียงได้
  - แสดงผล waveform กราฟิก
  - ดาวน์โหลดไฟล์เสียงที่สร้าง

### Speech-to-Text (STT)
  - รองรับการแปลงเสียงภาษาไทยและอังกฤษ
  - อัปโหลดไฟล์เสียงหรือบันทึกเสียงโดยตรง
  - ตรวจสอบภาษาแบบอัตโนมัติ

### ความต้องการระบบ
Docker (สำหรับการใช้งานผ่าน container)
หรือ Python 3.9+ (สำหรับการติดตั้งโดยตรง)

## การติดตั้งและใช้งาน
### วิธีที่ 1: ใช้ Docker (แนะนำ)
  1. คลอน repository: 
  ```
  git clone https://github.com/yourusername/tts-stt-app.git
  cd tts-stt-app
  ```
  2. สร้าง Docker image:  
  ```
  docker build -t tts-stt-app .
  ```
  3. รัน Docker container:
  ```
  docker run -d --name tts-app -p 8685:8685 tts-stt-app
  ```
  4. เปิดเบราว์เซอร์ที่:
  ```
  http://localhost:8685    <<<< 0.0.0.0 port 8685
  ```
### วิธีที่ 2: ติดตั้งโดยตรง
  1. ติดตั้ง dependencies: 
  ```
  conda create -n tts-stt-thai python=3.10 -y
  cd TTS-STT-Web-Application-thai
  pip install -r requirements.txt
  ```
  2. รันแอปพลิเคชัน:
  ```
  python app.py
  ```
  3. เปิดเบราว์เซอร์ที่:
  ```
  http://localhost:8685    <<<< 0.0.0.0 port 8685
  ```
### โครงสร้างไฟล์
```
tts-stt-app/
├── app.py               # โค้ดหลักของแอปพลิเคชัน
├── voices.json          # ข้อมูลเสียงที่รองรับ
├── requirements.txt     # รายการ dependencies
├── Dockerfile           # คอนฟิก Docker
└── audio_output/        # ไดเรกทอรีเก็บไฟล์เสียง (สร้างอัตโนมัติ)
```
## ไลบรารีที่ใช้และผู้พัฒนา
โปรแกรมนี้พัฒนาขึ้นโดยใช้ไลบรารีโอเพนซอร์สต่อไปนี้:
- Gradio - สร้างเว็บอินเทอร์เฟซ (พัฒนาโดย Abubakar Abid และทีม)
- edge-tts - ระบบ TTS ของ Microsoft Edge (พัฒนาโดย acheong08)
- SpeechRecognition - ระบบรู้จำเสียงพูด (พัฒนาโดย Anthony Zhang)
- pydub - ประมวลผลไฟล์เสียง (พัฒนาโดย Jiří Otáhal)
- ffmpeg-python - อินเทอร์เฟซ Python สำหรับ FFmpeg (พัฒนาโดย Karl Kroening)
ขอขอบคุณผู้พัฒนาทุกท่านที่สร้างไลบรารีที่มีประโยชน์เหล่านี้

## การพัฒนาต่อ
1. ติดตั้ง dependencies สำหรับการพัฒนา:
   
```
pip install -r requirements-dev.txt
```

2. รันในโหมดพัฒนา:
```
python app.py --dev
```

ใบอนุญาต
โครงการนี้อยู่ภายใต้ใบอนุญาต MIT 
