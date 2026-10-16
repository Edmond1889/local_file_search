# 분석 보고서 자동 저장

## 언제 저장되는가?

GUI에서 폴더를 선택하고 분석 시작을 눌러 AnalysisService가 정상 반환하면 JSON 한 개를 자동 저장한다.
일부 사진을 읽지 못해 실패 목록에 담긴 경우나 사진 목록이 비어 있는 경우도 완료 보고서를 저장한다.
모델 준비·임베딩·DB 저장 등의 오류로 분석 자체가 중단되면 완료 보고서는 만들지 않는다.
CLI 가상 데모 app.py와 AnalysisService.analyze() 직접 호출에는 자동 저장을 연결하지 않았다.

## 어디에 생기는가?

실행 중인 프로젝트 루트의 reports/다. VS Code 터미널의 현재 위치를 기준으로 정하지 않는다.
이 PC의 v2에서는 C:/Capstone/image-search-demo-v2/reports/에 저장한다.
저장 시점에 폴더를 만들며, 미리 작성한 결과 JSON을 프로젝트에 넣어두지 않는다.

파일 이름 형태:

```text
analysis_real_날짜_시간_마이크로초_고유번호.json
analysis_demo_날짜_시간_마이크로초_고유번호.json
```

시간대는 실행 PC의 로컬 시간대이며 JSON 시각에는 UTC 오프셋도 함께 기록한다.
매번 다른 파일을 만들어 이전 보고서를 덮어쓰지 않는다.
임시 파일에 전부 쓴 후 최종 JSON 이름으로 바꿔 불완전한 내용을 정상 보고서로 표시하지 않는다.

## 어떤 내용이 들어가는가?

| JSON 항목 | 내용 |
|---|---|
| schema_version / report_type | 보고서 형식 버전과 image_analysis 종류 |
| mode | real 또는 demo |
| started_at / finished_at | 분석 작업 시작·종료 시각, 시간대 포함 |
| elapsed_seconds | 첫 모델 준비를 포함한 분석 소요 시간, 보고서 파일 쓰기 시간은 제외 |
| source_folder | 사용자가 선택한 폴더의 절대 경로 |
| summary.processed_count | 성공과 읽기 실패를 합친 처리 개수 |
| summary.indexed_count | 파일 정보와 벡터 저장까지 성공한 개수 |
| summary.failure_count | 읽기 실패 개수 |
| indexed_files | 성공 파일의 이름·경로·크기·수정 시각·해시 등 메타데이터 |
| failures | 읽기 실패 파일의 메타데이터와 오류 이유 |

사진 원본, 이미지 픽셀, 임베딩 벡터는 보고서에 넣지 않는다.
검색 문장·검색 결과의 자동 기록은 이번 분석 보고서 기능에 포함하지 않았다.

## GUI에서는 어떻게 확인하는가?

분석이 끝나면 화면의 분석 보고서 칸에 저장된 절대 경로가 나타난다. 선택해서 복사할 수 있다.
이후 검색하더라도 같은 분석 보고서 경로를 유지한다.
새 폴더를 선택하거나 새 분석을 시작하면 이전 경로 표시를 초기화한다.

저장 권한 부족·디스크 오류 등으로 저장하지 못하면 해당 칸에 실패 이유를 표시한다.
이 경우 이미 완료된 분석 결과와 검색 서비스는 유지한다.
분석 자체가 중단된 경우에는 보고서가 생성되지 않았다고 표시한다.

## 실제 분석과 가상 데모

python gui.py는 실제 분석용이며 파일명에 analysis_real, mode에 real을 쓴다.
python gui.py --demo도 보고서를 저장하지만 파일명에 analysis_demo, mode에 demo를 쓴다.
가상 파일·고정 벡터의 결과를 실제 사진 분석으로 해석하지 않는다.

## 보고서 저장과 DB 영구 저장의 차이

JSON은 무엇을 분석했는지 확인하는 실행 기록이다. 재실행 후 검색을 복원하는 데이터가 아니다.
SQLite는 여전히 분석 세션의 임시 폴더를 쓰고 FAISS는 메모리에 있다.
앱을 다시 실행하면 검색을 위해 재분석해야 한다. DB·인덱스 영구 저장은 별도 후속 기능이다.

reports/는 자동 생성되는 로컬 데이터이므로 Git에서 제외했다.
프로그램은 예전 보고서를 자동 삭제하지 않는다. 필요할 때 사용자가 보관·정리할 수 있다.

## 기존 artifacts/checks JSON과의 구분

artifacts/checks/CAT_SEARCH_CHECK_2026-10-14.json은 별도 검증 실행 후 저장해둔 수동 기록이다.
GUI가 자동으로 생성한 파일이 아니며 이번 기능에서도 갱신하지 않는다.
이전 파일은 이동·삭제하지 않았다. 새 자동 보고서는 reports/에서 확인한다.

## 구현 위치와 검증

- [gui.py](../gui.py): 분석 완료 후 저장 요청, 결과·실패 경로 표시.
- [services/report_writer.py](../services/report_writer.py): JSON 작성·파일 저장.
- [tests/test_report_writer.py](../tests/test_report_writer.py): 내용, 한국어, 덮어쓰기 방지, 데모 구분, 실패 정리.
- [tests/test_gui_events.py](../tests/test_gui_events.py): 저장 호출, 저장 실패 후 검색 유지, 중단 시 저장하지 않음.

추가 라이브러리 없이 Python 표준 라이브러리를 사용한다.
기존 검사와 새 검사를 합쳐 unittest 36개가 통과했다.
