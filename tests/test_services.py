import unittest
from unittest.mock import Mock

from demo.demo_adapters import (
    DemoImageEncoder, DemoImageLoader, DemoRepository,
    DemoScanner, DemoTextEncoder, DemoVectorIndex,
)
from interface import ImageLoadError
from services.analysis_service import AnalysisService
from services.search_service import SearchService


class ServiceTests(unittest.TestCase):
    def test_progress_includes_failure_and_finishes_at_total(self):
        repository, index = DemoRepository(), DemoVectorIndex()
        callback = Mock()
        AnalysisService(DemoScanner(), DemoImageLoader(), DemoImageEncoder(), repository, index).analyze('demo', callback)
        self.assertEqual([call.args for call in callback.call_args_list], [(0, 3), (1, 3), (2, 3), (3, 3)])

    def test_empty_folder_reports_zero_progress(self):
        scanner, callback = Mock(), Mock()
        scanner.scan.return_value = []
        report = AnalysisService(scanner, Mock(), Mock(), Mock(), Mock()).analyze('empty', callback)
        callback.assert_called_once_with(0, 0)
        self.assertEqual(report.indexed_files, [])

    def test_analysis_and_search_share_file_ids(self):
        repository, index = DemoRepository(), DemoVectorIndex()
        analysis = AnalysisService(
            DemoScanner(), DemoImageLoader(), DemoImageEncoder(), repository, index,
        )
        report = analysis.analyze('demo')
        self.assertEqual(len(report.indexed_files), 2)
        self.assertEqual(len(report.failures), 1)
        self.assertEqual(report.failures[0].file.name, 'broken.jpg')
        results = SearchService(DemoTextEncoder(), index, repository).search('a sentence')
        self.assertEqual([r.file.name for r in results], ['sample_a.jpg', 'sample_b.jpg'])
        self.assertEqual([r.score for r in results], [1.0, 0.0])

    def test_damaged_image_does_not_stop_next_file(self):
        files = DemoScanner().scan('demo')
        scanner, loader, encoder, repository, index = [Mock() for _ in range(5)]
        scanner.scan.return_value = files[:2]
        loader.load.side_effect = [ImageLoadError('broken'), 'loaded image']
        encoder.encode.return_value = [0.5, 0.5]
        repository.save.return_value = 42
        report = AnalysisService(scanner, loader, encoder, repository, index).analyze('demo')
        self.assertEqual(report.indexed_files, [files[1]])
        repository.save.assert_called_once_with(files[1])
        index.add.assert_called_once_with(42, [0.5, 0.5])

    def test_full_sentence_and_top_k_are_forwarded(self):
        encoder, index, repository = Mock(), Mock(), Mock()
        encoder.encode.return_value = [0.2, 0.8]
        index.search.return_value = [(42, 0.9)]
        repository.find_by_id.return_value = DemoScanner().scan('demo')[0]
        result = SearchService(encoder, index, repository).search('  a cat on a chair  ', 1)
        encoder.encode.assert_called_once_with('a cat on a chair')
        index.search.assert_called_once_with([0.2, 0.8], 1)
        repository.find_by_id.assert_called_once_with(42)
        self.assertEqual(result[0].score, 0.9)

    def test_empty_query_and_invalid_count_skip_encoding(self):
        encoder = Mock()
        service = SearchService(encoder, Mock(), Mock())
        for query, count in [('   ', 5), ('cat', 0), ('cat', -1)]:
            self.assertEqual(service.search(query, count), [])
        encoder.encode.assert_not_called()

    def test_missing_metadata_is_reported(self):
        index, repository = Mock(), Mock()
        index.search.return_value = [(42, 0.9)]
        repository.find_by_id.return_value = None
        with self.assertRaises(LookupError):
            SearchService(Mock(), index, repository).search('cat')

    def test_storage_failure_is_not_reported_as_success(self):
        scanner, repository = Mock(), Mock()
        scanner.scan.return_value = DemoScanner().scan('demo')[:1]
        repository.save.side_effect = RuntimeError('storage failed')
        index = Mock()
        with self.assertRaises(RuntimeError):
            AnalysisService(scanner, DemoImageLoader(), DemoImageEncoder(), repository, index).analyze('demo')
        index.add.assert_not_called()


if __name__ == '__main__':
    unittest.main()
