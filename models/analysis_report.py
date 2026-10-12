from dataclasses import dataclass, field
from models.file_info import FileInfo


@dataclass
class AnalysisFailure:
    file: FileInfo
    reason: str


@dataclass
class AnalysisReport:
    """GUI가 성공 개수와 읽기 실패 사진을 안내하도록 결과를 묶는다."""
    # default_factory는 보고서마다 독립된 새 목록을 만든다.
    indexed_files: list[FileInfo] = field(default_factory=list)
    failures: list[AnalysisFailure] = field(default_factory=list)
