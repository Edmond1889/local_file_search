# DB와 이전 유사도 계산

## 현재 DB

[db_manager.py](../database/db_manager.py)의 팀원 원본을 유지한다.
로더가 DB의 `FileInfo`를 직접 생성하므로 별도 RepositoryAdapter는 없다.

| 필드 | 의미 |
|---|---|
| file_path / file_name / file_extension / file_size | 절대 경로 / 이름 / 확장자 / 바이트 크기 |
| file_hash | 파일 내용의 SHA-256 |
| created_at / updated_at | 정보 생성 시각 / 실제 파일 수정 시각, UTC 문자열 |
| file_id | DB가 저장 후 돌려주는 번호 |

기존 테이블명 `image_metadata`는 그대로다. DB는 임시 세션이며 재실행 후 검색 복원은 없다.
파일 경로 중복 저장 시 오류가 나고, DB·벡터 등록을 함께 되돌리는 기능도 없다.

## 이전 image-search-demo-v2에서 어디서 계산했나?

- [storage/db_manager.py](C:/Capstone/image-search-demo-v2/storage/db_manager.py)의 `VectorIndex`가 담당했다.
- `__init__()`의 `IndexFlatIP`는 **내적**을 계산한다.
- `_normalize_vector()`는 벡터 길이를 1로 맞춘다. 정상 벡터끼리 비교하면 내적이 코사인 유사도가 된다.
- `search()`가 점수를 받아 소수 넷째 자리로 반올림한다. **거리→유사도 변환은 따로 없었다.**
- [services/search_service.py](C:/Capstone/image-search-demo-v2/services/search_service.py)는 그 점수를 float로 바꾸어 파일 정보와 묶었다. 유사도 계산 위치가 아니다.

점수는 정확도나 확률이 아니다. `distances`라는 변수명이어도 이 인덱스에서는 높은 점수가 더 유사하다.
현재 DB 원본에도 옛 VectorIndex가 남아 있지만 호출하지 않는다. 새 비교는 [similarity/comparison.py](../similarity/comparison.py)의 미구현 자리다.
