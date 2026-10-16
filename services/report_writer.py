"""완료된 분석 결과를 JSON으로 저장한다. DB나 벡터 인덱스의 백업은 아니다."""
from dataclasses import asdict
from datetime import datetime
import json
import os
from pathlib import Path
from tempfile import NamedTemporaryFile
from uuid import uuid4

from models.analysis_report import AnalysisReport


class AnalysisReportWriter:
    def __init__(self, output_dir: str | Path | None = None):
        # VS Code의 현재 터미널 위치와 관계없이 이 프로젝트 아래에 저장한다.
        self.output_dir = (Path(output_dir) if output_dir is not None
                           else Path(__file__).resolve().parents[1] / "reports").resolve()

    def save(self, report: AnalysisReport, folder_path: str, *,
             started_at: datetime, elapsed_seconds: float, demo: bool = False) -> Path:
        finished_at = datetime.now().astimezone()
        mode = "demo" if demo else "real"
        payload = {
            "schema_version": 1,
            "report_type": "image_analysis",
            "mode": mode,
            "started_at": started_at.isoformat(),
            "finished_at": finished_at.isoformat(),
            "elapsed_seconds": round(elapsed_seconds, 3),
            "source_folder": str(Path(folder_path).resolve()),
            "summary": {
                "processed_count": len(report.indexed_files) + len(report.failures),
                "indexed_count": len(report.indexed_files),
                "failure_count": len(report.failures),
            },
            "indexed_files": [asdict(file) for file in report.indexed_files],
            "failures": [{"file": asdict(failure.file), "reason": failure.reason}
                         for failure in report.failures],
        }
        # 한국어를 그대로 보존하고 직렬화 오류는 파일을 만들기 전에 발견한다.
        text = json.dumps(payload, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        name = f"analysis_{mode}_{finished_at:%Y%m%d_%H%M%S_%f}_{uuid4().hex}.json"
        destination = self.output_dir / name
        temporary = None
        try:
            # 다 쓰기 전에는 최종 JSON 이름으로 나타나지 않도록 한다.
            with NamedTemporaryFile(mode="w", encoding="utf-8", newline="\n",
                                    dir=self.output_dir, prefix=".analysis-",
                                    suffix=".tmp", delete=False) as output:
                temporary = Path(output.name)
                output.write(text)
            os.replace(temporary, destination)
            return destination
        finally:
            if temporary is not None:
                try:
                    temporary.unlink(missing_ok=True)
                except OSError:
                    pass  # 원래 저장 오류를 정리 오류로 가리지 않는다.
