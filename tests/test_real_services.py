"""실제 사진·SQLite·FAISS 연결을 모델 대역으로 검증한다."""
from pathlib import Path
from tempfile import TemporaryDirectory
from concurrent.futures import ThreadPoolExecutor
from unittest import TestCase
from unittest.mock import Mock

import numpy as np
from PIL import Image

from adapters.encoder_adapters import ImageEncoderAdapter, TextEncoderAdapter
from real_services import RealServiceFactory


class RealServiceTests(TestCase):
    def test_real_pipeline_and_reanalysis_across_gui_workers(self):
        # GUI처럼 분석과 검색을 서로 다른 작업 스레드에서 수행한다.
        def image_vector(image):
            vector = np.zeros(512, dtype=np.float32)
            vector[0 if image.getpixel((0, 0))[0] > 100 else 1] = 1
            return vector

        image_encoder = Mock()
        image_encoder.encode.side_effect = image_vector
        text_encoder = Mock()
        text_encoder.encode_text.side_effect = lambda query: np.eye(1, 512, 0 if query == "빨강" else 1)[0]
        provider = Mock(return_value=(image_encoder, text_encoder))
        factory = RealServiceFactory(provider)
        with TemporaryDirectory() as folder:
            Image.new("RGB", (4, 4), "red").save(Path(folder) / "red.png")
            Image.new("RGB", (4, 4), "blue").save(Path(folder) / "blue.png")
            (Path(folder) / "broken.jpg").write_bytes(b"broken")
            for repeat in range(2):
                # 새 분석은 같은 사진을 중복 INSERT하지 않는 새 DB/인덱스를 쓴다.
                with ThreadPoolExecutor(max_workers=1) as worker:
                    analysis, search = worker.submit(factory).result()
                    report = worker.submit(analysis.analyze, folder).result()
                self.assertEqual(len(report.indexed_files), 2)
                self.assertEqual(len(report.failures), 1)
                self.assertIs(analysis.repository, search.repository)
                self.assertIs(analysis.vector_index, search.vector_index)
                try:
                    with ThreadPoolExecutor(max_workers=1) as worker:
                        red = worker.submit(search.search, "빨강").result()
                        blue = worker.submit(search.search, "파랑").result()
                    self.assertEqual(red[0].file.name, "red.png")
                    self.assertEqual(blue[0].file.name, "blue.png")
                    self.assertTrue(red[0].file.file_hash)
                    self.assertIsNotNone(red[0].file.modified_time)
                finally:
                    analysis.repository.session_directory.cleanup()
        provider.assert_called_once()

    def test_encoder_rejects_wrong_shape_nan_and_zero(self):
        for value in (np.ones(511), np.ones((1, 512)), np.full(512, np.nan), np.zeros(512)):
            with self.subTest(shape=value.shape):
                with self.assertRaises(ValueError):
                    TextEncoderAdapter(Mock(encode_text=Mock(return_value=value))).encode("사진")

    def test_image_adapter_passes_original_image_and_converts_dtype(self):
        image = object()
        encoder = Mock(encode=Mock(return_value=np.ones(512, dtype=np.float64)))
        vector = ImageEncoderAdapter(encoder).encode(image)
        encoder.encode.assert_called_once_with(image)
        self.assertEqual(vector.dtype, np.float32)
