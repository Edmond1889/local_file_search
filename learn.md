# 개인 학습 노트 — 이미지 로더, DB, 서비스 연결과 데모 준비

기준: 2026-10-16, `C:\Capstone\image-search-demo-v2`의 실제 파일을 읽어 작성.
이전 대화에 붙인 코드와 현재 파일은 버전이 다르다. 아래 설명은 현재 파일을 기준으로 한다.
개인 메모. 2026-10-16 v2 작업 폴더와 기능별 구조를 반영했다. 사용자 요청으로 내 GitHub 포크의 v2 브랜치에만 보관하며 팀 원본에는 올리지 않는다.

## 1. 지금 어떤 프로그램인가?

문장을 입력해서 내 컴퓨터의 사진을 찾는 Python 데스크톱 프로그램이다.

| 실행 방법 | 뜨는 화면 | 실제 사진 검색 여부 |
|---|---|---|
| `python gui.py` | Tkinter 별도 창 | 실제 로더·모델·SQLite·FAISS 연결 |
| `python gui.py --demo` | 가상 데이터용 Tkinter 창 | 가상 사진과 고정 벡터로 연결만 확인 |
| `python app.py` | 터미널 | 가상 데이터 콘솔 데모 |

새로 뜨는 창은 '데스크톱 GUI'라고 부르면 된다. 인터프리터는 Python 코드를 실행하는 프로그램이고, 터미널은 명령을 입력하는 화면이다.
현재 소스에는 웹 화면, 웹 서버 진입점, 프런트엔드가 없다. 브라우저에서 보는 웹 앱은 별도 구현이 필요하다. 노션에 화면을 올리는 것은 실행 화면을 공유하는 것이다.

중요: 창이 뜨는 것과 실제 검색에 성공하는 것은 별개다. 모델은 '분석 시작'을 누른 뒤 준비된다.
현재 실제 모드는 분석할 때마다 새 임시 DB와 메모리 인덱스를 만든다. 앱 재실행 시 재분석해야 한다.

## 2. 전체 흐름을 먼저 보기

```text
폴더 선택 → GUI의 분석 시작 → RealServiceFactory가 도구 준비
  → AnalysisService.analyze()
    → DefaultFileScanner.scan()       파일 정보 목록
    → DefaultImageLoader.load()       PIL RGB 이미지
    → ImageEncoderAdapter.encode()    이미지 임베딩
    → RepositoryAdapter.save()        SQLite 저장, 파일 ID 반환
    → VectorIndex.add(ID, 벡터)       같은 ID로 FAISS 저장

문장 입력 → SearchService.search()
  → TextEncoderAdapter.encode()      문장 임베딩
  → VectorIndex.search()              (파일 ID, 점수) 목록
  → RepositoryAdapter.find_by_id()    파일 정보 복원
  → SearchResult(file, score)         GUI 결과 목록과 미리보기
```

경로는 파일 주소, 이미지는 픽셀 데이터, 임베딩은 모델이 만든 특징 숫자 배열이다. 서로 다른 자료다.
DB에는 이미지 원본이나 픽셀을 넣지 않는다. 파일 정보를 저장하고, 벡터는 FAISS가 보관한다. 미리보기는 경로로 원본 사진을 다시 읽는다.

## 3. image_loader.py — 사진 찾기와 읽기

실제 파일: [image_loader.py](./imaging/image_loader.py)
이전 대화에서는 `collect_images()`, `check_image()`, `load_image()` 함수였다. 현재는 서비스 규격에 맞춘 두 클래스다.

### 3-1. DefaultFileScanner.scan(folder_path)

입력은 폴더 경로, 출력은 `list[FileInfo]`다. 아직 사진 내용을 읽거나 벡터를 만들지는 않는다.

```python
for root, _, files in os.walk(folder_path):
    for file_name in files:
        ext = os.path.splitext(file_name)[1].lower()
```

- `os.walk()`는 폴더와 하위 폴더를 탐색한다. `root`는 현재 탐색 위치, `files`는 그 위치의 파일 이름 목록이다.
- `_`에는 하위 폴더 목록이 들어오지만 여기서는 사용하지 않는다.
- `splitext()`는 이름과 확장자를 나누고, `[1]`은 확장자를 선택한다. `lower()`로 `.JPG`도 `.jpg`로 비교한다.
- `IMAGE_EXTENSIONS`는 허용 확장자를 모은 집합이다. JPG, JPEG, PNG, WEBP를 지원한다.
- `os.path.join()`으로 경로를 합치고 `abspath()`로 절대 경로를 만든다.
- `os.stat()`의 `st_size`는 바이트 크기, `st_mtime`은 수정 시각이다.

