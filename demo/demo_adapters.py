"""연결 확인용 가짜 구현. 실제 사진/모델/FAISS 및 디스크 저장을 사용하지 않는다."""
from interface import ImageLoadError, Vector
from models.file_info import FileInfo


class DemoScanner:
    def scan(self, folder_path: str) -> list[FileInfo]:
        # 실제 폴더를 탐색하지 않고 가상 파일 3개를 만든다. 크기와 시각의 0도 임시 값이다.
        return [FileInfo(name, f"{folder_path}/{name}", ".jpg", 0, 0.0)
                for name in ("sample_a.jpg", "sample_b.jpg", "broken.jpg")]


class DemoImageLoader:
    def load(self, file_path: str) -> str:
        # 실제 사진을 읽는 대신 경로 문자열을 다음 단계에 넘기고, 실패 상황 하나를 재현한다.
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
        # dict는 ID→파일 정보로 조회하는 메모리 저장소다. 프로그램을 종료하면 내용은 사라진다.
        self.files: dict[int, FileInfo] = {}

    def save(self, file_info: FileInfo) -> int:
        file_id = len(self.files) + 1  # 데모에서는 저장할 때마다 새 ID를 준다. 중복 방지는 하지 않는다.
        self.files[file_id] = file_info
        return file_id

    def find_by_id(self, file_id: int) -> FileInfo | None:
        return self.files.get(file_id)  # 없는 키를 조회하면 None을 반환한다.


class DemoVectorIndex:
    def __init__(self):
        self.vectors: dict[int, Vector] = {}

    def add(self, file_id: int, vector: Vector) -> None:
        self.vectors[file_id] = vector

    def search(self, vector: Vector, top_k: int) -> list[tuple[int, float]]:
        # 고정 단위 벡터들의 내적으로 연결을 확인한다. FAISS 구현은 아니다.
        # zip은 같은 위치의 숫자를 묶고, sum은 두 숫자를 곱한 값들을 더한다(내적).
        # 이 계산은 고정된 2차원 데모 벡터용이다. 실제 벡터 차원 검증은 아직 없다.
        hits = [(file_id, sum(a * b for a, b in zip(vector, stored)))
                for file_id, stored in self.vectors.items()]
        return sorted(hits, key=lambda hit: hit[1], reverse=True)[:top_k]
