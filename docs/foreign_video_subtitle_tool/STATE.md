# STATE — Foreign Video → Vietnamese Subtitle Tool v1

## Current status

Implemented baseline v1 package under `foreign_video_subtitle_tool/` with CLI, pipeline stages, docs, examples, tests, and feedback fixes for safer manual translation resume validation.

## Completed items

- `doctor`, `run`, `resume`, `batch` commands.
- Manual and optional OpenAI translation paths.
- FFmpeg audio extraction and subtitle burn command construction.
- faster-whisper transcription integration guarded by dependency checks.
- `state.json`, `report.json`, logs and deterministic job folders.
- Unit tests for SRT, translation batching, resume/skip logic, doctor, FFmpeg command construction, manual stop behavior, fenced SRT parsing, and manual translation timestamp validation.

## Pending items

- Real media integration smoke test on a Windows 11 machine with FFmpeg and faster-whisper model downloads available.
- Visual tuning of subtitle style against representative TikTok/Reels footage.

## Known limitations

- First faster-whisper run may download model files and can be slow.
- OpenAI mode depends on the user's configured model and account access.
- Burn-in styling depends on fonts installed on the host machine.
