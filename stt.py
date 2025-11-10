# stt.py (simple)
import os, io, wave, time
from pathlib import Path
from datetime import datetime

import numpy as np
import sounddevice as sd
from dotenv import load_dotenv
from openai import OpenAI

# ===== 설정 =====
SR = 16_000
CHANNELS = 1
CHUNK_SECONDS = 5

MODE = "file"  # "mic" 또는 "file"
AUDIO_PATH = "voice/2025apec_speechOfXijinping.mp3"  # MODE="file"일 때
LANGUAGE = "zh"  # 자동감지 원하면 None

MODEL = "whisper-1"
OUTDIR = Path("text")
SESSION_TS = datetime.now().strftime("%Y%m%d-%H%M%S")


def ensure_outdir():
    OUTDIR.mkdir(parents=True, exist_ok=True)


def to_wav_bytes(int16_audio: np.ndarray, sr: int = SR) -> bytes:
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(2)  # int16
        wf.setframerate(sr)
        wf.writeframes(int16_audio.tobytes())
    return buf.getvalue()


def record_chunk(seconds: int = CHUNK_SECONDS) -> np.ndarray:
    print(f"[REC] {seconds}초 녹음…")
    audio = sd.rec(int(seconds * SR), samplerate=SR, channels=CHANNELS,
                   dtype="int16", blocking=True)
    sd.wait()
    return audio.reshape(-1)


def transcribe_bytes(client: OpenAI, wav_bytes: bytes, language=None) -> str:
    resp = client.audio.transcriptions.create(
        model=MODEL,
        file=("audio.wav", wav_bytes, "audio/wav"),
        language=language
    )
    return resp.text


def transcribe_file(client: OpenAI, path: str, language=None) -> str:
    with open(path, "rb") as f:
        resp = client.audio.transcriptions.create(
            model=MODEL,
            file=f,
            language=language
        )
    return resp.text


def run_mic(client: OpenAI):
    ensure_outdir()
    out_txt = OUTDIR / f"mic_{SESSION_TS}.txt"
    print(f"[INFO] 마이크 전사 시작 (Ctrl+C 종료). 저장: {out_txt}")
    idx = 1
    try:
        while True:
            chunk = record_chunk()
            wav_bytes = to_wav_bytes(chunk)
            t0 = time.time()
            text = transcribe_bytes(client, wav_bytes, LANGUAGE)
            dt = time.time() - t0
            line = f"[{idx:03d}] {text}\n"
            print(f"[{idx:03d}] → {text} ({dt:.2f}s)")
            with open(out_txt, "a", encoding="utf-8") as f:
                f.write(line)
            idx += 1
    except KeyboardInterrupt:
        print("\n[INFO] 종료")


def run_file(client: OpenAI):
    ensure_outdir()
    stem = Path(AUDIO_PATH).stem or "audio"
    out_txt = OUTDIR / f"file_{stem}_{SESSION_TS}.txt"
    print(f"[INFO] 파일 전사 중: {AUDIO_PATH}")
    text = transcribe_file(client, AUDIO_PATH, LANGUAGE)
    with open(out_txt, "w", encoding="utf-8") as f:
        f.write(text)
    print(f"[INFO] 저장 완료: {out_txt}")


def main():
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY가 설정되지 않았습니다. .env 확인")
    client = OpenAI(api_key=api_key)

    if MODE == "file":
        run_file(client)
    elif MODE == "mic":
        run_mic(client)
    else:
        raise ValueError("MODE는 'mic' 또는 'file' 이어야 합니다.")


if __name__ == "__main__":
    main()
