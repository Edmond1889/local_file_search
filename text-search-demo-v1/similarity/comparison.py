"""새 유사도 비교 담당자가 구현할 자리. 함수 모양은 연결용 초안이다."""


class SimilaritySearch:
    def add(self, file_id, vector):
        # 파일 번호와 벡터를 비교 대상에 등록하는 기능이 들어올 자리다.
        raise NotImplementedError("새 벡터 등록·유사도 비교 부분은 아직 미구현입니다.")

    def search(self, query_vector, top_k):
        # 검색 벡터와 비교해 (파일 번호, 점수) 목록을 반환할 자리다.
        raise NotImplementedError("새 유사도 비교 부분은 아직 미구현입니다.")
