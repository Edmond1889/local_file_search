from dataclasses import dataclass, field
from models.file_info import FileInfo


@dataclass
class AnalysisFailure:
    # 읽지 못한 사진과 이유를 묶어 GUI가 어떤 사진에 문제가 있었는지 안내한다.
    file: FileInfo
    reason: str


@dataclass
class AnalysisReport:
    """GUI가 성공 개수와 읽기 실패 사진을 안내하도록 결과를 묶는다."""
    # default_factory는 보고서마다 독립된 새 목록을 만든다.
    indexed_files: list[FileInfo] = field(default_factory=list)  # 파일 정보와 벡터 저장까지 끝난 사진
    failures: list[AnalysisFailure] = field(default_factory=list)  # 사진 읽기 실패만 담는다.
