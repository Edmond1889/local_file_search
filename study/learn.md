# 코드 읽는 순서

1. **app.py**: 팀원 로더·인코더·DB 객체를 만들고 DocumentSearch에 전달한다. 이미지·문장 인코더에 같은 OpenCLIP 모델 객체를 전달한다.
2. **file_loader/document_loader.py**: 경로를 수집하고 process_file에서 형식을 구분한다. 반환값은 DocumentChunk 목록이다.
3. **connection/service.py의 analyze**: 본문 청크와 이미지 청크를 인코딩해 각각 FAISS에 전달한다. 파일별 OSError는 실패 목록에 남긴다.
4. **database/db_info.py**: DocumentInfo에 파일 이름·경로·크기 등을 묶는다. `이름=값`은 어떤 항목에 넣는지 명시하는 문법이다.
5. **database/manager.py**: 파일 정보를 저장·갱신하고 ID를 반환한다. 서비스는 파일 경로를 이 번호와 연결한다.
6. **similarity/document_embedder.py / query_encoder/text_encoder.py**: 본문·본문 검색어는 ko-SRoBERTa, 이미지 검색어는 OpenCLIP으로 바꾼다.
7. **database/faiss.py**: 본문·이미지 인덱스를 따로 만들고 벡터 유사도 순으로 검색한다. 서비스에서 파일별 최고 점수 하나를 남기고 기본 5개로 제한한다.
8. **gui/window.py**: 폴더 선택 → 분석 → 문서/이미지 모드 선택 → 검색 → 결과 표시·파일 열기 순서다. 모델 작업은 작업 스레드에서 처리한다.

DocumentInfo는 파일 정보를 담는 그릇이고, DocumentChunk는 본문·페이지·이미지를 담는 그릇이다.
벡터는 인코더가 만든 숫자 배열이며 DB의 파일 ID는 그 배열이 어느 파일에서 왔는지 연결하는 번호다.
DB는 `database.db_info`를 가져온다. 루트 document_info.py는 필요 없다.

DocumentEncoder는 문서에서 꺼낸 PIL 이미지를 받는다. PDF 파일 경로를 직접 받지 않는다.
이미지 검색은 KoreanTextEncoder의 `(1, 512)` 문장 벡터를 그대로 FAISS에 전달한다. 문장 인코더와 이미지 인코더는 같은 모델 객체를 공유한다. 본문은 별도 모델이므로 두 점수를 합치지 않는다.
[전체코드.ipynb](전체코드.ipynb)의 줄별 설명은 이전 구현 자료다. 최신 호출 흐름은 [연결 순서](../README.md#분석과-검색-흐름)를 따른다.
