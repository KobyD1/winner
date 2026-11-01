#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
manager_app.py - אפליקציית ניהול להרצת הסקריפטים בתיקייה והצגת לוגים חיים.

שימוש:
    python manager_app.py                # מנהל את התיקייה שבה נמצא הקובץ
    python manager_app.py C:\\path\\dir   # מנהל תיקייה אחרת

תכונות:
  * סריקה אוטומטית של קבצי .py / .bat / .cmd (+ req*.txt להתקנת חבילות)
  * זיהוי אוטומטי של אפליקציות Streamlit (אפשר לדרוס ידנית)
  * הרצה של כמה סקריפטים במקביל, לוג נפרד לכל אחד
  * טבלת Summary שהסקריפט מדפיס מזוהה ומוצגת בשדה נפרד מהלוג
  * צבע לכל כפתור ולכל רקע (כפתור "🎨 צבעים"), נשמר בין הרצות
  * תיבת "ימים" נפתחת (dropdown) שכותבת מיד DAYS = <ערך> לתוך globals.py
  * עצירה של כל עץ התהליכים (כולל תהליכי-בן של קבצי .bat)

הגדרות מתקדמות בקובץ .manager_config.json (אופציונלי):
  "summary_marker" - ביטוי רגולרי שמסמן תחילת טבלת סיכום (ברירת מחדל: summary / summery / סיכום)
  "names"          - שמות תצוגה לקבצים,  {"file.py": "השם שלי"}
  "visible"        - אילו קבצים מוצגים,  {"globals.py": false}
  "interpreter"    - מפרש Python אחר להרצת הסקריפטים (ברירת מחדל: המפרש שמריץ את המנג'ר)
  "days_var"       - שם המשתנה שנכתב ב-globals.py (ברירת מחדל: "DAYS")
  "days_options"   - רשימת הערכים בתיבת "ימים" (ברירת מחדל: 1,2,3,5,7,10,14,21,30)
  "error_marker"   - regex שקובע מתי נפתח באנר השגיאה (ברירת מחדל: המילה המדויקת ERROR,
                     רגישה לאותיות רישיות - Traceback/Exception רגיל לא מפעילים אותו)
"""
from __future__ import annotations

import ast
import json
import locale
import os
import queue
import re
import shlex
import shutil
import signal
import subprocess
import sys
import threading
import time
import tkinter as tk
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path
from tkinter import colorchooser, filedialog, messagebox, ttk
from typing import Optional

# ───────────────────────────── הגדרות ─────────────────────────────
IS_WIN = os.name == "nt"
BASE_DIR = (Path(sys.argv[1]).resolve() if len(sys.argv) > 1
            else Path(__file__).resolve().parent)
CONFIG_FILE = BASE_DIR / ".manager_config.json"

MAX_LOG_LINES = 20_000          # מקסימום שורות לוג שנשמרות לכל סקריפט
MAX_SUMMARY_LINES = 2_000
POLL_MS = 100                   # תדירות ריענון הלוג
MAX_ITEMS_PER_TICK = 2000       # מגבלת שורות לעיבוד בכל ריענון (שומר על UI זריז)

# קבצי עזר שאינם נועדו להרצה ישירה - מוסתרים כברירת מחדל (לפי שם בסיס, בלי סיומת,
# כך שזה עובד גם על globals.py וגם על globals.pyc אם מפיצים גרסה מקומפלת בלי מקור)
HELPER_FILES = {"__init__", "globals", "uiutils", Path(__file__).stem.lower()}

# ── תיבת "ימים" (days) שנכתבת ישירות ל-globals.py ──
GLOBALS_FILE = BASE_DIR / "globals.py"
DEFAULT_DAYS_VAR = "DAYS"                              # שם המשתנה שנכתב/נקרא ב-globals.py
DEFAULT_DAYS_OPTIONS = ["0","1", "2", "3",]
DEFAULT_LEAGUE_VAR = "LEAGUE"
DEFAULT_LEAGUE_OPTIONS = ["Spain", "England-PLeague", "NBA"]

ANSI_RE = re.compile(r"\x1b\[[0-9;?]*[A-Za-z]")
ERR_RE = re.compile(r"\b(error|exception|critical|fatal|failed)\b", re.I)
WARN_RE = re.compile(r"\bwarn(ing)?\b", re.I)
# הבאנר הקופץ נדלק רק על המילה המדויקת ERROR (רגיש לאותיות רישיות) - לא על
# "error" קטן, לא כחלק ממילה אחרת (למשל TclError), ולא בגלל Traceback/Exception סתם.
ERROR_WORD_RE = re.compile(r"\bERROR\b")
URL_RE = re.compile(r"https?://(?:localhost|127\.0\.0\.1):\d+")
STREAMLIT_RE = re.compile(r"^\s*(?:import|from)\s+streamlit\b", re.M)

# זיהוי טבלת סיכום
DEFAULT_SUMMARY_PATTERN = r"summ(?:a|e)ry|סיכום"       # כולל את האיות "summery"
BOX_CHARS = "│┃║┌┐└┘├┤┬┴┼╔╗╚╝╠╣╦╩╬─━═╭╮╯╰"
SEP_RE = re.compile(r"^[\s\-=+_*~]{3,}$")               # שורת מפריד: ----- / =====
COLS_RE = re.compile(r"\S {2,}\S|\S\t+\S")               # עמודות מופרדות ברווחים/טאבים
ROWS_RE = re.compile(r"^\[\d+ rows x \d+ columns\]$")   # סוף DataFrame של pandas

STATUS_TEXT = {"idle": "", "running": "● רץ", "done": "✔ הסתיים",
               "failed": "✖ נכשל", "stopped": "■ נעצר"}
STATUS_COLOR = {"idle": "#5f6368", "running": "#188038", "done": "#5f6368",
                "failed": "#c5221f", "stopped": "#b06000"}
STATUS_COLOR_DARK = {"idle": "#bdc1c6", "running": "#81c995", "done": "#bdc1c6",
                     "failed": "#f28b82", "stopped": "#fdd663"}
KIND_LABEL = {"py": "Python", "streamlit": "Streamlit", "bat": "Batch", "pip": "Setup"}

# צבעי ברירת מחדל (ניתנים לשינוי דרך "🎨 צבעים")
DEFAULT_COLORS = {
    "bg": "#f0f0f0", "log_bg": "#1e1e1e", "summary_bg": "#252b33",
    "run": "#188038", "stop": "#c5221f", "restart": "#e37400",
    "refresh": "#5f6368", "colors": "#7b1fa2",
    "clear": "#5f6368", "save": "#1a73e8", "copy": "#1a73e8",
    "error_bg": "#c5221f", "folder": "#1a73e8",
}
COLOR_LABELS = {
    "bg": "רקע החלון", "log_bg": "רקע הלוג", "summary_bg": "רקע טבלת הסיכום",
    "run": "כפתור: הרץ", "stop": "כפתור: עצור", "restart": "כפתור: הפעל מחדש",
    "refresh": "כפתור: רענן", "colors": "כפתור: צבעים",
    "clear": "כפתור: נקה", "save": "כפתור: שמור לוג",
    "copy": "כפתור: העתק סיכום", "error_bg": "רקע הודעת שגיאה (ERROR)",
    "folder": "כפתור: שנה תיקייה",
}
HEX_RE = re.compile(r"^#[0-9a-fA-F]{6}$")
PALETTE_DARK = {"out": "#d4d4d4", "err": "#f48771", "warn": "#e5c07b",
                "sys": "#569cd6", "ok": "#6a9955"}
PALETTE_LIGHT = {"out": "#1f1f1f", "err": "#c5221f", "warn": "#9a6700",
                 "sys": "#0b5cad", "ok": "#1e7e34"}


# ───────────────────────────── עזרי צבע ─────────────────────────────
def _rgb(h: str) -> tuple[int, int, int]:
    return int(h[1:3], 16), int(h[3:5], 16), int(h[5:7], 16)


def _hex(r: float, g: float, b: float) -> str:
    return "#%02x%02x%02x" % tuple(max(0, min(255, int(round(v)))) for v in (r, g, b))


def luminance(h: str) -> float:
    r, g, b = _rgb(h)
    return (0.299 * r + 0.587 * g + 0.114 * b) / 255


def contrast_fg(h: str) -> str:
    """צבע טקסט קריא (שחור/לבן) מעל הרקע h."""
    return "#000000" if luminance(h) > 0.6 else "#ffffff"


def shade(h: str, amount: float) -> str:
    """amount<0 מכהה, amount>0 מבהיר."""
    r, g, b = _rgb(h)
    if amount < 0:
        f = 1 + amount
        return _hex(r * f, g * f, b * f)
    return _hex(r + (255 - r) * amount, g + (255 - g) * amount, b + (255 - b) * amount)


def blend(a: str, b: str, t: float) -> str:
    return _hex(*(x + (y - x) * t for x, y in zip(_rgb(a), _rgb(b))))


class ColorButton(tk.Button):
    """כפתור עם צבע רקע מותאם (ttk לא תומך בזה באופן אחיד), טקסט בצבע קריא אוטומטית."""

    def __init__(self, master, key: str, text: str, command) -> None:
        super().__init__(master, text=text, command=command, relief="flat", bd=0,
                         padx=12, pady=6, cursor="hand2", highlightthickness=0,
                         font=("Segoe UI", 9, "bold"))
        self.key = key
        self._bg = DEFAULT_COLORS[key]
        self._enabled = True

    def paint(self, bg: str) -> None:
        self._bg = bg
        self._refresh()

    def set_enabled(self, enabled: bool) -> None:
        if enabled != self._enabled:
            self._enabled = enabled
            self._refresh()

    def _refresh(self) -> None:
        fg = contrast_fg(self._bg)
        if self._enabled:
            self.config(state="normal", bg=self._bg, fg=fg, cursor="hand2",
                        activebackground=shade(self._bg, -0.15), activeforeground=fg)
        else:
            muted = blend(self._bg, "#c8c8c8", 0.65)
            self.config(state="disabled", bg=muted, cursor="arrow",
                        disabledforeground=blend(contrast_fg(muted), muted, 0.45))


# ───────────────────────────── עזרים כלליים ─────────────────────────────
def split_args(text: str) -> list[str]:
    """פירוק שורת ארגומנטים (שומר על נתיבי Windows עם backslash)."""
    if not text.strip():
        return []
    parts = shlex.split(text, posix=not IS_WIN)
    return [p[1:-1] if len(p) >= 2 and p[0] == p[-1] and p[0] in "\"'" else p
            for p in parts]


def decode_line(raw: bytes) -> str:
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return raw.decode(locale.getpreferredencoding(False), errors="replace")


def fmt_elapsed(seconds: float) -> str:
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    return f"{h:d}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"


def looks_tabular(line: str) -> bool:
    """האם השורה נראית כחלק מטבלה (pandas / tabulate / קווים / תווי ציור)."""
    s = line.strip()
    if not s:
        return False
    if "|" in s or any(ch in s for ch in BOX_CHARS):
        return True
    if SEP_RE.match(s) or ROWS_RE.match(s):
        return True
    return bool(COLS_RE.search(s))


def kill_tree(proc: subprocess.Popen) -> None:
    """עצירת התהליך וכל תהליכי-הבן שלו."""
    try:
        if IS_WIN:
            subprocess.run(["taskkill", "/PID", str(proc.pid), "/T", "/F"],
                           capture_output=True,
                           creationflags=subprocess.CREATE_NO_WINDOW)
        else:
            pgid = os.getpgid(proc.pid)
            os.killpg(pgid, signal.SIGTERM)
            try:
                proc.wait(5)
            except subprocess.TimeoutExpired:
                os.killpg(pgid, signal.SIGKILL)
    except (ProcessLookupError, OSError):
        pass


def is_streamlit_file(path: Path) -> bool:
    try:
        with path.open("r", encoding="utf-8", errors="ignore") as f:
            return bool(STREAMLIT_RE.search(f.read(200_000)))
    except OSError:
        return False


def discover() -> list[tuple[str, Path, str, bool]]:
    """
    כל הקבצים שאפשר להריץ: [(name, path, base_kind, is_streamlit)].
    קבצי .pyc (בייטקוד מקומפל, בלי קוד מקור גלוי) נחשבים כמו .py לצורך הרצה -
    python מריץ אותם ישירות. אם לאותו שם קובץ יש גם .py וגם .pyc, מוצג רק ה-.py.
    """
    items = []
    py_stems = {p.stem.lower() for p in BASE_DIR.iterdir()
               if p.is_file() and p.suffix.lower() == ".py"}
    for p in BASE_DIR.iterdir():
        if not p.is_file():
            continue
        low, ext = p.name.lower(), p.suffix.lower()
        if ext == ".py":
            items.append((p.name, p, "py", is_streamlit_file(p)))
        elif ext == ".pyc":
            if p.stem.lower() in py_stems:
                continue                           # יש גם מקור .py - לא כופלים ברשימה
            items.append((p.name, p, "py", False))  # בייטקוד בינארי - לא בודקים streamlit
        elif ext in (".bat", ".cmd"):
            items.append((p.name, p, "bat", False))
        elif ext == ".txt" and low.startswith("req"):
            items.append((p.name, p, "pip", False))
    return items


def _var_pattern(var_name: str) -> re.Pattern:
    return re.compile(rf"^([ \t]*{re.escape(var_name)}[ \t]*=[ \t]*).*$", re.M)


def read_global_value(var_name: str) -> Optional[str]:
    """
    קורא את הערך הנוכחי של var_name מתוך globals.py, אם קיים, ומחזיר אותו כטקסט
    להצגה (למשל DAYS = 7 -> "7", LEAGUE = "Spain" -> "Spain", בלי הגרשיים).
    """
    try:
        text = GLOBALS_FILE.read_text(encoding="utf-8")
    except OSError:
        return None
    m = _var_pattern(var_name).search(text)
    if not m:
        return None
    raw = m.group(0).split("=", 1)[1].strip()
    try:
        return str(ast.literal_eval(raw))
    except (ValueError, SyntaxError):
        return raw


def write_global_literal(var_name: str, literal: str) -> None:
    """
    כותב `VAR = literal` לתוך globals.py (literal הוא כבר קוד פייתון תקין, למשל
    "7" למספר או "'Spain'" למחרוזת מצוטטת): מחליף את השורה אם המשתנה כבר קיים,
    ואחרת מוסיף שורה חדשה בסוף הקובץ (יוצר את הקובץ אם הוא לא קיים).
    """
    try:
        text = GLOBALS_FILE.read_text(encoding="utf-8")
    except OSError:
        text = ""
    pattern = _var_pattern(var_name)
    new_line = f"{var_name} = {literal}"
    if pattern.search(text):
        text = pattern.sub(new_line, text, count=1)
    else:
        if text and not text.endswith("\n"):
            text += "\n"
        text += new_line + "\n"
    GLOBALS_FILE.write_text(text, encoding="utf-8")


@dataclass
class Task:
    name: str
    path: Path
    base_kind: str                       # py | bat | pip
    detected_streamlit: bool = False
    mode: str = "auto"                   # auto | python | streamlit  (רק ל-py)
    alias: str = ""                      # שם תצוגה (ריק = שם הקובץ)
    proc: Optional[subprocess.Popen] = None
    status: str = "idle"                 # idle | running | done | failed | stopped
    exit_code: Optional[int] = None
    started: float = 0.0
    url: Optional[str] = None
    run_id: int = 0
    stop_requested: bool = False
    restart_pending: bool = False
    in_traceback: bool = False
    log: deque = field(default_factory=lambda: deque(maxlen=MAX_LOG_LINES))
    # ── טבלת סיכום ──
    summary: list = field(default_factory=list)       # מה שמוצג בשדה הסיכום
    sum_pending: list = field(default_factory=list)   # בלוק שנאסף כרגע
    sum_active: bool = False
    sum_body: int = 0                                 # כמה שורות טבלה נאספו
    tab_run: list = field(default_factory=list)       # רצף שורות טבלאיות אחרונות
    sum_dirty: bool = False

    @property
    def kind(self) -> str:
        if self.base_kind != "py":
            return self.base_kind
        if self.mode == "python":
            return "py"
        if self.mode == "streamlit":
            return "streamlit"
        return "streamlit" if self.detected_streamlit else "py"

    @property
    def display(self) -> str:
        return self.alias or self.name


# ───────────────────────────── האפליקציה ─────────────────────────────
class ManagerApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title(f"מנהל סקריפטים – {BASE_DIR.name}")
        self.geometry("1300x800")
        self.minsize(1000, 600)

        self.q: queue.Queue = queue.Queue()
        self.tasks: dict[str, Task] = {}
        self.selected: Optional[str] = None

        self.mode_var = tk.StringVar(value="auto")
        self.days_value = tk.StringVar()
        self.league_value = tk.StringVar()
        self.autoscroll = tk.BooleanVar(value=True)
        self.wrap = tk.BooleanVar(value=False)
        self.clear_on_run = tk.BooleanVar(value=True)
        self.hide_summary = tk.BooleanVar(value=False)
        self.buttons: dict[str, ColorButton] = {}
        self.err_active_task: Optional[str] = None
        self.err_count = 0

        self._reload_project_state()           # טוען cfg, צבעים, DAYS/LEAGUE וכו' עבור BASE_DIR
        self._build_ui()
        self.refresh_tasks()
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.after(POLL_MS, self._poll)
        self.after(1000, self._clock)

    # ── מצב שתלוי בתיקיית הפרויקט (BASE_DIR) - נטען גם בהפעלה וגם אחרי שינוי תיקייה ──
    def _reload_project_state(self) -> None:
        self.cfg = self._load_config()

        # המפרש = זה שמריץ את המנג'ר (אפשר לדרוס דרך "interpreter" בקובץ הקונפיג)
        self.interpreter = self.cfg.get("interpreter") or sys.executable
        saved = self.cfg.get("colors", {})
        self.colors = {k: (saved[k] if HEX_RE.match(str(saved.get(k, ""))) else d)
                       for k, d in DEFAULT_COLORS.items()}
        try:
            self.summary_re = re.compile(
                self.cfg.get("summary_marker") or DEFAULT_SUMMARY_PATTERN, re.I)
        except re.error:
            self.summary_re = re.compile(DEFAULT_SUMMARY_PATTERN, re.I)
        try:
            self.error_re = re.compile(self.cfg.get("error_marker") or ERROR_WORD_RE.pattern)
        except re.error:
            self.error_re = ERROR_WORD_RE

        self.days_var_name = str(self.cfg.get("days_var") or DEFAULT_DAYS_VAR)
        self.days_options = list(self.cfg.get("days_options") or DEFAULT_DAYS_OPTIONS)
        initial_days = (read_global_value(self.days_var_name)
                        or str(self.cfg.get("last_days", "")) or self.days_options[0])
        self.league_var_name = str(self.cfg.get("league_var") or DEFAULT_LEAGUE_VAR)
        self.league_options = list(self.cfg.get("league_options") or DEFAULT_LEAGUE_OPTIONS)
        initial_league = (read_global_value(self.league_var_name)
                          or str(self.cfg.get("last_league", "")) or self.league_options[0])
        if initial_league not in self.league_options:
            self.league_options.append(initial_league)

        self.days_value.set(initial_days)
        self.league_value.set(initial_league)
        self.hide_summary.set(bool(self.cfg.get("hide_summary", False)))

        if hasattr(self, "days_cb"):            # הווידג'טים כבר קיימים - עדכן אותם במקום
            self.days_cb.config(values=self.days_options)
            self.days_lbl.config(text=f"ימים ({self.days_var_name}):")
            self.league_cb.config(values=self.league_options)
            self.league_lbl.config(text=f"ליגה ({self.league_var_name}):")
            self.folder_lbl.config(text=f"📁 {BASE_DIR.name}")
            self._apply_theme()

    # ── בניית ממשק ──
    def _btn(self, parent, key: str, text: str, command) -> ColorButton:
        b = ColorButton(parent, key, text, command)
        self.buttons[key] = b
        return b

    def _make_text(self, parent) -> tk.Text:
        parent.rowconfigure(0, weight=1)
        parent.columnconfigure(0, weight=1)
        txt = tk.Text(parent, wrap="none", state="disabled", font=("Consolas", 10),
                      borderwidth=0, padx=8, pady=6)
        ys = ttk.Scrollbar(parent, orient="vertical", command=txt.yview)
        xs = ttk.Scrollbar(parent, orient="horizontal", command=txt.xview)
        txt.configure(yscrollcommand=ys.set, xscrollcommand=xs.set)
        txt.grid(row=0, column=0, sticky="nsew")
        ys.grid(row=0, column=1, sticky="ns")
        xs.grid(row=1, column=0, sticky="ew")
        txt.bind("<1>", lambda e, w=txt: w.focus_set())
        txt.bind("<Control-a>", lambda e, w=txt: (w.tag_add("sel", "1.0", "end"), "break")[1])
        return txt

    def _build_ui(self) -> None:
        self.style = ttk.Style(self)
        try:
            self.style.theme_use("clam")     # ערכת נושא שמאפשרת לשלוט בצבעי הרקע
        except tk.TclError:
            pass
        self.style.configure("Treeview", rowheight=26)

        self.status_lbl = ttk.Label(self, anchor="w", padding=(8, 3))
        self.status_lbl.pack(side="bottom", fill="x")

        # ── באנר שגיאות: מוסתר כברירת מחדל, מופיע בכל פעם שנכתב ERROR בלוגים ──
        self.err_banner = tk.Frame(self, bd=0)
        self.err_icon = tk.Label(self.err_banner, text="⚠", font=("Segoe UI", 12, "bold"),
                                 bd=0, pady=6)
        self.err_icon.pack(side="left", padx=(10, 4))
        self.err_lbl = tk.Label(self.err_banner, text="", font=("Segoe UI", 10, "bold"),
                                anchor="w", justify="left", bd=0, pady=6)
        self.err_lbl.pack(side="left", fill="x", expand=True)
        self.err_goto_btn = tk.Button(self.err_banner, text="עבור ללוג", bd=0,
                                      relief="flat", cursor="hand2",
                                      command=self._goto_error)
        self.err_goto_btn.pack(side="right", padx=(4, 6), pady=6)
        self.err_close_btn = tk.Button(self.err_banner, text="✕", bd=0, relief="flat",
                                       cursor="hand2", command=self._hide_error)
        self.err_close_btn.pack(side="right", padx=(4, 10), pady=6)
        # לא נארז (pack) עד שיש שגיאה בפועל - ר' _show_error / _hide_error

        paned = ttk.PanedWindow(self, orient="horizontal")
        self.main_paned = paned
        paned.pack(fill="both", expand=True, padx=8, pady=(8, 4))
        left = ttk.Frame(paned)
        right = ttk.Frame(paned)
        paned.add(left, weight=1)
        paned.add(right, weight=4)

        # ── תיקיית הפרויקט הנוכחית (ניתנת לשינוי) ──
        folder_frame = ttk.Frame(left)
        folder_frame.pack(fill="x", pady=(0, 6))
        self.folder_lbl = ttk.Label(folder_frame, text=f"📁 {BASE_DIR.name}", anchor="w")
        self.folder_lbl.pack(side="left", fill="x", expand=True)
        self._btn(folder_frame, "folder", "שנה תיקייה…", self.change_folder).pack(side="right")

        # ── צד שמאל: רשימת סקריפטים ──
        tree_frame = ttk.Frame(left)
        tree_frame.pack(fill="both", expand=True)
        self.tree = ttk.Treeview(tree_frame, columns=("kind", "status"),
                                 selectmode="browse")
        self.tree.heading("#0", text="סקריפט", anchor="w")
        self.tree.heading("kind", text="סוג", anchor="w")
        self.tree.heading("status", text="מצב", anchor="w")
        self.tree.column("#0", width=230, stretch=True)
        self.tree.column("kind", width=80, stretch=False)
        self.tree.column("status", width=95, stretch=False)
        tsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=tsb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        tsb.pack(side="left", fill="y")
        for st, col in STATUS_COLOR.items():
            self.tree.tag_configure(st, foreground=col)
        self.tree.bind("<<TreeviewSelect>>", self.on_select)
        self.tree.bind("<Double-1>", self.on_double_click)
        self.tree.bind("<Return>", lambda e: self.run_selected())

        opts = ttk.LabelFrame(left, text="הרצה", padding=8)
        opts.pack(fill="x", pady=(8, 0))
        opts.columnconfigure(1, weight=1)
        ttk.Label(opts, text="מצב הרצה:").grid(row=0, column=0, sticky="w")
        self.mode_cb = ttk.Combobox(opts, values=("auto", "python", "streamlit"),
                                    textvariable=self.mode_var, state="readonly",
                                    width=12)
        self.mode_cb.grid(row=0, column=1, sticky="w", padx=(6, 0))
        self.mode_cb.bind("<<ComboboxSelected>>", self.on_mode_change)

        self.days_lbl = ttk.Label(opts, text=f"ימים ({self.days_var_name}):")
        self.days_lbl.grid(row=1, column=0, sticky="w", pady=(6, 0))
        self.days_cb = ttk.Combobox(opts, values=self.days_options,
                                    textvariable=self.days_value, width=12)
        self.days_cb.grid(row=1, column=1, sticky="w", padx=(6, 0), pady=(6, 0))
        self.days_cb.bind("<<ComboboxSelected>>", self.on_days_change)
        self.days_cb.bind("<Return>", self.on_days_change)
        self.days_cb.bind("<FocusOut>", self.on_days_change)
        self.days_note = ttk.Label(opts, foreground="#188038")
        self.days_note.grid(row=2, column=0, columnspan=2, sticky="w")

        self.league_lbl = ttk.Label(opts, text=f"ליגה ({self.league_var_name}):")
        self.league_lbl.grid(row=3, column=0, sticky="w", pady=(6, 0))
        self.league_cb = ttk.Combobox(opts, values=self.league_options,
                                      textvariable=self.league_value, state="readonly",
                                      width=16)
        self.league_cb.grid(row=3, column=1, sticky="w", padx=(6, 0), pady=(6, 0))
        self.league_cb.bind("<<ComboboxSelected>>", self.on_league_change)
        self.league_note = ttk.Label(opts, foreground="#188038")
        self.league_note.grid(row=4, column=0, columnspan=2, sticky="w")

        btns = ttk.Frame(opts)
        btns.grid(row=5, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        for key, text, cmd in (("run", "▶ הרץ", self.run_selected),
                               ("stop", "■ עצור", self.stop_selected),
                               ("restart", "↻ הפעל מחדש", self.restart_selected)):
            self._btn(btns, key, text, cmd).pack(side="left", expand=True, fill="x", padx=2)

        bottom = ttk.Frame(left)
        bottom.pack(fill="x", pady=(8, 0))
        self._btn(bottom, "colors", "🎨 צבעים", self.colors_dialog).pack(
            side="left", expand=True, fill="x", padx=2)
        self._btn(bottom, "refresh", "⟳ רענן", self.refresh_tasks).pack(
            side="left", expand=True, fill="x", padx=2)

        # ── צד ימין: כותרת, אפשרויות, סיכום ולוג ──
        head = ttk.Frame(right)
        head.pack(fill="x")
        self.title_lbl = ttk.Label(head, font=("Segoe UI", 12, "bold"))
        self.title_lbl.pack(side="left")
        self.state_lbl = ttk.Label(head, font=("Segoe UI", 10))
        self.state_lbl.pack(side="left", padx=12)
        for key, text, cmd in (("clear", "נקה לוג", self.clear_log),
                               ("save", "שמור לוג…", self.save_log)):
            self._btn(head, key, text, cmd).pack(side="right", padx=(4, 0))

        lopts = ttk.Frame(right)
        lopts.pack(fill="x", pady=(6, 4))
        ttk.Checkbutton(lopts, text="גלילה אוטומטית",
                        variable=self.autoscroll).pack(side="left")
        ttk.Checkbutton(lopts, text="גלישת שורות", variable=self.wrap,
                        command=self._apply_wrap).pack(side="left", padx=10)
        ttk.Checkbutton(lopts, text="נקה לוג בכל הרצה",
                        variable=self.clear_on_run).pack(side="left")
        ttk.Checkbutton(lopts, text="הסתר את טבלת הסיכום מהלוג",
                        variable=self.hide_summary).pack(side="left", padx=10)

        rpane = ttk.PanedWindow(right, orient="vertical")
        rpane.pack(fill="both", expand=True)

        # שדה הסיכום (נפרד מהלוג)
        sum_frame = ttk.Frame(rpane)
        rpane.add(sum_frame, weight=2)
        sh = ttk.Frame(sum_frame)
        sh.pack(fill="x", pady=(0, 3))
        ttk.Label(sh, text="📊 טבלת סיכום (Summary)",
                  font=("Segoe UI", 10, "bold")).pack(side="left")
        self._btn(sh, "copy", "העתק סיכום", self.copy_summary).pack(side="right")
        sbody = ttk.Frame(sum_frame)
        sbody.pack(fill="both", expand=True)
        self.sum_text = self._make_text(sbody)

        # שדה הלוג
        log_frame = ttk.Frame(rpane)
        rpane.add(log_frame, weight=3)
        ttk.Label(log_frame, text="📜 לוג הרצה",
                  font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(6, 3))
        lbody = ttk.Frame(log_frame)
        lbody.pack(fill="both", expand=True)
        self.text = self._make_text(lbody)

        self._apply_theme()

    # ── ערכת צבעים ──
    def _style_text(self, w: tk.Text, bg: str) -> None:
        dark = luminance(bg) < 0.5
        pal = PALETTE_DARK if dark else PALETTE_LIGHT
        w.config(bg=bg, fg=pal["out"], insertbackground=pal["out"],
                 selectbackground="#264f78" if dark else "#a8c7fa",
                 selectforeground="#ffffff" if dark else "#000000")
        for tag in ("out", "err", "warn", "sys", "ok"):
            w.tag_configure(tag, foreground=pal[tag])
        w.tag_configure("sum", foreground=pal["out"])
        w.tag_configure("sum_head", foreground=pal["sys"], font=("Consolas", 10, "bold"))
        w.tag_configure("dim", foreground=blend(pal["out"], bg, 0.5))

    def _apply_theme(self) -> None:
        c = self.colors
        bg = c["bg"]
        fg = contrast_fg(bg)
        self.configure(bg=bg)
        s = self.style
        s.configure("TFrame", background=bg)
        s.configure("TLabel", background=bg, foreground=fg)
        s.configure("TCheckbutton", background=bg, foreground=fg)
        s.map("TCheckbutton", background=[("active", bg)], foreground=[("active", fg)])
        s.configure("TLabelframe", background=bg)
        s.configure("TLabelframe.Label", background=bg, foreground=fg)
        s.configure("TPanedwindow", background=bg)
        self._style_text(self.text, c["log_bg"])
        self._style_text(self.sum_text, c["summary_bg"])
        err_fg = contrast_fg(c["error_bg"])
        self.err_banner.configure(bg=c["error_bg"])
        for w in (self.err_icon, self.err_lbl):
            w.configure(bg=c["error_bg"], fg=err_fg)
        for w in (self.err_goto_btn, self.err_close_btn):
            w.configure(bg=c["error_bg"], fg=err_fg, activebackground=shade(c["error_bg"], -0.15),
                       activeforeground=err_fg, highlightthickness=0)
        for key, b in self.buttons.items():
            b.paint(c[key])
        self._update_header()

    def colors_dialog(self) -> None:
        """חלון לקביעת צבע לכל כפתור ולרקעים. השינויים מוחלים מיד ונשמרים."""
        win = tk.Toplevel(self)
        win.title("צבעים")
        win.geometry("480x610")
        win.transient(self)
        ttk.Label(win, padding=8, wraplength=440,
                  text="בחר צבע לכל כפתור ולרקעים. השינויים מוחלים מיד.").pack(fill="x")
        grid = ttk.Frame(win, padding=(10, 0))
        grid.pack(fill="both", expand=True)
        swatches: dict[str, tk.Label] = {}

        def paint_swatch(key: str) -> None:
            col = self.colors[key]
            swatches[key].config(text=col, bg=col, fg=contrast_fg(col))

        def set_color(key: str, value: str) -> None:
            self.colors[key] = value
            paint_swatch(key)
            self._apply_theme()
            self._save_config()

        def pick(key: str) -> None:
            res = colorchooser.askcolor(color=self.colors[key],
                                        title=COLOR_LABELS[key], parent=win)
            if res and res[1]:
                set_color(key, res[1].lower())

        def reset_all() -> None:
            for k, d in DEFAULT_COLORS.items():
                self.colors[k] = d
                paint_swatch(k)
            self._apply_theme()
            self._save_config()

        for i, key in enumerate(DEFAULT_COLORS):
            ttk.Label(grid, text=COLOR_LABELS[key]).grid(row=i, column=0, sticky="w", pady=3)
            sw = tk.Label(grid, width=11, relief="solid", bd=1)
            sw.grid(row=i, column=1, padx=8)
            swatches[key] = sw
            paint_swatch(key)
            ttk.Button(grid, text="בחר…",
                       command=lambda k=key: pick(k)).grid(row=i, column=2)
            ttk.Button(grid, text="איפוס",
                       command=lambda k=key: set_color(k, DEFAULT_COLORS[k])
                       ).grid(row=i, column=3, padx=(4, 0))
        bar = ttk.Frame(win, padding=8)
        bar.pack(fill="x")
        ttk.Button(bar, text="איפוס הכול", command=reset_all).pack(side="left")
        ttk.Button(bar, text="סגור", command=win.destroy).pack(side="right")

    # ── קונפיגורציה ──
    def _load_config(self) -> dict:
        try:
            return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {}

    def _save_config(self) -> None:
        modes = self.cfg.setdefault("modes", {})
        for n, t in self.tasks.items():
            if t.mode != "auto":
                modes[n] = t.mode
            else:
                modes.pop(n, None)
        self.cfg["colors"] = {k: v for k, v in self.colors.items()
                              if v != DEFAULT_COLORS[k]}
        self.cfg["hide_summary"] = bool(self.hide_summary.get())
        self.cfg["days_var"] = self.days_var_name
        self.cfg["days_options"] = self.days_options
        self.cfg["last_days"] = self.days_value.get().strip()
        self.cfg["league_var"] = self.league_var_name
        self.cfg["league_options"] = self.league_options
        self.cfg["last_league"] = self.league_value.get().strip()
        try:
            CONFIG_FILE.write_text(json.dumps(self.cfg, ensure_ascii=False, indent=2),
                                   encoding="utf-8")
        except OSError:
            pass

    # ── שינוי תיקיית הפרויקט ──
    def change_folder(self) -> None:
        """
        פותח דיאלוג לבחירת תיקייה אחרת, ואז סורק אותה מחדש במקום BASE_DIR הנוכחי.
        לכל תיקייה יש .manager_config.json משלה (צבעים, DAYS/LEAGUE, שמות וכו'),
        כך שמעבר בין תיקיות עובד כמו מעבר בין פרויקטים נפרדים.
        """
        global BASE_DIR, GLOBALS_FILE, CONFIG_FILE
        running = [t for t in self.tasks.values() if t.status == "running"]
        if running:
            if not messagebox.askyesno(
                    "שינוי תיקייה",
                    f"{len(running)} תהליכים עדיין רצים בתיקייה הנוכחית.\n"
                    "לעצור אותם ולהחליף תיקייה?"):
                return
            for t in running:
                if t.proc:
                    kill_tree(t.proc)

        chosen = filedialog.askdirectory(title="בחר תיקיית פרויקט", initialdir=str(BASE_DIR))
        if not chosen:
            return
        new_dir = Path(chosen).resolve()
        if new_dir == BASE_DIR:
            return
        if not new_dir.is_dir():
            messagebox.showerror("שגיאה", f"התיקייה לא נמצאה:\n{new_dir}")
            return

        self._save_config()      # שמור את מצב התיקייה הנוכחית לפני שעוזבים אותה

        BASE_DIR = new_dir
        GLOBALS_FILE = BASE_DIR / "globals.py"
        CONFIG_FILE = BASE_DIR / ".manager_config.json"

        self.tasks.clear()
        self.selected = None
        self._hide_error()
        self.err_count = 0

        self._reload_project_state()
        self.title(f"מנהל סקריפטים – {BASE_DIR.name}")
        self.refresh_tasks()

    # ── רשימת משימות ──
    def _is_visible(self, name: str) -> bool:
        """ברירת מחדל: הכול מוצג חוץ מקבצי עזר (אפשר לשנות דרך "visible" בקונפיג)."""
        stem = Path(name).stem.lower()
        return self.cfg.get("visible", {}).get(name, stem not in HELPER_FILES)

    def refresh_tasks(self) -> None:
        found = discover()
        names = {n for n, *_ in found}
        for name, path, kind, st in found:
            t = self.tasks.get(name)
            if t is None:
                self.tasks[name] = Task(
                    name, path, kind, st,
                    mode=self.cfg.get("modes", {}).get(name, "auto"),
                    alias=self.cfg.get("names", {}).get(name, ""))
            else:
                t.detected_streamlit = st
        for name in list(self.tasks):
            if name not in names and self.tasks[name].status != "running":
                del self.tasks[name]
        self._rebuild_tree()

    def _rebuild_tree(self) -> None:
        shown = [t for t in self.tasks.values()
                 if self._is_visible(t.name) or t.status == "running"]
        shown.sort(key=lambda t: t.display.lower())
        self.tree.delete(*self.tree.get_children())
        for t in shown:
            self.tree.insert("", "end", iid=t.name, text=t.display,
                             values=(KIND_LABEL[t.kind], STATUS_TEXT[t.status]),
                             tags=(t.status,))
        if self.selected and self.tree.exists(self.selected):
            self.tree.selection_set(self.selected)
        else:
            self.selected = None
            self._clear_widget()
            self._render_summary(None)
        self._update_header()
        self._update_statusbar()

    def _update_row(self, t: Task) -> None:
        if self.tree.exists(t.name):
            self.tree.item(t.name, text=t.display, tags=(t.status,))
            self.tree.set(t.name, "status", STATUS_TEXT[t.status])
            self.tree.set(t.name, "kind", KIND_LABEL[t.kind])

    def _cur(self) -> Optional[Task]:
        return self.tasks.get(self.selected) if self.selected else None

    # ── אירועי ממשק ──
    def on_select(self, _event=None) -> None:
        sel = self.tree.selection()
        if not sel:
            return
        self.selected = sel[0]
        t = self.tasks[self.selected]
        self.mode_var.set(t.mode)
        self.mode_cb.config(state="readonly" if t.base_kind == "py" else "disabled")
        self._render_log(t)
        self._render_summary(t)
        self._update_header()

    def on_double_click(self, event) -> None:
        iid = self.tree.identify_row(event.y)
        if iid:
            self.tree.selection_set(iid)
            self.on_select()
            self.run_selected()

    def on_mode_change(self, _event=None) -> None:
        t = self._cur()
        if t and t.base_kind == "py":
            t.mode = self.mode_var.get()
            self._update_row(t)

    def on_days_change(self, _event=None) -> None:
        """נקרא כשבוחרים/מקלידים ערך בתיבת 'ימים' - כותב אותו מיד ל-globals.py כמספר שלם."""
        value = self.days_value.get().strip()
        if not value:
            return
        try:
            int(value)
        except ValueError:
            self.days_note.config(text=f"⚠ '{value}' אינו מספר שלם", foreground="#c5221f")
            return
        try:
            write_global_literal(self.days_var_name, value)
        except OSError as e:
            self.days_note.config(text=f"✖ שגיאת כתיבה: {e}", foreground="#c5221f")
            return
        if value not in self.days_options:
            self.days_options.append(value)
            self.days_cb.config(values=self.days_options)
        self.days_note.config(
            text=f"✔ נכתב ל-globals.py: {self.days_var_name} = {value}",
            foreground="#188038")
        self._save_config()

    def on_league_change(self, _event=None) -> None:
        """נקרא כשבוחרים ליגה בתיבה - כותב אותה מיד ל-globals.py כמחרוזת מצוטטת."""
        value = self.league_value.get().strip()
        if not value:
            return
        try:
            write_global_literal(self.league_var_name, repr(value))
        except OSError as e:
            self.league_note.config(text=f"✖ שגיאת כתיבה: {e}", foreground="#c5221f")
            return
        self.league_note.config(
            text=f"✔ נכתב ל-globals.py: {self.league_var_name} = {value!r}",
            foreground="#188038")
        self._save_config()

    def _apply_wrap(self) -> None:
        self.text.config(wrap="word" if self.wrap.get() else "none")

    # ── הרצה / עצירה ──
    def _build_cmd(self, t: Task) -> list[str]:
        if t.kind == "bat":
            if not IS_WIN:
                raise RuntimeError("קבצי .bat / .cmd ניתנים להרצה רק ב-Windows.")
            return ["cmd", "/c", t.path.name]
        py = self.interpreter
        if not shutil.which(py):
            raise RuntimeError(f"מפרש Python לא נמצא:\n{py}")
        if t.kind == "streamlit":
            return [py, "-m", "streamlit", "run", str(t.path)]
        if t.kind == "pip":
            return [py, "-m", "pip", "install", "-r", str(t.path)]
        return [py, "-u", str(t.path)]

    def _reset_summary(self, t: Task) -> None:
        t.summary, t.sum_pending, t.tab_run = [], [], []
        t.sum_active, t.sum_body, t.sum_dirty = False, 0, True

    def start(self, t: Task) -> None:
        if t.status == "running":
            return
        try:
            cmd = self._build_cmd(t)
        except RuntimeError as e:
            messagebox.showerror("שגיאה", str(e))
            return

        env = os.environ.copy()
        env.update(PYTHONUNBUFFERED="1", PYTHONIOENCODING="utf-8",
                   STREAMLIT_BROWSER_GATHER_USAGE_STATS="false")
        kwargs = dict(cwd=str(BASE_DIR), env=env, stdin=subprocess.DEVNULL,
                      stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        if IS_WIN:
            kwargs["creationflags"] = (subprocess.CREATE_NEW_PROCESS_GROUP |
                                       subprocess.CREATE_NO_WINDOW)
        else:
            kwargs["start_new_session"] = True

        if self.clear_on_run.get():
            t.log.clear()
            if t.name == self.selected:
                self._clear_widget()

        try:
            proc = subprocess.Popen(cmd, **kwargs)
        except OSError as e:
            self._sys(t, f"✖ לא ניתן להפעיל: {e}", "err")
            return

        t.run_id += 1
        t.proc, t.status, t.exit_code = proc, "running", None
        t.started, t.url = time.time(), None
        t.stop_requested = t.restart_pending = t.in_traceback = False
        self._reset_summary(t)                 # סיכום חדש לכל הרצה
        if t.name == self.selected:
            self._render_summary(t)
        if self.err_active_task == t.name:
            self._hide_error()
        self._sys(t, f"▶ [{time.strftime('%H:%M:%S')}] {subprocess.list2cmdline(cmd)}")
        self._update_row(t)
        threading.Thread(target=self._reader, args=(t.name, t.run_id, proc),
                         daemon=True).start()
        self._update_header()
        self._update_statusbar()

    def _reader(self, name: str, run_id: int, proc: subprocess.Popen) -> None:
        """רץ ב-thread נפרד: קורא פלט שורה-שורה ומעביר לתור."""
        try:
            for raw in iter(proc.stdout.readline, b""):
                self.q.put((name, run_id, "line", decode_line(raw)))
        except (OSError, ValueError):
            pass
        finally:
            self.q.put((name, run_id, "exit", proc.wait()))

    def stop(self, t: Task) -> None:
        if t.proc and t.status == "running" and not t.stop_requested:
            t.stop_requested = True
            self._sys(t, "■ מבקש לעצור את התהליך…", "warn")
            threading.Thread(target=kill_tree, args=(t.proc,), daemon=True).start()

    def run_selected(self) -> None:
        t = self._cur()
        if t:
            self.start(t)

    def stop_selected(self) -> None:
        t = self._cur()
        if t:
            self.stop(t)

    def restart_selected(self) -> None:
        t = self._cur()
        if not t:
            return
        if t.status == "running":
            t.restart_pending = True
            self.stop(t)
        else:
            self.start(t)

    # ── טיפול בפלט ──
    def _classify(self, t: Task, raw: str) -> tuple[str, str]:
        line = ANSI_RE.sub("", raw.rstrip("\r\n"))
        if "\r" in line:                       # פסי התקדמות (tqdm וכד')
            parts = [p for p in line.split("\r") if p]
            line = parts[-1] if parts else ""
        tag = "out"
        if line.startswith("Traceback"):
            t.in_traceback, tag = True, "err"
        elif t.in_traceback:
            tag = "err"
            if line and not line[0].isspace():  # שורת החריגה מסיימת את ה-Traceback
                t.in_traceback = False
        elif ERR_RE.search(line):
            tag = "err"
        elif WARN_RE.search(line):
            tag = "warn"
        if t.url is None and t.kind == "streamlit":
            m = URL_RE.search(line)
            if m:
                t.url = m.group(0)
        return line, tag

    def _feed_summary(self, t: Task, line: str) -> bool:
        """
        מזהה בלוק "Summary" בפלט: שורת כותרת (summary/summery/סיכום) ואחריה שורות טבלה.
        מחזיר True אם השורה היא חלק מגוף הטבלה (ורק אז אפשר להסתיר אותה מהלוג).
        שורת הכותרת עצמה נשארת תמיד גם בלוג; סיכום קודם מוחלף רק אם נמצאה טבלה אמיתית.
        """
        tabular = looks_tabular(line)
        captured = False
        if self.summary_re.search(line):
            # כותרת בתוך מסגרת (┌──┐ │ SUMMARY │) - כוללים גם את שורות המסגרת שלפניה
            t.sum_pending = (list(t.tab_run) if tabular else []) + [line]
            t.sum_body = 1 if tabular else 0
            t.sum_active = True
            if t.sum_body:
                t.summary = t.sum_pending
                t.sum_dirty = True
        elif t.sum_active:
            if tabular:
                t.sum_pending.append(line)
                t.sum_body += 1
                if t.sum_body == 1:
                    t.summary = t.sum_pending
                del t.sum_pending[MAX_SUMMARY_LINES:]
                t.sum_dirty = True
                captured = True
            elif not line.strip():
                if t.sum_body:                 # שורה ריקה אחרי הטבלה = סוף
                    t.sum_active = False
            else:                              # שורת טקסט רגילה = סוף
                t.sum_active = False
        if tabular:
            t.tab_run.append(line)
            del t.tab_run[:-200]
        else:
            t.tab_run.clear()
        return captured

    def _on_exit(self, t: Task, code: int) -> tuple[str, str]:
        elapsed = fmt_elapsed(time.time() - t.started)
        t.exit_code, t.proc = code, None
        t.sum_active = False
        stamp = time.strftime("%H:%M:%S")
        if t.stop_requested:
            t.status = "stopped"
            item = (f"■ [{stamp}] נעצר ידנית (קוד {code}, זמן ריצה {elapsed})", "warn")
        elif code == 0:
            t.status = "done"
            item = (f"✔ [{stamp}] הסתיים בהצלחה (זמן ריצה {elapsed})", "ok")
        else:
            t.status = "failed"
            item = (f"✖ [{stamp}] נכשל עם קוד {code} (זמן ריצה {elapsed})", "err")
        t.log.append(item)
        self._update_row(t)
        if t.restart_pending:
            t.restart_pending = False
            self.after(300, lambda task=t: self.start(task))
        return item

    def _poll(self) -> None:
        ui_items: list[tuple[str, str]] = []
        changed = False
        for _ in range(MAX_ITEMS_PER_TICK):
            try:
                name, run_id, kind, payload = self.q.get_nowait()
            except queue.Empty:
                break
            t = self.tasks.get(name)
            if t is None or t.run_id != run_id:      # אירוע מהרצה ישנה
                continue
            if kind == "line":
                line, tag = self._classify(t, payload)
                if self.error_re.search(line):
                    self._show_error(t, line)
                in_summary = self._feed_summary(t, line)
                if not (in_summary and self.hide_summary.get()):
                    t.log.append((line, tag))
                    if name == self.selected:
                        ui_items.append((line, tag))
                if t.url and name == self.selected:
                    changed = True
            else:
                item = self._on_exit(t, payload)
                if name == self.selected:
                    ui_items.append(item)
                changed = True
        if ui_items:
            self._append_lines(ui_items)
        cur = self._cur()
        if cur and cur.sum_dirty:
            self._render_summary(cur)
            changed = True
        if changed:
            self._update_header()
            self._update_statusbar()
        self.after(POLL_MS, self._poll)

    def _sys(self, t: Task, text: str, tag: str = "sys") -> None:
        item = (text, tag)
        t.log.append(item)
        if t.name == self.selected:
            self._append_lines([item])

    # ── באנר שגיאות (מעל הלוג, מציג ERROR מכל סקריפט שרץ) ──
    def _show_error(self, t: Task, line: str) -> None:
        self.err_count += 1
        self.err_active_task = t.name
        text = line.strip() or "(שורה ריקה)"
        if len(text) > 300:
            text = text[:300] + "…"
        self.err_lbl.config(text=text)
        if not self.err_banner.winfo_ismapped():
            self.err_banner.pack(side="top", fill="x", before=self.main_paned)

    def _hide_error(self) -> None:
        self.err_banner.pack_forget()
        self.err_active_task = None

    def _goto_error(self) -> None:
        name = self.err_active_task
        if name and self.tree.exists(name):
            self.tree.selection_set(name)
            self.on_select()
        self._hide_error()

    # ── תצוגת הלוג ──
    def _clear_widget(self) -> None:
        self.text.config(state="normal")
        self.text.delete("1.0", "end")
        self.text.config(state="disabled")

    def _render_log(self, t: Task) -> None:
        self.text.config(state="normal")
        self.text.delete("1.0", "end")
        for line, tag in t.log:
            self.text.insert("end", line + "\n", tag)
        self.text.config(state="disabled")
        if self.autoscroll.get():
            self.text.see("end")

    def _append_lines(self, items: list[tuple[str, str]]) -> None:
        self.text.config(state="normal")
        for line, tag in items:
            self.text.insert("end", line + "\n", tag)
        extra = int(self.text.index("end-1c").split(".")[0]) - MAX_LOG_LINES
        if extra > 0:
            self.text.delete("1.0", f"{extra + 1}.0")
        self.text.config(state="disabled")
        if self.autoscroll.get():
            self.text.see("end")

    def clear_log(self) -> None:
        t = self._cur()
        if t:
            t.log.clear()
            self._clear_widget()

    def save_log(self) -> None:
        t = self._cur()
        if not t:
            return
        fn = filedialog.asksaveasfilename(
            defaultextension=".log",
            initialfile=f"{t.path.stem}_{time.strftime('%Y%m%d_%H%M%S')}.log",
            filetypes=[("Log", "*.log"), ("Text", "*.txt"), ("All", "*.*")])
        if fn:
            Path(fn).write_text("\n".join(line for line, _ in t.log) + "\n",
                                encoding="utf-8")

    # ── שדה הסיכום ──
    def _render_summary(self, t: Optional[Task]) -> None:
        w = self.sum_text
        w.config(state="normal")
        w.delete("1.0", "end")
        if t and t.summary:
            for line in t.summary:
                w.insert("end", line + "\n",
                         "sum_head" if self.summary_re.search(line) else "sum")
        else:
            w.insert("end", "(עדיין אין טבלת סיכום – היא תופיע כאן כשהסקריפט ידפיס אותה)",
                     "dim")
        w.config(state="disabled")
        if t:
            t.sum_dirty = False

    def copy_summary(self) -> None:
        t = self._cur()
        if t and t.summary:
            self.clipboard_clear()
            self.clipboard_append("\n".join(t.summary))
            self.status_lbl.config(text="טבלת הסיכום הועתקה ללוח")
            self.after(2500, self._update_statusbar)

    # ── כותרת / סרגל מצב ──
    def _update_header(self) -> None:
        B = self.buttons
        t = self._cur()
        if not t:
            self.title_lbl.config(text="בחר סקריפט מהרשימה")
            self.state_lbl.config(text="")
            for k in ("run", "stop", "restart", "save", "clear", "copy"):
                B[k].set_enabled(False)
            return
        dark = luminance(self.colors["bg"]) < 0.5
        running = t.status == "running"
        self.title_lbl.config(text=f"{t.alias}  ({t.name})" if t.alias else t.name)
        if running:
            txt = f"{STATUS_TEXT['running']} – {fmt_elapsed(time.time() - t.started)}"
        elif t.exit_code is not None:
            txt = f"{STATUS_TEXT[t.status]} (קוד {t.exit_code})"
        else:
            txt = "מוכן להרצה"
        self.state_lbl.config(
            text=txt, foreground=(STATUS_COLOR_DARK if dark else STATUS_COLOR)[t.status])
        B["run"].set_enabled(not running)
        B["stop"].set_enabled(running and not t.stop_requested)
        B["restart"].set_enabled(True)
        B["save"].set_enabled(True)
        B["clear"].set_enabled(True)
        B["copy"].set_enabled(bool(t.summary))

    def _update_statusbar(self) -> None:
        n = sum(1 for t in self.tasks.values() if t.status == "running")
        self.status_lbl.config(text=f"תהליכים רצים: {n}   |   תיקייה: {BASE_DIR}")

    def _clock(self) -> None:
        t = self._cur()
        if t and t.status == "running":
            self._update_header()
        self.after(1000, self._clock)

    # ── יציאה ──
    def on_close(self) -> None:
        running = [t for t in self.tasks.values() if t.status == "running"]
        if running:
            if not messagebox.askyesno(
                    "יציאה", f"{len(running)} תהליכים עדיין רצים.\nלעצור אותם ולצאת?"):
                return
            for t in running:
                if t.proc:
                    kill_tree(t.proc)
        self._save_config()
        self.destroy()


def main() -> None:
    if IS_WIN:
        try:
            import ctypes
            ctypes.windll.shcore.SetProcessDpiAwareness(1)   # טקסט חד במסכי HiDPI
        except Exception:
            pass
    ManagerApp().mainloop()


if __name__ == "__main__":
    main()