# 2026-10-14 최신 병합 점검

## 결론

GitHub demo 브랜치의 efca3c9를 C:/Capstone/image-search-demo에 fast-forward로 반영했다.
확인 시 로컬 HEAD와 origin/codex/image-search-service-gui-demo가 모두 같은 커밋이었다.
원본 main의 de8c414를 기준으로 비교했을 때 뒤처진 커밋은 0개였다.

따라서 확인한 원본 main의 변경은 병합돼 있다.
반영 직후 최신 DB 필드 때문에 어댑터 테스트 6개가 실패했으나, 후속 어댑터 수정으로 해결했다. 현재 테스트는 22개 모두 통과한다.

## 이번 pull로 바뀐 파일

| 파일 | 반영 내용 |
|---|---|
| image_loader.py | 스캐너가 공통 FileInfo의 extension, size, modified_time을 생성하도록 수정 |
| db_manager.py | DB FileInfo와 테이블·저장·조회에 updated_at 필드 추가 |
| text_encoder.py | KoreanTextEncoder 추가. encode_text() 제공 |
| requirements.txt | torch, open_clip_torch, numpy 목록으로 변경 |
| CapStone/Test_B, Test | 원본에서 삭제된 내용 반영 |
| CapStone/embedding/image_encoder.py | 이번 pull에서는 변경 없음 |

## 이미지 인코더가 경로를 받는가

현재 원본 main과 로컬의 이미지 인코더는 동일한 내용을 확인했다.
ImageEncoder.encode(image)는 PIL 이미지 객체를 입력받는다.
_preprocess_image()에서 isinstance(image, Image.Image)를 검사하며 문자열 경로는 해당 규격에 맞지 않는다.

경로를 받아 사진을 읽는 함수는 DefaultImageLoader.load(file_path)다.

~~~text
사진 경로
→ DefaultImageLoader.load()
→ PIL RGB 이미지
→ ImageEncoder.encode()
→ 512차원 NumPy float32 벡터
~~~

이미지 인코더를 경로 입력으로 바꾼 작업이 별도 브랜치나 로컬에 있다면, 확인한 원본 main과 demo에는 아직 그 변경이 보이지 않는다.
현재 확인한 코드와 다른 설명으로 문서를 바꾸지는 않았다.

## 병합 직후 검증 기록

| 검사 | 결과 |
|---|---|
| 기존 서비스·GUI 테스트 | 10개 통과 |
| DB 어댑터 테스트 | 9개 중 3개 통과, 6개 오류 |
| 전체 회귀 테스트 | 19개 중 13개 통과, 6개 오류 |
| 실제 정상 사진 수집·PIL RGB 읽기 | 통과 |
| updated_at을 직접 채운 실제 DB 저장·조회 | 통과 |
| 실제 FAISS의 파일 ID·점수 검색 | 통과 |
| 실제 AI 모델 로드·문장 검색 품질 | 미검증 |

어댑터 오류는 FileInfo.__init__() missing 1 required positional argument: 'updated_at'이다.
스캐너의 기존 unexpected keyword argument 'ext' 오류는 이번 수정으로 해결됐다.

## 후속 수정 및 남은 작업

1. 완료: updated_at을 사진 파일 수정 시각으로 합의하고 우리 어댑터에서 UTC 문자열로 저장·복원하도록 수정했다.
2. 기존 DB의 새 컬럼 대응 방식을 DB 담당자와 정한다.
3. 문장 인코더의 encode_text()를 서비스의 encode() 규격과 연결한다.
4. 모델·Pillow·FAISS의 공통 의존성 목록을 정리하고 실제 GUI 서비스 생성 함수를 연결한다.

후속 요청으로 우리 어댑터와 회귀 테스트를 수정했다. 팀원 코드는 수정하지 않았다.
최종 테스트 22개가 모두 통과했고 파일 삭제/변경 후 저장한 시각 유지와 시간대 변환도 확인했다.
위 13개 통과·6개 오류는 수정 전의 진단 기록이며 현재 상태와 구분한다.

## 실제 기능 연결 후속 작업

RealServiceFactory와 인코더 어댑터를 추가하고 기본 GUI에 실제 사진·SQLite·FAISS를 연결했다. 문장 encode_text()를 서비스 encode()로 변환한다. 재분석은 새 임시 DB/인덱스를 사용하며 모델은 재사용한다. 기존 DB 파일은 변경하지 않는다. requirements-app.txt와 README에 설치·실행 방법을 정리했다.

최종 테스트는 25개 통과했다. 실제 모델은 미설치라 테스트 인코더로 연결을 검증했으며, AI 검색 품질과 영구 저장·불러오기는 남아 있다. 위 22개 기록은 인코더·GUI 연결 이전 시점이다.
