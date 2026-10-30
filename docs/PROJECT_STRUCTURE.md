# 폴더별 역할

| 위치 | 하는 일 | 상태 |
|---|---|---|
| [file_loader/loader.py](../file_loader/loader.py) | 파일 찾기·본문 읽기·파일 정보 생성 | 구현됨 |
| [file_encoder/encoder.py](../file_encoder/encoder.py) | 본문 → 파일 벡터 | 미구현 |
| [query_encoder/text_encoder.py](../query_encoder/text_encoder.py) | 사용자 문장 → 입력 벡터 | 기존 팀원 코드 |
| [database/db_manager.py](../database/db_manager.py) | 파일 정보 저장·조회 | 기존 팀원 코드 |
| [similarity/comparison.py](../similarity/comparison.py) | 벡터 등록·유사도 비교 | 미구현 |
| [connection/service.py](../connection/service.py) | 위 기능을 순서대로 호출 | 내 연결 코드 |
| [app.py](../app.py) / [gui/window.py](../gui/window.py) | 기능 조립·실행 화면 | 현재 가능한 범위만 확인 |

로더는 UTF-8·CP949 텍스트/코드, DOCX, 노트북 본문을 읽는다. 지원 확장자는 `SUPPORTED_EXTENSIONS`에 있다.
PDF·HWP·옛 DOC·이미지 OCR은 지원하지 않는다. 폴더 탐색과 본문 읽기는 인코더 역할이 아니다.

`study/`는 전체 코드 셀과 공부 노트, `tests/`는 연결 검증이다.
`notes/`는 과거 메모다. 자동 보고서, 이미지 미리보기, 가짜 검색 데모는 현재 구현하지 않았다.
새 파일 인코더·유사도 비교가 들어오기 전에는 전체 검색이 완료되지 않는다.
