import gradio as gr
import edge_tts
import os
import uuid
import speech_recognition as sr
import tempfile
import subprocess
import wave
import contextlib
import asyncio
from io import BytesIO
import json

# โหลดข้อมูล voices จากไฟล์ JSON
with open('voices.json', 'r', encoding='utf-8') as f:
    VOICES = json.load(f)

async def generate_audio(text: str, voice: str, rate: int, progress=gr.Progress()):
    try:
        progress(0.1, desc="กำลังเริ่มต้น...")

        output_dir = "audio_output"
        os.makedirs(output_dir, exist_ok=True)

        task_id = str(uuid.uuid4())
        output_file = os.path.join(output_dir, f"{task_id}.wav")

        if int(rate) > 0:
            rate_str = f"+{rate}%"
        elif int(rate) < 0:
            rate_str = f"{rate}%"
        else:
            rate_str = None

        progress(0.3, desc="กำลังสร้างเสียง...")

        communicate = edge_tts.Communicate(text, voice, rate=rate_str) if rate_str else edge_tts.Communicate(text, voice)

        progress(0.6, desc="กำลังบันทึกไฟล์เสียง...")

        await communicate.save(output_file)

        if not os.path.exists(output_file):
            raise Exception("ไฟล์เสียงไม่ถูกสร้าง")

        progress(1.0, desc="สร้างเสียงสำเร็จ!")

        return output_file, None

    except Exception as e:
        return None, str(e)

def speech_to_text(audio_file, language: str):
    try:
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as wav_tmp:
            wav_tmp_path = wav_tmp.name

        try:
            cmd = [
                'ffmpeg',
                '-i', audio_file,
                '-ar', '16000',
                '-ac', '1',
                '-acodec', 'pcm_s16le',
                '-loglevel', 'error',
                '-y',
                wav_tmp_path
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                return None, f"การแปลงไฟล์เสียงล้มเหลว: {result.stderr}"

            try:
                with contextlib.closing(wave.open(wav_tmp_path, 'r')) as f:
                    frames = f.getnframes()
                    rate = f.getframerate()
                    if frames == 0 or rate != 16000:
                        return None, "คุณภาพไฟล์เสียงไม่เหมาะสม (ต้องเป็น 16kHz mono)"
            except wave.Error:
                return None, "ไฟล์ WAV ที่แปลงแล้วเสียหาย"

            recognizer = sr.Recognizer()
            with sr.AudioFile(wav_tmp_path) as source:
                recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio_data = recognizer.record(source)

                if language == "auto" or language == "th-TH":
                    try:
                        text = recognizer.recognize_google(audio_data, language="th-TH")
                        return text, None
                    except sr.UnknownValueError:
                        if language == "th-TH":
                            return None, "ไม่สามารถเข้าใจคำพูดภาษาไทย"

                try:
                    text = recognizer.recognize_google(audio_data, language="en-US")
                    return text, None
                except sr.UnknownValueError:
                    return None, "Could not understand the audio"
                except sr.RequestError as e:
                    return None, f"ไม่สามารถเชื่อมต่อกับบริการ Google: {str(e)}"

        finally:
            try:
                os.unlink(wav_tmp_path)
            except:
                pass

    except Exception as e:
        return None, f"ข้อผิดพลาดทั่วไป: {str(e)}"

def tts_tab():
    with gr.Blocks() as tts_interface:
        with gr.Row():
            with gr.Column():
                text_input = gr.Textbox(label="ข้อความ", placeholder="ป้อนข้อความที่นี่...", lines=5)
                voice_dropdown = gr.Dropdown(
                    choices=list(VOICES.items()),
                    label="เสียง",
                    value="th-TH-PremwadeeNeural"
                )
                rate_slider = gr.Slider(
                    minimum=-100,
                    maximum=100,
                    value=0,
                    label="ความเร็ว (%)"
                )
                generate_btn = gr.Button("สร้างเสียง", variant="primary")

            with gr.Column():
                audio_output = gr.Audio(label="เสียงที่สร้าง", interactive=False, visible=False)
                # เปลี่ยนเป็น gr.File สำหรับการดาวน์โหลด
                download_component = gr.File(
                    label="ดาวน์โหลดไฟล์เสียง",
                    visible=False,
                    interactive=False
                )
                error_output = gr.Textbox(label="ข้อผิดพลาด", visible=False)

        def generate(text, voice, rate, progress=gr.Progress()):
            progress(0.1, desc="กำลังเริ่มต้น...")
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            audio_file, error = loop.run_until_complete(generate_audio(text, voice, rate, progress))
            loop.close()

            if error:
                return (
                    None,  # audio_output
                    gr.update(visible=False),  # audio player visibility
                    None,  # download file
                    gr.update(visible=False),  # download component visibility
                    gr.update(value=error, visible=True)  # error
                )
            else:
                return (
                    audio_file,  # audio_output
                    gr.update(visible=True),  # audio player visibility
                    audio_file,  # download file
                    gr.update(visible=True),  # download component visibility
                    gr.update(visible=False)  # error
                )

        generate_btn.click(
            fn=generate,
            inputs=[text_input, voice_dropdown, rate_slider],
            outputs=[
                audio_output,
                audio_output,  # สำหรับอัปเดต visibility
                download_component,
                download_component,  # สำหรับอัปเดต visibility
                error_output
            ],
            show_progress=True
        )

    return tts_interface

def stt_tab():
    with gr.Blocks() as stt_interface:
        with gr.Row():
            with gr.Column():
                audio_input = gr.Audio(label="อัปโหลดไฟล์เสียง", type="filepath")
                language_dropdown = gr.Dropdown(
                    choices=["th-TH", "en-US", "auto"],
                    label="ภาษา",
                    value="auto"
                )
                convert_btn = gr.Button("แปลงเป็นข้อความ", variant="primary")

            with gr.Column():
                text_output = gr.Textbox(label="ผลลัพธ์", lines=5, interactive=False)
                error_output = gr.Textbox(label="ข้อผิดพลาด", visible=False)

        def convert(audio_file, language):
            text, error = speech_to_text(audio_file, language)
            if error:
                return None, gr.update(value=error, visible=True)
            else:
                return text, gr.update(visible=False)

        convert_btn.click(
            fn=convert,
            inputs=[audio_input, language_dropdown],
            outputs=[text_output, error_output]
        )

    return stt_interface

with gr.Blocks(title="TTS & STT Web UI", theme=gr.themes.Soft()) as app:
    gr.Markdown("# TTS & STT Web UI")
    with gr.Tabs():
        with gr.TabItem("Text-to-Speech (TTS)"):
            tts_tab()
        with gr.TabItem("Speech-to-Text (STT)"):
            stt_tab()

if __name__ == "__main__":
    app.launch(server_port=8685, server_name="0.0.0.0")
