"""연결 확인용 가짜 구현. 실제 사진/모델/FAISS 및 디스크 저장을 사용하지 않는다."""
from interface import ImageLoadError, Vector
from models.file_info import FileInfo


class DemoScanner:
    def scan(self, folder_path: str) -> list[FileInfo]:
        return [FileInfo(name, f"{folder_path}/{name}", ".jpg", 0, 0.0)
                for name in ("sample_a.jpg", "sample_b.jpg", "broken.jpg")]


class DemoImageLoader:
    def load(self, file_path: str) -> str:
        if file_path.endswith("broken.jpg"):
            raise ImageLoadError("데모용 손상 사진")
        return file_path


class DemoImageEncoder:
    def encode(self, image: str) -> Vector:
        # 경로로 테스트 값을 선택할 뿐 사진의 의미를 분석하지 않는다.
        return [1.0, 0.0] if image.endswith("sample_a.jpg") else [0.0, 1.0]


class DemoTextEncoder:
    def encode(self, query: str) -> Vector:
        # 모든 문장에 동일한 값을 반환하므로 검색 품질 검증에는 사용할 수 없다.
        return [1.0, 0.0]


class DemoRepository:
    def __init__(self):
        self.files: dict[int, FileInfo] = {}

    def save(self, file_info: FileInfo) -> int:
        file_id = len(self.files) + 1
        self.files[file_id] = file_info
        return file_id

    def find_by_id(self, file_id: int) -> FileInfo | None:
        return self.files.get(file_id)


class DemoVectorIndex:
    def __init__(self):
        self.vectors: dict[int, Vector] = {}

    def add(self, file_id: int, vector: Vector) -> None:
        self.vectors[file_id] = vector

    def search(self, vector: Vector, top_k: int) -> list[tuple[int, float]]:
        # 고정 단위 벡터들의 내적으로 연결을 확인한다. FAISS 구현은 아니다.
        hits = [(file_id, sum(a * b for a, b in zip(vector, stored)))
                for file_id, stored in self.vectors.items()]
        return sorted(hits, key=lambda hit: hit[1], reverse=True)[:top_k]
