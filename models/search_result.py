from dataclasses import dataclass

from models.file_info import FileInfo


# dataclass는 필드 정의를 바탕으로 생성자 등을 자동으로 만들어 준다.
# 따라서 SearchResult(file=file, score=3)처럼 결과 객체를 만들 수 있다.
@dataclass
class SearchResult:
    """검색된 파일과 이번 검색에서 계산한 점수를 함께 담는 데이터 구조.

    FileInfo는 파일 자체의 정보를 담고, SearchResult는 검색 결과를 담는다.
    같은 파일도 검색어에 따라 점수가 달라지므로 점수는 FileInfo와 분리한다.
    """

    # 타입 표시는 각 필드에 담을 값의 종류를 설명한다.
    # 파이썬이 실행 중에 타입을 자동으로 검사해 주는 것은 아니다.
    file: FileInfo
    score: int
