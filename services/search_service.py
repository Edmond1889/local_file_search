# 향후 임베딩과 FAISS를 연결할 때의 설계 흐름이다.
# 현재 search()는 아래 흐름 대신 키워드 포함 여부로 점수를 계산한다.
# Natural Language Query
#         ↓
# Text Encoder
#         ↓
# Query Embedding
#         ↓
# Normalization
#         ↓
# FAISS Search
#         ↓
# Top-K Vector IDs
#         ↓
# SQLite Metadata Lookup
#         ↓
# Actual File Paths

from models.file_info import FileInfo
from models.search_result import SearchResult


class SearchService:

    def search(
        self, files: list[FileInfo], query: str, top_k: int = 5
    ) -> list[SearchResult]:
        # files는 분석한 파일 목록, query는 검색어, top_k는 반환할 최대 개수다.
        # 반환값은 파일 정보와 검색 점수를 담은 SearchResult 객체들의 목록이다.
        results = []

        # lower()는 대소문자 차이를 없애고, split()은 공백으로 단어를 나눈다.
        # 예: "AI 프로젝트" -> ["ai", "프로젝트"]
        keywords = query.lower().split()

        # 검색할 단어가 없거나 요청한 결과 개수가 0 이하라면 빈 목록을 반환한다.
        if not keywords or top_k <= 0:
            return results

        for file in files:
            # 파일이 바뀔 때마다 점수를 초기화해 이전 파일의 점수가 섞이지 않게 한다.
            score = 0

            # 비교 대상도 소문자로 맞춘다. 내용이 없으면 빈 문자열로 검색한다.
            filename = file.name.lower()
            content = file.content.lower() if file.content else ""

            for keyword in keywords:
                # 파일명에 키워드가 포함되면 +2
                if keyword in filename:
                    score += 2

                # txt 내용에 키워드가 포함되면 +1
                if keyword in content:
                    score += 1

            # 모든 키워드가 일치할 필요는 없다. 하나라도 일치하면 결과에 포함한다.
            # 여러 키워드가 일치할수록 점수가 더해져 상위에 나올 수 있다.
            if score > 0:
                # 원본 파일 정보와 이번 검색의 점수를 하나의 결과 객체로 묶는다.
                results.append(SearchResult(file=file, score=score))

        # key는 정렬 기준을 지정하고, reverse=True는 높은 점수부터 정렬한다.
        results.sort(
            key=lambda result: result.score,
            reverse=True
        )

        # 슬라이싱 [:top_k]로 정렬된 목록의 앞에서 최대 top_k개만 반환한다.
        return results[:top_k]
