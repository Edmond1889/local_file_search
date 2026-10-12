# 모든 파일 정보를 담는 기본 그릇(뼈대)

from dataclasses import dataclass


@dataclass
class FileInfo:
    # 사진의 메타데이터만 담는다. 이미지 픽셀과 임베딩 벡터는 담당 기능에서 처리한다.
    name: str
    path: str
    extension: str
    size: int
    modified_time: float


"""
# 클래스를 더 간편하게 정의하고 사용할 수 있게 하는
파이썬 표준 라이브러리 dataclass를 이용.

class FileInfo:
    def __init__(self, name, path, size):
        self.name = name
        self.path = path
        self.size = size

        ||
        VV

@dataclass
class FileInfo:
    name: str
    path: str
    size: int

"""
