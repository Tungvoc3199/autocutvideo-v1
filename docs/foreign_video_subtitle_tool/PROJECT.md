# PROJECT — Foreign Video → Vietnamese Subtitle Tool v1

## Objective

Xây dựng tool CLI Python độc lập để chuyển video tiếng nước ngoài sang video MP4 có phụ đề tiếng Việt burn-in, chạy local-first trên Windows 11.

## Scope

- Validate FFmpeg/FFprobe.
- Extract audio WAV mono 16 kHz.
- Transcribe bằng faster-whisper.
- Xuất `original.srt`.
- Manual translation prompt cho ChatGPT/Gemini.
- Optional OpenAI translation khi người dùng cấu hình `OPENAI_API_KEY` và `OPENAI_MODEL`.
- Resume theo `state.json`, skip stage đã hoàn tất, hỗ trợ `--force`.
- Burn subtitle Việt bằng FFmpeg.
- Batch folder input.

## Constraints

- Không scraping, không CAPTCHA/account automation, không lưu credential.
- Chỉ xử lý video người dùng sở hữu/có quyền chuyển thể.
- Không refactor pipeline legacy không liên quan.
- Dùng `pathlib` và subprocess argument list để hỗ trợ Windows paths có dấu cách.

## Success criteria

Người dùng có thể thả video vào `input/`, chạy CLI, nhận `original.srt` và prompt dịch. Sau khi thêm `vietnamese.srt` hoặc dùng OpenAI mode, resume/run tạo `final_vi_sub.mp4` kèm log, report và state.
