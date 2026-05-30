# Codex Task — Foreign Video → Vietnamese Subtitle Tool v1

## Objective
Build a Windows 11 local-first Python CLI tool that converts a foreign-language video into a new MP4 with Vietnamese subtitles burned in.

The tool must be usable for videos the user owns, licenses, or has permission to adapt. Do not add scraping, watermark removal, or platform automation.

## Money-first outcome
Reduce the manual workflow for adapting English, Chinese, Japanese, Korean, and other foreign-language videos for Vietnamese content production.

## Scope v1
Implement a new independent package under:

```text
foreign_video_subtitle_tool/
```

Do not modify the legacy video reality editor pipeline except for root-level documentation links if needed.

## Required pipeline

```text
input video
→ validate FFmpeg / FFprobe
→ extract mono 16k WAV audio
→ transcribe with faster-whisper
→ save original transcript SRT
→ translate subtitle text into Vietnamese
→ save Vietnamese SRT
→ burn Vietnamese subtitles into MP4 with FFmpeg
→ write report.json and logs
```

## Translation modes
Implement both modes:

1. `manual` — default, no paid API required
   - Transcribe and export `original.srt`.
   - Create a copy-ready `translate_prompt.txt` for ChatGPT/Gemini.
   - Allow the user to place `vietnamese.srt` into the job folder and run `resume`.

2. `openai` — optional
   - Only activate when `OPENAI_API_KEY` is present.
   - Translate subtitle batches while preserving subtitle numbering and timestamps.
   - Read model name from `OPENAI_MODEL` environment variable.
   - Do not hardcode a model name.
   - Never commit secrets.

## CLI commands
Implement:

```bash
python -m foreign_video_subtitle_tool.cli doctor
python -m foreign_video_subtitle_tool.cli run --input "input/video.mp4" --translation-mode manual
python -m foreign_video_subtitle_tool.cli run --input "input/video.mp4" --translation-mode openai
python -m foreign_video_subtitle_tool.cli resume --job "output/<job_id>"
python -m foreign_video_subtitle_tool.cli batch --input-dir "input" --translation-mode manual
```

Optional flags:

```text
--language auto|en|zh|ja|ko|...
--model-size small|medium|large-v3
--device auto|cpu|cuda
--compute-type auto|int8|float16
--subtitle-style path/to/style.yaml
--force
--skip-burn
```

## Output structure

```text
output/<job_id>/
├── input_metadata.json
├── audio.wav
├── original.srt
├── translate_prompt.txt
├── vietnamese.srt
├── final_vi_sub.mp4
├── report.json
├── state.json
└── logs/
    └── run.log
```

## Resume behavior
- Each stage updates `state.json`.
- When re-running, skip completed stages whose output files exist and are non-empty.
- `--force` re-runs stages.
- Manual mode must stop cleanly after producing `original.srt` and `translate_prompt.txt` when `vietnamese.srt` does not exist.
- `resume` continues from the first incomplete stage.

## Subtitle rules
- Preserve exact timestamps.
- Keep Vietnamese subtitles concise and natural.
- Split long translated lines for readability.
- Default burn-in style should be readable for TikTok/Reels and general videos:
  - bottom-center
  - white text
  - black outline
  - safe bottom margin
  - UTF-8 compatible Vietnamese font fallback
- Support a YAML style config.
- Handle Windows paths with spaces.

## Package structure

```text
foreign_video_subtitle_tool/
├── __init__.py
├── cli.py
├── config.py
├── doctor.py
├── models.py
├── pipeline.py
├── state.py
├── logging_utils.py
├── ffmpeg_utils.py
├── audio.py
├── transcription.py
├── srt_utils.py
├── translation.py
└── rendering.py
```

Also add:

```text
docs/foreign_video_subtitle_tool/
├── README.md
├── PROJECT.md
├── STATE.md
└── CHANGELOG.md

examples/
├── subtitle_style.example.yaml
└── foreign_video_subtitle_commands.txt

.env.example
requirements-subtitle-tool.txt
tests_subtitle_tool/
```

## Dependencies
Prefer:

```text
faster-whisper
openai
PyYAML
pytest
```

FFmpeg and FFprobe are system dependencies. Keep optional API dependencies guarded so manual mode can work without an API key.

## Tests
Add tests for:
- SRT parsing and serialization.
- Translation batching preserving subtitle indices and timestamps.
- Resume / skip logic.
- FFmpeg command construction for Windows paths with spaces.
- Doctor command behavior using mocked binaries.
- Manual mode stopping cleanly before render when `vietnamese.srt` is missing.

Run:

```bash
python -m compileall foreign_video_subtitle_tool
python -m pytest -q tests_subtitle_tool
```

## Acceptance criteria
- A user can place a foreign-language `.mp4` in `input/` and run one command.
- The tool exports `original.srt` and a copy-ready translation prompt without requiring an API key.
- After adding `vietnamese.srt`, `resume` produces `final_vi_sub.mp4`.
- When `OPENAI_API_KEY` is configured, the optional mode can translate automatically.
- Errors are actionable and written in Vietnamese where user-facing.
- Existing legacy files remain working and unrelated code is not refactored.
- Include a concise completion report with commands run, tests passed, known limitations, and rollback instructions.

## Codex execution instruction
Create an isolated branch or Worktree named similar to:

```text
codex/foreign-video-vi-subtitle-tool-v1
```

Read `AGENTS.md`, inspect the repository, implement the complete v1 scope, run the verifiable tests, then open a pull request. Do not merge automatically.
