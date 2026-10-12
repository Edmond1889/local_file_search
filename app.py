from services.analysis_service import AnalysisService
from services.search_service import SearchService


def main():

    analysis_service = AnalysisService()
    search_service = SearchService()


     # 1. 폴더 분석
    folder_path = input("분석할 폴더 경로: ")

    files = analysis_service.analyze(folder_path)

    print(f"\n총 {len(files)}개의 파일을 찾았습니다.")


    # 2. 검색
    query = input("\n검색어: ")

    results = search_service.search(
        files=files,
        query=query,
        top_k=5
    )

    # 3. 검색 결과 출력
    print("\n===== 검색 결과 =====")

    if not results:
        print("검색 결과가 없습니다.")
        return

    for index, result in enumerate(results, start=1):
        # result는 SearchResult 객체이므로 속성으로 파일 정보와 점수를 꺼낸다.
        # result.file은 FileInfo 객체라서 name, path 등의 파일 정보에 접근할 수 있다.
        file = result.file
        score = result.score

        print(f"\n{index}. {file.name}")
        print(f"경로: {file.path}")
        print(f"확장자: {file.extension}")
        print(f"점수: {score}")


if __name__ == "__main__":
    main()
