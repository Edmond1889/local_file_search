"""연결 화면 초안. 파일 인코더·유사도 비교가 준비되기 전에는 검색이 완료되지 않는다."""
import tkinter as tk
from tkinter import filedialog, ttk


# %% 1. 화면 준비
class DocumentSearchApp:
    def __init__(self, root, service_factory):
        self.root = root
        self.service_factory = service_factory
        self.service = None
        self.folder = tk.StringVar()
        self.query = tk.StringVar()
        self.status = tk.StringVar(value="파일 인코더·유사도 비교 미구현")

        root.title("코드·문서 검색")
        root.geometry("760x480")
        frame = ttk.Frame(root, padding=16)
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text="로더는 구현되어 있습니다. 파일 인코더와 유사도 비교는 아직 미구현입니다.").pack(anchor="w")
        ttk.Label(frame, textvariable=self.folder).pack(anchor="w", pady=6)
        ttk.Button(frame, text="폴더 선택", command=self.select_folder).pack(anchor="w")
        ttk.Button(frame, text="분석", command=self.analyze).pack(anchor="w", pady=6)

        ttk.Entry(frame, textvariable=self.query).pack(fill="x")
        self.search_button = ttk.Button(frame, text="검색", command=self.search, state="disabled")
        self.search_button.pack(anchor="w", pady=6)
        ttk.Label(frame, textvariable=self.status).pack(anchor="w")

        self.output = tk.Text(frame, height=12, wrap="word", state="disabled")
        self.output.pack(fill="both", expand=True, pady=6)

    def select_folder(self):
        # 2. 폴더 변경 시 이전 검색 상태를 지운다.
        path = filedialog.askdirectory(parent=self.root)
        if path:
            self.folder.set(path)
            self.service = None
            self.search_button.configure(state="disabled")
            self.show_text("")
            self.status.set("분석 버튼을 누르세요.")

    def analyze(self):
        # 3. 연결 순서를 호출한다. 미구현 부분의 오류도 화면에 그대로 알린다.
        if not self.folder.get():
            self.status.set("폴더를 먼저 선택하세요.")
            return

        self.service = None
        self.search_button.configure(state="disabled")
        self.show_text("")
        self.status.set("실제 모델 준비·파일 분석 중입니다. 완료까지 기다려 주세요.")
        self.root.update_idletasks()

        try:
            service = self.service_factory()
            saved_files, failures = service.analyze(self.folder.get())
        except Exception as error:
            self.status.set(f"분석 실패: {error}")
            return

        self.service = service
        self.search_button.configure(state="normal")
        self.status.set(f"저장 {len(saved_files)}개 / 읽기 실패 {len(failures)}개")
        lines = []
        for path, reason in failures:
            lines.append(f"읽기 실패: {path.name} / {reason}")
        self.show_text("\n".join(lines))

    def search(self):
        # 4. 같은 인코더·DB로 검색하고 실제 이름과 경로를 표시한다.
        if self.service is None:
            return
        if not self.query.get().strip():
            self.status.set("검색 문장을 입력하세요.")
            return

        self.show_text("")
        try:
            results = self.service.search(self.query.get())
        except Exception as error:
            self.status.set(f"검색 실패: {error}")
            return

        lines = []
        for info, score in results:
            lines.append(f"{info.file_name} / 유사도 {score:.4f}\n{info.file_path}\n")
        self.show_text("\n".join(lines))
        self.status.set(f"검색 결과 {len(results)}개")

    def show_text(self, text):
        self.output.configure(state="normal")
        self.output.delete("1.0", "end")
        self.output.insert("1.0", text)
        self.output.configure(state="disabled")
