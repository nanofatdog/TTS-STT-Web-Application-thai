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
import pytesseract
from PIL import Image
import fitz  # PyMuPDF
import numpy as np

# Load voice data from JSON file
with open('voices.json', 'r', encoding='utf-8') as f:
    VOICES = json.load(f)


async def generate_audio(text: str, voice: str, rate: int, progress=gr.Progress()):
    try:
        progress(0.1, desc="Initializing...")

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

        progress(0.3, desc="Generating audio...")

        communicate = edge_tts.Communicate(text, voice, rate=rate_str) if rate_str else edge_tts.Communicate(text, voice)

        progress(0.6, desc="Saving audio file...")

        await communicate.save(output_file)

        if not os.path.exists(output_file):
            raise Exception("Audio file was not created")

        progress(1.0, desc="Audio generation complete!")

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
                return None, f"Audio conversion failed: {result.stderr}"

            try:
                with contextlib.closing(wave.open(wav_tmp_path, 'r')) as f:
                    frames = f.getnframes()
                    rate = f.getframerate()
                    if frames == 0 or rate != 16000:
                        return None, "Audio quality not suitable (must be 16kHz mono)"
            except wave.Error:
                return None, "Converted WAV file is corrupted"

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
                            return None, "Could not understand Thai speech"

                try:
                    text = recognizer.recognize_google(audio_data, language="en-US")
                    return text, None
                except sr.UnknownValueError:
                    return None, "Could not understand the audio"
                except sr.RequestError as e:
                    return None, f"Could not connect to Google service: {str(e)}"

        finally:
            try:
                os.unlink(wav_tmp_path)
            except:
                pass

    except Exception as e:
        return None, f"General error: {str(e)}"

def extract_text_from_pdf(pdf_file):
    try:
        doc = fitz.open(pdf_file)
        text = ""
        for page in doc:
            text += page.get_text()
        return text, None
    except Exception as e:
        return None, f"PDF extraction error: {str(e)}"

def extract_text_from_image(image_file):
    try:
        img = Image.open(image_file)
        # Use Tesseract OCR with automatic language detection
        text = pytesseract.image_to_string(img, lang='eng+tha+jpn+chi_sim')
        return text, None
    except Exception as e:
        return None, f"OCR error: {str(e)}"

def ocr_process(file, file_type):
    if file_type == "PDF":
        return extract_text_from_pdf(file)
    elif file_type == "Image":
        return extract_text_from_image(file)
    else:
        return None, "Unsupported file type"

def tts_tab():
    with gr.Blocks() as tts_interface:
        with gr.Row():
            with gr.Column():
                text_input = gr.Textbox(label="Text", placeholder="Enter text here...", lines=5)
                with gr.Row():
                    voice_dropdown = gr.Dropdown(
                        choices=list(VOICES.items()),
                        label="Voice",
                        value="th-TH-PremwadeeNeural"
                    )
                    rate_slider = gr.Slider(
                        minimum=-100,
                        maximum=100,
                        value=0,
                        label="Speed (%)"
                    )
                with gr.Accordion("OCR from File", open=False):
                    file_input = gr.File(label="Upload PDF or Image")
                    file_type = gr.Radio(
                        choices=["PDF", "Image"],
                        label="File Type",
                        value="PDF"
                    )
                    extract_btn = gr.Button("Extract Text")
                generate_btn = gr.Button("Generate Audio", variant="primary")

            with gr.Column():
                audio_output = gr.Audio(label="Generated Audio", interactive=False, visible=True)
                download_component = gr.File(
                    label="Download Audio",
                    visible=False,
                    interactive=False
                )
                error_output = gr.Textbox(label="Error", visible=False)

        def extract_text(file, file_type):
            text, error = ocr_process(file, file_type)
            if error:
                return None, gr.update(value=error, visible=True)
            else:
                return text, gr.update(visible=False)

        def generate(text, voice, rate, progress=gr.Progress()):
            progress(0.1, desc="Initializing...")
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            audio_file, error = loop.run_until_complete(generate_audio(text, voice, rate, progress))
            loop.close()

            if error:
                return (
                    None,
                    gr.update(visible=False),
                    None,
                    gr.update(visible=False),
                    gr.update(value=error, visible=True)
                )
            else:
                return (
                    audio_file,
                    gr.update(visible=True),
                    audio_file,
                    gr.update(visible=True),
                    gr.update(visible=False)
                )

        extract_btn.click(
            fn=extract_text,
            inputs=[file_input, file_type],
            outputs=[text_input, error_output]
        )

        generate_btn.click(
            fn=generate,
            inputs=[text_input, voice_dropdown, rate_slider],
            outputs=[
                audio_output,
                audio_output,
                download_component,
                download_component,
                error_output
            ],
            show_progress=True
        )

    return tts_interface

def stt_tab():
    with gr.Blocks() as stt_interface:
        with gr.Row():
            with gr.Column():
                audio_input = gr.Audio(label="Upload Audio File", type="filepath")
                language_dropdown = gr.Dropdown(
                    choices=["th-TH", "en-US", "auto"],
                    label="Language",
                    value="auto"
                )
                convert_btn = gr.Button("Convert to Text", variant="primary")

            with gr.Column():
                text_output = gr.Textbox(label="Result", lines=5, interactive=False)
                error_output = gr.Textbox(label="Error", visible=False)

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

with gr.Blocks(title="TTS & STT & OCR Web UI", theme=gr.themes.Soft()) as app:
    gr.Markdown("# Multi-language TTS, STT & OCR Web UI")
    with gr.Tabs():
        with gr.TabItem("Text-to-Speech (TTS)"):
            tts_tab()
        with gr.TabItem("Speech-to-Text (STT)"):
            stt_tab()

if __name__ == "__main__":
    # Check if Tesseract is available
    try:
        pytesseract.get_tesseract_version()
    except EnvironmentError:
        print("Warning: Tesseract OCR is not installed or not in your PATH")

    app.launch(server_port=8685, server_name="0.0.0.0")
