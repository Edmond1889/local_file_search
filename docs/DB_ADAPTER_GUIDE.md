# DB 어댑터 연결 가이드

## 현재 상태 — 2026-10-14

원본 DB에 추가된 필수 updated_at 필드를 우리 RepositoryAdapter에서 전달하도록 수정했다.
합의한 의미는 DB 갱신 시각이 아니라 사진 파일의 수정 시각이다.
팀원 DB·로더·인코더 코드는 수정하지 않았다.

## 필드 대응

| 공통 FileInfo | DB FileInfo | 변환 |
|---|---|---|
| path | file_path | 경로 |
| name | file_name | 이름 |
| extension | file_extension | 확장자 |
| size | file_size | 바이트 단위 크기 |
| file_hash | file_hash | 유지, 빈 값이면 실제 파일의 SHA-256 계산 |
| created_at | created_at | 유지, 빈 값이면 저장 요청 시각으로 보완 |
| modified_time | updated_at | Unix timestamp ↔ 시간대가 표시된 UTC 문자열 |
| 해당 없음 | file_id | 저장 결과로 받아 벡터 인덱스에도 사용 |

수정 시각 1700000000.125는 2023-11-14T22:13:20.125000+00:00로 저장한다.
조회 시 다시 숫자 시각으로 복원하므로 파일이 삭제되거나 바뀌어도 저장 당시 수정 시각을 유지한다.
문자열 정밀도는 마이크로초다. created_at은 FileInfo 객체 생성 시각이며 파일 생성·수정 시각과는 다르다.

## 알 수 없는 시각과 이전 형식

- modified_time이 None이면 updated_at에 빈 문자열을 넣는다. 현재 시각이나 0을 임의로 만들지 않는다.
- DB가 modified_time을 직접 제공하는 버전이면 해당 값을 우선 사용한다.
- 그 외에는 updated_at을 해석한다. Z 또는 명시된 시간대를 읽을 수 있다.
- 저장 값이 없거나 형식/시간대를 해석할 수 없을 때만 현재 파일의 수정 시각을 조회한다.
- 그때 파일도 읽을 수 없으면 modified_time은 None이다.
- 어댑터는 DB 테이블을 수정하지 않는다. 기존 updated_at 컬럼 없는 실제 DB의 이전은 별도다.

## 서비스 연결

~~~python
from adapters.repository_adapter import RepositoryAdapter
from storage.db_manager import Repository as DatabaseRepository

database = DatabaseRepository("image_metadata.db")
repository = RepositoryAdapter(database)
# AnalysisService와 SearchService의 repository 인자에 같은 객체를 전달한다.
~~~

서비스는 공통 FileInfo를 유지하고, 어댑터가 DB용 필드로 변환한다.
조회 결과도 공통 FileInfo로 돌려주므로 GUI는 path/name을 그대로 사용할 수 있다.
기본 GUI는 real_services.RealServiceFactory로 실제 서비스에 연결했다. 분석마다 독립된 임시 DB와 메모리 인덱스를 만들며, 영구 저장·불러오기는 아직 연결하지 않았다. --demo 옵션으로 기존 가상 데이터 데모도 실행할 수 있다.

## 검증

requirements-db.txt는 requirements.txt를 포함하므로 모델 라이브러리도 설치 대상이다.
Pillow·NumPy·FAISS가 설치된 환경에서 아래 명령으로 테스트 25개가 모두 통과했다.

~~~powershell
python -m unittest discover -s tests -v
~~~

실제 임시 이미지·SQLite·FAISS를 사용하고 AI 임베딩은 고정된 테스트 배열로 대신했다.
다른 시간대, 삭제/변경된 사진의 수정 시각 유지, 알 수 없는 시각도 검증했다.
자동 테스트와 별도로 실제 모델에서 고양이 사진 3장의 분석·한국어 검색도 확인했다. 다양한 사진에서의 품질 평가는 별도다.

## 남은 협업

기존 DB 이전, 재분석/중복 갱신, 일부 저장 실패 복구, 변경 파일의 해시 재계산 위치를 정해야 한다.
문장 인코더 함수명과 실제 GUI 연결은 완료했고 requirements-app.txt에 실행 의존성을 모았다. 실제 모델로 샘플 3장의 분석·검색을 확인했으며, 다양한 사진에서의 품질과 실제 GUI 검색 확인은 남아 있다.
