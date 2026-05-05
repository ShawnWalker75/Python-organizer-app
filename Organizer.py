import os
import shutil
import time
import zipfile
import ctypes
import threading
import string
from tkinter import filedialog
import customtkinter as ctk

# --- CONFIG ---
DEFAULT_FOLDER = os.path.normpath(os.path.expanduser("~/Downloads"))

FILE_TYPES = {
    "Images": [".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".svg"],
    "Documents": [".pdf", ".docx", ".txt", ".xlsx", ".pptx", ".csv", ".ods", ".odt"],
    "Archives": [".zip", ".rar", ".7z", ".tar", ".gz"],
    "Music": [".mp3", ".wav", ".flac"],
    "Videos": [".mp4", ".mov", ".avi", ".mkv"],
    "Executables": [".exe", ".msi"]
}

THEMES = {
    "Ocean Blue": {"primary": "#3b8ed0", "accent": "#2fa572", "sidebar": "#1e1e1e"},
    "Electric Purple": {"primary": "#a29bfe", "accent": "#ff007f", "sidebar": "#1a1a2e"},
    "Cyberpunk": {"primary": "#f1c40f", "accent": "#e74c3c", "sidebar": "#121212"},
    "Minimalist": {"primary": "#888888", "accent": "#444444", "sidebar": "#2b2b2b"}
}

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        try:
            self.script_name = os.path.basename(__file__)
        except NameError:
            self.script_name = "organizer.py"
        
        self.title("Organizer Suite")
        self.geometry("1100x850")
        ctk.set_appearance_mode("dark")
        
        # State Variables
        self.watch_folder = DEFAULT_FOLDER
        self.unzip_scan_folder = DEFAULT_FOLDER 
        self.found_archives = [] 
        self.current_theme_name = "Ocean Blue"
        self.last_move_history = [] 
        self.nav_buttons = []

        try:
            myappid = 'com.gemini.downloadorganizer.pro.v3' 
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        except Exception: 
            pass
        
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.sidebar = ctk.CTkFrame(self, width=220, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        
        self.logo = ctk.CTkLabel(self.sidebar, text="D O P S", font=("Impact", 42))
        self.logo.pack(pady=(30, 40))

        self.btn_org = self.create_nav_btn("Organizer", self.show_organizer)
        self.btn_unzip = self.create_nav_btn("Unarchive", self.show_unarchive)
        self.btn_launch = self.create_nav_btn("Launcher", self.show_launcher)
        self.btn_stats = self.create_nav_btn("Stats", self.show_stats)
        self.btn_advanced = self.create_nav_btn("Advanced", self.show_advanced)
        self.btn_settings = self.create_nav_btn("Settings", self.show_settings)

        self.content_frame = ctk.CTkFrame(self, corner_radius=20, border_width=2)
        self.content_frame.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")

        self.setup_pages()
        self.apply_global_theme() 
        self.show_organizer()
        self.update_stats()

    def create_nav_btn(self, text, command):
        btn = ctk.CTkButton(self.sidebar, text=text, fg_color="transparent", 
                            text_color="gray", hover_color="#333333", 
                            anchor="w", font=("Helvetica", 15, "bold"),
                            command=command, height=45)
        btn.pack(fill="x", padx=10, pady=5)
        self.nav_buttons.append(btn)
        return btn

    def setup_pages(self):
        # PAGE: ORGANIZER
        self.page_org = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        self.org_card = ctk.CTkFrame(self.page_org, corner_radius=15, border_width=2)
        self.org_card.pack(pady=20, padx=20, fill="x")
        self.folder_label = ctk.CTkLabel(self.org_card, text=f"Target: {self.watch_folder}", font=("Helvetica", 12, "italic"))
        self.folder_label.pack(pady=(10, 0))
        ctk.CTkLabel(self.org_card, text="Smart File Sweep", font=("Helvetica", 22, "bold")).pack(pady=10)
        self.progress = ctk.CTkProgressBar(self.org_card, width=500)
        self.progress.set(0)
        self.progress.pack(pady=10)
        self.btn_sweep = ctk.CTkButton(self.org_card, text="START SWEEP", font=("Helvetica", 14, "bold"), command=self.start_sweep_thread)
        self.btn_sweep.pack(pady=20)
        self.undo_btn = ctk.CTkButton(self.page_org, text="Undo Last Sweep", command=self.undo_last_sweep, fg_color="#c43e3e", state="disabled")
        self.undo_btn.pack(pady=5)
        self.log_box = ctk.CTkTextbox(self.page_org, font=("Consolas", 12))
        self.log_box.pack(pady=20, fill="both", expand=True, padx=20)

        # PAGE: UNARCHIVE
        self.page_unzip = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        self.unzip_header = ctk.CTkFrame(self.page_unzip, fg_color="transparent")
        self.unzip_header.pack(fill="x", padx=20, pady=10)
        ctk.CTkLabel(self.unzip_header, text="Unarchive Manager", font=("Helvetica", 24, "bold")).pack(side="left")
        self.btn_select_unzip = ctk.CTkButton(self.unzip_header, text="Change Scan Folder", command=self.browse_unzip_folder, width=150)
        self.btn_select_unzip.pack(side="right", padx=10)
        self.unzip_path_display = ctk.CTkLabel(self.page_unzip, text=f"Scanning: {self.unzip_scan_folder}", font=("Helvetica", 11, "italic"), text_color="gray")
        self.unzip_path_display.pack(padx=20, anchor="w")
        self.unzip_scroll = ctk.CTkScrollableFrame(self.page_unzip, label_text="Archives Found", fg_color="#1a1a1a")
        self.unzip_scroll.pack(fill="both", expand=True, padx=20, pady=10)
        self.unzip_controls = ctk.CTkFrame(self.page_unzip, fg_color="transparent")
        self.unzip_controls.pack(fill="x", padx=20, pady=10)
        self.refresh_unzip_btn = ctk.CTkButton(self.unzip_controls, text="Scan Folder", command=self.start_unzip_scan)
        self.refresh_unzip_btn.pack(side="left", expand=True, padx=5)
        self.unarchive_all_btn = ctk.CTkButton(self.unzip_controls, text="Unarchive All", fg_color="#2fa572", state="disabled", command=self.unarchive_all)
        self.unarchive_all_btn.pack(side="left", expand=True, padx=5)

        # PAGE: LAUNCHER
        self.page_launch = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        ctk.CTkLabel(self.page_launch, text="Quick Folder Launcher", font=("Helvetica", 24, "bold")).pack(pady=20)
        self.launch_grid = ctk.CTkFrame(self.page_launch, fg_color="transparent")
        self.launch_grid.pack(pady=10)
        self.refresh_launcher()

        # PAGE: STATS
        self.page_stats = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        self.stats_box = ctk.CTkTextbox(self.page_stats, font=("Consolas", 14))
        self.stats_box.pack(fill="both", expand=True, padx=20, pady=20)

        # PAGE: SETTINGS
        self.page_settings = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        ctk.CTkLabel(self.page_settings, text="Organization Target Folder", font=("Helvetica", 14, "bold")).pack(pady=(20, 5))
        self.path_entry = ctk.CTkEntry(self.page_settings, width=400)
        self.path_entry.insert(0, self.watch_folder)
        self.path_entry.pack(pady=5)
        self.browse_btn = ctk.CTkButton(self.page_settings, text="Browse Folder", command=self.browse_folder)
        self.browse_btn.pack(pady=5)
        ctk.CTkLabel(self.page_settings, text="Sorting Method", font=("Helvetica", 14, "bold")).pack(pady=(20, 5))
        self.sort_option = ctk.CTkSegmentedButton(self.page_settings, values=["Year Only", "Year/Month", "Year/Month/Day"])
        self.sort_option.set("Year Only")
        self.sort_option.pack(pady=10)
        ctk.CTkLabel(self.page_settings, text="UI Color Theme", font=("Helvetica", 14, "bold")).pack(pady=(20, 5))
        self.theme_menu = ctk.CTkOptionMenu(self.page_settings, values=list(THEMES.keys()), command=self.set_theme_name)
        self.theme_menu.pack(pady=10)

        # ADVANCED PAGE
        self.page_advanced = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        self.btn_dup = ctk.CTkButton(self.page_advanced, text="Scan Duplicates", command=self.start_dup_thread)
        self.btn_dup.pack(pady=20)
        self.prefix_entry = ctk.CTkEntry(self.page_advanced, placeholder_text="Prefix...")
        self.prefix_entry.pack(pady=5)
        self.btn_rename = ctk.CTkButton(self.page_advanced, text="Rename Misc", command=self.run_bulk_rename)
        self.btn_rename.pack(pady=5)

    def get_contrast_color(self, hex_color):
        hex_color = hex_color.lstrip('#')
        r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
        return "black" if luminance > 0.5 else "white"

    def set_theme_name(self, name):
        self.current_theme_name = name
        self.apply_global_theme()

    def apply_global_theme(self):
        theme = THEMES[self.current_theme_name]
        primary_text = self.get_contrast_color(theme["primary"])
        accent_text = self.get_contrast_color(theme["accent"])

        self.logo.configure(text_color=theme["primary"])
        self.sidebar.configure(fg_color=theme["sidebar"])
        self.content_frame.configure(border_color=theme["primary"])
        self.org_card.configure(border_color=theme["primary"])
        self.progress.configure(progress_color=theme["primary"])
        self.browse_btn.configure(fg_color=theme["primary"], text_color=primary_text)
        self.refresh_unzip_btn.configure(fg_color=theme["primary"], text_color=primary_text)
        self.btn_select_unzip.configure(fg_color=theme["primary"], text_color=primary_text)
        self.theme_menu.configure(fg_color=theme["primary"], button_color=theme["primary"], text_color=primary_text)
        self.sort_option.configure(selected_color=theme["primary"])
        self.btn_dup.configure(fg_color=theme["primary"], text_color=primary_text)
        self.btn_rename.configure(fg_color=theme["primary"], text_color=primary_text)
        self.btn_sweep.configure(fg_color=theme["accent"], hover_color=theme["primary"], text_color=accent_text)

    def browse_unzip_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.unzip_scan_folder = os.path.normpath(folder)
            self.unzip_path_display.configure(text=f"Scanning: {self.unzip_scan_folder}")

    def start_unzip_scan(self):
        self.refresh_unzip_btn.configure(state="disabled", text="Scanning...")
        self.unarchive_all_btn.configure(state="disabled")
        self.found_archives = []
        for widget in self.unzip_scroll.winfo_children():
            widget.destroy()
        threading.Thread(target=self.scan_folder_for_archives, daemon=True).start()

    def scan_folder_for_archives(self):
        theme = THEMES[self.current_theme_name]
        btn_text_color = self.get_contrast_color(theme["primary"])
        # FIXED: endswith requires a tuple for multiple values
        archive_exts = (".zip", ".rar", ".7z", ".tar", ".gz")
        
        try:
            for root, _, files in os.walk(self.unzip_scan_folder):
                for f in files:
                    if f.lower().endswith(archive_exts):
                        full_path = os.path.join(root, f)
                        self.found_archives.append(full_path)
                        self.after(0, lambda p=full_path: self.add_archive_item(p, theme["primary"], btn_text_color))
        except Exception as e:
            self.log(f"Scan Error: {e}")

        if not self.found_archives:
            self.after(0, lambda: ctk.CTkLabel(self.unzip_scroll, text="No archives found in this folder.").pack(pady=10))
        else:
            self.after(0, lambda: self.unarchive_all_btn.configure(state="normal"))
        
        self.after(0, lambda: self.refresh_unzip_btn.configure(state="normal", text="Scan Folder"))

    def add_archive_item(self, filepath, btn_color, text_color):
        item_frame = ctk.CTkFrame(self.unzip_scroll, fg_color="#252525")
        item_frame.pack(fill="x", pady=4, padx=5)
        text_container = ctk.CTkFrame(item_frame, fg_color="transparent")
        text_container.pack(side="left", fill="both", expand=True, padx=10, pady=5)
        ctk.CTkLabel(text_container, text=os.path.basename(filepath), font=("Helvetica", 12, "bold"), anchor="w").pack(fill="x")
        ctk.CTkLabel(text_container, text=filepath, font=("Helvetica", 9), text_color="gray", anchor="w").pack(fill="x")
        btn = ctk.CTkButton(item_frame, text="Extract", width=80, height=28,
                            fg_color=btn_color, text_color=text_color,
                            command=lambda p=filepath: self.extract_single(p))
        btn.pack(side="right", padx=10, pady=5)

    def extract_single(self, filepath):
        target = os.path.splitext(filepath)[0]
        # Handle cases where folder already exists to prevent zipfile errors
        if not os.path.exists(target):
            os.makedirs(target, exist_ok=True)
            
        try:
            # Note: zipfile only handles .zip. .rar/.7z require external libraries (rarfile/py7zr)
            if filepath.lower().endswith(".zip"):
                with zipfile.ZipFile(filepath, 'r') as z:
                    z.extractall(target)
                self.log(f"Extracted: {os.path.basename(filepath)}")
            else:
                self.log(f"Format not supported for auto-extract: {os.path.basename(filepath)}")
        except Exception as e:
            self.log(f"Error extracting {os.path.basename(filepath)}: {e}")

    def unarchive_all(self):
        if not self.found_archives: return
        self.unarchive_all_btn.configure(state="disabled", text="Extracting...")
        threading.Thread(target=self.run_unarchive_all_task, daemon=True).start()

    def run_unarchive_all_task(self):
        count = 0
        for path in self.found_archives:
            self.extract_single(path)
            count += 1
        self.log(f"Batch unarchive complete: {count} items processed.")
        self.after(0, lambda: self.unarchive_all_btn.configure(state="normal", text="Unarchive All"))

    def browse_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.watch_folder = os.path.normpath(folder)
            self.path_entry.delete(0, "end")
            self.path_entry.insert(0, self.watch_folder)
            self.folder_label.configure(text=f"Target: {self.watch_folder}")
            self.update_stats()
            self.refresh_launcher()

    def start_sweep_thread(self):
        threading.Thread(target=self.run_organizer_sweep, daemon=True).start()

    def run_organizer_sweep(self):
        self.btn_sweep.configure(state="disabled", text="Working...")
        search_targets = ['.'] + list(FILE_TYPES.keys()) + ["Misc"]
        moved = 0
        gran = self.sort_option.get()
        try:
            for i, target in enumerate(search_targets):
                self.progress.set((i + 1) / len(search_targets))
                path = os.path.join(self.watch_folder, target)
                if not os.path.exists(path): continue
                for f in os.listdir(path):
                    if f == "organizer_log.txt" or f == self.script_name: continue
                    fp = os.path.join(path, f)
                    if not os.path.isfile(fp): continue
                    ext = os.path.splitext(f)[1].lower()
                    cat = next((k for k, v in FILE_TYPES.items() if ext in v), "Misc")
                    mtime = time.localtime(os.stat(fp).st_mtime)
                    y, m, d = time.strftime("%Y", mtime), time.strftime("%B", mtime), time.strftime("%d", mtime)
                    dp = y if gran == "Year Only" else os.path.join(y, m) if gran == "Year/Month" else os.path.join(y, m, d)
                    dest = os.path.join(self.watch_folder, cat, dp)
                    if os.path.abspath(os.path.dirname(fp)) == os.path.abspath(dest): continue
                    os.makedirs(dest, exist_ok=True)
                    shutil.move(fp, os.path.join(dest, f))
                    self.last_move_history.append((fp, os.path.join(dest, f)))
                    moved += 1
            self.log(f"Sweep Finished: {moved} items organized.")
            self.undo_btn.configure(state="normal" if moved > 0 else "disabled")
            self.update_stats()
        except Exception as e: 
            self.log(f"Error: {e}")
        self.btn_sweep.configure(state="normal", text="START SWEEP")

    def refresh_launcher(self):
        for widget in self.launch_grid.winfo_children(): widget.destroy()
        theme = THEMES[self.current_theme_name]
        btn_text_color = self.get_contrast_color(theme["primary"])
        for i, cat in enumerate(list(FILE_TYPES.keys()) + ["Misc"]):
            p = os.path.join(self.watch_folder, cat)
            b = ctk.CTkButton(self.launch_grid, text=f"Open {cat}", width=160, height=100, 
                              fg_color=theme["primary"], text_color=btn_text_color,
                              command=lambda path=p: os.startfile(path) if os.path.exists(path) else None)
            b.grid(row=i//3, column=i%3, padx=15, pady=15)

    def log(self, msg):
        ts = time.strftime("%H:%M:%S")
        self.log_box.insert("end", f"[{ts}] {msg}\n")
        self.log_box.see("end")

    def update_stats(self):
        self.stats_box.delete("1.0", "end")
        res = f"--- STORAGE DASHBOARD ({self.watch_folder}) ---\n\n"
        for cat in list(FILE_TYPES.keys()) + ["Misc"]:
            p = os.path.join(self.watch_folder, cat)
            fc, sz = 0, 0
            if os.path.exists(p):
                for r, _, files in os.walk(p):
                    for f in files:
                        fc += 1
                        sz += os.path.getsize(os.path.join(r, f))
            res += f"{cat.ljust(12)}: {fc} Files ({sz/(1024*1024):.2f} MB)\n"
        self.stats_box.insert("1.0", res)

    def switch_page(self, page, nav_btn):
        for p in [self.page_org, self.page_unzip, self.page_launch, self.page_stats, self.page_advanced, self.page_settings]:
            p.pack_forget()
        for b in self.nav_buttons:
            b.configure(fg_color="transparent", text_color="gray")
        nav_btn.configure(fg_color="#333333", text_color="white")
        page.pack(fill="both", expand=True)

    def show_organizer(self): self.switch_page(self.page_org, self.btn_org)
    def show_unarchive(self): self.switch_page(self.page_unzip, self.btn_unzip)
    def show_launcher(self): self.switch_page(self.page_launch, self.btn_launch)
    def show_stats(self): self.switch_page(self.page_stats, self.btn_stats)
    def show_advanced(self): self.switch_page(self.page_advanced, self.btn_advanced)
    def show_settings(self): self.switch_page(self.page_settings, self.btn_settings)

    def start_dup_thread(self): threading.Thread(target=self.find_duplicates, daemon=True).start()
    def find_duplicates(self):
        self.log("Searching...")
        seen, dups = {}, []
        for r, _, files in os.walk(self.watch_folder):
            for f in files:
                p = os.path.join(r, f)
                try:
                    id = f"{f}_{os.path.getsize(p)}"
                    if id in seen: dups.append(f)
                    else: seen[id] = p
                except: pass
        self.log(f"Found {len(dups)} duplicates.")

    def run_bulk_rename(self):
        pre = self.prefix_entry.get()
        p = os.path.join(self.watch_folder, "Misc")
        if not pre or not os.path.exists(p): return
        for f in os.listdir(p):
            if os.path.isfile(os.path.join(p, f)):
                os.rename(os.path.join(p, f), os.path.join(p, f"{pre}{f}"))
        self.update_stats()

    def undo_last_sweep(self):
        for o, n in self.last_move_history:
            if os.path.exists(n): shutil.move(n, o)
        self.last_move_history = []
        self.undo_btn.configure(state="disabled")
        self.update_stats()

if __name__ == "__main__":
    app = App()
    app.mainloop()