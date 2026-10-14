"""실제 SQLite/FAISS와 연결하되 AI 모델 대신 명시적인 테스트 벡터를 사용한다."""
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import importlib.util
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

from models.file_info import FileInfo

HAS_DATABASE_DEPS = all(importlib.util.find_spec(name) is not None for name in ("numpy", "faiss"))
if HAS_DATABASE_DEPS:
    import numpy as np
    from adapters.repository_adapter import RepositoryAdapter
    from db_manager import Repository as DatabaseRepository, VectorIndex
    from image_loader import DefaultImageLoader
    from PIL import Image
    from services.analysis_service import AnalysisService
    from services.search_service import SearchService


@unittest.skipUnless(HAS_DATABASE_DEPS, "Install requirements-db.txt to run actual DB integration tests")
class RepositoryAdapterTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.photo = self.root / "sample.png"
        Image.new("RGB", (8, 8), "red").save(self.photo)
        # 소수점 마이크로초까지 저장·복원할 수 있는 고정 파일 수정 시각으로 검증한다.
        os.utime(self.photo, (1700000000.125, 1700000000.125))
        self.db_path = str(self.root / "metadata.db")
        self.database = DatabaseRepository(self.db_path)
        self.adapter = RepositoryAdapter(self.database)
        stat = self.photo.stat()
        self.info = FileInfo(self.photo.name, str(self.photo), ".png", stat.st_size, stat.st_mtime)

    def test_save_maps_fields_and_generates_full_file_hash(self):
        file_id = self.adapter.save(self.info)
        stored = self.database.find_by_id(file_id)
        self.assertEqual(stored.file_path, self.info.path)
        self.assertEqual(stored.file_name, self.info.name)
        self.assertEqual(stored.file_extension, ".png")
        self.assertEqual(stored.file_size, self.info.size)
        expected_hash = sha256(self.photo.read_bytes()).hexdigest()
        self.assertEqual(stored.file_hash, expected_hash)
        self.assertEqual(self.info.file_hash, expected_hash)
        self.assertEqual(stored.created_at, self.info.created_at)

    def test_lookup_returns_common_file_info_with_persisted_extra_fields(self):
        file_id = self.adapter.save(self.info)
        # 새 어댑터를 만들어도 DB에서 메타데이터를 복원할 수 있는지 확인한다.
        restored = RepositoryAdapter(DatabaseRepository(self.db_path)).find_by_id(file_id)
        self.assertIsInstance(restored, FileInfo)
        self.assertEqual(restored, self.info)

    def test_supplied_hash_and_created_at_are_preserved(self):
        self.info.file_hash = "provided-hash"
        self.info.created_at = "2026-10-14T00:00:00+00:00"
        with patch.object(self.adapter, "_file_hash", side_effect=AssertionError("must not recalculate")):
            file_id = self.adapter.save(self.info)
        stored = self.database.find_by_id(file_id)
        self.assertEqual(stored.file_hash, "provided-hash")
        self.assertEqual(stored.created_at, self.info.created_at)

    def test_updated_at_is_utc_file_time_not_database_save_time(self):
        file_id = self.adapter.save(self.info)
        stored = self.database.find_by_id(file_id)
        timestamp = datetime.fromisoformat(stored.updated_at)
        self.assertEqual(timestamp.utcoffset(), timedelta(0))
        self.assertAlmostEqual(timestamp.timestamp(), 1700000000.125, delta=0.000001)

    def test_unknown_modification_time_is_not_fabricated(self):
        self.info.modified_time = None
        file_id = self.adapter.save(self.info)
        self.assertEqual(self.database.find_by_id(file_id).updated_at, "")
        self.photo.unlink()
        self.assertIsNone(self.adapter.find_by_id(file_id).modified_time)

    def test_timezone_offset_is_restored_without_reading_deleted_file(self):
        file_id = self.adapter.save(self.info)
        stored = self.database.find_by_id(file_id)
        stored.updated_at = datetime.fromtimestamp(
            1700000000.125, timezone(timedelta(hours=9))
        ).isoformat(timespec="microseconds")
        database = Mock()
        database.find_by_id.return_value = stored
        self.photo.unlink()
        restored = RepositoryAdapter(database).find_by_id(file_id)
        self.assertAlmostEqual(restored.modified_time, 1700000000.125, delta=0.000001)

    def test_missing_id_returns_none(self):
        self.assertIsNone(self.adapter.find_by_id(999))

    def test_deleted_file_keeps_persisted_modification_time(self):
        file_id = self.adapter.save(self.info)
        self.photo.unlink()
        restored = self.adapter.find_by_id(file_id)
        self.assertEqual(restored.path, self.info.path)
        self.assertEqual(restored.file_hash, self.info.file_hash)
        self.assertAlmostEqual(restored.modified_time, self.info.modified_time, delta=0.000001)

    def test_missing_file_is_not_written_to_database(self):
        self.photo.unlink()
        with self.assertRaises(FileNotFoundError):
            self.adapter.save(self.info)
        self.assertIsNone(self.database.find_by_id(1))
        self.assertEqual(self.info.file_hash, "")

    def test_saved_modification_time_is_preserved_when_file_changes(self):
        file_id = self.adapter.save(self.info)
        os.utime(self.photo, (1700000000, 1700000000))
        restored = self.adapter.find_by_id(file_id)
        self.assertAlmostEqual(restored.modified_time, self.info.modified_time, delta=0.000001)
        self.assertNotEqual(restored.modified_time, self.photo.stat().st_mtime)

    def test_future_database_modification_time_is_forwarded_and_preserved(self):
        @dataclass
        class FutureDatabaseInfo:
            file_path: str
            file_name: str
            file_extension: str
            file_size: int
            file_hash: str
            created_at: str
            modified_time: float | None
        database = Mock()
        database.save.return_value = 42
        adapter = RepositoryAdapter(database)
        self.info.file_hash = "test-hash"
        with patch("adapters.repository_adapter.DatabaseFileInfo", FutureDatabaseInfo):
            self.assertEqual(adapter.save(self.info), 42)
        stored = database.save.call_args.args[0]
        self.assertEqual(stored.modified_time, self.info.modified_time)
        database.find_by_id.return_value = stored
        self.photo.unlink()
        self.assertEqual(adapter.find_by_id(42).modified_time, self.info.modified_time)

    def test_services_share_actual_database_and_faiss_through_adapter(self):
        # 사진 수집과 모델 다운로드를 이 DB 연결 테스트에서 분리한다.
        scanner = Mock()
        scanner.scan.return_value = [self.info]
        image_encoder, text_encoder = Mock(), Mock()
        def image_vector(image):
            self.assertIsInstance(image, Image.Image)
            self.assertEqual(image.mode, "RGB")
            image.close()
            return np.array([1.0, 0.0], dtype=np.float32)
        image_encoder.encode.side_effect = image_vector
        text_encoder.encode.return_value = np.array([1.0, 0.0], dtype=np.float32)
        index = VectorIndex(embedding_dim=2)
        analysis = AnalysisService(scanner, DefaultImageLoader(), image_encoder, self.adapter, index)
        search = SearchService(text_encoder, index, self.adapter)
        report = analysis.analyze(str(self.root))
        results = search.search("test sentence")
        self.assertEqual(report.indexed_files, [self.info])
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].file, self.info)
        self.assertEqual(results[0].score, 1.0)
        self.assertIsInstance(results[0].file.file_hash, str)


if __name__ == "__main__":
    unittest.main()
