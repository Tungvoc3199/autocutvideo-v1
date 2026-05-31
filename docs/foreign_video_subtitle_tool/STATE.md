# STATE — Foreign Video → Vietnamese Subtitle Tool v1

## Current status

Implemented baseline v1 package under `foreign_video_subtitle_tool/` with CLI, pipeline stages, docs, examples, tests, CI, and feedback fixes for safer rendering, resumability, batch behavior, and manual translation validation.

## Completed items

- `doctor`, `run`, `resume`, `batch` commands.
- Manual and optional OpenAI translation paths.
- FFmpeg audio extraction and subtitle burn command construction.
- MP4 render now uses H.264 video, AAC audio at 192k, and `+faststart` instead of stream-copying potentially incompatible source audio.
- faster-whisper is treated as a required doctor dependency; OpenAI and PyYAML remain optional/conditional.
- `.env` is loaded for OpenAI mode without overriding exported environment variables.
- Input job identity includes resolved path, file size, and `mtime_ns` so replacing a video at the same path does not reuse stale outputs.
- `state.json`, `report.json`, logs, failed stage details, and deterministic job folders.
- Batch processing continues after per-video failures and prints a success/failed/skipped summary.
- CI workflow runs compile and pytest checks on pull requests.
- Unit tests for SRT parsing, translation batching, empty translated subtitle rejection, resume/skip logic, input fingerprinting, failed-state persistence, batch continuation, doctor behavior, FFmpeg command construction, manual stop behavior, fenced SRT parsing, and manual translation timestamp validation.

## Pending items

- Real media integration smoke test on a Windows 11 machine with FFmpeg and faster-whisper model downloads available.
- Windows checklist still to run on real owned/licensed media:
  - MP4/AAC
  - WebM/Opus
  - MKV
  - path with spaces
  - path with Vietnamese characters
  - manual resume
  - malformed manual SRT
  - mixed batch success/failure
- Visual tuning of subtitle style against representative TikTok/Reels footage.

## Known limitations

- First faster-whisper run may download model files and can be slow.
- OpenAI mode depends on the user's configured model and account access.
- Burn-in styling depends on fonts installed on the host machine.
- Sandbox verification did not include real FFmpeg/faster-whisper media processing because those binaries/packages are not installed here.
