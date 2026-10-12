# Library import
from pathlib import Path
from models.file_info import FileInfo




class AnalysisService:

    allowed_extensions = [
        ".jpg",
        ".jpeg",
        ".png",
        ".webp",
        ".txt",
        ".pdf",
        ".docx",
        ".pptx"
    ]


    def analyze(self, folder_path):
        files = []

        root = Path(folder_path)

        for path in root.rglob("*"): # 폴더 아래 폴더를 재귀적으로 검사

            # 파일만 처리
            if not path.is_file():
                continue

            # 지원 확장자만 처리
            if path.suffix.lower() not in self.allowed_extensions:
                continue

            # 파일 정보 가져오기
            stat = path.stat()

            content = ""

            # txt 파일이면 내용도 읽기
            if path.suffix.lower() == ".txt":
                try:
                    content = path.read_text(
                        encoding="utf-8"
                    )
                except UnicodeDecodeError:
                    content = path.read_text(
                        encoding="cp949"
                    )

            file_info = FileInfo(
                name=path.name,
                path=str(path.resolve()),
                extension=path.suffix.lower(),
                size=stat.st_size,
                modified_time=stat.st_mtime,
                content=content
            )

            files.append(file_info)

        return files