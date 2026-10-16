# local_file_search

문장으로 내 컴퓨터의 사진을 찾는 캡스톤 프로젝트.

## 현재 상태 — 2026-10-14

기본 GUI에 팀원 구현을 연결했다. 폴더의 실제 사진을 읽고 이미지 인코더로 벡터화한 뒤 SQLite와 FAISS에 저장한다. 검색 문장은 문장 인코더를 거쳐 사진과 비교하며 결과 사진을 미리 볼 수 있다.

팀원 로더·DB·인코더 원본 코드는 수정하지 않았다. 우리 쪽 어댑터가 함수 이름·파일 정보·벡터 형식을 맞춘다.

**현재 저장 범위는 한 번의 분석 세션이다.** 분석 시작마다 새 임시 DB와 메모리 인덱스를 만들고 이전 분석 결과를 교체한다. 앱을 다시 실행하면 재분석해야 한다. 기존 DB 파일은 읽거나 변경하지 않는다. 영구 저장·불러오기와 기존 DB 이전은 아직 연결하지 않았다.

## 설치와 실행

VS Code에서 사용할 Python 인터프리터를 선택한 뒤 새 터미널에서 실행한다. Tkinter가 포함된 Python이 필요하다.

~~~powershell
python -m pip install -r requirements-app.txt
python gui.py
~~~

1. 폴더를 선택하고 **분석 시작**을 누른다.
2. 처음에는 모델과 토크나이저 다운로드에 인터넷 연결과 시간이 필요할 수 있다.
3. 분석이 끝나면 찾고 싶은 사진을 문장으로 입력한다.
4. 결과를 선택하면 사진 미리보기와 파일 경로가 표시된다.

지원 확장자는 JPG, JPEG, PNG, WEBP다. 하위 폴더도 탐색한다. 손상된 사진은 실패 목록에 표시하고 다음 사진을 처리한다. 그 외 모델·저장 오류는 화면에 표시하고 분석을 중단한다.

설치한 라이브러리는 위 명령을 실행한 Python 환경에 있어야 한다. Windows에서 python 명령이 Python만 출력한다면 실행 별칭 대신 실제 실행 파일 경로를 사용한다.

~~~powershell
& '실제 Python 실행 파일 경로' -m pip install -r requirements-app.txt
& '실제 Python 실행 파일 경로' gui.py
~~~

현재 로컬 검증용 Python은 3.14.3이다. torch 2.14.1, open_clip_torch 3.3.0, transformers 4.57.6을 설치하고 실제 모델로 샘플 사진 3장의 분석·한국어 검색을 확인했다. 실제 모델에는 이미지·문장 인코더가 각각 모델을 로드하므로 충분한 메모리도 필요하다.



### 현재 Windows PC에서 바로 실행하는 명령

터미널에 Python만 출력되거나 창이 열리지 않으면, 이 PC에서는 아래 전체 경로를 사용한다.

~~~powershell
cd C:\Capstone\image-search-demo-v2
& 'C:\Users\이수아\AppData\Local\Python\pythoncore-3.14-64\python.exe' -m pip install -r requirements-app.txt
& 'C:\Users\이수아\AppData\Local\Python\pythoncore-3.14-64\python.exe' gui.py
~~~

설치는 처음 한 번 필요하다. 설치 완료 후부터는 마지막 GUI 실행 명령만 사용하면 된다. 창에서 폴더 선택 후 분석 시작을 눌러야 실제 모델 준비와 사진 분석이 시작된다. 터미널이 >>로 시작하면 Ctrl+C로 미완성 입력을 취소하고 명령을 다시 입력한다.

모델 없이 GUI만 확인하려면 마지막 명령 끝에 --demo를 추가한다. 이 전체 경로는 이수아 PC용이며, 다른 팀원은 본인의 Python 실행 파일 경로를 사용한다.

## 모델 없이 데모 실행

~~~powershell
python gui.py --demo
python app.py
~~~

GUI 데모만 사용하려면 모델 라이브러리 없이 실행할 수 있다. Pillow는 미리보기용이다.

~~~powershell
python -m pip install Pillow
python gui.py --demo
~~~

데모는 가상 사진 3개 중 성공 2개·읽기 실패 1개를 재현한다. 검색 문장에 관계없이 고정된 결과를 반환한다. app.py는 기존 콘솔 데모로 유지했다.

## 기능 연결

~~~text
GUI → RealServiceFactory
분석: DefaultFileScanner → DefaultImageLoader → ImageEncoderAdapter
    → RepositoryAdapter → SQLite
    → 같은 파일 ID로 FAISS 저장
검색: TextEncoderAdapter → 같은 FAISS 검색
    → 같은 RepositoryAdapter에서 파일 정보 조회 → GUI 미리보기
~~~

| 연결 부분 | 실제 규격 | 우리 쪽 처리 |
|---|---|---|
| 이미지 로더 | 경로 → PIL RGB 이미지 | 읽은 이미지를 인코더로 전달 |
| 이미지 인코더 | encode(PIL 이미지) → 512차원 벡터 | ImageEncoderAdapter가 배열 형식·차원·유효값 검사 |
| 문장 인코더 | encode_text(문장) → 벡터 | TextEncoderAdapter가 서비스의 encode()로 연결 |
| DB | DB용 FileInfo 저장·조회 | RepositoryAdapter가 공통 필드 이름과 시각 표현 변환 |
| FAISS | NumPy float32 배열과 파일 ID | 분석·검색에서 동일한 인덱스 객체 공유 |

