from __future__ import annotations

from pathlib import Path

from src.core.models import ClipDecision, SegmentAnalysis
from src.io.files import save_csv, save_json


def write_reports(
    analyses: list[SegmentAnalysis], decisions: list[ClipDecision], stitch_result: dict, output_dir: str | Path
) -> None:
    out = Path(output_dir)
    rows = []
    for a in analyses:
        rows.append(
            {
                "video_path": a.segment.video_path,
                "start": a.segment.start,
                "end": a.segment.end,
                "realism_score": a.realism_score,
                "confidence": a.confidence,
                "critical_failures": ";".join(a.critical_failures),
                "needs_review": a.needs_review,
                **a.metrics,
            }
        )

    decisions_json = []
    for d in decisions:
        decisions_json.append(
            {
                "video_path": d.video_path,
                "rejected": d.rejected,
                "reasons": d.reasons,
                "kept_segments": [k.to_dict() for k in d.kept_segments],
                "rejected_segments": [r.to_dict() for r in d.rejected_segments],
            }
        )

    summary = {
        "segments_total": len(analyses),
        "segments_kept": sum(len(d.kept_segments) for d in decisions),
        "clips_rejected": sum(1 for d in decisions if d.rejected),
        "final": stitch_result,
        "rejected_clips": [
            {"video_path": d.video_path, "reasons": d.reasons} for d in decisions if d.rejected
        ],
    }

    save_json([a.to_dict() for a in analyses], out / "analysis_results.json")
    save_json(decisions_json, out / "edit_decisions.json")
    save_json(summary, out / "report.json")
    save_csv(rows, out / "report.csv")
