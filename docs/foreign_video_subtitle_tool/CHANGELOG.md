# CHANGELOG — Foreign Video → Vietnamese Subtitle Tool

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
