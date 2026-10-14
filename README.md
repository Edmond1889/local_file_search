# local_file_search
자연어 기반 로컬 파일 검색 시스템

## 실행 준비

아래 연결 데모는 Python 3.10 이상과 Tkinter가 필요하다. 현재 Python 3.14.3에서 서비스 테스트를 확인했다.
VS Code의 `Python: Select Interpreter`에서 실제 Python 실행 파일을 선택하고 새 터미널을 연다.

```powershell
python -m pip install -r requirements.txt
python gui.py
```

`python` 명령이 버전이나 결과 대신 `Python`만 출력하면 Windows 실행 별칭을 호출하는지 확인한다.
이 경우 실제 실행 파일을 지정한다: `& '실제 Python 실행 파일 경로' gui.py`.
Pillow는 설치 이름이며 코드에서 사용하는 이름은 `PIL`이다.

## 현재 범위

두 서비스는 각 팀원의 기능을 호출하는 연결 계층이다. `interface.py`는 합의 전 규격 초안이다.
원본 저장소의 실제 임베딩·DB·FAISS 구현과 아래 연결 데모는 아직 직접 연결되지 않았다.

- 분석: 사진 수집 → 이미지 읽기 → 임베딩 → 파일 정보 저장 → 같은 ID로 벡터 저장
- 검색: 문장 임베딩 → 벡터 검색 → 파일 ID로 정보 조회 → SearchResult 반환
- 사진 읽기 실패는 ImageLoadError로 전달받아 보고서에 남기고 다음 사진을 처리한다.
- 임베딩/저장 오류와 검색 결과의 없는 파일 ID는 호출자에게 오류로 전달한다.

## 연결 데모

`python app.py`로 가상 사진 3개 중 성공 2개, 읽기 실패 1개를 재현한다.
고정 벡터와 메모리 저장소를 사용하며 모든 검색 문장에 같은 순서를 반환한다.
실제 사진 검색 성능이나 영구 저장을 검증하는 예제가 아니다.

## 기본 GUI

`python gui.py`로 폴더 선택, 분석 진행률, 검색창, 결과 목록과 미리보기 영역을 사용한다.
기본 실행은 연결 데모다. 선택한 폴더의 실제 사진은 분석하지 않고 가상 사진을 처리한다.
진행 숫자에는 성공과 읽기 실패를 모두 포함한다. 분석/검색은 작업 스레드에서 실행하고,
큐를 통해 결과를 받아 메인 스레드에서 화면을 갱신한다.

팀원 구현 연결 시 `PhotoSearchApp(root, service_factory=실제_서비스_생성함수, demo=False)`로
실제 서비스를 전달한다. 실제 이미지 미리보기에는 Pillow가 필요하다.

## 합의할 사항

- 이미지 자료형, 벡터 차원과 정규화 방식
- DB 파일 ID와 FAISS ID 연결
- 높은 유사도부터 반환한다는 초안 규격 (거리 사용 시 변환 필요)
- 폴더 검증, 읽기 오류 전달, GUI 진행 상황 전달
- 재분석 시 중복 처리, DB/인덱스 저장 실패 복구, 저장·불러오기

실제 연결 시 app.py의 가짜 객체를 팀원 구현으로 교체한다.
두 서비스에는 같은 저장소와 벡터 인덱스를 전달해야 한다.

함수별 역할과 실제 호출 위치는 [연결 규격 가이드](./INTERFACE_GUIDE.md)를 참고한다.

## 검증

`python -m unittest discover -s tests -v`로 연결 규격, 읽기 실패 후 계속 처리,
검색 문장 전달, 파일 ID 조회와 저장 오류 전달을 검증한다.

## 원본 구현과의 연결 상태

- `CapStone/embedding/image_encoder.py`는 현재 PIL 이미지를 입력으로 받는다.
  서비스의 이미지 입력 규격과 맞지만, 실제 모델 설치 및 GUI 연결 검증은 별도다.
- `db_manager.py`는 Repository와 VectorIndex로 분리되어 있다.
  공통 FileInfo와 DB FileInfo의 필드 차이는 RepositoryAdapter로 변환한다.
- requirements.txt는 이 연결 데모의 미리보기 의존성만 담는다.
  원본의 AI 모델/FAISS까지 설치하는 전체 프로젝트 의존성 목록은 아니다.
- 기존 실제 구현 파일과 테스트 사진은 이번 변경에서 수정하지 않는다.


## DB 어댑터

공통 FileInfo에 file_hash와 created_at을 추가했다.
필드 변환과 requirements-db.txt 설치 방법은 [DB 어댑터 가이드](./DB_ADAPTER_GUIDE.md)를 참고한다.
기본 GUI는 여전히 데모이며, 팀원 구현 파일은 수정하지 않았다.
