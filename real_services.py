"""실제 로더·모델·SQLite·FAISS를 묶는 GUI용 생성 함수."""
from tempfile import TemporaryDirectory
from pathlib import Path

from services.analysis_service import AnalysisService
from services.search_service import SearchService

MODEL_NAME = "xlm-roberta-base-ViT-B-32"
PRETRAINED = "laion5b_s13b_b90k"


class RealServiceFactory:
    def __init__(self, encoder_factory=None):
        # 테스트에서는 모델 다운로드 없이 대역 인코더만 주입할 수 있다.
        self.encoder_factory = encoder_factory or self._load_encoders
        self.encoders = None

    @staticmethod
    def _load_encoders():
        # 무거운 라이브러리는 분석을 누른 작업 스레드에서 불러온다.
        try:
            from encoders.image_encoder import ImageEncoder
            from encoders.text_encoder import KoreanTextEncoder
        except ImportError as error:
            raise RuntimeError(
                "모델 라이브러리를 불러올 수 없습니다. 현재 Python에서 "
                "python -m pip install -r requirements-app.txt 실행 후 다시 시도해주세요. "
                f"원인: {error}"
            ) from error
        # 사진과 문장은 반드시 같은 모델 이름과 학습 가중치를 사용한다.
        image = ImageEncoder(model_name=MODEL_NAME, pretrained=PRETRAINED)
        text = KoreanTextEncoder(model_name=MODEL_NAME, pretrained=PRETRAINED)
        return image, text

    def __call__(self):
        from adapters.encoder_adapters import ImageEncoderAdapter, TextEncoderAdapter
        from adapters.repository_adapter import RepositoryAdapter
        from storage.db_manager import Repository, VectorIndex
        from imaging.image_loader import DefaultFileScanner, DefaultImageLoader

        if self.encoders is None:
            self.encoders = self.encoder_factory()
        image, text = self.encoders
        # 매 분석은 독립된 세션이다. 기존 사용자 DB를 변경하거나 지우지 않는다.
        session = TemporaryDirectory(prefix="image-search-")
        try:
            repository = RepositoryAdapter(Repository(str(Path(session.name) / "metadata.db")))
            index = VectorIndex(embedding_dim=512)
            # 검색 서비스가 살아 있는 동안 임시 DB 폴더도 유지한다.
            repository.session_directory = session
            return (
                AnalysisService(DefaultFileScanner(), DefaultImageLoader(),
                                ImageEncoderAdapter(image), repository, index),
                SearchService(TextEncoderAdapter(text), index, repository),
            )
        except Exception:
            session.cleanup()
            raise