각 파일을 공통 `FileInfo(name, path, extension, size, modified_time)`로 포장해 목록에 넣는다. `FileInfo`는 파일 정보의 그릇이다.

현재 한계: 없는 폴더는 빈 목록을 반환한다. `isdir()` 검사와 탐색 중 권한 오류 안내가 없어 잘못된 폴더와 빈 폴더를 구분하기 어렵다. `stat()` 실패 시 크기와 시각을 0으로 넣는다. 수정 시각 0은 '알 수 없음'이 아니라 실제 시각 값으로 해석될 수 있어 후속 개선 대상이다.
확장자가 맞아도 손상 파일일 수 있다. 손상 여부는 다음 로더 단계에서 확인한다.

### 3-2. DefaultImageLoader.load(file_path)

입력은 사진 경로, 출력은 `PIL.Image.Image` 형태의 RGB 이미지다.

1. `getsize()`로 0바이트인지 검사한다.
2. 파일 접근이 실패하면 `ImageLoadError`를 발생시킨다.
3. `with Image.open(...) as img: img.verify()`로 이미지 구조를 검사한다.
4. 파일을 다시 열고 `img.load()`로 실제 픽셀을 읽는다.
5. `img.convert("RGB")`로 색상 채널을 맞춘 새 이미지를 반환한다.

`verify()` 후에는 검사한 객체로 픽셀 처리를 계속하지 않고 다시 연다. RGB는 빨강·초록·파랑 3채널을 뜻한다. 원본 파일을 덮어쓰는 작업은 아니다. 크기 조절·모델 전용 정규화는 인코더 쪽 역할이다.

```python
try:
    image = self.image_loader.load(file.path)
except ImageLoadError as error:
    # 서비스가 실패 보고서에 기록하고 다음 사진을 처리한다.
    ...
```

예전 함수는 실패하면 `None`을 반환했지만 현재 로더는 예외를 발생시킨다. 서비스가 `None`을 이미지로 인코더에 넘기는 일을 피하고, 실패 이유를 GUI에 전달할 수 있다.

개선 메모: 두 번째 `Image.open()`도 `with`로 감싸면 파일 핸들 정리가 명확해진다. 모든 읽기 오류를 '손상된 이미지'로 표시하므로 원인은 메시지 안의 상세 오류까지 확인한다.

## 4. db_manager.py — 파일 정보와 벡터 관리

실제 파일: [db_manager.py](./storage/db_manager.py)
이전 대화의 `ImageMetadataDBManager` 단일 클래스와 다르다. 지금은 `FileInfo`, `Repository`, `VectorIndex`로 나뉜다.

| 구성 | 책임 |
|---|---|
| DB용 `FileInfo` | DB에 저장할 한 파일의 정보 |
| `Repository` | SQLite 파일 정보 저장·조회 |
| `VectorIndex` | FAISS 벡터 저장·유사도 검색 |

### 4-1. DB용 FileInfo

`@dataclass`는 필드 정의로 생성자 등을 만들어 주는 문법이다.
DB용 필드는 `file_path`, `file_name`, `file_extension`, `file_size`, `file_hash`, `created_at`, `updated_at`, `file_id`다.
`Optional[int]`는 정수 또는 `None`이라는 뜻이다. 저장 전에는 ID가 없을 수 있다.

주의: `models/file_info.py`에도 `FileInfo`가 있다. 이름은 같지만 별개 클래스다. 공통 모델의 `path`와 DB 모델의 `file_path`처럼 필드 이름이 달라 어댑터가 필요하다.

### 4-2. Repository.__init__()와 _init_db()

`db_path`를 보관하고 SQLite 연결을 열어 `image_metadata` 테이블이 없으면 만든다.

- `sqlite3.connect()`는 DB 파일에 연결한다.
- `cursor()`는 SQL을 실행하고 결과를 받는 도구다.
- `CREATE TABLE IF NOT EXISTS`는 기존 테이블을 삭제하지 않는다. 기존 테이블에 새 컬럼을 추가하는 기능도 아니다.
- `file_id INTEGER PRIMARY KEY AUTOINCREMENT`는 SQLite가 새 파일 ID를 발급하도록 한다.
- `file_path TEXT UNIQUE NOT NULL`은 경로의 중복과 NULL 값을 막는다. 빈 문자열이나 같은 내용의 다른 경로까지 막는 것은 아니다.
- `commit()`은 변경을 확정하고 `close()`는 연결을 닫는다.

