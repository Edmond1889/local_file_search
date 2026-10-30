# 텍스트 검색 연결 작업본

코드·문서를 검색하도록 전환하는 중이다. **파일 인코더와 유사도 비교는 미구현**이다.

- 구현됨: 파일 로더, 기존 사용자 입력 인코더, 기존 DB.
- 내 담당: 각 기능의 호출 순서와 DB 연결.
- 로더는 `file_loader/loader.py`, 인코더는 `file_encoder/encoder.py`로 구분한다.

```powershell
python -m pip install -r requirements.txt
python app.py          # 기존 사용자 입력 인코딩 확인
python app.py --gui    # 연결 화면 초안
```

파일 분석·검색은 미구현 부분에서 중단된다. 완성된 검색 시연은 아직 할 수 없다.

[구조·규격 문서](docs/README.md) · [공부 순서](study/learn.md) · [전체 코드 셀](study/전체코드.ipynb)
