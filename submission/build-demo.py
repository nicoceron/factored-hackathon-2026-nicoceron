"""Render a narrated walkthrough from local-app captures and labeled diagrams.

Requires Python + Pillow, FFmpeg/FFprobe, and macOS say (Samantha voice).
No network, browser automation, or paid service is used by this render script.
Run from any directory; output is submission/claro-demo.mp4 plus timed captions.
"""

import hashlib
import json
import os
import shutil
import subprocess
import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps

ROOT = Path(__file__).resolve().parent
BUILD = ROOT.parent / "artifacts" / "demo-build"
SCENES = json.loads((ROOT / "demo-scenes.json").read_text())
FONT_PATH = os.environ.get("DEMO_FONT", "/System/Library/Fonts/Avenir Next.ttc")
NAVY = "#142a32"
LIME = "#c5f16d"
MUTED = "#acc0c4"


def run(args):
    subprocess.run(args, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)


def duration(path):
    return float(
        subprocess.check_output(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                str(path),
            ],
            text=True,
        ).strip()
    )


def font(size):
    return ImageFont.truetype(FONT_PATH, size)


def frame(scene, index):
    canvas = Image.new("RGB", (1920, 1080), NAVY)
    draw = ImageDraw.Draw(canvas)
    draw.rounded_rectangle((48, 44, 107, 103), 17, fill=LIME)
    draw.text((60, 42), "c.", font=font(48), fill=NAVY)
    draw.text((124, 43), "claro", font=font(43), fill="white")
    draw.text((49, 148), scene["eyebrow"], font=font(16), fill=LIME)
    title_lines = scene["title"].split("\n")
    title_size = 46
    while max(draw.textlength(line, font=font(title_size)) for line in title_lines) > 414:
        title_size -= 1
    y = 211
    for line in title_lines:
        draw.text((47, y), line, font=font(title_size), fill="white")
        y += 61
    y += 38
    for point in scene["points"]:
        draw.ellipse((51, y + 12, 58, y + 19), fill=LIME)
        for line in textwrap.wrap(point, width=29):
            draw.text((75, y), line, font=font(24), fill=MUTED)
            y += 36
        y += 28
    draw.text((49, 929), f"{index + 1:02d} / {len(SCENES):02d}", font=font(19), fill=LIME)
    draw.text((49, 978), "FACTORED AI & DATA", font=font(16), fill=MUTED)
    draw.text((49, 1005), "HACKATHON 2026", font=font(16), fill=MUTED)
    screenshot = Image.open(ROOT / "demo-assets" / scene["image"]).convert("RGB")
    if scene.get("crop"):
        screenshot = screenshot.crop(tuple(scene["crop"]))
    screenshot = ImageOps.contain(screenshot, (1372, 902), Image.Resampling.LANCZOS)
    x = 490 + (1372 - screenshot.width) // 2
    y = 93 + (902 - screenshot.height) // 2
    draw.rounded_rectangle(
        (x - 2, y - 2, x + screenshot.width + 2, y + screenshot.height + 2), 6, fill="#456168"
    )
    canvas.paste(screenshot, (x, y))
    draw.text(
        (494, 32),
        scene.get("source_label", "ACTUAL LOCAL APP  /  TEAM-AUTHORED FIXTURES"),
        font=font(18),
        fill=MUTED,
    )
    draw.text(
        (494, 1024),
        scene.get(
            "source_footer",
            "Narrated screenshot walkthrough · no real banking action · synthetic system voice",
        ),
        font=font(17),
        fill=MUTED,
    )
    output = BUILD / f"scene-{index:02d}.png"
    canvas.save(output)
    return output


def srt_time(value):
    millis = round(value * 1000)
    hours, millis = divmod(millis, 3600000)
    minutes, millis = divmod(millis, 60000)
    seconds, millis = divmod(millis, 1000)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{millis:03d}"


