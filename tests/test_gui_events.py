"""창을 열지 않고 작업 결과 전달과 GUI 상태 전환을 검증한다."""
from pathlib import Path
from queue import Queue
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from gui import PhotoSearchApp
from models.analysis_report import AnalysisReport


class GuiEventTests(unittest.TestCase):
    def make_app(self):
        # Tk 창 생성 대신 화면 부품을 Mock으로 바꿔 이벤트 흐름만 확인한다.
        app = object.__new__(PhotoSearchApp)
        app.events = Queue()
        app.root = Mock()
        app.progress = Mock()
        app.status = Mock()
        app.report_status = Mock()
        app.folder_button = Mock()
        app.analyze_button = Mock()
        app.search_button = Mock()
        app.set_failures = Mock()
        app.search_service = None
        app.busy = True
        return app

    def test_analysis_completion_enables_search(self):
        app = self.make_app()
        search_service = Mock()
        app.events.put(('progress', (3, 3)))
        app.events.put(('analyzed', (AnalysisReport(), search_service)))
        app.poll_events()
        app.progress.configure.assert_called_once_with(maximum=3, value=3)
        self.assertIs(app.search_service, search_service)
        self.assertFalse(app.busy)
        app.search_button.configure.assert_called_with(state='normal')
        app.root.after.assert_called_once()

    def test_analysis_error_does_not_enable_search(self):
        app = self.make_app()
        app.events.put(('error', 'storage failed'))
        app.poll_events()
        self.assertFalse(app.busy)
        self.assertIsNone(app.search_service)
        app.search_button.configure.assert_called_with(state='disabled')
        self.assertIn('storage failed', app.status.set.call_args.args[0])


    def run_analysis(self, *, save_error=None, analysis_error=None, demo=False):
        app = self.make_app()
        app.busy = False
        app.demo = demo
        app.folder = Mock()
        app.folder.get.return_value = "photos"
        app.clear_results = Mock()
        report, search = AnalysisReport(), Mock()
        analysis = Mock()
        analysis.analyze.return_value = report
        if analysis_error:
            analysis.analyze.side_effect = analysis_error
        app.service_factory = Mock(return_value=(analysis, search))
        app.report_writer = Mock()
        app.report_writer.save.return_value = Path("saved-analysis.json")
        if save_error:
            app.report_writer.save.side_effect = save_error
        with patch("gui.Thread", side_effect=lambda target, daemon: SimpleNamespace(start=target)):
            app.analyze()
        app.poll_events()
        return app, report, search

    def test_gui_saves_report_and_displays_path_after_analysis(self):
        app, report, search = self.run_analysis()
        args, kwargs = app.report_writer.save.call_args
        self.assertEqual(args, (report, "photos"))
        self.assertFalse(kwargs["demo"])
        self.assertGreaterEqual(kwargs["elapsed_seconds"], 0)
        app.report_status.set.assert_called_with("saved-analysis.json")
        self.assertIs(app.search_service, search)
        self.assertFalse(app.busy)

    def test_report_save_failure_keeps_analysis_and_search_available(self):
        app, _, search = self.run_analysis(save_error=PermissionError("permission denied"))
        self.assertIs(app.search_service, search)
        app.search_button.configure.assert_called_with(state="normal")
        self.assertIn("보고서 저장 실패", app.report_status.set.call_args.args[0])
        self.assertIn("permission denied", app.report_status.set.call_args.args[0])
        self.assertIn("분석 완료", app.status.set.call_args.args[0])

    def test_aborted_analysis_does_not_write_a_completed_report(self):
        app, _, _ = self.run_analysis(analysis_error=RuntimeError("model failed"))
        app.report_writer.save.assert_not_called()
        self.assertIsNone(app.search_service)
        self.assertIn("보고서가 생성되지 않았습니다", app.report_status.set.call_args.args[0])

    def test_gui_marks_virtual_analysis_as_demo(self):
        app, _, _ = self.run_analysis(demo=True)
        self.assertTrue(app.report_writer.save.call_args.kwargs["demo"])


if __name__ == '__main__':
    unittest.main()
