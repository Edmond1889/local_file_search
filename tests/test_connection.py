from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import Mock

from connection.service import TextSearch
from file_encoder.encoder import FileEncoder
from similarity.comparison import SimilaritySearch
from file_loader.loader import find_files, load_file


class ConnectionTests(unittest.TestCase):
    def test_loader_loads_file(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / 'test.txt'
            path.write_text('본문 읽기', encoding='utf-8')
            self.assertEqual(find_files(directory), [path])
            info, text = load_file(path)
            self.assertEqual(text, '본문 읽기')
            self.assertEqual(info.file_name, 'test.txt')

    def test_missing_file_encoder_does_not_save_metadata(self):
        with TemporaryDirectory() as directory:
            (Path(directory) / 'test.txt').write_text('본문', encoding='utf-8')
            repository = Mock()
            service = TextSearch(FileEncoder(), Mock(), repository, SimilaritySearch())
            with self.assertRaises(NotImplementedError):
                service.analyze(directory)
            repository.save.assert_not_called()

    def test_query_encoder_is_only_used_for_query(self):
        query_encoder = Mock()
        query_encoder.encode_text.return_value = [1, 2]
        service = TextSearch(FileEncoder(), query_encoder, Mock(), SimilaritySearch())
        self.assertEqual(service.encode_query('  검색 문장  '), [1, 2])
        query_encoder.encode_text.assert_called_once_with('검색 문장')
        with self.assertRaises(NotImplementedError):
            service.search('검색 문장')
