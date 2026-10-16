# 함수 규격과 사용 위치

`interface.py`는 담당자끼리 합의할 함수 규격 초안이다.
서비스는 이 규격을 갖춘 객체를 받아 함수를 호출하고, 반환값을 다음 단계로 전달한다.
현재 `demo/demo_adapters.py`의 구현은 연결 확인용 가짜 구현이다.

## 사진 분석 — AnalysisService.analyze()

| 규격 | 입력 → 출력 | 호출 위치 | 필요한 이유 |
|---|---|---|---|
| `FileScanner.scan()` | 폴더 경로 → FileInfo 목록 | [사진 목록 수집](../services/analysis_service.py#L28) | 분석할 사진을 한 장씩 처리하기 위해 |
| `ImageLoader.load()` | 사진 경로 → 이미지 데이터 | [이미지 읽기](../services/analysis_service.py#L36) | 임베딩 담당자에게 실제 이미지 데이터를 전달하기 위해 |
| `ImageEncoder.encode()` | 이미지 데이터 → 숫자 배열 | [이미지 임베딩](../services/analysis_service.py#L45) | 사진 특징을 검색 가능한 벡터로 표현하기 위해 |
| `Repository.save()` | FileInfo → 파일 ID | [파일 정보 저장](../services/analysis_service.py#L46) | 검색 후 파일 이름과 경로를 다시 찾기 위해 |
| `VectorIndex.add()` | 파일 ID와 벡터 → 반환값 없음 | [벡터 저장](../services/analysis_service.py#L48) | 사진 벡터와 파일 정보를 같은 ID로 연결하기 위해 |

`file`은 파일 정보, `image`는 읽은 이미지 데이터, `vector`는 이미지 특징의 숫자 배열이다.
`Repository.save()`에서 받은 ID를 `VectorIndex.add()`에도 전달한다.

사진 읽기 담당자는 손상되거나 읽을 수 없는 사진에 `ImageLoadError`를 발생시키기로 제안한다.
[오류 처리 위치](../services/analysis_service.py#L37)에서 실패 이유를 기록하고,
`continue`로 다음 사진을 처리한다. 임베딩이나 저장 오류는 호출자에게 전달한다.

## 사진 검색 — SearchService.search()

| 규격 | 입력 → 출력 | 호출 위치 | 필요한 이유 |
|---|---|---|---|
| `TextEncoder.encode()` | 검색 문장 → 숫자 배열 | [문장 임베딩](../services/search_service.py#L22) | 검색 문장을 사진 벡터와 비교하기 위해 |
| `VectorIndex.search()` | 문장 벡터와 top_k → (파일 ID, 유사도) 목록 | [벡터 검색](../services/search_service.py#L23) | 가장 유사한 사진의 ID와 점수를 얻기 위해 |
| `Repository.find_by_id()` | 파일 ID → FileInfo 또는 None | [파일 정보 조회](../services/search_service.py#L27) | 검색 결과의 실제 사진 경로를 얻기 위해 |

`top_k`는 요청할 최대 결과 개수다. 현재 초안에서는 높은 유사도부터 반환한다.
실제 FAISS 구현이 거리를 반환한다면 검색 담당자와 점수 변환 규격을 합의해야 한다.

조회한 파일 정보와 점수는 [SearchResult 생성 위치](../services/search_service.py#L32)에서
하나로 묶어 GUI에 전달할 목록에 담는다. 파일 정보가 없으면 저장소 불일치 오류를 발생시킨다.

## 링크 유지 방법

링크는 이 문서를 기준으로 한 상대 경로와 #L줄번호 형식이다. 예: ../services/analysis_service.py#L28
VS Code에서 이 Markdown 문서의 링크를 Ctrl+클릭하거나 미리보기에서 클릭한다.
Python 주석의 경로는 사용 위치 안내이며, Markdown 링크와 동일하게 동작한다고 보장하지 않는다.
서비스 코드 앞에 줄이 추가되면 링크의 줄 번호도 갱신해야 한다.
주석에는 줄 번호 대신 파일명과 함수명을 남겨, 줄 번호가 바뀌어도 사용 위치를 찾을 수 있도록 했다.

## GUI 진행 상황 콜백

`AnalysisService.analyze(folder_path, on_progress=함수)`로 진행 알림 함수를 전달한다.
함수는 `(처리한 개수, 전체 개수)`를 받는다. 사진 읽기 실패도 처리 개수에 포함한다.
사진 목록 수집 후 처음에 `(0, 전체 개수)`를 알리므로 빈 폴더는 `(0, 0)`으로 전달된다.
콜백을 생략하면 기존처럼 보고서만 반환한다.

`gui.py`는 작업 스레드에서 분석/검색을 수행하고, 큐에 알림을 넣는다.
메인 스레드의 `PhotoSearchApp.poll_events()`가 큐를 읽어 화면을 갱신한다.
콜백 자체의 오류도 호출자에게 전달되므로 콜백은 간단하고 빠르게 실행되는 함수로 작성한다.


## 2026-10-14 최신 연결 상태

현재 이미지 로더는 경로를 받아 PIL 이미지를 반환하고, ImageEncoder.encode()는 그 PIL 이미지를 받는다.
스캐너의 FileInfo 생성 인자는 수정됐다. RepositoryAdapter는 파일 수정 시각 modified_time을 UTC 문자열 updated_at으로 저장하고 조회 시 복원한다.
KoreanTextEncoder는 encode_text()를 제공하지만 SearchService는 encode()를 호출하므로 연결이 필요하다.
정확한 검증 결과와 남은 작업은 [최신 병합 점검](history/MERGE_CHECK_2026-10-14.md)을 참고한다.

## 실제 GUI 연결

기본 GUI는 real_services.RealServiceFactory에서 실제 로더·인코더·SQLite·FAISS를 생성한다. TextEncoderAdapter가 encode()를 encode_text()에 연결하고, ImageEncoderAdapter는 현재 PIL 입력을 그대로 전달하면서 벡터를 검사한다. 분석과 검색은 동일한 RepositoryAdapter와 VectorIndex를 공유한다.

분석마다 새 임시 DB와 메모리 인덱스를 사용한다. --demo 옵션은 기존 가상 데이터 실행이다. 설치와 실제 모델 검증 범위는 README를 참고한다.


2026-10-16 폴더 정리: 파일별 현재 위치는 [구조 안내](PROJECT_STRUCTURE.md)를 참고한다.
