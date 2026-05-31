# autocutvideo-v1

tự động phát hiện cắt đoạn video lỗi, ghép thành video hoàn chỉnh

## Foreign Video → Vietnamese Subtitle Tool v1

Tool mới nằm độc lập trong `foreign_video_subtitle_tool/` và tài liệu tại `docs/foreign_video_subtitle_tool/README.md`.

Lệnh nhanh:

```bash
python -m foreign_video_subtitle_tool.cli doctor
python -m foreign_video_subtitle_tool.cli run --input "input/video.mp4" --translation-mode manual
python -m foreign_video_subtitle_tool.cli resume --job "output/<job_id>"
```
