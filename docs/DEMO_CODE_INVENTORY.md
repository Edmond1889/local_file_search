# 옛 데모 코드와 보관 후보

2026-10-16 실제 파일과 현재 import를 확인했다. 이번에는 목록만 작성했으며 waste로 이동·삭제하지 않았다.

## 1. 통합 전 project 폴더의 가상 데모

현재 경로는 C:/Capstone/project다. demo-v0로 이름을 바꾸려 했지만 Windows 폴더 잠금 때문에 아직 원래 이름이다.

| 옛 파일 | 당시 역할 | 현재 v2에서의 상태 |
|---|---|---|
| project/app.py | 가상 사진·고정 벡터 콘솔 데모 | app.py에 콘솔 데모 기능 유지 |
| project/demo_adapters.py | DemoScanner, DemoImageLoader, DemoImageEncoder, DemoTextEncoder, DemoRepository, DemoVectorIndex | demo/demo_adapters.py로 이동해 --demo·테스트에서 사용 |
| project/gui.py | 기본 실행이 가상 데이터인 Tkinter 화면 | v2 gui.py는 기본을 실제 기능으로 바꾸고 --demo만 가상으로 유지 |
| project/interface.py | 연결할 함수 규격 | v2 실제·데모 공용으로 계속 사용 |
| project/services/ | 분석·검색 흐름 연결 | v2 실제 기능에도 계속 사용 |
| project/models/ | 파일 정보·분석 보고서·검색 결과 | v2 실제 기능에도 계속 사용 |
| project/tests/ | 당시 연결 확인 테스트 | 후속 테스트를 추가해 v2에서도 검증 |

가상 기능의 중심은 app.py와 demo_adapters.py였다.
interface/services/models/gui는 이후 실제 기능에 재사용됐으므로 v2의 같은 파일을 구파일로 판단해 옮기면 안 된다.
project 쪽 사본은 v2가 import하지 않는다. 옛 개발 기록으로 폴더 전체를 보관하는 것은 별개다.

## 2. another 폴더의 더 오래된 초안

| 경로 | 확인한 내용 | 보관 판단 |
|---|---|---|
| C:/Capstone/another/ver1/app.py | 서비스 생성 도구가 연결되지 않은 실행 초안 | 과거 설계 참고 후보 |
| C:/Capstone/another/ver1/analysis_service.py | find_by_path/save_embedding 등 현재와 다른 규격 | 과거 설계 참고 후보 |
| C:/Capstone/another/ver1/search_ervice.py | 현재와 다른 검색 반환 규격, 파일명에 search_ervice 오타 | 과거 설계 참고 후보 |
| C:/Capstone/another/ver1/interface.py | 구형 연결 규격 초안 | 폴더 단위 보관 후보 |
| C:/Capstone/another/ver1/구현.text, 쿼리.text | 설계 메모 | 삭제보다 구버전 기록 보관 권장 |
| C:/Capstone/another/test_proto/main.py, prototype_text.py | TXT 파일명·내용의 키워드 일치 검색 | 실제로 작성한 텍스트 검색 프로토타입이며 가상 이미지 데모와는 다름 |

위 폴더들은 현재 v2 코드에서 참조하지 않는다. another/test_db는 과거 입력 샘플이므로 소스와 별도로 판단한다.

## 3. 현재 v2에서 아직 쓰는 데모 코드

- app.py → demo/demo_adapters.py를 사용한다.
- gui.py의 build_demo_services()와 --demo → 같은 가상 구현을 사용한다.
- tests/test_services.py → 같은 가상 구현으로 호출 순서·오류 처리를 검사한다.

따라서 현재 v2의 app.py, demo/를 waste로 옮기려면 실행 진입점과 테스트도 함께 바꿔야 한다.
이번 정리에서는 그대로 유지했다.

## 4. 보관 폴더를 만든다면

```text
C:/Capstone/waste/
├── demo-v0/          # 통합 전 project 폴더 전체
├── early-service/    # another/ver1 전체
└── text-prototype/   # another/test_proto 전체
```

위 구조는 제안이며 아직 생성·이동하지 않았다.
먼저 예전 편집기·터미널의 작업 경로를 닫고 Git 연결을 확인한다.
project에는 미커밋 변경과 연결된 Git 작업 사본이 있으므로 파일 몇 개만 빼기보다 이력을 보존해 판단한다.
demo-v1은 완료한 1차 데모의 로컬 사본이므로 이번 후보 목록과 구분해 유지한다.
