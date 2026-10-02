#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import queue
import threading
import time
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

import download_papers as engine

APP_NAME = "Yonsei Paper Downloader"
APP_VERSION = "1.0.1"
CONFIG_DIR = Path(os.getenv("APPDATA", str(Path.home()))) / "YonseiPaperDownloader"
CONFIG_PATH = CONFIG_DIR / "config.json"
DEFAULT_OUTPUT_DIR = Path.home() / "Downloads" / "Yonsei Paper Downloader"

STATUS_TEXT = {
    "downloaded": "다운로드 완료",
    "skipped": "이미 받은 파일",
    "unsupported": "지원하지 않는 출판사",
    "not_found": "DOI를 찾지 못함",
    "forbidden": "접근 권한 확인 필요",
    "rate_limited": "API 요청 제한",
    "error": "오류",
}


def parse_doi_text(text: str) -> list[str]:
    dois: list[str] = []
    seen: set[str] = set()

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue

        doi = engine.normalize_doi(line)
        if doi and doi not in seen:
            seen.add(doi)
            dois.append(doi)

    return dois


def load_config() -> dict[str, str]:
    if not CONFIG_PATH.exists():
        return {}

    try:
        data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return {str(k): str(v) for k, v in data.items()}
    except Exception:
        pass

    return {}


