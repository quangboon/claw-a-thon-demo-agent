#!/usr/bin/env python3
"""Dựng slideshow video từ ảnh thật + ghép giọng đọc → mp4 h264/aac.
Đọc durations.json (thời lượng audio từng cảnh) và chia cho các ảnh trong cảnh theo tỉ lệ.
Chạy: ./.venv/bin/python3 build_video.py"""
import json
import subprocess
from pathlib import Path

HERE = Path(__file__).parent
SHOTS = HERE / "shots"
SCENES = ["s1", "s2", "s3", "s4", "s5", "fly", "s6"]

# cảnh -> [(ảnh, tỉ lệ thời lượng trong cảnh)]
LAYOUT = {
    "s1": [("01_login.png", 0.40), ("02_playground_empty.png", 0.60)],
    "s2": [("03_pg_source.png", 0.26), ("04_pg_result.png", 0.74)],
    "s3": [("05_termbase.png", 0.50), ("06_candidates.png", 0.50)],
    "s4": [("07_pg_review_needed.png", 0.38), ("08_review_queue.png", 0.33), ("09_review_edit.png", 0.29)],
    "s5": [("10_corrections.png", 1.0)],
    "fly": [("12_fly_corrections.png", 0.52), ("13_fly_result.png", 0.48)],
    "s6": [("11_dashboard.png", 1.0)],
}


def main() -> None:
    dur = json.loads((HERE / "durations.json").read_text())

    # 1) audlist
    (HERE / "audlist.txt").write_text("".join(f"file '{HERE/(s+'.wav')}'\n" for s in SCENES))
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0",
                    "-i", str(HERE / "audlist.txt"), "-ar", "44100", "-ac", "2",
                    str(HERE / "narration.wav")], check=True)

    # 2) imglist (thời lượng ảnh = tỉ lệ * thời lượng cảnh)
    lines, last = [], None
    for s in SCENES:
        for img, ratio in LAYOUT[s]:
            d = round(dur[s] * ratio, 3)
            p = SHOTS / img
            lines.append(f"file '{p}'\nduration {d}\n")
            last = p
    lines.append(f"file '{last}'\n")  # concat demuxer cần lặp ảnh cuối
    (HERE / "imglist.txt").write_text("".join(lines))

    # 3) slideshow -> h264 (pad 1366x768)
    vf = ("scale=1366:768:force_original_aspect_ratio=decrease,"
          "pad=1366:768:(ow-iw)/2:(oh-ih)/2:white,format=yuv420p")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0",
                    "-i", str(HERE / "imglist.txt"), "-vf", vf, "-r", "25",
                    "-c:v", "libx264", "-preset", "medium", "-crf", "20",
                    str(HERE / "video_silent.mp4")], check=True)

    # 4) mux
    out = HERE / "demo-claw-a-thon.mp4"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(HERE / "video_silent.mp4"),
                    "-i", str(HERE / "narration.wav"), "-c:v", "copy", "-c:a", "aac",
                    "-b:a", "192k", "-shortest", str(out)], check=True)

    total = round(sum(dur.values()), 2)
    print("scene durations:", dur, "TOTAL:", total, "s")
    print("OUTPUT:", out)


if __name__ == "__main__":
    main()
