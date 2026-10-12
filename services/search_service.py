from interface import Repository, TextEncoder, VectorIndex
from models.search_result import SearchResult


class SearchService:
    """문장 벡터로 검색한 사진 ID를 실제 파일 정보와 연결한다."""

    def __init__(
        self, text_encoder: TextEncoder, vector_index: VectorIndex, repository: Repository,
    ):
        self.text_encoder = text_encoder
        self.vector_index = vector_index
        self.repository = repository

    def search(self, query: str, top_k: int = 5) -> list[SearchResult]:
        # 앞뒤 공백만 제거한다. 문장 내부 공백과 단어 순서는 유지한다.
        query = query.strip()
        # 빈 문장/0 이하 개수는 모델을 실행하지 않고 빈 결과로 처리한다.
        if not query or top_k <= 0:
            return []
        # 문장을 통째로 전달한다. 단어 분리나 키워드 점수 계산은 하지 않는다.
        vector = self.text_encoder.encode(query)
        hits = self.vector_index.search(vector, top_k)
        results = []
        # (파일 ID, 유사도)를 각각 꺼낸다. [:top_k]로 최대 요청 개수만 사용한다.
        for file_id, score in hits[:top_k]:
            file = self.repository.find_by_id(file_id)
            if file is None:
                # 없는 ID는 저장소 불일치이므로 정상 결과처럼 숨기지 않는다.
                raise LookupError(f"검색 결과의 파일 ID {file_id}가 저장소에 없습니다.")
            # float()는 점수 자료형을 맞춘다. 거리→유사도 변환이나 정규화를 하는 것은 아니다.
            results.append(SearchResult(file=file, score=float(score)))
        # 유사도 순서는 인덱스 담당자의 반환 규격을 따른다.
        return results
