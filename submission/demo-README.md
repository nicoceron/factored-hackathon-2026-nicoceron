# Claro demo video

`claro-demo.mp4` is a 1920×1080 narrated walkthrough lasting **2 minutes 44.55 seconds**, below the three-minute submission limit. It contains H.264 video, AAC mono narration, and an English subtitle track. A separate `claro-demo.en.srt` and the full `demo-script.md` are included.

The nine scenes demonstrate transaction clarification, evidence, a case proposal, explicit confirmation, a verified receipt, analyst review, operating telemetry, evaluation, and architectural boundaries. The UI is Portuguese for the customer and analyst workflow; the narration is English.

## Provenance

The source JPEGs in `demo-assets/` are genuine CUA-controlled Chrome captures of the running app at `127.0.0.1:8096` on October 2, 2026. Every screen contains team-authored fixtures. They were captured during actual customer and analyst actions described in `docs/UI.md`; case references belong only to that isolated local workspace.

This is an edited screenshot walkthrough, **not a continuous screen recording or proof of a hosted deployment**. Every scene says so. Crops and scaling improve readability; no screenshot text, figures, or application outcomes were fabricated. Captures precede final wording refinements to restart disclosures and metric labels; the video crops exclude the old metric labels. `demo-manifest.json` records source hashes, crop rectangles, timing, synthetic voice provenance, and the final output hash.

The narration uses the macOS Samantha system voice, labeled in the video. It does not imitate a team member. No paid service, remote model call, or voice-cloning service was used.

## Rebuild

Requires Python with Pillow, local FFmpeg/FFprobe, and macOS `say` with Samantha. The script checks tools and rejects a pitch over three minutes. It writes intermediate audio and frames into ignored `artifacts/demo-build/`.

```sh
python3 submission/build-demo.py
```

On this workspace, Pillow is available in the Codex bundled Python runtime. `DEMO_FONT` may point to an installed TrueType/OpenType font; the default is the built-in macOS Avenir Next collection. Font choice and local voice versions can change layout and timing, so repeat visual and media checks after rebuilding.

```sh
ffprobe -v error -show_entries format=duration,size:stream=codec_name,width,height,sample_rate,channels -of json submission/claro-demo.mp4
ffmpeg -v error -i submission/claro-demo.mp4 -f null -
ffmpeg -hide_banner -i submission/claro-demo.mp4 -vn -af volumedetect -f null -
```

Validation: all nine composed scene images visually inspected; full encoded file decoded without errors; audio contains signal with measured mean −16.0 dB and peak −1.5 dB; embedded captions and external SRT present. This establishes stream health and timing, not an independent linguistic or human listening review.

## References

- [Pillow ImageDraw](https://pillow.readthedocs.io/en/stable/reference/ImageDraw.html) for standard image/text composition.
- [FFmpeg formats](https://ffmpeg.org/ffmpeg-formats.html) for concat demuxing and MP4 output.
- [FFmpeg filters](https://ffmpeg.org/ffmpeg-filters.html) for audio padding and volume measurement.
- Local macOS `man say` for the system speech interface.
