"""팀원들과 합의할 연결 규격 초안. 각 기능은 담당자가 구현한다."""
from typing import Any, Protocol, Sequence
from models.file_info import FileInfo

Vector = Sequence[float]


class ImageLoadError(Exception):
    """사진 읽기 담당자가 손상/읽기 실패를 알릴 때 사용하는 오류 초안."""


# Protocol은 필요한 함수의 모양을 정의한다.
# 팀원 클래스는 이를 상속하지 않아도 동일한 함수를 제공하면 연결할 수 있다.
class FileScanner(Protocol):
    def scan(self, folder_path: str) -> list[FileInfo]: ...


class ImageLoader(Protocol):
    # 이미지 자료형은 팀원과 합의 전이므로 Any로 표시한다.
    def load(self, file_path: str) -> Any: ...


class ImageEncoder(Protocol):
    def encode(self, image: Any) -> Vector: ...


class TextEncoder(Protocol):
    def encode(self, query: str) -> Vector: ...


class Repository(Protocol):
    def save(self, file_info: FileInfo) -> int: ...
    def find_by_id(self, file_id: int) -> FileInfo | None: ...


class VectorIndex(Protocol):
    def add(self, file_id: int, vector: Vector) -> None: ...
    # 초안: (파일 ID, 유사도) 목록을 높은 유사도부터 반환한다.
    # FAISS에서 거리를 사용하면 담당자의 어댑터에서 이 규격으로 변환해야 한다.
    def search(self, vector: Vector, top_k: int) -> list[tuple[int, float]]: ...
