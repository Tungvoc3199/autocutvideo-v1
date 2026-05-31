# CHANGELOG — Foreign Video → Vietnamese Subtitle Tool

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
