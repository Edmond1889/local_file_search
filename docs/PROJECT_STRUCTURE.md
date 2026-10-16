# 프로젝트 구조와 파일 찾기

2026-10-16 기준. 기능별로 위치를 정리했으며 모델·로더·DB의 동작은 변경하지 않았다.
출처가 다른 코드는 기능별 폴더에서 함께 관리하고, 차이는 어댑터에서 맞춘다.

## 전체 구조

```text
image-search-demo-v2/
├── gui.py                  # 실제 GUI / --demo
├── app.py                  # 기존 콘솔 데모
├── real_services.py        # 실제 구현 조립
├── interface.py            # 협업 함수 규격
├── imaging/image_loader.py
├── encoders/
│   ├── image_encoder.py
│   └── text_encoder.py
├── storage/db_manager.py
├── adapters/
├── services/
├── models/
├── demo/demo_adapters.py
├── assets/images/          # 시연 사진 3장
├── docs/
│   ├── PROJECT_STRUCTURE.md
│   ├── INTERFACE_GUIDE.md
│   ├── DB_ADAPTER_GUIDE.md
│   └── history/
├── artifacts/checks/       # 실제 모델 검색 기록
├── tests/
├── README.md
├── requirements/          # 모델·DB·앱 설치 목록
└── learn.md                # 내 포크에만 보관, 원본 브랜치에는 없음
```

## 팀원 구현과 연결 코드

| 구분 | 현재 위치 | 역할 |
|---|---|---|
| 통합한 팀원 구현 | imaging/image_loader.py | 폴더에서 파일 정보 수집, PIL RGB 이미지 읽기 |
| 통합한 팀원 구현 | storage/db_manager.py | DB용 FileInfo, Repository, VectorIndex |
| 통합한 팀원 구현 | encoders/image_encoder.py | PIL 이미지 임베딩 |
| 통합한 팀원 구현 | encoders/text_encoder.py | 한국어 문장 임베딩 |
| 서비스 연결 | adapters/ | 필드·함수 이름·벡터 형식 맞추기 |
| 서비스 연결 | services/ | 분석·검색 호출 순서와 오류 전달 |
| 서비스 연결 | real_services.py | 모델 재사용, 임시 DB/인덱스 생성 |
| 공통 규격 | interface.py / models/ | 역할별 함수와 데이터 구조 |
| 실행 화면 | gui.py | 스레드·큐·화면·미리보기 |
| 가상 데이터 | demo/demo_adapters.py / app.py | 모델 없이 연결 확인 |

이 표는 코드 역할과 통합 경로를 설명한다. 개인별 저작자 판정은 Git 이력으로 확인한다.
팀원 구현의 내용은 그대로 옮겼고 호출하는 쪽의 import 경로를 수정했다.

## 이전 경로 → 현재 경로

| 이전 | 현재 |
|---|---|
| image_loader.py | imaging/image_loader.py |
| db_manager.py | storage/db_manager.py |
| text_encoder.py | encoders/text_encoder.py |
| CapStone/embedding/image_encoder.py | encoders/image_encoder.py |
| demo_adapters.py | demo/demo_adapters.py |
| CapStone/IMG/ | assets/images/ |
| INTERFACE_GUIDE.md | docs/INTERFACE_GUIDE.md |
| DB_ADAPTER_GUIDE.md | docs/DB_ADAPTER_GUIDE.md |
| MERGE_CHECK_2026-10-14.md | docs/history/MERGE_CHECK_2026-10-14.md |
| CAT_SEARCH_CHECK_2026-10-14.json | artifacts/checks/CAT_SEARCH_CHECK_2026-10-14.json |
| requirements.txt | requirements/requirements.txt |
| requirements-db.txt | requirements/requirements-db.txt |
| requirements-app.txt | requirements/requirements-app.txt |

예: DB를 불러올 때 `from storage.db_manager import Repository`를 사용한다.
사진·모델 파일을 복제하지 않고 이동했으며 기존 CapStone 이름의 중첩을 없앴다.
과거 기록에는 당시 경로가 남아 있을 수 있다. 현재 실행 경로는 이 문서를 따른다.

