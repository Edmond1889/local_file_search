import os
from PIL import Image


from interface import FileScanner, ImageLoader, FileInfo, ImageLoadError

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


class DefaultFileScanner(FileScanner):
 
    def scan(self, folder_path: str) -> list[FileInfo]:
        file_list = []
        if not os.path.exists(folder_path):
            return file_list

        for root, _, files in os.walk(folder_path):
            for file_name in files:
                ext = os.path.splitext(file_name)[1].lower()
                if ext in IMAGE_EXTENSIONS:
                    abs_path = os.path.abspath(os.path.join(root, file_name))
                    file_list.append(
                        FileInfo(
                            path=abs_path,
                            name=file_name,
                            ext=ext
                        )
                    )
        return file_list


class DefaultImageLoader(ImageLoader):

    def load(self, file_path: str):

        try:
            if os.path.getsize(file_path) == 0:
                raise ImageLoadError(f"0바이트 빈 파일입니다: {file_path}")
        except OSError as e:
            raise ImageLoadError(f"파일 접근 불가: {file_path} ({e})")


        try:
            with Image.open(file_path) as img:
                img.verify()
            
  
            img = Image.open(file_path)
            img.load()
            return img.convert("RGB")
        except Exception as e:
            raise ImageLoadError(f"손상된 이미지 파일입니다: {file_path} ({e})")