def save_config(config: dict[str, str]) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(
        json.dumps(config, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


class PaperDownloaderApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title(f"{APP_NAME} {APP_VERSION}")
        self.root.geometry("780x680")
        self.root.minsize(700, 600)

        self.config = load_config()
        self.output_dir = Path(
            self.config.get("output_dir", str(DEFAULT_OUTPUT_DIR))
        )
        self.events: queue.Queue[tuple] = queue.Queue()
        self.running = False

        self._build_ui()
        self.root.after(100, self._poll_events)

        if not self._credentials_ready():
            self.root.after(300, self.open_settings)

    def _build_ui(self) -> None:
        container = ttk.Frame(self.root, padding=18)
        container.pack(fill="both", expand=True)

        title = ttk.Label(
            container,
            text="연세대학교 논문 자동 다운로드",
            font=("Malgun Gothic", 17, "bold"),
        )
        title.pack(anchor="w")

        notice = ttk.Label(
            container,
            text="① YSVPN 연결  →  ② DOI 붙여넣기  →  ③ 다운로드 시작",
            font=("Malgun Gothic", 10),
        )
        notice.pack(anchor="w", pady=(5, 14))

        warning = ttk.Label(
            container,
            text="※ 교외에서는 다운로드 전에 YSVPN이 연결되어 있는지 확인하세요.",
            font=("Malgun Gothic", 9, "bold"),
        )
        warning.pack(anchor="w", pady=(0, 12))

        toolbar = ttk.Frame(container)
        toolbar.pack(fill="x", pady=(0, 8))

        ttk.Button(toolbar, text="클립보드에서 붙여넣기", command=self.paste_dois).pack(side="left")
        ttk.Button(toolbar, text="전체 지우기", command=self.clear_dois).pack(side="left", padx=(8, 0))
        ttk.Button(toolbar, text="API 키 설정", command=self.open_settings).pack(side="right")

        ttk.Label(
            container,
            text="DOI 목록 (한 줄에 하나씩)",
            font=("Malgun Gothic", 10, "bold"),
        ).pack(anchor="w")

        text_frame = ttk.Frame(container)
        text_frame.pack(fill="both", expand=True, pady=(6, 10))

        self.doi_text = tk.Text(
            text_frame,
            height=14,
            wrap="none",
            font=("Consolas", 10),
        )
        self.doi_text.pack(side="left", fill="both", expand=True)

        scroll = ttk.Scrollbar(text_frame, orient="vertical", command=self.doi_text.yview)
        scroll.pack(side="right", fill="y")
        self.doi_text.configure(yscrollcommand=scroll.set)

        folder_row = ttk.Frame(container)
        folder_row.pack(fill="x", pady=(0, 10))

        ttk.Label(folder_row, text="저장 위치:").pack(side="left")
        self.folder_var = tk.StringVar(value=str(self.output_dir))
        self.folder_label = ttk.Label(
            folder_row,
            textvariable=self.folder_var,
            width=65,
        )
        self.folder_label.pack(side="left", padx=(7, 7), fill="x", expand=True)
        ttk.Button(folder_row, text="변경", command=self.choose_output_folder).pack(side="right")

        button_row = ttk.Frame(container)
        button_row.pack(fill="x", pady=(0, 10))

        self.start_button = ttk.Button(
            button_row,
            text="다운로드 시작",
            command=self.start_download,
        )
        self.start_button.pack(side="left")

        ttk.Button(
            button_row,
            text="다운로드 폴더 열기",
            command=self.open_output_folder,
        ).pack(side="left", padx=(8, 0))

        self.progress = ttk.Progressbar(container, mode="determinate")
        self.progress.pack(fill="x", pady=(4, 5))

        self.status_var = tk.StringVar(value="준비됨")
        ttk.Label(container, textvariable=self.status_var).pack(anchor="w")

        ttk.Label(
            container,
            text="진행 기록",
            font=("Malgun Gothic", 9, "bold"),
        ).pack(anchor="w", pady=(10, 4))

        self.log = tk.Text(
            container,
            height=8,
            wrap="word",
            state="disabled",
            font=("Malgun Gothic", 9),
        )
        self.log.pack(fill="both")

    def _credentials_ready(self) -> bool:
        return bool(
            self.config.get("wiley_token", "").strip()
            and self.config.get("elsevier_api_key", "").strip()
        )

    def open_settings(self) -> None:
        dialog = tk.Toplevel(self.root)
        dialog.title("API 키 설정")
        dialog.geometry("600x310")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()

        frame = ttk.Frame(dialog, padding=18)
        frame.pack(fill="both", expand=True)

        ttk.Label(
            frame,
            text="처음 한 번만 입력하면 이 PC에 저장됩니다.",
            font=("Malgun Gothic", 11, "bold"),
        ).pack(anchor="w", pady=(0, 14))

        ttk.Label(frame, text="Wiley TDM Token").pack(anchor="w")
        wiley_var = tk.StringVar(value=self.config.get("wiley_token", ""))
        wiley_entry = ttk.Entry(frame, textvariable=wiley_var, show="•", width=75)
        wiley_entry.pack(fill="x", pady=(4, 12))

        ttk.Label(frame, text="Elsevier API Key").pack(anchor="w")
        elsevier_var = tk.StringVar(value=self.config.get("elsevier_api_key", ""))
        elsevier_entry = ttk.Entry(frame, textvariable=elsevier_var, show="•", width=75)
        elsevier_entry.pack(fill="x", pady=(4, 8))

        show_var = tk.BooleanVar(value=False)

        def toggle_show() -> None:
            show = "" if show_var.get() else "•"
            wiley_entry.configure(show=show)
            elsevier_entry.configure(show=show)

        ttk.Checkbutton(
            frame,
            text="입력값 보기",
            variable=show_var,
            command=toggle_show,
        ).pack(anchor="w")

        ttk.Label(
            frame,
            text="※ API 키는 이 PC의 사용자 설정 폴더에만 저장됩니다.",
            font=("Malgun Gothic", 8),
        ).pack(anchor="w", pady=(8, 14))

        def save_and_close() -> None:
            wiley = wiley_var.get().strip()
            elsevier = elsevier_var.get().strip()

            if not wiley or not elsevier:
                messagebox.showwarning(
                    "입력 확인",
                    "Wiley TDM Token과 Elsevier API Key를 모두 입력하세요.",
                    parent=dialog,
                )
                return

            self.config["wiley_token"] = wiley
            self.config["elsevier_api_key"] = elsevier
            self.config["output_dir"] = str(self.output_dir)
            save_config(self.config)
            dialog.destroy()
            self.status_var.set("API 키가 저장되었습니다.")

        ttk.Button(frame, text="저장", command=save_and_close).pack(anchor="e")

    def paste_dois(self) -> None:
        try:
            text = self.root.clipboard_get()
        except tk.TclError:
            messagebox.showinfo("클립보드", "클립보드에 텍스트가 없습니다.")
            return

        self.doi_text.delete("1.0", "end")
        self.doi_text.insert("1.0", text)

    def clear_dois(self) -> None:
        self.doi_text.delete("1.0", "end")

    def choose_output_folder(self) -> None:
        selected = filedialog.askdirectory(
            title="PDF 저장 폴더 선택",
            initialdir=str(self.output_dir),
        )
        if not selected:
            return

        self.output_dir = Path(selected)
        self.folder_var.set(str(self.output_dir))
        self.config["output_dir"] = str(self.output_dir)
        save_config(self.config)

    def open_output_folder(self) -> None:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        try:
            os.startfile(str(self.output_dir))
        except Exception as exc:
            messagebox.showerror("폴더 열기 실패", str(exc))

    def start_download(self) -> None:
        if self.running:
            return

        if not self._credentials_ready():
            messagebox.showwarning(
                "API 키 필요",
                "먼저 'API 키 설정'에서 Wiley와 Elsevier API 키를 저장하세요.",
            )
            self.open_settings()
            return

        dois = parse_doi_text(self.doi_text.get("1.0", "end"))
        if not dois:
            messagebox.showwarning(
                "DOI 없음",
                "다운로드할 DOI를 한 줄에 하나씩 붙여넣으세요.",
            )
            return

        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.running = True
        self.start_button.configure(state="disabled")
        self.progress.configure(maximum=len(dois), value=0)
        self.status_var.set(f"0 / {len(dois)} 처리 중")
        self._clear_log()

        thread = threading.Thread(
            target=self._download_worker,
            args=(dois,),
            daemon=True,
        )
        thread.start()

    def _download_worker(self, dois: list[str]) -> None:
        wiley_token = self.config.get("wiley_token", "").strip()
        elsevier_key = self.config.get("elsevier_api_key", "").strip()

        last_wiley = 0.0
        last_elsevier = 0.0
        downloaded = 0
        skipped = 0

        for index, doi in enumerate(dois, 1):
            self.events.put(("status", index - 1, len(dois), f"{doi} 확인 중"))

            try:
                publisher = engine.detect_publisher(doi)
            except Exception as exc:
                result = engine.DownloadResult(
                    doi,
                    "unknown",
                    "error",
                    "",
                    f"출판사 확인 실패: {exc}",
                )
                self.events.put(("result", index, len(dois), result))
                continue

            target = self.output_dir / f"{engine.safe_filename(doi)}.pdf"

            if target.exists() and target.stat().st_size > 0:
                result = engine.DownloadResult(
                    doi,
                    publisher,
                    "skipped",
                    str(target),
                    "이미 받은 파일",
                )
                skipped += 1
                self.events.put(("result", index, len(dois), result))
                continue

            if publisher == "wiley":
                elapsed = time.monotonic() - last_wiley
                if last_wiley and elapsed < 10.0:
                    wait_seconds = 10.0 - elapsed
                    self.events.put(
                        (
                            "status",
                            index - 1,
                            len(dois),
                            f"Wiley 요청 제한 준수: {wait_seconds:.0f}초 대기",
                        )
                    )
                    time.sleep(wait_seconds)

                last_wiley = time.monotonic()
                result = engine.download_wiley(
                    doi,
                    wiley_token,
                    target,
                )

            elif publisher == "elsevier":
                elapsed = time.monotonic() - last_elsevier
                if last_elsevier and elapsed < 1.0:
                    time.sleep(1.0 - elapsed)

                last_elsevier = time.monotonic()
                result = engine.download_elsevier(
                    doi,
                    elsevier_key,
                    target,
                )

            else:
                result = engine.DownloadResult(
                    doi,
                    publisher,
                    "unsupported",
                    "",
                    "Wiley 또는 Elsevier 논문이 아님",
                )

            if result.status == "downloaded":
                downloaded += 1

            self.events.put(("result", index, len(dois), result))

        self.events.put(("done", len(dois), downloaded, skipped))

    def _poll_events(self) -> None:
        try:
            while True:
                event = self.events.get_nowait()
                kind = event[0]

                if kind == "status":
                    _, completed, total, text = event
                    self.progress.configure(value=completed)
                    self.status_var.set(f"{completed} / {total} · {text}")

                elif kind == "result":
                    _, index, total, result = event
                    self.progress.configure(value=index)
                    status = STATUS_TEXT.get(result.status, result.status)
                    self.status_var.set(f"{index} / {total} · {status}")
                    self._append_log(
                        f"[{index}/{total}] {result.doi}\n"
                        f"  {status}: {result.message}\n"
                    )
                    self._append_diagnostic_file(result)

                elif kind == "done":
                    _, total, downloaded, skipped = event
                    self.running = False
                    self.start_button.configure(state="normal")
                    self.progress.configure(value=total)
                    self.status_var.set(
                        f"완료 · 새로 다운로드 {downloaded}개 · 기존 파일 {skipped}개"
                    )
                    messagebox.showinfo(
                        "완료",
                        f"처리가 끝났습니다.\n\n"
                        f"전체: {total}개\n"
                        f"새로 다운로드: {downloaded}개\n"
                        f"기존 파일: {skipped}개",
                    )
        except queue.Empty:
            pass

        self.root.after(100, self._poll_events)

    def _append_diagnostic_file(self, result) -> None:
        """Persist provider diagnostics without ever writing API credentials."""
        try:
            self.output_dir.mkdir(parents=True, exist_ok=True)
            log_path = self.output_dir / "download_log.txt"
            timestamp = datetime.now().astimezone().isoformat(timespec="seconds")
            with log_path.open("a", encoding="utf-8") as handle:
                handle.write(
                    f"{timestamp}\t"
                    f"doi={result.doi}\t"
                    f"provider={result.publisher}\t"
                    f"status={result.status}\t"
                    f"{result.message}\n"
                )
        except Exception:
            # Diagnostic logging must never interrupt downloads.
            pass

    def _append_log(self, text: str) -> None:
        self.log.configure(state="normal")
        self.log.insert("end", text)
        self.log.see("end")
        self.log.configure(state="disabled")

    def _clear_log(self) -> None:
        self.log.configure(state="normal")
        self.log.delete("1.0", "end")
        self.log.configure(state="disabled")


def main() -> None:
    root = tk.Tk()
    app = PaperDownloaderApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