## 무엇을 수정할 때 어디를 보는가?

- 사진을 못 읽는다: imaging/image_loader.py
- 임베딩 입력·모델을 바꾼다: encoders/와 adapters/encoder_adapters.py
- DB 필드 이름을 맞춘다: adapters/repository_adapter.py
- DB 테이블·FAISS 저장 방식을 바꾼다: storage/db_manager.py
- 분석·검색 처리 순서를 바꾼다: services/
- 실제 도구의 생성·수명을 바꾼다: real_services.py
- 화면과 버튼을 바꾼다: gui.py

## 실행·검증

저장소 루트에서 실행한다. 내부 모듈을 파일 경로로 직접 실행하지 않는다.

```powershell
python gui.py
python gui.py --demo
python app.py
python -m unittest discover -s tests -v
```

문장 인코더의 자체 예제는 `python -m encoders.text_encoder`로 실행할 수 있다.
GUI에서 사용할 샘플 폴더는 `C:\Capstone\image-search-demo-v2\assets\images`다.
현재도 임시 세션 저장이며 영구 저장이나 웹 UI를 새로 구현한 것은 아니다.

## Git과 다른 작업 폴더

- C:/Capstone/project: 통합 전 개인 코드. demo-v0라는 용도로 구분하며 실제 이름은 아직 유지한다.
- C:/Capstone/demo-v1: 기존 image-search-demo에서 이름 변경한 1차 데모·정리 작업 사본.
- C:/Capstone/image-search-demo-v2: 앞으로 실제로 개발하는 새 폴더.
- origin: 내 GitHub Edmond1889/local_file_search.
- upstream: 팀 원본 nohminju/local_file_search.
- codex/image-search-demo-v2: 내 포크의 v2 브랜치. 개인 학습 노트도 포함한다.
- edmond1889-service-gui-patch-1: 팀 원본의 공유 브랜치. 개인 메모 없는 코드만 반영한다.

완료한 1차 데모 브랜치와 기존 로컬 폴더는 보존했다.
개인 노트를 추가하기 전 공유 코드 커밋을 원본 브랜치에 먼저 반영하고,
그 위에 개인 노트 커밋을 더해 내 포크 v2에만 올리는 방식으로 분리했다.
개인 메모를 삭제한 결과만 푸시해도 이전 커밋에 메모가 남을 수 있으므로,
원본에는 개인 노트 커밋이 포함된 v2 전체 이력을 병합하지 않는다.
후속 공유 작업은 내 포크의 메모 없는 공유 브랜치에서 원본의 내 브랜치로 PR을 보낸다. 원본에는 직접 푸시하지 않는다.

기존 폴더를 계속 동기화하지 말고 새 v2 폴더에서 작업한다.
채팅이나 편집기가 옛 project 경로에 연결돼 있다면 새 v2 폴더를 열어 작업 경로를 맞춘다.
미커밋 변경이 있으면 브랜치 전환 전 상태를 확인한다.
추후 원본의 동일 파일 수정은 이전 경로 → 현재 경로 표를 기준으로 병합한다.

__pycache__와 .pyc는 재생성되는 캐시이므로 올리지 않는다.
공유 문서는 docs/에, 개인 학습 내용은 내 포크의 learn.md에 둔다.


## 담당자·설치 파일·구버전 구분

- [코드 담당자와 출처](CODE_OWNERSHIP.md): Git 기록으로 확인한 작성자, 이전 위치, 현재 위치.
- [데모 코드와 보관 후보](DEMO_CODE_INVENTORY.md): 옛 사본과 현재도 필요한 데모 코드의 구분.
- [설치 파일 안내](../requirements/README.md): 세 TXT의 역할과 설치 명령.

requirements.txt, requirements-db.txt, requirements-app.txt는 requirements/로 이동했다.
이 세 파일의 내용과 내부 -r 포함 관계는 유지했다. 설치 명령은 저장소 루트에서
`python -m pip install -r requirements/requirements-app.txt`다.
