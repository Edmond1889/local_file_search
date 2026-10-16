"""보고서 내용·파일 충돌·저장 실패·실행 위치와 독립적인 경로를 검증한다."""
from datetime import datetime, timezone
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from models.analysis_report import AnalysisFailure, AnalysisReport
from models.file_info import FileInfo
from services.report_writer import AnalysisReportWriter


class ReportWriterTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.output = Path(self.temp.name) / "reports"
        self.writer = AnalysisReportWriter(self.output)
        self.started_at = datetime(2026, 10, 16, tzinfo=timezone.utc)
        self.file = FileInfo("고양이.jpg", str(Path(self.temp.name) / "고양이.jpg"), ".jpg", 123, 100.0)

    def save(self, report, **kwargs):
        return self.writer.save(report, self.temp.name, started_at=self.started_at,
                                elapsed_seconds=1.25, **kwargs)

    def test_report_keeps_unicode_metadata_counts_and_failure_reason(self):
        broken = FileInfo("손상.png", str(Path(self.temp.name) / "손상.png"), ".png", 0, None)
        report = AnalysisReport([self.file], [AnalysisFailure(broken, "0바이트 파일")])
        path = self.save(report)
        text = path.read_text(encoding="utf-8")
        data = json.loads(text)
        self.assertIn("고양이", text)
        self.assertEqual(data["summary"], {"processed_count": 2, "indexed_count": 1, "failure_count": 1})
        self.assertEqual(data["indexed_files"][0]["path"], self.file.path)
        self.assertEqual(data["failures"][0]["reason"], "0바이트 파일")
        self.assertEqual(data["source_folder"], str(Path(self.temp.name).resolve()))
        self.assertEqual(data["started_at"], self.started_at.isoformat())
        self.assertIsNotNone(datetime.fromisoformat(data["finished_at"]).tzinfo)
        self.assertEqual(data["elapsed_seconds"], 1.25)
        self.assertEqual(data["mode"], "real")

    def test_repeated_saves_keep_previous_reports(self):
        first = self.save(AnalysisReport([self.file]))
        original = first.read_bytes()
        second = self.save(AnalysisReport())
        self.assertNotEqual(first, second)
        self.assertEqual(first.read_bytes(), original)
        self.assertEqual(len(list(self.output.glob("*.json"))), 2)
        self.assertEqual(json.loads(second.read_text(encoding="utf-8"))["summary"]["processed_count"], 0)

    def test_demo_is_explicit_in_filename_and_content(self):
        path = self.save(AnalysisReport(), demo=True)
        self.assertTrue(path.name.startswith("analysis_demo_"))
        self.assertEqual(json.loads(path.read_text(encoding="utf-8"))["mode"], "demo")

    def test_default_directory_uses_project_root_without_creating_it(self):
        self.assertEqual(AnalysisReportWriter().output_dir,
                         Path(__file__).resolve().parents[1] / "reports")

    def test_invalid_data_does_not_leave_a_report(self):
        self.file.modified_time = float("nan")
        with self.assertRaises(ValueError):
            self.save(AnalysisReport([self.file]))
        self.assertFalse(self.output.exists())

    def test_failed_publish_cleans_temporary_file_and_leaves_no_final_json(self):
        with patch("services.report_writer.os.replace", side_effect=PermissionError("read-only")):
            with self.assertRaises(PermissionError):
                self.save(AnalysisReport([self.file]))
        self.assertEqual(list(self.output.iterdir()), [])

    def test_output_directory_error_is_reported_to_caller(self):
        self.output.write_text("not a directory", encoding="utf-8")
        with self.assertRaises(OSError):
            self.save(AnalysisReport())
        self.assertEqual(self.output.read_text(encoding="utf-8"), "not a directory")
