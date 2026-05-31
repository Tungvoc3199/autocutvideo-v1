# CHANGELOG — Foreign Video → Vietnamese Subtitle Tool

## 2026-05-31 — PR review implementation fixes

### Changed

- Reject translated subtitle cues with empty text when the source cue has content.
- Render MP4 outputs with H.264 video, AAC 192k audio, and `+faststart`; escape apostrophes using FFmpeg single-quote rules.
- Include resolved path, size, and `mtime_ns` input fingerprint in job identity and metadata to avoid stale cache reuse.
- Persist failed stage details to `state.json`, `report.json`, and `logs/run.log`.
- Continue batch processing after per-video failures and return a partial-failure summary/exit code.
- Treat `faster_whisper` as a required doctor dependency; keep OpenAI and PyYAML optional/conditional.
- Load simple `.env` values before reading OpenAI credentials.
- Add GitHub Actions CI for compile and pytest checks.

### Rollback instructions

- Revert this commit to restore the previous PR feedback-fix behavior.
- Delete affected `output/<job_id>/` folders if they contain failed-state reports or fingerprinted cache folders you no longer need.

## 2026-05-31 — v1 feedback fixes

### Changed

- Validate manual `vietnamese.srt` against `original.srt` before rendering so subtitle numbering and timestamps cannot drift during `resume`.
- Normalize translated subtitle line wrapping in place after validation for readability.
- Accept common Markdown fenced SRT output from ChatGPT/Gemini/OpenAI before parsing.

### Rollback instructions

- Revert this commit to return to baseline v1 behavior.
- Delete generated `output/<job_id>/` folders if they contain unwanted normalized SRT artifacts.

## 2026-05-31 — v1 baseline

### Added

- Independent `foreign_video_subtitle_tool` Python package.
- CLI commands for doctor, single run, resume, and batch.
- Manual translation prompt workflow and optional OpenAI translation.
- FFmpeg/FFprobe validation, audio extraction, subtitle rendering.
- State, report, logs, examples, dependency file, and tests.

### Rollback instructions

- Delete generated `output/<job_id>/` folders to remove local artifacts.
- Revert this branch/PR to remove code changes.
