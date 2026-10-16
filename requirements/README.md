# 설치 의존성 목록

TXT 세 파일은 설명 메모가 아니라 pip가 읽는 설치 목록이다.
파일 내용을 수정하지 않고 같은 requirements/ 폴더로 이동했다.

| 파일 | 역할 | 이력상 구분 |
|---|---|---|
| [requirements.txt](requirements.txt) | torch, open_clip_torch, numpy 등 모델 의존성 | 기존 파일을 duoloo가 모델 목록으로 수정 |
| [requirements-db.txt](requirements-db.txt) | 기본 목록 + NumPy 범위 + FAISS | Edmond1889 통합 작업에서 추가 |
| [requirements-app.txt](requirements-app.txt) | DB 목록 + Pillow, transformers, sentencepiece | Edmond1889 실제 GUI 연결 작업에서 추가 |

```text
requirements-app.txt
  └─ -r requirements-db.txt
       └─ -r requirements.txt
```

pip의 -r 포함 경로는 포함하는 파일 위치를 기준으로 읽는다.
세 파일을 함께 이동했으므로 내부 -r 행은 그대로 유지한다.

저장소 루트에서 실제 GUI 설치:

```powershell
python -m pip install -r requirements/requirements-app.txt
python gui.py
```

DB 연결만 준비할 때는 requirements/requirements-db.txt를 사용한다.
이 파일도 기본 모델 목록을 포함하므로 모델 라이브러리가 함께 설치 대상이 된다.
모델 없이 GUI 데모만 확인하려면 기존처럼 Pillow만 설치하고 python gui.py --demo로 실행할 수 있다.

작성 근거: [모델 목록 수정 5b08637](https://github.com/nohminju/local_file_search/commit/5b0863763f89dc659ae3c177369082f1289038f6),
DB 목록 추가 f77320b, 앱 목록 추가 dadcd89. 마지막 두 커밋의 Git 작성자는 실습용 FinalExamUser로 남아 있으며 사용자 통합 작업 이력이다.
