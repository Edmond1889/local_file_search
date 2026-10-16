"""DB 담당자의 코드를 수정하지 않고 공통 FileInfo를 저장·조회한다."""
from dataclasses import fields
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path

from storage.db_manager import FileInfo as DatabaseFileInfo
from storage.db_manager import Repository as DatabaseRepository
from models.file_info import FileInfo, metadata_created_at


class RepositoryAdapter:
    """서비스에서는 이 객체를 Repository 대신 전달한다."""

    def __init__(self, repository: DatabaseRepository):
        self.repository = repository

    @staticmethod
    def _file_hash(file_path: str) -> str:
        # 파일 전체를 한꺼번에 메모리에 올리지 않고 1MB씩 읽어 SHA-256을 계산한다.
        digest = sha256()
        with Path(file_path).open("rb") as source:
            for block in iter(lambda: source.read(1024 * 1024), b""):
                digest.update(block)
        return digest.hexdigest()

    @staticmethod
    def _to_updated_at(modified_time: float | None) -> str:
        # 합의한 의미: DB의 updated_at은 사진 파일의 수정 시각이다.
        # Unix timestamp를 시간대가 표시된 UTC 문자열로 바꾼다.
        if modified_time is None:
            return ""  # 알 수 없는 시각을 현재 시각이나 0으로 만들어 넣지 않는다.
        return datetime.fromtimestamp(modified_time, tz=timezone.utc).isoformat(
            timespec="microseconds"
        )

    @staticmethod
    def _from_updated_at(updated_at: str) -> float | None:
        if not updated_at:
            return None
        try:
            # Z 표기도 UTC로 읽는다. 시간대 없는 문자열은 임의로 해석하지 않는다.
            timestamp = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
            if timestamp.tzinfo is None:
                return None
            return timestamp.timestamp()
        except (AttributeError, TypeError, ValueError, OverflowError, OSError):
            return None

    def save(self, file_info: FileInfo) -> int:
        # 값이 이미 있으면 유지한다. 비어 있는 해시/생성 시각만 보완한다.
        file_hash = file_info.file_hash or self._file_hash(file_info.path)
        created_at = file_info.created_at or metadata_created_at()
        values = {
            "file_path": file_info.path,
            "file_name": file_info.name,
            "file_extension": file_info.extension,
            "file_size": file_info.size,
            "file_hash": file_hash,
            "created_at": created_at,
        }
        # DB 버전별 필드 이름 차이를 우리 쪽에서 흡수한다.
        database_fields = {item.name for item in fields(DatabaseFileInfo)}
        if "modified_time" in database_fields:
            values["modified_time"] = file_info.modified_time
        if "updated_at" in database_fields:
            values["updated_at"] = self._to_updated_at(file_info.modified_time)

        database_info = DatabaseFileInfo(**values)
        file_id = self.repository.save(database_info)
        # 저장이 성공한 뒤 보완한 값을 원본 객체에도 반영한다.
        # AnalysisReport의 파일 정보와 DB에 저장한 해시/시각을 같게 유지하기 위해서다.
        file_info.file_hash = file_hash
        file_info.created_at = created_at
        return file_id

    def find_by_id(self, file_id: int) -> FileInfo | None:
        database_info = self.repository.find_by_id(file_id)
        if database_info is None:
            return None

        # DB가 수정 시각을 제공하면 그 값을 우선 사용한다.
        modified_time = getattr(database_info, "modified_time", None)
        if modified_time is None:
            modified_time = self._from_updated_at(
                getattr(database_info, "updated_at", "")
            )
        if modified_time is None:
            # 저장된 수정 시각을 복원할 수 없는 구버전/빈 값만 실제 파일에서 보완한다.
            # 이 경우에만 아래 값이 분석 당시가 아닌 현재 파일의 수정 시각이다.
            try:
                modified_time = Path(database_info.file_path).stat().st_mtime
            except OSError:
                # 사진이 삭제되거나 접근 불가여도 나머지 메타데이터는 결과로 돌려준다.
                modified_time = None

        return FileInfo(
            name=database_info.file_name,
            path=database_info.file_path,
            extension=database_info.file_extension,
            size=database_info.file_size,
            modified_time=modified_time,
            file_hash=database_info.file_hash,
            created_at=database_info.created_at,
        )
