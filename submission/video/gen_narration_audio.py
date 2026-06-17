#!/usr/bin/env python3
"""Sinh giọng đọc tiếng Việt (Edge TTS giọng NAM 'vi-VN-NamMinhNeural') cho từng
cảnh demo, chuyển sang wav 44.1kHz stereo, đo thời lượng bằng ffprobe, ghi durations.json.
Chạy (cần network — tắt sandbox): ./.venv/bin/python3 gen_narration_audio.py"""
import json
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).parent
VOICE = "vi-VN-NamMinhNeural"  # giọng nam tiếng Việt
RATE = "-4%"                    # chậm nhẹ cho "vừa đủ", rõ ràng

# Lời thoại khớp dữ liệu THẬT trên sản phẩm live (không phóng đại).
SCENES = [
    ("s1", "Xin chào. Đây là Agent dịch và kiểm định chất lượng nội dung game, "
           "từ tiếng Trung sang tiếng Việt và tiếng Thái, chạy trên nền tảng GreenNode AgentBase. "
           "Mỗi đội game là một hồ sơ riêng, với termbase, tông giọng và danh sách từ cần tránh độc lập. "
           "Trước tiên, ta đăng nhập vào hệ thống."),
    ("s2", "Ở màn Playground, tôi dán một câu tiếng Trung có chứa thuật ngữ tu tiên, "
           "rồi bấm Dịch và QC. Agent quét termbase, ép bản dịch dùng đúng thuật ngữ, "
           "và một bộ QC độc lập sẽ chấm điểm. "
           "Kết quả: bản dịch giữ đúng bốn thuật ngữ bắt buộc được tô sáng, "
           "điểm trôi chảy năm trên năm, trạng thái Đạt, và được tự động duyệt. "
           "Mọi bản dịch đều tự gắn nhãn Nội dung dịch bởi A I."),
    ("s3", "Chuyển sang màn Termbase. Đây là nơi quản lý thuật ngữ để giữ nhất quán giữa các bản dịch. "
           "Ta có thể tìm kiếm thuật ngữ, và ở tab Đề xuất, "
           "hệ thống tự gợi ý thuật ngữ mới do agent trích xuất, người duyệt chỉ việc chốt."),
    ("s4", "Không phải lúc nào QC cũng Đạt. Tôi đổi sang hồ sơ Game B và dịch sang tiếng Thái. "
           "Lần này QC chấm trôi chảy thấp, trạng thái Cần người duyệt, "
           "và bản dịch được đẩy vào hàng đợi. Mở màn Review Queue, "
           "người duyệt xem lại, chọn Sửa lại và nhập bản dịch đúng. "
           "Đây chính là cơ chế con người trong vòng lặp."),
    ("s5", "Mỗi lần người sửa, cặp bản dịch sai và đúng được lưu lại ở màn Corrections. "
           "Đây là bánh đà của hệ thống: những correction này được đưa ngược vào lần dịch sau, "
           "và một agent Curator sẽ đề xuất bổ sung termbase. Càng dùng, agent càng chuẩn."),
    ("fly", "Và đây là bánh đà giúp agent ngày càng chuẩn. Trước đó, ở hồ sơ Game A, "
            "agent từng dịch sai chữ máy chủ thành tinh thần, và đã được người duyệt sửa lại. "
            "Bây giờ, khi gặp lại đúng nội dung đó, agent áp dụng correction đã học "
            "và dịch đúng là máy chủ, không lặp lại lỗi cũ. "
            "Càng dùng, agent càng chuẩn và người duyệt càng đỡ việc."),
    ("s6", "Cuối cùng là Dashboard, tổng hợp các chỉ số: số thuật ngữ, số bản chờ duyệt, "
           "số correction đã học. Toàn bộ chạy thật trên endpoint công khai của AgentBase. "
           "Cảm ơn đã theo dõi."),
]


def ffprobe_duration(path: Path) -> float:
    out = subprocess.check_output([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", str(path),
    ])
    return float(out.strip())


def main() -> None:
    durations = {}
    for sid, text in SCENES:
        mp3 = HERE / f"{sid}.mp3"
        wav = HERE / f"{sid}.wav"
        # bỏ qua cảnh đã render hợp lệ (cho phép chạy lại nhiều lần vượt throttle)
        if wav.exists() and wav.stat().st_size > 1000:
            durations[sid] = round(ffprobe_duration(wav), 2)
            print(f"{sid}: {durations[sid]}s (skip, đã có)")
            continue
        time.sleep(6)  # giãn cách tránh burst
        # edge-tts hay bị Microsoft throttle → retry + backoff
        for attempt in range(1, 9):
            r = subprocess.run([
                sys.executable, "-m", "edge_tts", "--voice", VOICE, f"--rate={RATE}",
                "--text", text, "--write-media", str(mp3),
            ])
            if r.returncode == 0 and mp3.exists() and mp3.stat().st_size > 1000:
                break
            wait = min(5 * attempt, 30)
            print(f"  {sid} attempt {attempt} failed, retry in {wait}s")
            time.sleep(wait)
        else:
            raise RuntimeError(f"edge-tts failed for {sid}")
        subprocess.run([
            "ffmpeg", "-y", "-loglevel", "error", "-i", str(mp3),
            "-ar", "44100", "-ac", "2", str(wav),
        ], check=True)
        mp3.unlink(missing_ok=True)
        durations[sid] = round(ffprobe_duration(wav), 2)
        print(f"{sid}: {durations[sid]}s")
    (HERE / "durations.json").write_text(json.dumps(durations, indent=2))
    print("TOTAL:", round(sum(durations.values()), 2), "s")


if __name__ == "__main__":
    main()
