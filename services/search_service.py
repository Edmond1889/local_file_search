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

class SearchService:

    def search(self, files, query, top_k=5):
        results = []

        query = query.lower()

        for file in files:
            score = 0

            # 파일명에 검색어가 포함되면 +2
            if query in file.name.lower():
                score += 2

            # txt 내용에 검색어가 포함되면 +1
            if file.content and query in file.content.lower():
                score += 1

            # 하나라도 일치한 파일만 결과에 추가
            if score > 0:
                results.append({
                    "file": file,
                    "score": score
                })

        # 점수가 높은 순서대로 정렬
        results.sort(
            key=lambda result: result["score"],
            reverse=True
        )

        # 상위 top_k개만 반환
        return results[:top_k]