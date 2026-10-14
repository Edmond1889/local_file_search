# DB 어댑터 연결 가이드

## 어떤 문제를 해결하는가

공통 FileInfo와 DB 담당자의 FileInfo는 같은 사진을 표현하지만 필드 이름이 다르다.
RepositoryAdapter는 서비스의 save/find_by_id 규격을 유지하면서 두 형식을 변환한다.
db_manager.py, image_loader.py, 팀원 임베딩 코드는 수정하지 않는다.

| 공통 FileInfo | DB FileInfo | 처리 |
|---|---|---|
| path | file_path | 같은 경로 전달 |
| name | file_name | 같은 이름 전달 |
| extension | file_extension | 같은 확장자 전달 |
| size | file_size | 바이트 단위 크기 전달 |
| file_hash | file_hash | 값이 있으면 유지, 없으면 파일 전체의 SHA-256 계산 |
| created_at | created_at | 값이 있으면 유지, 빈 값만 저장 요청 시각으로 보완 |
| modified_time | 추가 예정 | DB가 제공하면 그대로 사용, 구버전은 현재 파일에서 조회 |
| 해당 없음 | file_id | save() 반환값으로 받아 벡터 인덱스에도 사용 |

공통 FileInfo에 file_hash와 created_at을 추가했다. 기본값이 있어 기존 생성 코드도 동작한다.
created_at의 기본값은 FileInfo 객체가 만들어진 UTC 시각이며 파일의 실제 생성 시각과는 다르다.
어댑터가 빈 값을 보완하면 DB 저장 성공 후 공통 객체에도 반영한다.

구버전 DB에서 조회하는 modified_time은 현재 파일의 수정 시각이다. 분석 당시의 기록을 복원한 값이 아니다.
파일이 없거나 접근할 수 없으면 None으로 표시한다. DB 담당자가 해당 필드를 저장·반환하면 그 값을 우선 사용한다.

## 서비스에 연결하기

~~~python
from adapters.repository_adapter import RepositoryAdapter
from db_manager import Repository as DatabaseRepository
from services.analysis_service import AnalysisService
from services.search_service import SearchService

database = DatabaseRepository("image_metadata.db")
repository = RepositoryAdapter(database)

# scanner, loader, encoders, vector_index는 담당자 구현 객체를 전달한다.
analysis = AnalysisService(
    scanner, image_loader, image_encoder, repository, vector_index,
)
search = SearchService(text_encoder, vector_index, repository)
~~~

두 서비스에 같은 어댑터와 벡터 인덱스를 전달한다.
DB 생성/인덱스 복원 시점과 실제 GUI용 서비스 생성 함수의 연결은 별도 작업이다.
현재 GUI의 기본 실행은 여전히 가상 데이터 데모다.

## 설치와 검증

~~~powershell
python -m pip install -r requirements-db.txt
python -m unittest discover -s tests -v
~~~

DB 의존성이 없으면 어댑터 통합 테스트는 명시적으로 건너뛴다.
통합 테스트는 실제 임시 이미지·SQLite·FAISS를 사용하며 AI 임베딩만 고정된 테스트 배열로 대신한다.

## 아직 다루지 않는 사항

- 같은 사진의 재분석/갱신과 DB·벡터 동시 저장 실패 복구는 DB 담당자와 합의가 필요하다.
- 해시가 이미 있으면 어댑터는 재계산하지 않는다. 파일 변경 감지 시 새 해시를 만들 책임을 정해야 한다.
- 팀원 스캐너의 ext/extension 및 필수 인자 차이는 이 어댑터가 고치는 범위가 아니다.
- 데모 벡터는 list지만 실제 VectorIndex는 NumPy 배열을 요구한다. 실제 인코더 배열을 사용해야 한다.
- 이미지/문장 모델과 GUI의 실제 서비스 연결은 이 DB 어댑터와 별도로 검증한다.
