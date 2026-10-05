# Claro demo video

The current local video uses the immediate chat, automatic ES/PT with stable identity, natural transaction references and the same composer for customer replies. Its diagrams use the finalized current deck and source-matched v3 regressions. The public v1.1 release and hosted application remain unchanged.

`claro-demo.mp4` is a 1920×1080 narrated walkthrough lasting **2 minutes 37.17 seconds**, below the three-minute submission limit. It contains H.264 video, AAC mono narration, and an English subtitle track. A separate `claro-demo.en.srt` and the full `demo-script.md` are included.

The nine scenes demonstrate transaction clarification, a specific redacted report, explicit confirmation, a verified receipt, analyst question, customer reply, persisted history, evaluation, and architectural boundaries. The captured interface includes Spanish and Portuguese; the narration is English.

## Provenance

The source JPEGs in `demo-assets/` are genuine CUA-controlled Chrome captures of the running app at `localhost:8096` / `127.0.0.1:8096` on October 4, 2026 in America/Bogota. Every screen contains team-authored fixtures. They were captured during actual customer and analyst actions described in `docs/UI.md`; case references belong only to that isolated local workspace.

This is an edited screenshot walkthrough with separately labeled architecture and evaluation slides, **not a continuous screen recording or proof of a hosted deployment**. Each scene identifies its source type. The two PNG diagrams come from the final presentation export. Crops and scaling improve readability; no screenshot text, figures, or application outcomes were fabricated. The source screenshots are unchanged. Declared crop rectangles frame the actual evidence, confirmation, receipt, reply composer, four-event timeline and closed-case answer. The reviewer timeline uses Spanish UI with a Spanish report and Portuguese question/reply. Historical dates and amounts remain visible: the same customer’s transaction TX-ES-102 is COP 129000.00, pending, from the June 17 snapshot. External provider inference was disabled for all captured app actions; the architecture slide and narration explicitly distinguish implemented integrations from unverified live inference. `demo-manifest.json` records source hashes, crop rectangles, timing, synthetic voice provenance, and the final output hash.

The narration uses the macOS Samantha system voice, labeled in the video. It does not imitate a team member. No paid service, remote model call, or voice-cloning service was used.

## Rebuild

Requires Python with Pillow, local FFmpeg/FFprobe, and macOS `say` with Samantha. The script checks tools and rejects a pitch over three minutes. It writes intermediate audio and frames into ignored `artifacts/demo-build/`.

```sh
python3 submission/build-demo.py
```

On this workspace, Pillow is available in the Codex bundled Python runtime. `DEMO_FONT` may point to an installed TrueType/OpenType font; the default is the built-in macOS Avenir Next collection. Font choice and local voice versions can change layout and timing, so repeat visual and media checks after rebuilding.

Each actual-app scene declares `capture_provenance` in `demo-scenes.json`; the builder refuses an app scene without it and records it per scene and in the aggregate manifest. The current captures use `http://127.0.0.1:8096`, October 4, 2026 America/Bogota, team fixtures and disabled providers. No hardcoded previous capture date is substituted. Scenes 7–8 are separately labeled diagrams copied from slides 3 and 5 of the finalized current deck. The manifest binds their source hashes to that deck. Rebuilding resets generated media receipts; repeat source, scene and encoded-stream checks before claiming a later build verified.

```sh
ffprobe -v error -show_entries format=duration,size:stream=codec_name,width,height,sample_rate,channels -of json submission/claro-demo.mp4
ffmpeg -v error -i submission/claro-demo.mp4 -f null -
ffmpeg -hide_banner -i submission/claro-demo.mp4 -vn -af volumedetect -f null -
```

Validation: all nine composed scene images visually inspected; full encoded file decoded without errors; audio contains signal with measured mean −16.0 dB and peak −1.1 dB; H.264 1080p at 24 fps, AAC mono 48 kHz, English embedded captions and 29 external SRT cues are present. This establishes stream health and timing, not an independent linguistic or human listening review.

## References

- [Pillow ImageDraw](https://pillow.readthedocs.io/en/stable/reference/ImageDraw.html) for standard image/text composition.
- [FFmpeg formats](https://ffmpeg.org/ffmpeg-formats.html) for concat demuxing and MP4 output.
- [FFmpeg filters](https://ffmpeg.org/ffmpeg-filters.html) for audio padding and volume measurement.
- Local macOS `man say` for the system speech interface.