두 인코더는 동일한 모델 이름 xlm-roberta-base-ViT-B-32와 가중치 laion5b_s13b_b90k를 사용한다. 모델은 첫 분석 때 작업 스레드에서 로드하고 이후 재분석에서는 재사용한다. 화면 갱신은 Queue를 통해 메인 스레드에서 처리한다.

현재 병합된 이미지 인코더는 PIL 이미지 입력이다. 경로 입력으로 바꾼 별도 버전의 반영 여부는 담당자 확인이 필요하다.

### 파일 정보 대응

| 서비스 | DB | 변환 |
|---|---|---|
| path | file_path | 경로 |
| name | file_name | 이름 |
| extension | file_extension | 확장자 |
| size | file_size | 바이트 단위 크기 |
| modified_time | updated_at | Unix timestamp ↔ 시간대가 표시된 UTC 문자열 |
| file_hash | file_hash | 유지, 빈 값이면 실제 파일의 SHA-256 계산 |
| created_at | created_at | 유지, 빈 값이면 저장 요청 시각으로 보완 |
| 별도 필드 없음 | file_id | DB 반환 ID를 FAISS에도 사용 |

updated_at은 사진 파일의 수정 시각이다. created_at은 파일 정보 객체 생성 시각이며 실제 사진 파일 생성 시각과 다르다.

## 의존성 목록

- requirements.txt: 팀원 모델 의존성 목록.
- requirements-db.txt: 위 목록에 NumPy·FAISS 추가.
- requirements-app.txt: 위 목록에 Pillow·다국어 모델용 transformers·sentencepiece 추가. 실제 GUI 실행 시 사용한다.

## 검증

~~~powershell
python -m unittest discover -s tests -v
~~~

테스트 25개 통과. 실제 임시 사진·손상 사진·스캐너·로더·SQLite·FAISS를 사용해 분석부터 검색까지 검증했다. 별도 작업 스레드 간 조회, 재분석, 검색 결과에 따른 파일 정보 복원도 확인했다.

위 자동 테스트에서는 AI 인코더를 테스트용 벡터 생성기로 대체했다. 별도로 실제 모델을 사용해 assets/images의 고양이 사진 3장을 분석했고 읽기 실패는 0건이었다. ‘하품하는 고양이’는 Test2.jpg, ‘고양이 얼굴 클로즈업’은 Test3.jpg가 1위였다. 전체 결과는 [실제 모델 검색 기록](artifacts/checks/CAT_SEARCH_CHECK_2026-10-14.json)에 저장했다. 사진 3장으로 한 제한된 확인이며 일반적인 검색 정확도와 사용자 화면에서의 최종 검색 동작은 별도 검증이 필요하다.

## 남은 협업

- 이미지 인코더의 최종 입력 규격 확정.
- 더 다양한 사진과 한국어 문장으로 검색 품질 및 실제 GUI 검색 동작 확인.
- DB와 FAISS의 영구 저장·불러오기 및 기존 DB 컬럼 이전 정책.
- 누적 분석 시 중복 파일 갱신, 해시 재계산, 일부 저장 실패 복구 정책.

## 관련 문서

- [함수 규격과 사용 위치](docs/INTERFACE_GUIDE.md)
- [DB 어댑터 연결](docs/DB_ADAPTER_GUIDE.md)
- [병합 점검과 후속 연결 기록](docs/history/MERGE_CHECK_2026-10-14.md)


## 폴더 구조 — 2026-10-16

1차 데모를 보존하고 v2 작업 폴더에서 기능별로 파일을 정리했다. 내 포크의 브랜치는 `codex/image-search-demo-v2`, 원본 공유 브랜치는 `edmond1889-service-gui-patch-1`이다.
`python gui.py`, `python gui.py --demo`, `python app.py` 실행 방법은 동일하다.
샘플 폴더는 `assets/images`로 이동했다.

| 폴더 | 역할 |
|---|---|
| imaging/ | 사진 탐색과 읽기 |
| encoders/ | 이미지·문장 임베딩 |
| storage/ | SQLite 메타데이터와 FAISS 인덱스 |
| adapters/ | 팀원 구현과 공통 규격 사이의 변환 |
| services/ | 분석·검색 흐름 |
| models/ | 공통 데이터 구조 |
| demo/ | 모델 없이 실행하는 가상 데이터 구현 |
| assets/images/ | 시연용 샘플 사진 |
| docs/ | 함수 규격·DB 연결·구조 설명 |
| docs/history/ | 과거 병합·검증 기록 |
| artifacts/checks/ | 실제 검색 결과 기록 |
| tests/ | 자동 검증 |

기존 경로 대응과 수정할 파일 선택 기준은 [프로젝트 구조 안내](docs/PROJECT_STRUCTURE.md)를 참고한다.

새 작업 폴더는 `C:/Capstone/image-search-demo-v2`다. origin은 내 포크, upstream은 팀 원본이다. 개인 학습 노트는 내 포크에만 보관한다.
