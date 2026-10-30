# 출처와 커밋 범위

이전 v2의 CODE_OWNERSHIP 문서를 기준으로 정리했다. 폴더 이동이 작성자 변경을 뜻하지 않는다.

| 현재 코드 | 출처 / 상태 |
|---|---|
| query_encoder/text_encoder.py | duoloo의 기존 텍스트 인코더, 원본 유지 |
| database/db_manager.py | nohminju의 SQLite·FAISS 코드, 원본 유지 |
| file_loader/loader.py | 이번 텍스트 전환 과정에서 추가한 로더, 기존 이미지 로더와 별개 |
| file_encoder / similarity | 새 담당자 구현을 기다리는 자리, 구현 완료 아님 |
| connection / app.py | 내 연결 작업 |
| gui / docs / study | 화면 초안과 설명·공부 자료 |

이전 이미지 로더(wpptpyqe)와 이미지 인코더(hyunsli7557-ux)는 v2 원본에 남아 있다.

이 폴더에는 `.git`이 없다. 팀 저장소 전체를 덮어쓰지 말고 내 브랜치에서 연결 변경만 반영한다.
`git add -- 파일경로`로 골라 올린 뒤 `git diff --cached --name-status`와 `git diff --cached`로 확인한다.
팀원 파일 삭제·이동은 임의로 포함하지 않는다. 로더·GUI 변경도 해당 담당자와 범위를 맞춘다.
개인 `study/`, 과거 `notes/`, 캐시·DB 데이터는 공유 PR에서 제외한다. 이번 작업은 커밋·푸시하지 않았다.
