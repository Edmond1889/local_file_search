"""기본 GUI 초안. 기본 실행은 고정된 가짜 사진을 사용하는 연결 데모다."""
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
    # 분석할 때마다 새 데모 저장소를 만든다. 실제 재분석 정책은 팀원들과 합의해야 한다.
    repository, index = DemoRepository(), DemoVectorIndex()
    return (
        AnalysisService(DemoScanner(), DemoImageLoader(), DemoImageEncoder(), repository, index),
        SearchService(DemoTextEncoder(), index, repository),
    )


class PhotoSearchApp:
    def __init__(self, root, service_factory=build_demo_services, demo=True):
        # 실제 연결 시 동일한 저장소/인덱스를 공유하는 두 서비스를 만드는 함수를 전달한다.
        self.root = root
        self.service_factory = service_factory
        self.demo = demo
        self.events = Queue()
        self.busy = False
        self.search_service = None
        self.results = []
        self.preview_image = None
        root.title("문장으로 사진 찾기" + (" · 연결 데모" if demo else ""))
        root.geometry("960x620")
        root.minsize(760, 520)

        frame = ttk.Frame(root, padding=18)
        frame.pack(fill="both", expand=True)
        ttk.Label(frame, text="문장으로 사진 찾기", font=("맑은 고딕", 18, "bold")).pack(anchor="w")
        if demo:
            ttk.Label(frame, wraplength=850, text=(
                "연결 데모: 선택한 폴더의 실제 사진을 읽지 않습니다. 가상 사진 3개와 고정 벡터를 사용하며, "
                "검색 문장에 관계없이 결과가 같습니다."
            )).pack(anchor="w", pady=(6, 12))

        folder_row = ttk.Frame(frame)
        folder_row.pack(fill="x", pady=6)
        self.folder = tk.StringVar()
        ttk.Entry(folder_row, textvariable=self.folder, state="readonly").pack(side="left", fill="x", expand=True)
        self.folder_button = ttk.Button(folder_row, text="폴더 선택", command=self.select_folder)
        self.folder_button.pack(side="left", padx=6)
        self.analyze_button = ttk.Button(folder_row, text="분석 시작", command=self.analyze)
        self.analyze_button.pack(side="left")
        self.progress = ttk.Progressbar(frame, maximum=1)
        self.progress.pack(fill="x", pady=6)
        self.status = tk.StringVar(value="분석할 폴더를 선택해주세요.")
        ttk.Label(frame, textvariable=self.status).pack(anchor="w")

        search_row = ttk.Frame(frame)
        search_row.pack(fill="x", pady=12)
        self.query = tk.StringVar()
        self.query_entry = ttk.Entry(search_row, textvariable=self.query)
        self.query_entry.pack(side="left", fill="x", expand=True)
        self.query_entry.bind("<Return>", lambda event: self.search())
        self.search_button = ttk.Button(search_row, text="검색", command=self.search, state="disabled")
        self.search_button.pack(side="left", padx=(6, 0))

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
        self.result_list.bind("<<TreeviewSelect>>", self.show_preview)
        self.preview = ttk.Label(preview_frame, text="결과를 선택하면 사진 정보를 표시합니다.", anchor="center")
        self.preview.pack(fill="both", expand=True)
        self.details = tk.StringVar()
        ttk.Label(preview_frame, textvariable=self.details, wraplength=360).pack(fill="x", pady=6)

        self.failure_text = tk.Text(frame, height=3, wrap="word", state="disabled")
        self.failure_text.pack(fill="x", pady=(10, 0))
        # Tk 위젯은 메인 스레드에서만 갱신한다. 작업 스레드는 큐에 결과만 넣는다.
        root.after(100, self.poll_events)

    def select_folder(self):
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
        self.results = []
        self.result_list.delete(*self.result_list.get_children())
        self.preview_image = None
        self.preview.configure(image="", text="결과를 선택하면 사진 정보를 표시합니다.")
        self.details.set("")

    def set_failures(self, text):
        self.failure_text.configure(state="normal")
        self.failure_text.delete("1.0", "end")
        self.failure_text.insert("1.0", text)
        self.failure_text.configure(state="disabled")

    def set_busy(self, busy):
        self.busy = busy
        state = "disabled" if busy else "normal"
        self.folder_button.configure(state=state)
        self.analyze_button.configure(state=state)
        self.search_button.configure(state="normal" if not busy and self.search_service else "disabled")

    def analyze(self):
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
            try:
                analysis, search = self.service_factory()
                # 이 콜백은 진행 숫자를 큐에 전달한다. 화면 갱신은 poll_events()가 맡는다.
                report = analysis.analyze(folder, on_progress=lambda done, total: self.events.put(("progress", (done, total))))
                self.events.put(("analyzed", (report, search)))
            except Exception as error:
                # GUI 경계에서는 처리 실패를 사용자에게 표시한다.
                self.events.put(("error", str(error)))
        Thread(target=work, daemon=True).start()

    def search(self):
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
                self.events.put(("searched", service.search(query, top_k=5)))
            except Exception as error:
                self.events.put(("error", str(error)))
        Thread(target=work, daemon=True).start()

    def poll_events(self):
        try:
            while True:
                kind, payload = self.events.get_nowait()
                if kind == "progress":
                    done, total = payload
                    self.progress.configure(maximum=max(total, 1), value=done)
                    self.status.set(f"{total}장 중 {done}장 처리됨")
                elif kind == "analyzed":
                    report, self.search_service = payload
                    self.status.set(f"분석 완료 · 성공 {len(report.indexed_files)}개 · 읽기 실패 {len(report.failures)}개")
                    self.set_failures("\n".join(f"읽기 실패: {failure.file.name} — {failure.reason}" for failure in report.failures))
                    self.set_busy(False)
                elif kind == "searched":
                    self.results = payload
                    for number, result in enumerate(payload):
                        self.result_list.insert("", "end", iid=str(number), values=(result.file.name, f"{result.score:.3f}"))
                    self.status.set(f"검색 결과 {len(payload)}개" + (" · 고정된 데모 결과" if self.demo else ""))
                    self.set_busy(False)
                elif kind == "error":
                    self.status.set(f"처리 실패: {payload}")
                    self.set_busy(False)
        except Empty:
            pass
        self.root.after(100, self.poll_events)

    def show_preview(self, event=None):
        selection = self.result_list.selection()
        if not selection:
            return
        result = self.results[int(selection[0])]
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
                image.thumbnail((360, 300))
                self.preview_image = ImageTk.PhotoImage(image.copy(), master=self.root)
            # 참조를 보관해야 Tk 사진이 가비지 컬렉션으로 사라지지 않는다.
            self.preview.configure(image=self.preview_image)
        except ImportError:
            self.preview.configure(text="사진 미리보기에는 Pillow 설치가 필요합니다.")
        except (OSError, ValueError, tk.TclError):
            self.preview.configure(text="사진을 읽을 수 없습니다. 경로와 파일 상태를 확인해주세요.")


if __name__ == "__main__":
    window = tk.Tk()
    PhotoSearchApp(window)
    window.mainloop()