`_init_db`의 밑줄은 내부용이라는 관례다. 외부 호출을 언어 차원에서 금지하지는 않는다.

### 4-3. Repository.save(file_info)

DB용 FileInfo의 값을 `INSERT`로 저장하고 `cursor.lastrowid`를 반환한다.
`?`는 값을 넣을 자리를 표시한다. SQL 문자열에 경로를 직접 이어 붙이지 않고 별도 인자로 전달한다.

```python
file_id = repository.save(file_info)
vector_index.add(file_id, vector)
```

이 ID가 파일 정보와 벡터를 연결하는 열쇠다. 예를 들어 DB의 ID 7이 고양이 사진이면 FAISS에도 그 사진 벡터를 ID 7로 넣는다.
같은 경로를 같은 DB에 다시 넣으면 UNIQUE 제약 오류가 난다. 현재 `save()`에는 자동 갱신이나 중복 건너뛰기가 없다.

### 4-4. Repository.find_by_id(file_id)

`SELECT ... WHERE file_id = ?`로 한 행을 찾고 `fetchone()`으로 가져온다. 있으면 DB용 FileInfo로 복원하고, 없으면 `None`을 반환한다.
`(file_id,)`의 쉼표는 요소가 하나인 튜플을 만드는 문법이다.
사진이 삭제됐더라도 DB에 행이 있으면 메타데이터 조회는 가능하다. 실제 미리보기 성공 여부는 별개다.

### 4-5. VectorIndex.__init__()와 add()

```python
self.base_index = faiss.IndexFlatIP(self.embedding_dim)
self.index = faiss.IndexIDMap2(self.base_index)
```

`IndexFlatIP`는 저장 벡터와 검색 벡터의 내적을 비교한다. `IndexIDMap2`는 우리가 지정한 파일 ID를 연결한다.
현재 코드는 `add_with_ids()`로 DB에서 받은 ID를 명시적으로 넣으므로, 예전 버전의 '추가 순번과 DB ID가 우연히 같아야 한다'는 문제는 개선됐다.

정규화 과정:

```python
vec = vec.astype(np.float32).reshape(1, -1)
norm = np.linalg.norm(vec)
if norm > 0:
    vec = vec / norm
```

- `float32`는 각 숫자를 32비트 실수로 맞춘다.
- `reshape(1, -1)`은 512개 숫자를 `(1, 512)` 모양, 즉 벡터 한 개의 묶음으로 만든다.
- `norm`은 벡터 길이다. 나눠서 길이를 1로 맞춘다.
- 저장·검색 양쪽의 정상 벡터를 정규화하므로 내적을 코사인 유사도로 사용할 수 있다.
- 파일 ID는 `np.int64` 배열로 만들어 전달한다.

