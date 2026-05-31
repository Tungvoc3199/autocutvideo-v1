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

Tạo biến môi trường, không commit secret. Tool cũng tự đọc file `.env` dạng `KEY=VALUE` trong thư mục đang chạy và không ghi đè biến môi trường đã export:

```powershell
$env:OPENAI_API_KEY="sk-..."
$env:OPENAI_MODEL="model-name-from-your-account"
python -m foreign_video_subtitle_tool.cli run --input "input\video.mp4" --translation-mode openai
```

## Batch nhiều video

```powershell
python -m foreign_video_subtitle_tool.cli batch --input-dir "input" --translation-mode manual
```

Batch sẽ tiếp tục xử lý video còn lại nếu một video lỗi, in summary `success/failed/skipped`, và trả exit code `1` nếu có bất kỳ job nào thất bại.

## Resume, cache, và lỗi

- Job id được tính từ path đã resolve, kích thước file, và `mtime_ns`; nếu bạn thay video mới vào cùng một path, tool tạo job mới thay vì dùng lại subtitle/audio cũ.
- Khi stage lỗi, `state.json` đánh dấu stage đó là `failed`; `report.json` ghi `failed_stage`, loại lỗi, thông báo lỗi, và timestamp để resume/debug dễ hơn.
- Resume sẽ chạy lại stage chưa hoàn tất hoặc stage failed; dùng `--force` để chạy lại toàn bộ stage đã completed.

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
- `vietnamese.srt` bị từ chối khi `resume`: kiểm tra bản dịch có giữ nguyên 100% số thứ tự/timestamp từ `original.srt` và không để trống nội dung subtitle khi bản gốc có text; tool sẽ tự bỏ code fence Markdown phổ biến và wrap lại dòng phụ đề nếu hợp lệ.
- Phụ đề lỗi font tiếng Việt: chỉnh `font_name` trong YAML style sang font có sẵn trên máy Windows, ví dụ Arial hoặc Segoe UI.

## CI và checklist smoke test Windows

GitHub Actions chạy tối thiểu:

```bash
python -m compileall foreign_video_subtitle_tool
python -m pytest -q tests_subtitle_tool
```

Checklist cần chạy thủ công trên Windows 11 với media bạn sở hữu/có quyền dùng:

- MP4/AAC
- WebM/Opus
- MKV
- Path có dấu cách
- Path có ký tự tiếng Việt
- Manual resume
- Malformed manual SRT
- Mixed batch success/failure
