"""팀원들과 합의할 연결 규격 초안. 각 기능은 담당자가 구현한다.

사용 위치로 이동하는 링크와 흐름 설명은 docs/INTERFACE_GUIDE.md를 참고한다.
"""
from typing import Any, Protocol, Sequence
from models.file_info import FileInfo

# Sequence[float]는 순서가 있는 숫자 배열을 뜻한다. 데모는 list를 사용한다.
# 실제 모델의 배열 자료형, 차원, 정규화 방식은 임베딩/검색 담당자가 합의해야 한다.
Vector = Sequence[float]


class ImageLoadError(Exception):
    """사진 읽기 담당자가 손상/읽기 실패를 알릴 때 사용하는 오류 초안."""


# Protocol은 필요한 함수의 모양을 정의한다.
# 팀원 클래스는 이를 상속하지 않아도 동일한 함수를 제공하면 연결할 수 있다.
# 타입 검사를 돕는 규격이며 실행 중 함수나 값의 타입을 자동으로 검사하지는 않는다.
class FileScanner(Protocol):
    # 사용: services/analysis_service.py → AnalysisService.analyze()
    # 폴더에서 수집한 사진의 파일 정보 목록을 받아 분석 반복문을 시작한다.
    def scan(self, folder_path: str) -> list[FileInfo]: ...


class ImageLoader(Protocol):
    # 사용: services/analysis_service.py → AnalysisService.analyze()
    # 사진 경로로 이미지 데이터를 읽는다. 읽기 실패는 ImageLoadError로 알린다.
    # 이미지 자료형은 팀원과 합의 전이므로 Any로 표시한다.
    def load(self, file_path: str) -> Any: ...


class ImageEncoder(Protocol):
    # 사용: services/analysis_service.py → AnalysisService.analyze()
    # 읽은 이미지를 문장 벡터와 비교 가능한 숫자 배열로 바꾼다.
    def encode(self, image: Any) -> Vector: ...


class TextEncoder(Protocol):
    # 사용: services/search_service.py → SearchService.search()
    # 검색 문장 전체를 이미지 벡터와 비교 가능한 숫자 배열로 바꾼다.
    def encode(self, query: str) -> Vector: ...


class Repository(Protocol):
    # 사용: services/analysis_service.py → AnalysisService.analyze()
    # 파일 정보를 저장하고, 벡터 저장에도 사용할 파일 ID를 반환한다.
    def save(self, file_info: FileInfo) -> int: ...
    # 사용: services/search_service.py → SearchService.search()
    # 검색된 파일 ID로 이름과 경로를 조회한다. 해당 ID가 없으면 None을 반환한다.
    def find_by_id(self, file_id: int) -> FileInfo | None: ...


class VectorIndex(Protocol):
    # 사용: services/analysis_service.py → AnalysisService.analyze()
    # 파일 정보 저장소에서 받은 ID와 이미지 벡터를 함께 저장한다.
    def add(self, file_id: int, vector: Vector) -> None: ...
    # 사용: services/search_service.py → SearchService.search()
    # 문장 벡터로 유사한 사진을 찾아 파일 ID와 점수 목록을 반환한다.
    # 초안: (파일 ID, 유사도) 목록을 높은 유사도부터 반환한다.
    # FAISS에서 거리를 사용하면 담당자의 어댑터에서 이 규격으로 변환해야 한다.
    def search(self, vector: Vector, top_k: int) -> list[tuple[int, float]]: ...
