# 텍스트 파일 검색 프로젝트

기준: **2026-10-29** · 브랜치: `file-serch-demo-v1`

이미지 검색에서 코드·문서의 텍스트 검색으로 전환 중이다.

- 현재 작업 위치: [text-search-demo-v1/](text-search-demo-v1/)
- 구현됨: 파일 로더, 기존 사용자 입력 인코더, 기존 DB.
- 미구현: 새 파일 인코더, 새 유사도 비교. 전체 검색은 아직 완료되지 않았다.

```powershell
cd text-search-demo-v1
python -m pip install -r requirements.txt
python app.py          # 사용자 입력 인코딩 확인
python app.py --gui    # 연결 화면 초안
```

[현재 구조·규격 문서](text-search-demo-v1/docs/README.md)

개인 `study/`는 업로드에서 제외했다. 루트에 남은 이미지 검색 코드는 이전 버전 보존용이다.
