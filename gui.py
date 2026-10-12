"""기본 GUI 초안. 기본 실행은 고정된 가짜 사진을 사용하는 연결 데모다.

읽는 순서: __init__(화면 준비) → analyze()/search()(작업 시작)
→ Queue(결과 전달) → poll_events()(화면 갱신) → show_preview()(선택 사진 표시).
"""
from pathlib import Path
from queue import Empty, Queue
from threading import Thread
import tkinter as tk
from tkinter import filedialog, ttk

from demo_adapters import (
    DemoImageEncoder, DemoImageLoader, DemoRepository,
    DemoScanner, DemoTextEncoder, DemoVectorIndex,
)
from services.analysis_service import AnalysisService
from services.search_service import SearchService


def build_demo_services():
    # 같은 저장소와 인덱스를 공유하는 분석 서비스/검색 서비스를 만든다.
    # 분석할 때마다 새 데모 저장소를 만든다. 실제 재분석 정책은 팀원들과 합의해야 한다.
    repository, index = DemoRepository(), DemoVectorIndex()
    return (
        AnalysisService(DemoScanner(), DemoImageLoader(), DemoImageEncoder(), repository, index),
        SearchService(DemoTextEncoder(), index, repository),
    )


class PhotoSearchApp:
    def __init__(self, root, service_factory=build_demo_services, demo=True):
        # 1. 작업 상태를 보관하고, 창과 화면 부품을 만든다.
        # 실제 연결 시 동일한 저장소/인덱스를 공유하는 두 서비스를 만드는 함수를 전달한다.
        self.root = root
        self.service_factory = service_factory
        self.demo = demo
        self.events = Queue()  # 작업 스레드 → 메인 스레드로 메시지를 전달하는 통로
        self.busy = False  # 분석/검색 중인지 표시해 중복 실행을 막는다.
        self.search_service = None  # 분석 완료 후 같은 저장소를 쓰는 검색 서비스를 받는다.
        self.results = []  # 결과 목록의 각 행과 연결할 SearchResult 객체들
        self.preview_image = None  # 화면에 띄운 사진 객체의 참조를 유지한다.
        root.title("문장으로 사진 찾기" + (" · 연결 데모" if demo else ""))
        root.geometry("960x620")
        root.minsize(760, 520)

        # Frame은 화면 부품을 담는 영역, pack()은 부품을 배치하는 함수다.
        frame = ttk.Frame(root, padding=18)
        frame.pack(fill="both", expand=True)
        ttk.Label(frame, text="문장으로 사진 찾기", font=("맑은 고딕", 18, "bold")).pack(anchor="w")
        if demo:
            ttk.Label(frame, wraplength=850, text=(
                "연결 데모: 선택한 폴더의 실제 사진을 읽지 않습니다. 가상 사진 3개와 고정 벡터를 사용하며, "
                "검색 문장에 관계없이 결과가 같습니다."
            )).pack(anchor="w", pady=(6, 12))

        # 폴더 선택 영역: command는 버튼을 클릭할 때 호출할 함수다.
        folder_row = ttk.Frame(frame)
        folder_row.pack(fill="x", pady=6)
        self.folder = tk.StringVar()  # get()/set()으로 화면의 문자열 값을 읽고 바꾼다.
        ttk.Entry(folder_row, textvariable=self.folder, state="readonly").pack(side="left", fill="x", expand=True)
        self.folder_button = ttk.Button(folder_row, text="폴더 선택", command=self.select_folder)
        self.folder_button.pack(side="left", padx=6)
        self.analyze_button = ttk.Button(folder_row, text="분석 시작", command=self.analyze)
        self.analyze_button.pack(side="left")
        # 진행 영역: 진행 막대와 현재 상태 문구를 표시한다.
        self.progress = ttk.Progressbar(frame, maximum=1)
        self.progress.pack(fill="x", pady=6)
        self.status = tk.StringVar(value="분석할 폴더를 선택해주세요.")
        ttk.Label(frame, textvariable=self.status).pack(anchor="w")

        # 검색 영역: 입력창에서 Enter를 누르거나 검색 버튼을 누르면 search()를 호출한다.
        search_row = ttk.Frame(frame)
        search_row.pack(fill="x", pady=12)
        self.query = tk.StringVar()
        self.query_entry = ttk.Entry(search_row, textvariable=self.query)
        self.query_entry.pack(side="left", fill="x", expand=True)
        self.query_entry.bind("<Return>", lambda event: self.search())
        self.search_button = ttk.Button(search_row, text="검색", command=self.search, state="disabled")
        self.search_button.pack(side="left", padx=(6, 0))

        # 결과 영역: 왼쪽은 사진 목록, 오른쪽은 선택한 사진의 미리보기다.
        panes = ttk.Panedwindow(frame, orient="horizontal")
        panes.pack(fill="both", expand=True)
        list_frame, preview_frame = ttk.Frame(panes), ttk.Frame(panes, padding=12)
        panes.add(list_frame, weight=1)
        panes.add(preview_frame, weight=1)
        self.result_list = ttk.Treeview(list_frame, columns=("name", "score"), show="headings")
        self.result_list.heading("name", text="사진 이름")
        self.result_list.heading("score", text="데모 점수" if demo else "유사도")
        self.result_list.column("name", width=240)
        self.result_list.column("score", width=90, stretch=False)
        scroll = ttk.Scrollbar(list_frame, orient="vertical", command=self.result_list.yview)
        self.result_list.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        self.result_list.pack(fill="both", expand=True)
        self.result_list.bind("<<TreeviewSelect>>", self.show_preview)  # 행 선택 시 호출
        self.preview = ttk.Label(preview_frame, text="결과를 선택하면 사진 정보를 표시합니다.", anchor="center")
        self.preview.pack(fill="both", expand=True)
        self.details = tk.StringVar()
        ttk.Label(preview_frame, textvariable=self.details, wraplength=360).pack(fill="x", pady=6)

        # 실패 안내 영역: 읽지 못한 사진과 이유를 표시한다.
        self.failure_text = tk.Text(frame, height=3, wrap="word", state="disabled")
        self.failure_text.pack(fill="x", pady=(10, 0))
        # Tk 위젯은 메인 스레드에서만 갱신한다. 작업 스레드는 큐에 결과만 넣는다.
        root.after(100, self.poll_events)

    def select_folder(self):
        # 2. 폴더 선택창을 열고, 새 폴더를 선택하면 이전 결과를 초기화한다.
        path = filedialog.askdirectory(parent=self.root)
        if path:
            self.folder.set(path)
            # 폴더를 바꾸면 이전 분석 결과를 새 폴더 결과로 착각하지 않도록 지운다.
            self.search_service = None
            self.search_button.configure(state="disabled")
            self.clear_results()
            self.progress.configure(value=0)
            self.set_failures("")
            self.status.set("분석 시작을 눌러주세요.")

    def clear_results(self):
        # 목록 데이터, 화면의 행, 미리보기를 함께 비워 이전 결과가 남지 않게 한다.
        self.results = []
        self.result_list.delete(*self.result_list.get_children())
        self.preview_image = None
        self.preview.configure(image="", text="결과를 선택하면 사진 정보를 표시합니다.")
        self.details.set("")

    def set_failures(self, text):
        # 안내창을 잠시 편집 가능하게 바꿔 내용을 넣고, 다시 읽기 전용으로 돌린다.
        self.failure_text.configure(state="normal")
        self.failure_text.delete("1.0", "end")
        self.failure_text.insert("1.0", text)
        self.failure_text.configure(state="disabled")

    def set_busy(self, busy):
        # 작업 중에는 버튼을 잠근다. 검색은 분석을 마친 서비스가 있을 때만 허용한다.
        self.busy = busy
        state = "disabled" if busy else "normal"
        self.folder_button.configure(state=state)
        self.analyze_button.configure(state=state)
        self.search_button.configure(state="normal" if not busy and self.search_service else "disabled")

    def analyze(self):
        # 3. 분석 입력을 확인하고, 이전 결과를 지운 뒤 별도 스레드에서 분석한다.
        if self.busy:
            return
        folder = self.folder.get()
        if not folder:
            self.status.set("먼저 폴더를 선택해주세요.")
            return
        self.search_service = None
        self.clear_results()
        self.set_failures("")
        self.progress.configure(value=0)
        self.status.set("사진 목록을 준비하는 중…")
        self.set_busy(True)

        def work():
            # 작업 스레드에서 실행할 함수: 화면을 직접 바꾸지 않고 Queue에 알린다.
            try:
                analysis, search = self.service_factory()
                # 이 콜백은 진행 숫자를 큐에 전달한다. 화면 갱신은 poll_events()가 맡는다.
                report = analysis.analyze(folder, on_progress=lambda done, total: self.events.put(("progress", (done, total))))
                # lambda는 짧은 함수다. 콜백 호출 시 (처리 개수, 전체 개수)를 큐에 넣는다.
                self.events.put(("analyzed", (report, search)))  # 완료 보고서와 검색 도구 전달
            except Exception as error:
                # GUI 경계에서는 처리 실패를 사용자에게 표시한다.
                self.events.put(("error", str(error)))
        # 분석 중에도 화면이 반응하도록 work()를 별도로 실행한다.
        # daemon=True인 작업은 창을 닫아 프로그램이 종료될 때 완료를 기다리지 않는다.
        Thread(target=work, daemon=True).start()

    def search(self):
        # 4. 검색 준비 상태와 문장을 확인하고, 별도 스레드에서 검색한다.
        if self.busy or self.search_service is None:
            return
        query = self.query.get().strip()
        if not query:
            self.status.set("검색 문장을 입력해주세요.")
            return
        self.clear_results()
        self.status.set("검색하는 중…")
        self.set_busy(True)
        service = self.search_service

        def work():
            try:
                self.events.put(("searched", service.search(query, top_k=5)))  # 결과 목록 전달
            except Exception as error:
                self.events.put(("error", str(error)))
        Thread(target=work, daemon=True).start()

    def poll_events(self):
        # 5. 메인 스레드에서 메시지를 꺼내 화면에 반영한다.
        # kind는 메시지 종류, payload는 그 메시지에 담긴 데이터다.
        try:
            while True:
                kind, payload = self.events.get_nowait()  # 기다리지 않고 꺼내며, 비면 Empty 발생
                if kind == "progress":
                    # 진행 알림: 숫자와 막대를 갱신한다. 전체가 0이어도 최대값은 1로 둔다.
                    done, total = payload
                    self.progress.configure(maximum=max(total, 1), value=done)
                    self.status.set(f"{total}장 중 {done}장 처리됨")
                elif kind == "analyzed":
                    # 분석 완료: 성공/실패를 표시하고 검색 서비스를 보관한 뒤 버튼을 푼다.
                    report, self.search_service = payload
                    self.status.set(f"분석 완료 · 성공 {len(report.indexed_files)}개 · 읽기 실패 {len(report.failures)}개")
                    self.set_failures("\n".join(f"읽기 실패: {failure.file.name} — {failure.reason}" for failure in report.failures))
                    self.set_busy(False)
                elif kind == "searched":
                    # 검색 완료: 결과 객체를 보관하고 이름과 점수를 목록의 행으로 만든다.
                    self.results = payload
                    for number, result in enumerate(payload):
                        # 행 ID(iid)에 결과 순번을 넣어 선택한 행의 결과를 다시 찾을 수 있다.
                        self.result_list.insert("", "end", iid=str(number), values=(result.file.name, f"{result.score:.3f}"))
                    self.status.set(f"검색 결과 {len(payload)}개" + (" · 고정된 데모 결과" if self.demo else ""))
                    self.set_busy(False)
                elif kind == "error":
                    # 작업 실패: 이유를 표시하고 작업 중 상태를 해제한다.
                    self.status.set(f"처리 실패: {payload}")
                    self.set_busy(False)
        except Empty:
            pass  # 큐가 비면 이번 확인을 끝낸다. 오류 상황이 아니다.
        self.root.after(100, self.poll_events)  # 화면을 멈추지 않고 100ms 뒤 다시 확인한다.

    def show_preview(self, event=None):
        # 6. 선택한 행 ID로 SearchResult를 찾고, 사진 정보와 미리보기를 표시한다.
        selection = self.result_list.selection()
        if not selection:
            return
        result = self.results[int(selection[0])]  # 행 ID로 저장한 순번을 다시 사용한다.
        self.preview_image = None
        self.preview.configure(image="", text="")
        self.details.set(f"{result.file.name}\n{result.file.path}\n점수: {result.score:.3f}")
        if self.demo:
            # 가상 결과 경로와 실제 파일명이 우연히 같아도 실제 사진으로 표시하지 않는다.
            self.preview.configure(text="가상 사진 결과\n실제 구현 연결 후 사진을 표시합니다.")
            return
        try:
            # Pillow가 설치돼 있으면 JPG 등도 표시한다. 팀의 이미지 자료형과는 별개다.
            from PIL import Image, ImageTk
            with Image.open(Path(result.file.path)) as image:
                image.thumbnail((360, 300))  # 사진 비율을 유지하며 미리보기 크기에 맞춘다.
                self.preview_image = ImageTk.PhotoImage(image.copy(), master=self.root)
            # 참조를 보관해야 Tk 사진이 가비지 컬렉션으로 사라지지 않는다.
            self.preview.configure(image=self.preview_image)
        except ImportError:
            self.preview.configure(text="사진 미리보기에는 Pillow 설치가 필요합니다.")
        except (OSError, ValueError, tk.TclError):
            self.preview.configure(text="사진을 읽을 수 없습니다. 경로와 파일 상태를 확인해주세요.")


if __name__ == "__main__":
    # 이 파일을 직접 실행할 때만 창을 만든다. import할 때는 창이 뜨지 않는다.
    window = tk.Tk()
    PhotoSearchApp(window)
    window.mainloop()  # 클릭, 키 입력, after() 예약 등을 처리하는 GUI 이벤트 루프
