"""구현된 입력 인코더·DB와 미구현 파일 인코더·유사도 비교 자리를 연결한다."""
from pathlib import Path
from tempfile import TemporaryDirectory

from query_encoder.text_encoder import KoreanTextEncoder
from database.db_manager import Repository
from file_encoder.encoder import FileEncoder
from similarity.comparison import SimilaritySearch
from connection.service import TextSearch


# %% 1. 실제 인코더와 DB를 연결하기
def build_service():
    # 기존 인코더는 사용자 입력에만 쓴다. 파일 인코더로 재사용하지 않는다.
    query_encoder = KoreanTextEncoder()
    file_encoder = FileEncoder()  # 미구현 자리
    similarity = SimilaritySearch()  # 미구현 자리

    # 이전 이미지 DB를 덮어쓰지 않도록 이번 분석용 실제 SQLite 파일을 만든다.
    session = TemporaryDirectory(prefix="text-search-")
    repository = Repository(str(Path(session.name) / "text_metadata.db"))
    service = TextSearch(file_encoder, query_encoder, repository, similarity)
    service.session_directory = session  # 서비스가 살아 있는 동안 DB 폴더를 유지한다.
    return service


# %% 2. 현재 구현되어 있는 사용자 입력 인코딩만 확인하기
def main():
    print("파일 인코더와 유사도 비교는 미구현입니다. 완성된 검색 프로그램이 아닙니다.")
    query = input("인코딩할 사용자 입력 문장: ").strip()
    if not query:
        return
    service = build_service()
    vector = service.encode_query(query)
    print("입력 인코더 출력 크기:", vector.shape)
    print("검색 결과는 새 파일 인코더와 유사도 비교 구현 후 연결합니다.")


# %% 3. 실행 시작점
if __name__ == "__main__":
    import sys

    if "--gui" in sys.argv:
        import tkinter as tk
        from gui.window import TextSearchApp

        root = tk.Tk()
        TextSearchApp(root, build_service)
        root.mainloop()
    else:
        main()
