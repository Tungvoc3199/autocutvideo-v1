# video_reality_editor

`video_reality_editor` is a fully local, CLI-first Windows 11 video quality pipeline that detects technically unrealistic/low-trust spans (artifact-heavy, flickery, warped, unstable segments), trims/rejects those spans, and stitches higher-quality spans into a polished final MP4.

## 1) Project plan

1. **Ingest**: discover video files (`.mp4/.mov/.mkv`) and probe metadata via `ffprobe`.
2. **Segment**: split each clip into fixed windows and optionally merge scene boundaries from PySceneDetect.
3. **Analyze**: compute heuristic quality metrics per segment with OpenCV + NumPy.
4. **Score**: map metrics to weighted realism score (0–100), confidence, critical failures, and review queue flags.
5. **Decide**: reject low-scoring/broken spans, trim safety padding around kept spans, and reject entire clips that become too short.
6. **Stitch**: extract kept spans, normalize video/audio with FFmpeg, and concat into `final_video.mp4`.
7. **Report**: emit `report.json`, `report.csv`, per-segment diagnostics, rejected clip reasons, and decision logs.
8. **Resume**: reuse cached scan/analysis JSON for deterministic reruns.

## 2) Repository structure

```text
video_reality_editor/
  main.py
  requirements.txt
  config.example.yaml
  README.md
  src/
    cli/main_cli.py
    core/{config.py,models.py,decision.py,pipeline.py,reporting.py}
    analysis/{segmentation.py,scene_detect.py,metrics.py,plugins.py}
    scoring/scorer.py
    stitching/stitcher.py
    io/{files.py,ingest.py}
    utils/{logger.py,ffmpeg_utils.py}
  tests/
    test_scorer.py
    test_decision.py
  examples/
    sample_commands.txt
  input_videos/
  output/
```

## 3) Features implemented

- **Scan**: metadata extraction (duration/fps/resolution/audio/aspect).
- **Analyze** metrics:
  - sharpness/blur (Laplacian variance)
  - flicker (inter-frame luminance variance)
  - duplicate/frozen frame ratio (frame-diff threshold)
  - exposure stability (brightness evolution)
  - color consistency (histogram drift)
  - motion stability (optical flow variance)
  - face consistency (Haar face count stability if detectable)
  - heuristic artifact risks (hand/body/object)
  - continuity potential and corrupted-frame ratio
  - optional plugin hook for advanced local models
- **Scoring**:
  - weighted realism score (0–100)
  - confidence score
  - critical failure detection
  - `needs_review` tagging for low-confidence segments
- **Repair/stitch**:
  - segment rejection + trim padding
  - clip rejection if too short
  - FFmpeg normalization + concat
- **Reports**:
  - `analysis_results.json`
  - `edit_decisions.json`
  - `report.json`
  - `report.csv`

## 4) Install on Windows 11

### Prerequisites
- Python 3.11 (64-bit)
- FFmpeg (must provide both `ffmpeg.exe` and `ffprobe.exe` in PATH)

### Setup
```powershell
# from repository root
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt
```

### Verify FFmpeg
```powershell
ffmpeg -version
ffprobe -version
```

## 5) Usage

### Full pipeline
```powershell
python main.py run-all --input .\input_videos --output .\output --config .\config.example.yaml
```

### Individual stages
```powershell
python main.py scan --input .\input_videos --output .\output --config .\config.example.yaml
python main.py analyze --input .\input_videos --output .\output --config .\config.example.yaml
python main.py stitch --analysis .\output --output .\output --config .\config.example.yaml
python main.py resume --input .\input_videos --output .\output --config .\config.example.yaml
```

### Demo command
```powershell
python main.py demo --output .\output --config .\config.example.yaml
```

## 6) Output files

- `output/pipeline.log`
- `output/scan_metadata.json`
- `output/analysis_results.json`
- `output/edit_decisions.json`
- `output/report.json`
- `output/report.csv`
- `output/final_video.mp4`

## 7) Troubleshooting

- **"ffmpeg/ffprobe not found"**: install FFmpeg and add `bin` directory to PATH.
- **No videos detected**: ensure files are in `input_videos/` and extensions are `mp4/mov/mkv`.
- **Very few kept segments**: lower `realism_threshold` or reduce `trim_padding_ms`.
- **Slow processing**: increase `analysis_window_sec` (fewer segments) and reduce target resolution.

## 8) Determinism and resumability

- Same input + same config -> deterministic scoring flow.
- `resume` command loads cached analysis from `output/analysis_results.json` when present.

## 9) Safety and limitations

- Heuristics are strong baselines, not perfect truth detectors.
- If confidence is low, segments are flagged as **needs review** instead of overconfident classification.
- Lip-sync scoring is currently heuristic fallback (`0.5`) unless extended via plugin.

## 10) Advanced extension point

Implement `VisionAnalyzerPlugin` in `src/analysis/plugins.py` and pass it into `SegmentAnalyzer` to add local VLM/face-recognition/semantic artifact checks without changing core pipeline.
