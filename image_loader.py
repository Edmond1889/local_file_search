import os
from PIL import Image

from interface import FileScanner, ImageLoader, ImageLoadError
from models.file_info import FileInfo

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


class DefaultFileScanner(FileScanner):
    """
    폴더 내 사진 파일을 재귀 탐색하여 공통 FileInfo 목록을 반환하는 스캐너
    """
    def scan(self, folder_path: str) -> list[FileInfo]:
        file_list = []
        if not os.path.exists(folder_path):
            return file_list

        for root, _, files in os.walk(folder_path):
            for file_name in files:
                ext = os.path.splitext(file_name)[1].lower()
                if ext in IMAGE_EXTENSIONS:
                    abs_path = os.path.abspath(os.path.join(root, file_name))
                    try:
                        stat = os.stat(abs_path)
                        file_size = stat.st_size
                        modified_time = stat.st_mtime
                    except OSError:
                        file_size = 0
                        modified_time = 0.0

                    # 공통 FileInfo 규격에 맞춰 생성
                    file_list.append(
                        FileInfo(
                            name=file_name,
                            path=abs_path,
                            extension=ext,
                            size=file_size,
                            modified_time=modified_time,
                        )
                    )

        return file_list


class DefaultImageLoader(ImageLoader):
    """
    사진 경로로 이미지 데이터를 읽는 로더 (PIL RGB 객체 반환)
    """
    def load(self, file_path: str) -> Image.Image:
        try:
            if os.path.getsize(file_path) == 0:
                raise ImageLoadError(f"0바이트 빈 파일입니다: {file_path}")
        except OSError as e:
            raise ImageLoadError(f"파일 접근 실패: {file_path} ({e})")

        try:
            with Image.open(file_path) as img:
                img.verify()
            img = Image.open(file_path)
            img.load()
            return img.convert("RGB")
        except Exception as e:
            raise ImageLoadError(f"손상된 이미지 파일입니다: {file_path} ({e})")
