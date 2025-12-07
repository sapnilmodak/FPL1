"""
Voice Service using Hugging Face
Handles Speech-to-Text (STT) and Text-to-Speech (TTS)
"""

import requests
import os
import tempfile
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class VoiceService:
    """Handles voice operations using Hugging Face models"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.headers = {"Authorization": f"Bearer {api_key}"}
        
        self.stt_models = [
            "openai/whisper-large-v3",
            "openai/whisper-large-v2",
            "openai/whisper-medium",
            "openai/whisper-small",
            "openai/whisper-tiny",
            "jonatasgrosman/whisper-large-v2-portuguese",
        ]
        
        self.tts_models = [
            "espnet/kan-bayashi_ljspeech_vits",
            "facebook/mms-tts-eng",
            "microsoft/speecht5_tts"
        ]
    
    async def speech_to_text(self, audio_data: bytes) -> str:
        tmp_path = None
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
                tmp_file.write(audio_data)
                tmp_path = tmp_file.name
            
            for model in self.stt_models:
                try:
                    logger.info(f"Trying STT model: {model}")
                    
                    with open(tmp_path, "rb") as f:
                        response = requests.post(
                            f"https://api-inference.huggingface.co/models/{model}",
                            headers=self.headers,
                            data=f.read(),
                            timeout=60
                        )
                    
                    if response.status_code == 200:
                        result = response.json()
                        transcribed_text = None
                        
                        if isinstance(result, dict):
                            if "text" in result:
                                transcribed_text = result["text"]
                            elif "transcription" in result:
                                transcribed_text = result["transcription"]
                        elif isinstance(result, list) and len(result) > 0:
                            if isinstance(result[0], dict):
                                transcribed_text = result[0].get("text", "") or result[0].get("transcription", "")
                            else:
                                transcribed_text = str(result[0])
                        
                        if transcribed_text and len(transcribed_text.strip()) > 0:
                            logger.info(f"STT successful using model: {model}")
                            return transcribed_text.strip()
                        else:
                            logger.warning(f"STT model {model} returned empty transcription")
                            continue
                    
                    elif response.status_code == 503:
                        logger.info(f"Model {model} is loading, waiting...")
                        import time
                        time.sleep(5)
                        continue
                    elif response.status_code == 410:
                        logger.warning(f"STT model {model} returned 410 (Gone), trying next model")
                        continue
                    else:
                        logger.warning(f"STT model {model} returned status {response.status_code}")
                        continue
                
                except Exception as e:
                    logger.warning(f"Error with STT model {model}: {str(e)}")
                    continue
            
            logger.error("All STT models failed")
            return "Sorry, I couldn't process your audio. Please try typing your message instead."
        
        except Exception as e:
            logger.error(f"Error in speech_to_text: {str(e)}")
            return "Error processing audio. Please try again."
        
        finally:
            if tmp_path and os.path.exists(tmp_path):
                try:
                    os.unlink(tmp_path)
                except:
                    pass
    
    async def text_to_speech(self, text: str) -> str:
        for model in self.tts_models:
            try:
                logger.info(f"Trying TTS model: {model}")
                
                if "espnet" in model:
                    payload = {"inputs": text}
                elif "mms" in model:
                    payload = {"inputs": text}
                else:
                    payload = {"inputs": text}
                
                response = requests.post(
                    f"https://api-inference.huggingface.co/models/{model}",
                    headers=self.headers,
                    json=payload,
                    timeout=60
                )
                
                if response.status_code == 200:
                    if response.content and len(response.content) > 100:
                        tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
                        tmp_file.write(response.content)
                        tmp_file.close()
                        logger.info(f"TTS successful using model: {model}")
                        return tmp_file.name
                    else:
                        logger.warning(f"TTS model {model} returned empty response")
                        continue
                elif response.status_code == 503:
                    logger.info(f"Model {model} is loading, waiting...")
                    import time
                    time.sleep(5)
                    continue
                else:
                    logger.warning(f"TTS model {model} returned status {response.status_code}")
                    continue
            
            except Exception as e:
                logger.warning(f"Error with TTS model {model}: {str(e)}")
                continue
        
        logger.warning("All TTS models failed, using fallback")
        return self._create_fallback_audio(text)
    
    def _create_fallback_audio(self, text: str) -> str:
        sample_rate = 16000
        duration = 1
        num_samples = sample_rate * duration
        
        wav_header = bytearray([
            0x52, 0x49, 0x46, 0x46,
            0x24, 0x08, 0x00, 0x00,
            0x57, 0x41, 0x56, 0x45,
            0x66, 0x6D, 0x74, 0x20,
            0x10, 0x00, 0x00, 0x00,
            0x01, 0x00,
            0x01, 0x00,
            sample_rate & 0xFF, (sample_rate >> 8) & 0xFF, (sample_rate >> 16) & 0xFF, (sample_rate >> 24) & 0xFF,
            (sample_rate * 2) & 0xFF, ((sample_rate * 2) >> 8) & 0xFF, ((sample_rate * 2) >> 16) & 0xFF, ((sample_rate * 2) >> 24) & 0xFF,
            0x02, 0x00,
            0x10, 0x00,
            0x64, 0x61, 0x74, 0x61,
            (num_samples * 2) & 0xFF, ((num_samples * 2) >> 8) & 0xFF, ((num_samples * 2) >> 16) & 0xFF, ((num_samples * 2) >> 24) & 0xFF,
        ])
        
        audio_data = b'\x00\x00' * num_samples
        wav_data = wav_header + audio_data
        
        tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
        tmp_file.write(wav_data)
        tmp_file.close()
        
        logger.warning(f"Created fallback silent audio file. TTS models unavailable. Text was: {text[:50]}...")
        return tmp_file.name

