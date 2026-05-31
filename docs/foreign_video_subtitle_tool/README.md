# Foreign Video → Vietnamese Subtitle Tool v1

CLI Python local-first cho Windows 11 để tạo phụ đề tiếng Việt cho video bạn sở hữu, có license, hoặc được phép chuyển thể.

## Cài đặt Windows 11

1. Cài Python 3.11+.
2. Cài FFmpeg, bảo đảm `ffmpeg.exe` và `ffprobe.exe` nằm trong `PATH`.
3. Tạo môi trường ảo và cài dependency:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-subtitle-tool.txt
```

4. Kiểm tra môi trường:

```powershell
python -m foreign_video_subtitle_tool.cli doctor
```

## Chạy manual mode (mặc định, không cần API key)

```powershell
python -m foreign_video_subtitle_tool.cli run --input "input\video.mp4" --translation-mode manual
```

Tool sẽ tạo `output\<job_id>\original.srt` và `translate_prompt.txt`, sau đó dừng sạch để chờ bản dịch. Mở `translate_prompt.txt`, copy sang ChatGPT/Gemini, lưu kết quả thành `output\<job_id>\vietnamese.srt`, rồi chạy:

```powershell
python -m foreign_video_subtitle_tool.cli resume --job "output\<job_id>"
```

## Chạy OpenAI mode (tuỳ chọn)

Tạo biến môi trường hoặc file `.env` local, không commit secret. OpenAI mode sẽ đọc `.env` dạng `KEY=VALUE` nếu biến chưa có sẵn trong process environment:

```powershell
$env:OPENAI_API_KEY="sk-..."
$env:OPENAI_MODEL="model-name-from-your-account"
python -m foreign_video_subtitle_tool.cli run --input "input\video.mp4" --translation-mode openai
```

## Batch nhiều video

```powershell
python -m foreign_video_subtitle_tool.cli batch --input-dir "input" --translation-mode manual
```

## Output

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
└── logs/run.log
```

## Tuỳ chọn hữu ích

- `--language auto|en|zh|ja|ko|...`
- `--model-size small|medium|large-v3`
- `--device auto|cpu|cuda`
- `--compute-type auto|int8|float16`
- `--subtitle-style examples/subtitle_style.example.yaml`
- `--force` chạy lại stage đã hoàn tất.
- `--skip-burn` tạo SRT nhưng không render video.

## Troubleshooting

- `Không tìm thấy ffmpeg/ffprobe`: cài FFmpeg, thêm thư mục `bin` vào `PATH`, mở terminal mới.
- `Chưa cài faster-whisper`: chạy `python -m pip install -r requirements-subtitle-tool.txt`.
- OpenAI mode báo thiếu key/model: kiểm tra `OPENAI_API_KEY` và `OPENAI_MODEL`.
- `vietnamese.srt` bị từ chối khi `resume`: kiểm tra bản dịch có giữ nguyên 100% số thứ tự/timestamp từ `original.srt` và không để trống nội dung ở bất kỳ cue nào; tool sẽ tự bỏ code fence Markdown phổ biến và wrap lại dòng phụ đề nếu timestamp hợp lệ.
- Cache/resume: job id bao gồm đường dẫn tuyệt đối, kích thước file và `mtime_ns`, nên thay video mới vào cùng path sẽ tạo job folder mới thay vì tái dùng phụ đề cũ.
- Nếu một stage lỗi, `state.json`, `report.json`, và `logs/run.log` sẽ ghi stage `failed`, loại lỗi, message và timestamp để lần resume kế tiếp retry đúng stage lỗi.
- Batch mode tiếp tục xử lý video còn lại khi một job lỗi và trả exit code khác 0 nếu có bất kỳ failure nào.
- Phụ đề lỗi font tiếng Việt: chỉnh `font_name` trong YAML style sang font có sẵn trên máy Windows, ví dụ Arial hoặc Segoe UI.

## CI và smoke test Windows

CI tối thiểu chạy `python -m compileall foreign_video_subtitle_tool` và `python -m pytest -q tests_subtitle_tool` trên GitHub Actions. Checklist cần chạy thủ công trên Windows 11 khi có FFmpeg/model thật:

- MP4/AAC render end-to-end.
- WebM/Opus render sang MP4 với audio AAC.
- MKV input.
- Đường dẫn có dấu cách.
- Đường dẫn có ký tự tiếng Việt.
- Manual resume với `vietnamese.srt` hợp lệ.
- Manual resume với SRT malformed/thiếu nội dung để xác nhận bị reject.
- Mixed batch success/failure để xác nhận batch tiếp tục và summary đúng.