def main():
    for binary in ("ffmpeg", "ffprobe", "say"):
        if not shutil.which(binary):
            raise SystemExit(f"Required local tool unavailable: {binary}")
    BUILD.mkdir(parents=True, exist_ok=True)
    subtitle_items = []
    manifest = {
        "capture_provenance": (
            "CUA Chrome, localhost:8096, 2026-10-02; actual isolated sandbox; "
            "evaluation and architecture slides explicitly labeled"
        ),
        "format": "Narrated screenshots and labeled diagrams, not a continuous screen recording",
        "voice": "macOS Samantha synthetic voice; no voice cloning",
        "scenes": [],
    }
    offset = 0.0
    concat = []
    transcript = [
        "# Claro narrated demo",
        "",
        "Actual screenshots of the running local sandbox; "
        "narrated with the macOS Samantha system voice.",
        "No footage is represented as a continuous recording. "
        "Architecture and evaluation slides are labeled separately. "
        "UI content is from team-authored fixtures.",
        "",
    ]
    for index, scene in enumerate(SCENES):
        image_path = frame(scene, index)
        sentence_files = []
        sentence_clock = 0.35
        transcript.extend([f"## {index + 1}. {scene['title'].replace(chr(10), ' ')}", ""])
        for sentence_index, sentence in enumerate(scene["sentences"]):
            text_path = BUILD / f"voice-{index:02d}-{sentence_index:02d}.txt"
            voice_path = text_path.with_suffix(".aiff")
            wav_path = text_path.with_suffix(".wav")
            text_path.write_text(sentence)
            run(["say", "-v", "Samantha", "-r", "177", "-f", str(text_path), "-o", str(voice_path)])
            run(
                [
                    "ffmpeg",
                    "-y",
                    "-i",
                    str(voice_path),
                    "-ar",
                    "48000",
                    "-ac",
                    "1",
                    "-c:a",
                    "pcm_s16le",
                    str(wav_path),
                ]
            )
            length = duration(wav_path)
            subtitle_items.append(
                (offset + sentence_clock, offset + sentence_clock + length, sentence)
            )
            sentence_clock += length
            sentence_files.append(wav_path)
            transcript.append(sentence)
        audio_list = BUILD / f"audio-{index:02d}.txt"
        audio_list.write_text("\n".join(f"file '{path}'" for path in sentence_files))
        audio_path = BUILD / f"scene-{index:02d}.wav"
        run(
            [
                "ffmpeg",
                "-y",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                str(audio_list),
                "-af",
                "adelay=350,apad=pad_dur=0.55",
                "-c:a",
                "pcm_s16le",
                str(audio_path),
            ]
        )
        seconds = duration(audio_path)
        segment = BUILD / f"scene-{index:02d}.mp4"
        run(
            [
                "ffmpeg",
                "-y",
                "-loop",
                "1",
                "-framerate",
                "24",
                "-i",
                str(image_path),
                "-i",
                str(audio_path),
                "-t",
                str(seconds),
                "-c:v",
                "libx264",
                "-preset",
                "fast",
                "-tune",
                "stillimage",
                "-crf",
                "22",
                "-pix_fmt",
                "yuv420p",
                "-c:a",
                "aac",
                "-b:a",
                "128k",
                "-movflags",
                "+faststart",
                str(segment),
            ]
        )
        concat.append(segment)
        source = ROOT / "demo-assets" / scene["image"]
        manifest["scenes"].append(
            {
                "title": scene["title"],
                "source": str(source.relative_to(ROOT)),
                "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
                "source_kind": scene.get("source_kind", "actual_local_app_capture"),
                "crop": scene.get("crop"),
                "start_seconds": offset,
                "duration_seconds": seconds,
            }
        )
        offset += seconds
        transcript.append("")
        print(f"Rendered scene {index + 1}/{len(SCENES)}: {seconds:.2f}s", flush=True)
    if offset >= 180:
        raise SystemExit(f"Pitch exceeds 3-minute limit: {offset:.3f}s")
    concat_file = BUILD / "segments.txt"
    concat_file.write_text("\n".join(f"file '{path}'" for path in concat))
    subtitles = ROOT / "claro-demo.en.srt"
    subtitles.write_text(
        "\n\n".join(
            f"{n + 1}\n{srt_time(start)} --> {srt_time(end)}\n" + "\n".join(textwrap.wrap(text, 78))
            for n, (start, end, text) in enumerate(subtitle_items)
        )
        + "\n"
    )
    output = ROOT / "claro-demo.mp4"
    run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(concat_file),
            "-i",
            str(subtitles),
            "-map",
            "0:v",
            "-map",
            "0:a",
            "-map",
            "1:0",
            "-c:v",
            "copy",
            "-c:a",
            "copy",
            "-c:s",
            "mov_text",
            "-metadata:s:s:0",
            "language=eng",
            "-movflags",
            "+faststart",
            str(output),
        ]
    )
    manifest["duration_seconds"] = duration(output)
    manifest["output_sha256"] = hashlib.sha256(output.read_bytes()).hexdigest()
    (ROOT / "demo-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    (ROOT / "demo-script.md").write_text("\n".join(transcript))
    print(f"DONE {manifest['duration_seconds']:.2f}s: {output}", flush=True)


if __name__ == "__main__":
    main()
