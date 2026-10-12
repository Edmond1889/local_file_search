# 모든 파일 정보를 담는 기본 그릇(뼈대)

from dataclasses import dataclass


@dataclass
class FileInfo:
    name: str
    path: str
    extension: str
    size: int
    modified_time: float
    content: str = ""


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