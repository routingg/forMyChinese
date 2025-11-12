# format_text_indexed.py
from pathlib import Path
import re

# ===== 사용자 설정 =====
FOLDER = Path("text")      # 텍스트 파일들이 있는 폴더
INDEX = 0                  # 0 = 첫 번째 파일, 1 = 두 번째 파일 ...
ENCODING = "utf-8"

# ===== 함수 정의 =====
def get_target_file(folder: Path, index: int) -> Path:
    """폴더 안 txt 파일 중 index번째 파일 반환"""
    files = sorted(folder.glob("*.txt"))
    if not files:
        raise FileNotFoundError(f"{folder} 안에 .txt 파일이 없습니다.")
    if index >= len(files):
        raise IndexError(f"{index}번째 파일이 없습니다. (총 {len(files)}개 존재)")
    print("[INFO] 선택된 파일:", files[index].name)
    return files[index]

def clean_text(text: str) -> str:
    """문장 단위로 줄바꿈 및 중복 제거"""
    text = text.replace("\n", " ").strip()
    text = re.sub(r"\s{2,}", " ", text)
    text = re.sub(r"([。！？；.!?])", r"\1\n", text)
    lines, prev = [], ""
    for line in text.splitlines():
        if line.strip() and line.strip() != prev:
            lines.append(line.strip())
            prev = line.strip()
    return "\n\n".join(lines).strip()

def main():
    infile = get_target_file(FOLDER, INDEX)
    outfile = infile.with_name(f"{infile.stem}_formatted.txt")

    text = infile.read_text(encoding=ENCODING)
    formatted = clean_text(text)
    outfile.write_text(formatted, encoding=ENCODING)
    print(f"[INFO] 정리 완료 → {outfile}")

if __name__ == "__main__":
    main()
