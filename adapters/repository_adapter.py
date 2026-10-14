"""DB 담당자의 코드를 수정하지 않고 공통 FileInfo를 저장·조회한다."""
from dataclasses import fields
from hashlib import sha256
from pathlib import Path

from db_manager import FileInfo as DatabaseFileInfo
from db_manager import Repository as DatabaseRepository
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
        # DB 담당자가 modified_time을 추가한 버전도 같은 어댑터로 연결한다.
        # 현재 DB 버전에 없는 인자를 넘겨 TypeError가 발생하지 않게 확인한다.
        if any(item.name == "modified_time" for item in fields(DatabaseFileInfo)):
            values["modified_time"] = file_info.modified_time

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
            # 구버전 DB에는 이 항목이 없다. 아래 값은 분석 당시가 아닌 현재 파일의 수정 시각이다.
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
