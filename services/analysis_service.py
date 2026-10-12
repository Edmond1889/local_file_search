from interface import FileScanner, ImageEncoder, ImageLoader, ImageLoadError, Repository, VectorIndex
from models.analysis_report import AnalysisFailure, AnalysisReport


class AnalysisService:
    """사진 분석 흐름을 연결한다. 개별 기능은 전달받은 담당 객체가 수행한다."""

    def __init__(
        self, scanner: FileScanner, image_loader: ImageLoader,
        image_encoder: ImageEncoder, repository: Repository, vector_index: VectorIndex,
    ):
        # 도구를 외부에서 받으면 팀원 구현이나 테스트용 구현으로 교체할 수 있다.
        self.scanner = scanner
        self.image_loader = image_loader
        self.image_encoder = image_encoder
        self.repository = repository
        self.vector_index = vector_index

    def analyze(self, folder_path: str) -> AnalysisReport:
        report = AnalysisReport()
        # 폴더 검증과 사진 확장자 필터링은 사진 수집 담당자의 scan()이 맡는다.
        for file in self.scanner.scan(folder_path):
            try:
                image = self.image_loader.load(file.path)
            except ImageLoadError as error:
                # 손상 사진 하나 때문에 나머지 사진 분석까지 중단하지 않는다.
                report.failures.append(AnalysisFailure(file=file, reason=str(error)))
                continue
            vector = self.image_encoder.encode(image)
            file_id = self.repository.save(file)
            # DB와 벡터 인덱스에 같은 ID를 써야 검색 후 실제 사진을 찾을 수 있다.
            self.vector_index.add(file_id, vector)
            report.indexed_files.append(file)
        # 임베딩/저장 오류는 숨기지 않고 호출자에게 전달한다.
        # 동시 저장 실패 복구, 중복 분석, 디스크 저장은 담당자와 후속 합의가 필요하다.
        return report
