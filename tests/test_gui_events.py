"""창을 열지 않고 작업 결과 전달과 GUI 상태 전환을 검증한다."""
from queue import Queue
import unittest
from unittest.mock import Mock

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


if __name__ == '__main__':
    unittest.main()
