from typing import Callable

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

    def analyze(
        self, folder_path: str,
        # 두 정수(처리 개수, 전체 개수)를 받고 반환값이 없는 함수다. None이면 알림을 생략한다.
        on_progress: Callable[[int, int], None] | None = None,
    ) -> AnalysisReport:
        report = AnalysisReport()
        # 폴더 검증과 사진 확장자 필터링은 사진 수집 담당자의 scan()이 맡는다.
        files = self.scanner.scan(folder_path)
        total = len(files)
        # 콜백은 호출자가 전달한 함수다. GUI가 없어도 분석 서비스를 사용할 수 있다.
        if on_progress is not None:
            on_progress(0, total)
        # enumerate는 순번과 파일을 함께 준다. start=1로 첫 사진의 처리 개수를 1로 센다.
        for processed, file in enumerate(files, start=1):
            try:
                image = self.image_loader.load(file.path)
            except ImageLoadError as error:
                # 손상 사진 하나 때문에 나머지 사진 분석까지 중단하지 않는다.
                report.failures.append(AnalysisFailure(file=file, reason=str(error)))  # 오류를 안내 문자열로 저장
                # 실패한 사진도 처리 시도는 끝났으므로 진행 개수에 포함한다.
                if on_progress is not None:
                    on_progress(processed, total)
                continue
            # file은 메타데이터, image는 읽은 사진, vector는 사진 특징의 숫자 배열이다.
            vector = self.image_encoder.encode(image)
            file_id = self.repository.save(file)
            # DB와 벡터 인덱스에 같은 ID를 써야 검색 후 실제 사진을 찾을 수 있다.
            self.vector_index.add(file_id, vector)
            report.indexed_files.append(file)
            # 저장까지 성공한 뒤 진행 상황을 알린다. 저장 오류가 나면 여기까지 오지 않는다.
            if on_progress is not None:
                on_progress(processed, total)
        # 임베딩/저장 오류는 숨기지 않고 호출자에게 전달한다.
        # 동시 저장 실패 복구, 중복 분석, 디스크 저장은 담당자와 후속 합의가 필요하다.
        return report  # 호출자가 성공 목록과 읽기 실패 목록을 각각 사용할 수 있다.
