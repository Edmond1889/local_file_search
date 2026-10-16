# 코드 담당자와 경로 대응

2026-10-16 확인. 함수의 역할과 Git의 최초 추가·후속 수정 기록을 함께 정리했다.
현재 폴더명은 기능을 기준으로 하며 코드의 담당자나 출처를 바꾸는 뜻이 아니다.
이 문서는 GitHub 자동 리뷰 담당자를 지정하는 CODEOWNERS 설정 파일이 아니다.

## 팀원 구현

| GitHub / Git 작성자 | 맡은 기능 | 통합 전 경로 | 현재 v2 위치 |
|---|---|---|---|
| wpptpyqe / 김하은 | 사진 수집·읽기 | image_loader.py | [imaging/image_loader.py](../imaging/image_loader.py) |
| nohminju | SQLite 파일 정보와 FAISS 검색 인덱스 | db_manager.py | [storage/db_manager.py](../storage/db_manager.py) |
| hyunsli7557-ux | 이미지 임베딩 | CapStone/embedding/image_encoder.py | [encoders/image_encoder.py](../encoders/image_encoder.py) |
| duoloo | 문장 임베딩 | text_encoder.py | [encoders/text_encoder.py](../encoders/text_encoder.py) |
| hyunsli7557-ux | 모델 확인용 사진 3장 | CapStone/IMG/ | [assets/images/](../assets/images/) |

확인한 근거:

- 사진 로더: [a51c2f2 최초 추가](https://github.com/nohminju/local_file_search/commit/a51c2f298bcb476992aa088ea7e127bca5a3d2ae), ff464a9·34eedf0 후속 수정.
- DB: [7229fcd 최초 추가](https://github.com/nohminju/local_file_search/commit/7229fcd26b08ad1d58832b1e12664d00a5e6513f), 90e3cc0 역할 분리, de8c414 updated_at 추가.
- 이미지 인코더와 샘플: [1acebc6 업로드](https://github.com/nohminju/local_file_search/commit/1acebc67c0325d445fa39431627da64c665d7cb7), 07ac66b·0cb1127 후속 수정.
- 문장 인코더: [5b08637 추가](https://github.com/nohminju/local_file_search/commit/5b0863763f89dc659ae3c177369082f1289038f6). 같은 커밋에서 모델 의존성 목록도 수정했다.

별도 팀원 브랜치의 미병합 변경을 이번 정리에 임의로 포함하지 않았다.

## Edmond1889의 통합·연결 영역

| 현재 위치 | 하는 일 | 가짜 데이터 전용인가? |
|---|---|---|
| [interface.py](../interface.py) | 각 담당 기능이 제공할 함수 규격 | 실제·데모 공용 |
| [models/](../models/) | FileInfo, AnalysisReport, SearchResult | 실제·데모 공용 |
| [services/analysis_service.py](../services/analysis_service.py) | 수집 → 읽기 → 임베딩 → 저장 연결 | 실제·데모 공용 |
| [services/search_service.py](../services/search_service.py) | 문장 → 검색 → 파일 정보 연결 | 실제·데모 공용 |
| [adapters/repository_adapter.py](../adapters/repository_adapter.py) | 공통 자료형과 DB 자료형 사이 변환 | 실제 연결 |
| [adapters/encoder_adapters.py](../adapters/encoder_adapters.py) | 함수 이름·벡터 형식 검사 | 실제 연결 |
| [real_services.py](../real_services.py) | 실제 모델·임시 DB·인덱스를 조립 | 실제 연결 |
| [gui.py](../gui.py) | Tkinter 화면·작업 스레드·미리보기 | 기본은 실제, --demo만 가상 |
| [app.py](../app.py) | 고정 데이터 콘솔 데모 | 가상 데모 전용 |
| [demo/demo_adapters.py](../demo/demo_adapters.py) | 가상 스캐너·로더·인코더·저장소 | 가상 데모·테스트용 |
| [tests/](../tests/) | 서비스·DB 어댑터·GUI 연결 검증 | 검증 코드 |

이는 사용자의 기존 작업과 통합 경로에 따른 구분이다.
초기 통합 커밋 6b805c6, f77320b, dadcd89 등에는 Git 작성자 정보가 FinalExamUser로 기록돼 있다.
마지막 수정자나 폴더를 이동한 사람을 최초 기능 작성자로 잘못 해석하지 않는다.

## 설치 목록과 문서

- requirements/requirements.txt: 기존 공통 목록을 duoloo가 모델 의존성으로 수정.
- requirements/requirements-db.txt, requirements-app.txt: 통합 과정에서 추가한 설치 목록.
- docs/INTERFACE_GUIDE.md, DB_ADAPTER_GUIDE.md: 서비스 규격·연결 설명.
- docs/history/: 과거 병합과 검증 기록. 당시 경로가 남아 있을 수 있다.
- artifacts/checks/: 실제 모델 검색 결과 기록.
- 개인용 learn.md는 내 포크에서만 관리하며 원본으로 전달하는 PR에는 제외한다.

## 폴더 정리 때 지키는 기준

폴더 이동도 import, 설치 명령, 샘플 경로와 팀원의 병합에 영향을 준다.
이번 추가 정리는 팀원 Python 파일을 다시 옮기지 않고 출처를 문서로 보완한다.
설치 목록 세 파일은 내용과 포함 관계를 유지한 채 requirements/로 묶었다.
필요한 설치 안내 문자열과 문서 경로만 수정한다.
변경은 내 포크에서 기록하고 원본의 내 작업 브랜치로 PR을 보내 검토·병합한다.
원본의 main이나 팀원 브랜치에 직접 반영하지 않는다.
