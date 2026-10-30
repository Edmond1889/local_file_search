# 연결 순서

| 순서 | 함수 | 입력 → 출력 |
|---|---|---|
| 파일 목록 | `find_files(folder_path)` | 폴더 → 경로 목록 |
| 파일 로드 | `load_file(path)` | 경로 → `(FileInfo, 본문)` |
| 파일 인코딩 | `FileEncoder.encode(text)` | 본문 → 벡터 **(미구현)** |
| 정보 저장 | `Repository.save(info)` | FileInfo → 파일 ID |
| 벡터 등록 | `SimilaritySearch.add(id, vector)` | ID·벡터 등록 **(미구현)** |
| 입력 인코딩 | `KoreanTextEncoder.encode_text(query)` | 사용자 문장 → 벡터 |
| 유사도 비교 | `SimilaritySearch.search(vector, top_k)` | 벡터 → `(ID, 점수)` 목록 **(미구현)** |
| 정보 조회 | `Repository.find_by_id(id)` | ID → FileInfo 또는 None |

[DocumentSearch](../connection/service.py)의 `analyze()`는 위의 파일 목록~벡터 등록을, `search()`는 입력 인코딩~정보 조회를 호출한다.
`analyze()` 반환값은 `(저장한 파일 목록, (실패 경로, 이유) 목록)`이다. `search()`는 `(FileInfo, 점수)` 목록을 반환한다.

읽기 실패는 기록하고 다음 파일을 처리한다. 미구현·모델·DB 오류는 호출자에게 전달한다.
미구현 자리의 함수 이름·벡터 형식은 연결 초안이며 담당자와 맞춰야 한다.
파일 벡터와 입력 벡터는 차원과 의미 비교 기준이 모두 맞아야 한다.