512는 현재 모델과 맞춘 특징 차원이다. 사진 픽셀 수나 이미지 개수가 아니다.
공식 참고: [FAISS의 ID 지원](https://github.com/facebookresearch/faiss/wiki/Faiss-indexes), [내적과 코사인 유사도](https://github.com/facebookresearch/faiss/wiki/MetricType-and-distances).

### 4-6. VectorIndex.search(query_vector, top_k)

인덱스가 비었으면 `[]`를 반환한다. 검색 벡터를 정규화하고 FAISS에서 상위 결과를 받는다.
`indices`는 파일 ID, `distances`는 이 인덱스에서는 내적 점수다. 변수 이름이 distances라고 해서 항상 낮을수록 좋은 거리는 아니다.
`zip()`으로 ID와 점수를 묶고, `-1`인 빈 결과는 건너뛴다. 반환 형식은 `[(파일 ID, 점수), ...]`다.
점수 0.26을 '정확도 26%'로 설명하면 안 된다. 모델이 계산한 유사도이며 확률이 아니다.

### 4-7. save_index()와 load_index()

FAISS 인덱스를 파일로 저장하거나 불러오는 함수는 존재한다. 하지만 현재 `RealServiceFactory`와 기본 GUI의 실행 흐름에서는 호출하지 않는다.
SQLite는 임시 폴더의 DB 파일에 커밋하고, FAISS는 메모리에 둔다. 따라서 현재 앱을 '검색 기록 영구 저장 완료'로 소개하면 안 된다.

## 5. 어댑터와 서비스가 필요한 이유

실제 파일: [RepositoryAdapter](./adapters/repository_adapter.py), [인코더 어댑터](./adapters/encoder_adapters.py), [RealServiceFactory](./real_services.py)

어댑터는 팀원 기능의 입출력을 서비스 규격에 맞추는 연결 코드다.

| 서비스에서 쓰는 값 | DB에 전달되는 값 |
|---|---|
| path / name / extension / size | file_path / file_name / file_extension / file_size |
| modified_time | updated_at: 시간대를 포함한 UTC 문자열 |
| file_hash가 빈 경우 | 실제 파일 전체를 1MB씩 읽어 SHA-256 계산 |
| created_at | 파일 정보 객체 생성 시각, 빈 값이면 보완 |

`updated_at`은 이 프로젝트에서 사진 파일의 수정 시각으로 사용한다. DB 행 수정 시각과 혼동하지 않는다. `created_at`도 실제 사진 파일의 생성 시각과 다르다.
조회할 때는 반대 방향으로 변환해 공통 FileInfo를 만든다.
이전 코드의 '처음 4096바이트만 해싱'과 달리 현재 어댑터는 파일 전체를 읽는다. 다만 해시를 저장하는 것과 해시로 내용 중복을 제거하는 것은 별개다. 현재 자동 중복 제거는 없다.

인코더 어댑터는 출력이 512개 유한 숫자의 1차원 벡터인지 확인하고 영벡터를 거부한다. 문장 인코더의 `encode_text()`를 서비스가 요구하는 `encode()`로 연결한다.
`interface.py`의 Protocol은 요구 함수의 모양을 설명하는 규격이다. 실제 모델·DB를 구현하는 파일은 아니다.

`AnalysisService`는 호출 순서와 성공·읽기 실패 보고서를 관리한다. `SearchService`는 문장 → 벡터 → ID → 파일 정보 → SearchResult를 연결한다.
사진 읽기 실패는 기록하고 다음 사진으로 진행하지만 임베딩·DB·인덱스 오류는 호출자에게 전달한다.
DB 저장 후 FAISS 추가가 실패했을 때 두 저장소를 함께 되돌리는 처리는 아직 없다. 앞단의 벡터 검증만으로 모든 저장 실패가 해결되는 것은 아니다.

`RealServiceFactory`는 실제 도구들을 조립한다. 분석과 검색이 같은 repository/index 객체를 사용하도록 하고 인코더는 재분석 시 재사용한다. 매 분석의 임시 저장소는 새로 만든다.
GUI는 작업 스레드에서 분석·검색하고 Queue로 결과를 전달받아 메인 스레드에서 화면을 갱신한다.

## 6. 실제 기능을 확인하는 순서 (1차 데모 참고)

1. 아래 명령으로 실제 모드를 실행한다. 제목에 '연결 데모'가 붙는 `--demo` 모드와 구별한다.
2. 샘플 폴더 `C:\Capstone\image-search-demo-v2\assets\images`를 선택한다.
3. '분석 시작'을 누르고 성공·실패 개수를 확인한다. 창 실행 시점이 아니라 이때 모델 준비가 시작된다.
4. '하품하는 고양이'를 검색하고 결과 이름·점수를 확인한다.
5. 결과를 선택해 실제 사진 미리보기를 확인한다.
6. '고양이 얼굴 클로즈업'으로 바꿔 결과 순서가 바뀌는지 확인한다.

```powershell
cd C:\Capstone\image-search-demo-v2
& 'C:\Users\이수아\AppData\Local\Python\pythoncore-3.14-64\python.exe' gui.py
```

라이브러리 오류가 있으면 같은 Python으로 `-m pip install -r requirements/requirements-app.txt`를 실행한다. 회의 직전에는 설치 환경을 불필요하게 바꾸지 않고 기존 환경에서 먼저 확인한다. 첫 모델 다운로드에는 인터넷과 시간이 필요할 수 있다.

기존 기록 `artifacts/checks/CAT_SEARCH_CHECK_2026-10-14.json`에는 샘플 3장 분석 성공, '하품하는 고양이'의 Test2.jpg 1위, '고양이 얼굴 클로즈업'의 Test3.jpg 1위가 남아 있다. 이는 이전 실행 기록이다. 이번 문서 작성 중 실제 모델이나 GUI를 새로 실행한 결과는 아니다.
README에는 자동 테스트 25개 통과 기록이 있다. 이번 작업에서 테스트를 다시 실행한 것은 아니다.

회의 설명 예시:

> 현재 Python Tkinter로 데스크톱 GUI를 구현했습니다. 폴더 사진을 읽어 이미지 임베딩을 만들고 SQLite에 파일 정보, FAISS에 벡터를 저장합니다. 문장을 같은 모델 공간의 벡터로 바꿔 유사한 사진을 검색합니다. 샘플 사진 검색 기록이 있으며, 이번 시연에서는 분석부터 검색과 미리보기까지 보여드리겠습니다. 현재는 분석 세션 단위이고 영구 저장과 웹 UI는 후속 범위입니다.

노션에는 '실행 창', '분석 완료 화면', '문장과 검색 결과', '선택한 사진 미리보기'를 구분해서 올리면 진행 범위가 잘 드러난다. 창만 확인했다면 아직 검색까지 직접 검증했다고 말하지 않는다.

## 7. 현재 폴더 읽는 법

실제 구조와 이전 경로 대응은 [프로젝트 구조 안내](./docs/PROJECT_STRUCTURE.md)에 정리했다.
imaging은 사진 읽기, encoders는 모델, storage는 DB·FAISS, adapters는 변환, services는 흐름 연결이다.
본문의 image_loader.py와 db_manager.py 설명은 각각 imaging/image_loader.py와 storage/db_manager.py를 가리킨다.

읽는 순서: 이 노트 → imaging/image_loader.py → models/file_info.py → storage/db_manager.py
→ adapters/repository_adapter.py → services 두 파일 → real_services.py → gui.py.

## 8. v2에서 작업하기

작업 폴더: C:/Capstone/image-search-demo-v2
내 GitHub 브랜치: codex/image-search-demo-v2
팀 원본 공유 브랜치: edmond1889-service-gui-patch-1

origin은 내 포크, upstream은 팀 원본이다. 일반 개발과 개인 메모는 내 v2에서 기록한다.
이번에는 공유 코드 커밋을 먼저 만들고 원본에 푸시한 뒤 이 노트를 별도 커밋으로 추가했다.
이 노트는 더 이상 v2에서 로컬 전용이 아니다. 내 포크에 추적·업로드하며, 원본에는 포함하지 않는다.
기존 1차 데모 폴더에 있는 learn.md의 로컬 제외 설정은 그대로 보존한다.

원본으로 후속 변경을 전달할 때는 개인 노트 커밋을 포함한 v2 전체를 합치지 않는다.
내 포크의 메모 없는 공유 브랜치에 코드·공유 문서 변경만 담고, 원본의 내 브랜치로 PR을 보낸다. 원본 작업 브랜치에는 직접 푸시하지 않는다.
노트를 파일 목록에서 지우는 것만으로 과거 커밋에서 사라지는 것은 아니다.

C:/Capstone/project는 통합 전 개인 작업(demo-v0),
C:/Capstone/demo-v1은 기존 1차 데모 폴더이며 이름 변경이 완료됐다.
project → demo-v0 이름 변경은 Windows에서 폴더 사용 중 잠금이 있어 아직 완료되지 않았다.
새 개발은 v2 폴더에서 한다. 기존 두 폴더를 수동으로 동기화하지 않는다.

## 9. 스스로 설명해 보기

- scan은 경로 문자열 목록이 아니라 왜 FileInfo 목록을 주는가?
- load가 반환하는 이미지와 encode가 반환하는 벡터는 무엇이 다른가?
- DB 저장의 반환 ID를 FAISS에 그대로 전달하는 이유는 무엇인가?
- 이름이 같은 FileInfo 두 개 사이에 왜 어댑터가 필요한가?
- save_index 함수가 있는데도 왜 재실행하면 재분석해야 하는가?
- 창이 뜬 상태와 실제 검색 검증 완료는 어떻게 구분하는가?


## 10. 담당자와 옛 데모 코드 찾기

- [담당자·이전 경로·현재 경로](./docs/CODE_OWNERSHIP.md)
- [옛 데모와 보관 후보](./docs/DEMO_CODE_INVENTORY.md)
- [설치 목록 세 파일의 역할](./requirements/README.md)

현재 app.py와 demo/demo_adapters.py도 데모·테스트에서 사용하므로 waste로 옮기지 않았다.
통합 전 project 사본과 another/ver1, another/test_proto는 현재 v2에서 참조하지 않는 옛 구현이다.
코드를 실행하지 않는 구버전 기록인지 확인한 뒤 폴더 단위로 보관할 수 있다.
이번에는 이 목록만 작성했고 waste 이동은 하지 않았다.

검증 기록(2026-10-16): 이번 의존성 정리 후 테스트 25개가 통과했고 pip --dry-run --no-index --no-deps로 세 파일의 포함 경로를 확인했다. 실제 모델 추론을 다시 실행한 것은 아니다.
