"""고정된 가짜 데이터로 서비스 연결 흐름만 확인하는 실행 예제."""
from demo_adapters import (
    DemoImageEncoder, DemoImageLoader, DemoRepository,
    DemoScanner, DemoTextEncoder, DemoVectorIndex,
)
from services.analysis_service import AnalysisService
from services.search_service import SearchService


def main():
    print("[연결 데모] 실제 사진 읽기·AI 임베딩·FAISS 검색은 아직 연결되지 않았습니다.")
    print("검색 문장과 관계없이 고정된 테스트 벡터를 사용합니다.")
    # 같은 저장소/인덱스를 공유해야 분석한 사진을 검색할 수 있다.
    repository = DemoRepository()
    vector_index = DemoVectorIndex()
    analysis_service = AnalysisService(
        DemoScanner(), DemoImageLoader(), DemoImageEncoder(), repository, vector_index,
    )
    search_service = SearchService(DemoTextEncoder(), vector_index, repository)
    report = analysis_service.analyze("demo")
    print(f"분석 성공: {len(report.indexed_files)}개 / 읽기 실패: {len(report.failures)}개")
    for failure in report.failures:
        print(f"읽기 실패: {failure.file.name} ({failure.reason})")
    results = search_service.search(input("검색 문장: "), top_k=5)
    if not results:
        print("검색 결과가 없습니다.")
    for index, result in enumerate(results, start=1):
        # result.file은 FileInfo, result.score는 이번 검색의 유사도다.
        print(f"{index}. {result.file.name} / 데모 점수: {result.score:.2f}")
        print(f"가상 경로: {result.file.path}")


if __name__ == "__main__":
    main()
