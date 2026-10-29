"""코드·문서에서 실제 본문과 DB에 넣을 파일 정보를 읽는다."""
from datetime import datetime, timezone
from hashlib import sha256
from io import BytesIO
from pathlib import Path
import json
from xml.etree import ElementTree
from zipfile import BadZipFile, ZipFile

from database.db_manager import FileInfo


# %% 1. 읽을 파일 종류와 건너뛸 폴더
SUPPORTED_EXTENSIONS = {
    ".txt", ".text", ".md", ".rst", ".py", ".ipynb", ".json", ".csv", ".tsv",
    ".js", ".jsx", ".ts", ".tsx", ".java", ".c", ".cpp", ".h", ".hpp",
    ".cs", ".html", ".css", ".sql", ".xml", ".yaml", ".yml", ".toml",
    ".ini", ".sh", ".ps1", ".docx",
}
SKIP_FOLDERS = {".git", ".venv", "venv", "node_modules", "__pycache__"}


# %% 2. 폴더 아래의 코드·문서 경로 찾기
def find_files(folder_path):
    folder = Path(folder_path).expanduser().resolve()
    if not folder.is_dir():
        raise ValueError("존재하는 폴더 경로를 입력하세요.")

    files = []
    for path in folder.rglob("*"):
        if SKIP_FOLDERS.intersection(path.relative_to(folder).parts):
            continue

        if path.is_file() and not path.is_symlink() and path.suffix.lower() in SUPPORTED_EXTENSIONS:
            files.append(path)

    return sorted(files)


# %% 3. 파일에서 실제 본문 읽기
def load_file(path):
    path = Path(path)
    data = path.read_bytes()

    if path.suffix.lower() == ".docx":
        # DOCX 안의 본문 XML에서 문단 텍스트만 꺼낸다. 그림의 OCR은 하지 않는다.
        try:
            with ZipFile(BytesIO(data)) as document:
                root = ElementTree.fromstring(document.read("word/document.xml"))
            namespace = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
            paragraphs = []
            for paragraph in root.iter(namespace + "p"):
                words = []
                for word in paragraph.iter(namespace + "t"):
                    words.append(word.text or "")
                paragraphs.append("".join(words))
            text = "\n".join(paragraphs)
        except (BadZipFile, KeyError, ElementTree.ParseError) as error:
            raise ValueError("DOCX 본문을 읽을 수 없습니다.") from error
    else:
        # UTF-8을 먼저 읽고, 예전 한글 파일이면 CP949로 한 번 더 시도한다.
        try:
            text = data.decode("utf-8-sig")
        except UnicodeDecodeError:
            text = data.decode("cp949")

        if path.suffix.lower() == ".ipynb":
            notebook = json.loads(text)
            text = "\n".join("".join(cell.get("source", [])) for cell in notebook["cells"])

    if not text.strip():
        raise ValueError("파일에 검색할 본문이 없습니다.")

    # DB 담당자의 FileInfo를 그대로 쓴다. 별도 자료형 변환 클래스는 없다.
    stat = path.stat()
    info = FileInfo(
        file_path=str(path),
        file_name=path.name,
        file_extension=path.suffix.lower(),
        file_size=stat.st_size,
        file_hash=sha256(data).hexdigest(),
        created_at=datetime.now(timezone.utc).isoformat(),
        updated_at=datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat(),
    )

    return info, text
