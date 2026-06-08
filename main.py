import os
import sys
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
from dotenv import load_dotenv

try:
    from zoho_api import ShaktiCreatorAPI
except ImportError:
    ShaktiCreatorAPI = None

from tabs import build_instructions_tab, build_tab1, build_tab2, build_tab3, build_tab4

BRAND_BLUE = "#0056b3"
BG_WHITE = "#ffffff"
TEXT_DARK = "#333333"
TEXT_LIGHT = "#666666"


def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


class SIMSApplicationTracker:
    def __init__(self, root):
        self.root = root
        self.root.title("SIMS Application Tracker - Nagarkot Forwarders")
        self.root.geometry("1100x750")
        self.root.state("zoomed")
        self.root.configure(bg=BG_WHITE)

        load_dotenv()
        self.api = ShaktiCreatorAPI() if ShaktiCreatorAPI else None

        self._setup_styles()
        self._create_header()
        self._create_tab_icons()
        self._create_notebook()
        self._create_footer()

    def _create_tab_icons(self):
        # Create wide colored background images to simulate colored tab headers
        # We use a larger height and width to ensure it fills the tab area
        def create_bg(color, width=220, height=40):
            img = Image.new("RGB", (width, height), color)
            return ImageTk.PhotoImage(img)
        
        self.bg_blue = create_bg("#b3e5fc")   # Light Blue
        self.bg_green = create_bg("#c8e6c9")  # Light Green
        self.bg_orange = create_bg("#ffe0b2") # Light Orange

    def _setup_styles(self):
        s = ttk.Style()
        s.theme_use("clam")
        s.configure("TFrame", background=BG_WHITE)
        s.configure("TLabel", background=BG_WHITE, font=("Segoe UI", 10), foreground=TEXT_DARK)
        s.configure("Header.TLabel", font=("Helvetica", 24, "bold"), foreground=BRAND_BLUE)
        s.configure("Footer.TLabel", font=("Segoe UI", 9), foreground=TEXT_LIGHT)
        s.configure("TNotebook", background=BG_WHITE, borderwidth=0)
        s.configure("TNotebook.Tab", 
                    padding=[0, 0], 
                    font=("Segoe UI", 10, "bold"), 
                    background="#e1e1e1",
                    borderwidth=1)
        
        s.map("TNotebook.Tab",
              background=[("selected", "#ffffff")],
              foreground=[("selected", BRAND_BLUE)])
        s.configure("TLabelframe", background=BG_WHITE)
        s.configure("TLabelframe.Label", background=BG_WHITE, foreground=BRAND_BLUE, font=("Segoe UI", 11, "bold"))
        s.configure("Primary.TButton", font=("Segoe UI", 10, "bold"), foreground="white", background=BRAND_BLUE)
        s.map("Primary.TButton", background=[("active", "#004494")])

    def _create_header(self):
        hdr = ttk.Frame(self.root)
        hdr.pack(fill="x", padx=40, pady=(20, 5))
        hdr.columnconfigure(0, weight=0)
        hdr.columnconfigure(1, weight=1)

        try:
            logo_path = resource_path("Nagarkot Logo.png")
            if os.path.exists(logo_path):
                img = Image.open(logo_path)
                h = 25
                w = int((h / float(img.size[1])) * float(img.size[0]))
                img = img.resize((w, h), Image.Resampling.LANCZOS)
                self.logo_img = ImageTk.PhotoImage(img)
                ttk.Label(hdr, image=self.logo_img).grid(row=0, column=0, rowspan=2, padx=(0, 30))
        except Exception:
            pass

        ttk.Label(hdr, text="SIMS Application Tracker", style="Header.TLabel").grid(row=0, column=1, sticky="w")

    def _create_notebook(self):
        nb = ttk.Notebook(self.root)
        nb.pack(fill="both", expand=True, padx=40, pady=10)

        t0 = ttk.Frame(nb); nb.add(t0, text="   Instructions   ")
        t1 = ttk.Frame(nb); nb.add(t1, text=" Module 1 (Ref & CSV) ", image=self.bg_blue, compound="center")
        t3 = ttk.Frame(nb); nb.add(t3, text=" Module 2 (Check 1) ", image=self.bg_blue, compound="center")
        t2 = ttk.Frame(nb); nb.add(t2, text=" Module 3 (Extractor) ", image=self.bg_green, compound="center")
        t4 = ttk.Frame(nb); nb.add(t4, text=" Module 4 (Check 2) ", image=self.bg_orange, compound="center")

        build_instructions_tab(t0, self)
        build_tab1(t1, self)
        build_tab3(t3, self)
        build_tab2(t2, self)
        build_tab4(t4, self)

    def _create_footer(self):
        f = ttk.Frame(self.root)
        f.pack(fill="x", side="bottom", padx=40, pady=10)
        ttk.Label(f, text="© Nagarkot Forwarders Pvt Ltd", style="Footer.TLabel").pack(side="left")
        ttk.Label(f, text="v2.0.0", style="Footer.TLabel").pack(side="right")


if __name__ == "__main__":
    root = tk.Tk()
    SIMSApplicationTracker(root)
    root.mainloop()
