# CHANGELOG — Foreign Video → Vietnamese Subtitle Tool

## 2026-05-31 — PR feedback hardening

### Changed

- Reject translated subtitle blocks that preserve index/timestamp but leave text empty when the source subtitle has text.
- Render MP4 output with H.264 video, AAC 192k audio, and `+faststart` for better compatibility with WebM/MKV/AVI sources and social platforms.
- Include resolved path, file size, and `mtime_ns` in job identity and metadata to avoid stale cache reuse when a file is replaced at the same path.
- Persist failed stage status, error type/message, timestamp, report details, and log traceback before propagating pipeline errors.
- Continue batch processing after per-video failures and return a summary with a non-zero CLI exit when any item fails.
- Treat `faster_whisper` as a required `doctor` dependency while keeping `openai` and `yaml` optional/conditional.
- Load simple `.env` key/value files before OpenAI credential reads.
- Add GitHub Actions CI for compile and pytest checks.

### Rollback instructions

- Revert this commit to restore the previous validation/render/batch behavior.
- Delete generated `output/<job_id>/` folders if they contain failed-state reports or fingerprinted job directories from test runs.

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
