"""내 담당: 로더·파일 인코더·입력 인코더·DB·유사도 비교의 연결 순서."""
from file_loader.loader import find_files, load_file


# %% 1. 각 담당자의 기능을 구분해서 보관하기
class TextSearch:
    def __init__(self, file_encoder, query_encoder, repository, similarity):
        self.file_encoder = file_encoder
        self.query_encoder = query_encoder
        self.repository = repository
        self.similarity = similarity

    def analyze(self, folder_path):
        # 2. 실제 폴더에서 코드·문서 목록을 받는다.
        files = find_files(folder_path)
        saved_files = []
        failures = []

        for path in files:
            # 3. 실제 본문과 DB용 파일 정보를 받는다. 읽기 실패만 건너뛴다.
            try:
                info, text = load_file(path)
            except (OSError, UnicodeError, ValueError, KeyError) as error:
                failures.append((path, str(error)))
                continue

            # 4. 새 파일 인코더 자리다. 미구현이므로 여기서 명확히 중단된다.
            vector = self.file_encoder.encode(text)

            # 5. DB가 정한 파일 번호로 정보와 벡터를 연결한다.
            file_id = self.repository.save(info)
            self.similarity.add(file_id, vector)
            saved_files.append(info)

        return saved_files, failures

    def encode_query(self, query):
        # 6. 사용자 입력은 이미 구현된 입력 전용 인코더를 호출한다.
        query = query.strip()
        if not query:
            raise ValueError("검색 문장을 입력하세요.")
        return self.query_encoder.encode_text(query)

    def search(self, query, top_k=5):
        if not query.strip() or top_k <= 0:
            return []

        vector = self.encode_query(query)

        # 7. 새 유사도 비교 자리다. 기존 이미지용 FAISS 검색으로 대신하지 않는다.
        hits = self.similarity.search(vector, top_k)
        results = []
        for file_id, score in hits:
            info = self.repository.find_by_id(file_id)
            if info is None:
                raise LookupError(f"DB에 파일 번호 {file_id}가 없습니다.")

            results.append((info, score))

        return results
