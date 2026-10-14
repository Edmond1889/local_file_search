"""분석·검색·GUI가 함께 사용하는 파일 메타데이터."""
from dataclasses import dataclass, field
from datetime import datetime, timezone


def metadata_created_at() -> str:
    # 실제 파일의 생성 시각이 아니라, 파일 정보 객체가 만들어진 시각이다.
    # 시간대 혼동을 피하기 위해 UTC와 시간대 표시를 함께 저장한다.
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass
class FileInfo:
    # 이미지 픽셀이나 벡터는 담지 않고 파일의 정보만 전달한다.
    name: str
    path: str
    extension: str
    size: int  # 바이트 단위 파일 크기
    # DB에 수정 시각이 없고 실제 파일도 읽을 수 없다면 None(알 수 없음)이다.
    modified_time: float | None
    # 기본값을 두어 기존 FileInfo(name, path, extension, size, modified_time)도 사용할 수 있다.
    file_hash: str = ""  # SHA-256. 비어 있으면 RepositoryAdapter가 저장 전에 계산한다.
    created_at: str = field(default_factory=metadata_created_at)
