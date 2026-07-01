"""
Tab UI builders for SIMS Application Tracker.
Each function builds one tab's widgets inside the given parent frame.
"""
import os
import threading
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime

from tracker_logic import process_tracker_files
from extractor_logic import run_extraction
from matcher_logic import match_csv_with_sims, build_check1_payload, build_check2_payload, create_logisys_csv, clean_cth

TEXT_LIGHT = "#666666"
BRAND_BLUE = "#0056b3"
TEXT_DARK = "#333333"

# ======================================================================
#  TAB 0: Instructions / User Guide
# ======================================================================
def build_instructions_tab(parent, app):
    # Main container
    main_frame = ttk.Frame(parent, padding=10)
    main_frame.pack(fill="both", expand=True)

    header = ttk.Label(main_frame, text=" How to use", font=("Segoe UI", 14, "bold"), foreground=BRAND_BLUE)
    header.pack(pady=(0, 10), anchor="w")

    sections = [
        {
            "title": "Docs Support Flow (Modules 1 & 2)",
            "usage": "Primary User: Docs Support Team",
            "tag_color": "#007bff",
            "items": [
                {
                    "name": "Module 1 (Ref & CSV Generator)",
                    "purpose": "Updates Job No. in Shakti & Skoda DSR. Generates the CSV input for the SIMS bot and flags other licence requirements (Even if no SIMS is required) in a separate Excel.",
                    "purpose_hi": "शक्ति और Skoda DSR में Job No. अपडेट करता है। SIMS bot के लिए CSV input जनरेट करता है और अगर कोई और licence requirement हो तो उसे अलग Excel में हाइलाइट करता है।"
                },
                {
                    "name": "Module 2 (Check 1 - Support)",
                    "purpose": "Confirms SIMS registration per line item and pushes payment details + registration date to Shakti.",
                    "purpose_hi": "हर line item का SIMS registration कन्फर्म करता है और payment details + registration date शक्ति में पुश करता है।"
                }
            ]
        },
        {
            "title": "Shared Utility (Module 3)",
            "usage": "Used by: Both Support & Docs Teams",
            "tag_color": "#28a745",
            "items": [
                {
                    "name": "Module 3 (SIMS PDF Extractor)",
                    "purpose": "Extracts SIMS certificate data (reg. no. & date) to prepare for Logisys CSV mapping.",
                    "purpose_hi": "SIMS certificates से reg. no. और date एक्सट्रैक्ट करता है — Logisys CSV mapping के लिए।"
                }
            ]
        },
        {
            "title": "Docs Team Finalization (Module 4)",
            "usage": "Primary User: Docs Team",
            "tag_color": "#fd7e14",
            "items": [
                {
                    "name": "Module 4 (Check 2 - Verification)",
                    "purpose": "Auto-assigns a unique SIMS reg. no. to each CSV line item (matched on CTH, SQC, qty) for Logisys upload, with manual override for discrepancies.",
                    "purpose_hi": "CTH, SQC qty मैच करके हर CSV line item को unique SIMS reg. no. ऑटो-असाइन करता है Logisys upload के लिए। कोई discrepancy हो तो manually adjust कर सकते हो।"
                }
            ]
        }
    ]

    for sec in sections:
        f = ttk.LabelFrame(main_frame, text=f" {sec['title']} ", padding=8)
        f.pack(fill="x", pady=4)
        
        tag_frame = ttk.Frame(f)
        tag_frame.pack(fill="x", pady=(0, 2))
        tk.Label(tag_frame, bg=sec['tag_color'], width=1, height=1).pack(side="left")
        ttk.Label(tag_frame, text=f"  {sec['usage']}", font=("Segoe UI", 9, "italic", "bold"), foreground=TEXT_LIGHT).pack(side="left")
        
        for item in sec['items']:
            item_f = ttk.Frame(f)
            item_f.pack(fill="x", pady=2)
            
            ttk.Label(item_f, text=item['name'], font=("Segoe UI", 10, "bold"), foreground=BRAND_BLUE).pack(anchor="w")
            
            p_text = f"Purpose: {item['purpose']}"
            ttk.Label(item_f, text=p_text, font=("Segoe UI", 9), foreground=TEXT_DARK).pack(anchor="w", padx=10)
            
            p_hi = f"उद्देश्य: {item['purpose_hi']}"
            ttk.Label(item_f, text=p_hi, font=("Segoe UI", 9), foreground="#CC5500").pack(anchor="w", padx=10)


def _add_placeholder(widget, var, text):
    var.set(text)
    widget.config(foreground=TEXT_LIGHT, font=("Segoe UI", 9, "italic"))
    
    def on_focus_in(e):
        if var.get() == text:
            var.set("")
            widget.config(foreground=TEXT_DARK, font=("Segoe UI", 9))
            
    def on_focus_out(e):
        if not var.get():
            var.set(text)
            widget.config(foreground=TEXT_LIGHT, font=("Segoe UI", 9, "italic"))
            
    widget.bind("<FocusIn>", on_focus_in)
    widget.bind("<FocusOut>", on_focus_out)
    
    def on_var_change(*args):
        if var.get() and var.get() != text:
            widget.config(foreground=TEXT_DARK, font=("Segoe UI", 9))
            # Keep FocusOut so that if they clear the text manually, the placeholder comes back
            
    var.trace_add("write", on_var_change)
    
def _add_copy_menu(tree):
    """Adds a right-click menu to copy data from the Treeview."""
    menu = tk.Menu(tree, tearoff=0)
    
    def copy_model():
        sel = tree.selection()
        if not sel: return
        values = tree.item(sel[0])['values']
        tree.clipboard_clear()
        tree.clipboard_append(str(values[0]))
        tree.update()

    def copy_cth():
        sel = tree.selection()
        if not sel: return
        values = tree.item(sel[0])['values']
        tree.clipboard_clear()
        tree.clipboard_append(str(values[1]))
        tree.update()

    def copy_row():
        sel = tree.selection()
        if not sel: return
        values = tree.item(sel[0])['values']
        text = " | ".join(str(v) for v in values)
        tree.clipboard_clear()
        tree.clipboard_append(text)
        tree.update()

    menu.add_command(label="Copy Model", command=copy_model)
    menu.add_command(label="Copy CTH", command=copy_cth)
    menu.add_separator()
    menu.add_command(label="Copy Entire Row", command=copy_row)

    def show_menu(event):
        item = tree.identify_row(event.y)
        if item:
            tree.selection_set(item)
            menu.post(event.x_root, event.y_root)

    tree.bind("<Button-3>", show_menu)


# ======================================================================
#  TAB 1: Reference & CSV Generator
# ======================================================================
def build_tab1(parent, app):
    app.job_no_var = tk.StringVar()
    app.mbl_var = tk.StringVar()
    app.master_var = tk.StringVar()
    app.invoice_var = tk.StringVar()
    app.output_dir_var = tk.StringVar()

    form = ttk.LabelFrame(parent, text=" File Selection & Job Details ", padding=20)
    form.pack(fill="x", padx=20, pady=10)
    form.columnconfigure(1, weight=1)

    app.tab1_method = tk.StringVar(value="item")
    app.tab1_method_display = tk.StringVar(value="Method: Auto-Detecting on Process...")
    method_frame = ttk.Frame(form)
    method_frame.grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 10))
    ttk.Label(method_frame, textvariable=app.tab1_method_display, font=("Segoe UI", 10, "bold"), foreground=BRAND_BLUE).pack(side="left", padx=5)

    ttk.Label(form, text="Job Number (5 digits):").grid(row=1, column=0, sticky="w", pady=8, padx=5)
    e_job = ttk.Entry(form, textvariable=app.job_no_var)
    e_job.grid(row=1, column=1, sticky="ew", pady=8)
    _add_placeholder(e_job, app.job_no_var, "Add proper job number. e.g. 55553 as it will get pushed to Shakti and DSR")

    ttk.Label(form, text="MBL (MAWB/MBL):").grid(row=2, column=0, sticky="w", pady=8, padx=5)
    e_mbl = ttk.Entry(form, textvariable=app.mbl_var)
    e_mbl.grid(row=2, column=1, sticky="ew", pady=8)
    _add_placeholder(e_mbl, app.mbl_var, "Enter proper MBL number as it will push job number to existing pre alert record")

    ttk.Label(form, text="Master Sheet (Excel/CSV):").grid(row=3, column=0, sticky="w", pady=8, padx=5)
    e_mst = ttk.Entry(form, textvariable=app.master_var)
    e_mst.grid(row=3, column=1, sticky="ew", pady=8)
    _add_placeholder(e_mst, app.master_var, "Select latest DHL Master Sheet (Download from google sheets)")
    ttk.Button(form, text="Browse", command=lambda: _browse_any(app.master_var, [("Excel/CSV", "*.xlsx *.xls *.csv")])).grid(row=3, column=2, padx=5)

    ttk.Label(form, text="Extracted Invoice (Excel/CSV):").grid(row=4, column=0, sticky="w", pady=8, padx=5)
    e_inv = ttk.Entry(form, textvariable=app.invoice_var)
    e_inv.grid(row=4, column=1, sticky="ew", pady=8)
    _add_placeholder(e_inv, app.invoice_var, "Select Extracted Invoice csv/excel file through Invoice Parsers")
    ttk.Button(form, text="Browse", command=lambda: _browse_file(app.invoice_var, app.output_dir_var, [("Excel/CSV", "*.xlsx *.xls *.csv")])).grid(row=4, column=2, padx=5)

    ttk.Label(form, text="Output Directory:").grid(row=5, column=0, sticky="w", pady=8, padx=5)
    e_out = ttk.Entry(form, textvariable=app.output_dir_var)
    e_out.grid(row=5, column=1, sticky="ew", pady=8)
    _add_placeholder(e_out, app.output_dir_var, "Select Output folder")
    ttk.Button(form, text="Browse", command=lambda: _browse_dir(app.output_dir_var)).grid(row=5, column=2, padx=5)

    app.tab1_status = tk.StringVar(value="Ready.")
    ttk.Label(parent, textvariable=app.tab1_status, font=("Segoe UI", 10, "italic"), foreground=TEXT_LIGHT).pack(pady=5)
    
    btn_frame1 = ttk.Frame(parent)
    btn_frame1.pack(pady=10)
    
    app.btn_tab1 = ttk.Button(btn_frame1, text="PROCESS & CREATE JOB", style="Primary.TButton", command=lambda: _run_tab1(app))
    app.btn_tab1.pack(side="left", padx=5)
    
    ttk.Button(btn_frame1, text="CLEAR", command=lambda: _clear_tab1(app)).pack(side="left", padx=5)


def _clear_tab1(app):
    app.job_no_var.set("")
    app.mbl_var.set("")
    app.master_var.set("")
    app.invoice_var.set("")
    app.output_dir_var.set("")
    app.tab1_status.set("Ready.")


def _run_tab1(app):
    job = app.job_no_var.get().strip()
    if not job.isdigit() or len(job) != 5 or job == "e.g. 55553":
        messagebox.showerror("Error", "Job number must be exactly 5 digits."); return
    mbl = app.mbl_var.get().strip()
    m, inv, out = app.master_var.get(), app.invoice_var.get(), app.output_dir_var.get()
    
    # Check against placeholders
    if m == "Select Master Sheet file" or inv == "Select Extracted Invoice file" or out == "Select Output folder" or mbl == "Enter MBL number":
        messagebox.showerror("Error", "Please fill all fields with real values."); return
        
    if not all([m, inv, out]):
        messagebox.showerror("Error", "Please fill all file fields."); return
    app.btn_tab1.config(state="disabled")
    app.tab1_status.set("Processing...")

    def worker():
        method = "item"
        skoda_user = ""
        if app.api:
            app.root.after(0, lambda: app.tab1_method_display.set("Method: Fetching from Shakti..."))
            skoda_user, reason = app.api.get_skoda_user_by_mbl(mbl)
            if not skoda_user:
                app.root.after(0, lambda r=reason: messagebox.showerror("Error", f"Cannot proceed.\n\n{r}"))
                app.root.after(0, lambda r=reason: app.tab1_status.set(f"Failed: {r.split(':')[0]}"))
                app.root.after(0, lambda: app.btn_tab1.config(state="normal"))
                return
            if skoda_user in ["Ranjit (PUNE)", "Ashish (CSN)"]:
                method = "hs"
            else:
                method = "item"
        
        def set_ui_method():
            app.tab1_method.set(method)
            disp = "HS Method" if method == "hs" else "Item Method"
            user_str = skoda_user if skoda_user else "None"
            app.tab1_method_display.set(f"Method: {disp} (User: {user_str})")
        app.root.after(0, set_ui_method)

        def upd(msg): app.root.after(0, lambda: app.tab1_status.set(msg))
        def err(e):
            err_msg = str(e)
            app.root.after(0, lambda m=err_msg: messagebox.showerror("Error", m))
            app.root.after(0, lambda: app.btn_tab1.config(state="normal"))
            
        def shakti_push_cb(items):
            if app.api:
                if method == "hs":
                    unique_items = []
                    seen_cth = set()
                    for item in items:
                        if item["CTH"] not in seen_cth:
                            seen_cth.add(item["CTH"])
                            new_item = {
                                "CTH": item.get("CTH", ""),
                                "SIMS_Code": item.get("SIMS_Code", "")
                            }
                            unique_items.append(new_item)
                    items = unique_items
                ok, msg = app.api.create_job_with_pre_alert(job, mbl, items)
                if ok:
                    app.api.trigger_sims_tracker_refresh()
                return ok, msg
            else:
                return True, "Offline mode (No API config)"

        def done(xls, csv, shakti_msg):
            fm = f"Done!\nExcel: {os.path.basename(xls)}\n"
            if csv: fm += f"CSV: {os.path.basename(csv)}\n"
            fm += f"\nShakti: {shakti_msg}"
            app.root.after(0, lambda: messagebox.showinfo("Success", fm))
            app.root.after(0, lambda: app.btn_tab1.config(state="normal"))
            app.root.after(0, lambda: app.tab1_status.set("Ready."))
            
        process_tracker_files(job, m, inv, out, upd, err, shakti_push_cb, done)

    threading.Thread(target=worker, daemon=True).start()


# ======================================================================
#  TAB 2: SIMS PDF Extractor
# ======================================================================
def build_tab2(parent, app):
    app.pdf_files = []
    app.ext_output_dir = tk.StringVar()
    app.ext_output_name = tk.StringVar(value=f"SIMS_Extracted_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    app.ext_progress = tk.DoubleVar(value=0)
    app.ext_status = tk.StringVar(value="Ready — Select PDF files.")

    form = ttk.LabelFrame(parent, text=" SIMS PDF Extraction ", padding=20)
    form.pack(fill="x", padx=20, pady=10)
    form.columnconfigure(1, weight=1)

    ttk.Button(form, text="Select SIMS Certificate  PDF Files", style="Primary.TButton", command=lambda: _select_pdfs(app)).grid(row=0, column=0, pady=8, padx=5)
    app.pdf_lbl = ttk.Label(form, text="No files selected.")
    app.pdf_lbl.grid(row=0, column=1, sticky="w", pady=8, padx=10)

    ttk.Label(form, text="Output Directory:").grid(row=1, column=0, sticky="w", pady=8, padx=5)
    e_ext_out = ttk.Entry(form, textvariable=app.ext_output_dir)
    e_ext_out.grid(row=1, column=1, sticky="ew", pady=8)
    _add_placeholder(e_ext_out, app.ext_output_dir, "Select Output folder for Excel")
    ttk.Button(form, text="Browse", command=lambda: _browse_dir(app.ext_output_dir)).grid(row=1, column=2, padx=5)

    ttk.Label(form, text="File Name:").grid(row=2, column=0, sticky="w", pady=8, padx=5)
    ttk.Entry(form, textvariable=app.ext_output_name).grid(row=2, column=1, sticky="ew", pady=8)
    ttk.Label(form, text=".xlsx").grid(row=2, column=2, sticky="w")

    pf = ttk.Frame(parent)
    pf.pack(fill="x", padx=20, pady=5)
    ttk.Progressbar(pf, variable=app.ext_progress, maximum=100).pack(fill="x", pady=5)
    ttk.Label(pf, textvariable=app.ext_status, font=("Segoe UI", 10, "italic"), foreground=TEXT_LIGHT).pack()

    btn_frame2 = ttk.Frame(parent)
    btn_frame2.pack(pady=10)

    app.btn_tab2 = ttk.Button(btn_frame2, text="START EXTRACTION", style="Primary.TButton", command=lambda: _run_tab2(app))
    app.btn_tab2.pack(side="left", padx=5)
    
    ttk.Button(btn_frame2, text="CLEAR", command=lambda: _clear_tab2(app)).pack(side="left", padx=5)


def _clear_tab2(app):
    app.pdf_files = []
    app.pdf_lbl.config(text="No files selected.")
    app.ext_output_dir.set("")
    app.ext_output_name.set("SIMS_Extracted")
    app.ext_status.set("Ready.")
    app.ext_progress.set(0)


def _select_pdfs(app):
    files = filedialog.askopenfilenames(filetypes=[("PDF files", "*.pdf")])
    if files:
        app.pdf_files = list(files)
        app.pdf_lbl.config(text=f"{len(app.pdf_files)} files selected.")
        app.ext_output_dir.set(os.path.dirname(app.pdf_files[0]))


def _run_tab2(app):
    if not app.pdf_files:
        messagebox.showwarning("Warning", "Select PDF files first."); return
    out_dir = app.ext_output_dir.get()
    if not out_dir or out_dir == "Select Output folder for Excel":
        messagebox.showwarning("Warning", "Select output directory."); return
    app.btn_tab2.config(state="disabled")
    name = app.ext_output_name.get().strip()
    if not name.endswith(".xlsx"): name += ".xlsx"
    out = os.path.join(app.ext_output_dir.get(), name)

    def prog(pct, msg):
        app.root.after(0, lambda: app.ext_progress.set(pct))
        app.root.after(0, lambda: app.ext_status.set(msg))
    def done(path):
        app.root.after(0, lambda: messagebox.showinfo("Success", f"Extracted to:\n{os.path.basename(path)}"))
        app.root.after(0, lambda: app.btn_tab2.config(state="normal"))
    def err(e):
        err_msg = str(e)
        app.root.after(0, lambda m=err_msg: messagebox.showerror("Error", m))
        app.root.after(0, lambda: app.btn_tab2.config(state="normal"))

    threading.Thread(target=run_extraction, args=(app.pdf_files, out, prog, done, err), daemon=True).start()


# ======================================================================
#  TAB 3: Check 1 — CSV + SIMS (Docs Support)
# ======================================================================
def build_tab3(parent, app):
    app.c1_method = tk.StringVar(value="item")
    app.c1_csv = tk.StringVar()
    app.c1_sims = tk.StringVar()
    app.c1_hs_job = tk.StringVar()
    app.c1_hs_mbl = tk.StringVar()
    app.c1_slips = [] # List of paths
    app.c1_slips_text = tk.StringVar(value="No files selected")
    app.c1_status = tk.StringVar(value="Ready.")
    app.c1_display = []
    app.c1_unused_pool = []  # Pool of unused SIMS codes

    form = ttk.LabelFrame(parent, text=" Check 1 — Docs Support ", padding=15)
    form.pack(fill="x", padx=20, pady=5)
    
    # Method Selection
    app.c1_method_display = tk.StringVar(value="Method: Auto-Detecting on Match...")
    method_frame = ttk.Frame(form)
    method_frame.pack(fill="x", pady=(0, 10))
    ttk.Label(method_frame, textvariable=app.c1_method_display, font=("Segoe UI", 10, "bold"), foreground=BRAND_BLUE).pack(side="left", padx=5)

    # ITEM FRAME
    app.c1_item_frame = ttk.Frame(form)
    app.c1_item_frame.pack(fill="x")
    app.c1_item_frame.columnconfigure(1, weight=1)

    ttk.Label(app.c1_item_frame, text="CSV (from Module 1):").grid(row=0, column=0, sticky="w", pady=5, padx=5)
    e_c1_csv = ttk.Entry(app.c1_item_frame, textvariable=app.c1_csv)
    e_c1_csv.grid(row=0, column=1, sticky="ew", pady=5)
    _add_placeholder(e_c1_csv, app.c1_csv, "Select Csv file generated and provided to bot as input file in Module 1")
    ttk.Button(app.c1_item_frame, text="Browse", command=lambda: _browse_any(app.c1_csv, [("CSV", "*.csv")])).grid(row=0, column=2, padx=5)

    ttk.Label(app.c1_item_frame, text="SIMS Extracted (Excel):").grid(row=1, column=0, sticky="w", pady=5, padx=5)
    e_c1_sims = ttk.Entry(app.c1_item_frame, textvariable=app.c1_sims)
    e_c1_sims.grid(row=1, column=1, sticky="ew", pady=5)
    _add_placeholder(e_c1_sims, app.c1_sims, "Select SIMS Extracted Excel file from Module 3")
    ttk.Button(app.c1_item_frame, text="Browse", command=lambda: _browse_any(app.c1_sims, [("Excel", "*.xlsx")])).grid(row=1, column=2, padx=5)



    # COMMON FRAME (Payment Receipts)
    app.c1_common_frame = ttk.Frame(form)
    app.c1_common_frame.pack(fill="x")
    app.c1_common_frame.columnconfigure(1, weight=1)

    def _browse_slips():
        paths = filedialog.askopenfilenames(filetypes=[("PDF", "*.pdf")])
        if paths:
            app.c1_slips = list(paths)
            app.c1_slips_text.set(f"{len(paths)} slips selected")

    ttk.Label(app.c1_common_frame, text="Payment Reciepts (PDF):").grid(row=0, column=0, sticky="w", pady=5, padx=5)
    e_c1_slips = ttk.Entry(app.c1_common_frame, textvariable=app.c1_slips_text, state="readonly")
    e_c1_slips.grid(row=0, column=1, sticky="ew", pady=5)
    _add_placeholder(e_c1_slips, app.c1_slips_text, "Select SIMS Payment Receipts PDF Files")
    ttk.Button(app.c1_common_frame, text="Browse", command=_browse_slips).grid(row=0, column=2, padx=5)

    # --- Manual Assignment Area (HS Method only) ---
    app.c1_assign_frame = ttk.Frame(form)
    
    ttk.Label(app.c1_assign_frame, text="Fix CTH / Assign:").pack(side="left", padx=5)
    app.c1_combo_unused = ttk.Combobox(app.c1_assign_frame, state="readonly", width=30)
    app.c1_combo_unused.pack(side="left", padx=5)
    
    app.btn_c1_assign = ttk.Button(app.c1_assign_frame, text="ASSIGN", command=lambda: _assign_sim_code_c1(app), state="disabled")
    app.btn_c1_assign.pack(side="left", padx=5)
    
    app.btn_c1_undo = ttk.Button(app.c1_assign_frame, text="UNDO", command=lambda: _undo_assign_sim_code_c1(app), state="disabled")
    app.btn_c1_undo.pack(side="left", padx=5)
    
    app.c1_hint_label = ttk.Label(app.c1_assign_frame, text="(Select a red row)", font=("Segoe UI", 8, "italic"))
    app.c1_hint_label.pack(side="left", padx=5)
    
    # PREVIEW FRAME
    app.c1_pv_frame = ttk.LabelFrame(parent, text=" Preview ", padding=5)
    app.c1_pv_frame.pack(fill="both", expand=True, padx=20, pady=5)

    cols = ("Model", "CTH", "SQC Qty", "SIMS Code")
    app.c1_tree = ttk.Treeview(app.c1_pv_frame, columns=cols, show="headings", height=8)
    for c in cols: app.c1_tree.heading(c, text=c)
    app.c1_tree.column("Model", width=200)
    app.c1_tree.column("CTH", width=100)
    app.c1_tree.column("SQC Qty", width=100)
    app.c1_tree.column("SIMS Code", width=200)
    app.c1_tree.tag_configure("missing", background="#ffcccc")
    sb = ttk.Scrollbar(app.c1_pv_frame, orient="vertical", command=app.c1_tree.yview)
    app.c1_tree.configure(yscrollcommand=sb.set)
    sb.pack(side="right", fill="y")
    app.c1_tree.pack(fill="both", expand=True)
    _add_copy_menu(app.c1_tree)
    
    app.c1_tree.bind("<<TreeviewSelect>>", lambda e: _on_tree_select_c1(app))


    # BUTTONS FRAME
    bf = ttk.Frame(parent)
    bf.pack(fill="x", padx=20, pady=5)
    ttk.Label(bf, textvariable=app.c1_status, font=("Segoe UI", 9, "italic"), foreground=TEXT_LIGHT).pack(side="left")
    
    app.btn_c1_push = ttk.Button(bf, text="PUSH CHECK 1", style="Primary.TButton", command=lambda: _push_c1(app), state="disabled")
    app.btn_c1_push.pack(side="right", padx=5)
    
    app.btn_c1_match = ttk.Button(bf, text="MATCH & PREVIEW", style="Primary.TButton", command=lambda: _match_c1(app))
    app.btn_c1_match.pack(side="right", padx=5)
    
    ttk.Button(bf, text="CLEAR", command=lambda: _clear_tab3(app)).pack(side="right", padx=5)
    
    # Initialize UI state
    _toggle_c1_method(app)

def _toggle_c1_method(app):
    method = app.c1_method.get()
    app.c1_item_frame.pack(fill="x", before=app.c1_common_frame)
    app.c1_assign_frame.forget()
        
    app.c1_pv_frame.pack(fill="both", expand=True, padx=20, pady=5, before=app.btn_c1_push.master)
    app.btn_c1_match.pack(side="right", padx=5, before=app.btn_c1_push)
    
    app.c1_status.set("Method changed. Please match again.")
    app.btn_c1_push.config(state="disabled")


def _clear_tab3(app):
    app.c1_csv.set("")
    app.c1_sims.set("")
    app.c1_slips = []
    app.c1_slips_text.set("No files selected")
    app.c1_status.set("Ready.")
    app.c1_display = []
    app.c1_unused_pool = []
    if hasattr(app, "c1_combo_unused"):
        app.c1_combo_unused.config(values=[])
        app.c1_combo_unused.set("")
        app.btn_c1_assign.config(state="disabled")
        app.btn_c1_undo.config(state="disabled")
    _refresh_tab3_tree(app)
    _toggle_c1_method(app)

def _update_c1_status(app):
    job = _extract_job_from_csv(app.c1_csv.get())
    miss = sum(1 for x in app.c1_display if x["missing"])
    extra = len(getattr(app, 'c1_unused_pool', []))
    job_label = f" (Job: {job})" if job else ""
    app.c1_status.set(f"Loaded {len(app.c1_display)} items. Missing: {miss} | Extra Certs: {extra}{job_label}")
    
    method = app.c1_method.get()
    can_push = len(app.c1_display) > 0 and miss == 0
    if method == "item" and extra > 0:
        can_push = False
        
    if can_push:
        app.btn_c1_push.config(state="normal")
    else:
        app.btn_c1_push.config(state="disabled")


def _on_tree_select_c1(app):
    sel = app.c1_tree.selection()
    if not sel:
        app.btn_c1_assign.config(state="disabled")
        app.btn_c1_undo.config(state="disabled")
        return
    idx = app.c1_tree.index(sel[0])
    item = app.c1_display[idx]
    if item["missing"]:
        app.btn_c1_assign.config(state="normal" if app.c1_unused_pool else "disabled")
        app.btn_c1_undo.config(state="disabled")
        app.c1_hint_label.config(text="(Ready to assign)")
    elif item.get("manually_assigned"):
        app.btn_c1_assign.config(state="disabled")
        app.btn_c1_undo.config(state="normal")
        app.c1_hint_label.config(text="(Manual - Undo enabled)")
    else:
        app.btn_c1_assign.config(state="disabled")
        app.btn_c1_undo.config(state="disabled")
        app.c1_hint_label.config(text="(Auto-matched)")

def _assign_sim_code_c1(app):
    sel = app.c1_tree.selection()
    if not sel: return
    idx = app.c1_tree.index(sel[0])
    code = app.c1_combo_unused.get()
    if not code: return
    app.c1_display[idx]["sim"] = code
    app.c1_display[idx]["missing"] = False
    app.c1_display[idx]["manually_assigned"] = True
    app.c1_unused_pool.remove(code)
    app.c1_combo_unused.config(values=app.c1_unused_pool)
    app.c1_combo_unused.set(app.c1_unused_pool[0] if app.c1_unused_pool else "")
    _refresh_tab3_tree(app)
    _update_c1_status(app)

def _undo_assign_sim_code_c1(app):
    sel = app.c1_tree.selection()
    if not sel: return
    idx = app.c1_tree.index(sel[0])
    item = app.c1_display[idx]
    if not item.get("manually_assigned"): return
    code = item["sim"]
    app.c1_unused_pool.append(code)
    app.c1_unused_pool.sort()
    app.c1_combo_unused.config(values=app.c1_unused_pool)
    item["sim"] = ""
    item["missing"] = True
    item["manually_assigned"] = False
    _refresh_tab3_tree(app)
    _update_c1_status(app)


def _refresh_tab3_tree(app):
    for i in app.c1_tree.get_children(): app.c1_tree.delete(i)
    # Sort again so missing are on top
    app.c1_display.sort(key=lambda x: x["missing"], reverse=True)
    for d in app.c1_display:
        tag = ("missing",) if d["missing"] else ()
        app.c1_tree.insert("", "end", values=(d["model"], d["cth"], d["sqc_qty"], d["sim"]), tags=tag)


def _extract_job_from_csv(csv_path: str) -> str:
    """Extract job number from CSV filename like IR55553.csv → 55553."""
    import re
    basename = os.path.basename(csv_path)  # IR55553.csv
    # Strict check: Must be IR followed by exactly 5 digits
    match = re.match(r'^IR(\d{5})\.csv$', basename)
    if match:
        return match.group(1)
    return ""


def _match_c1(app):
    csv_path = app.c1_csv.get()
    sims_path = app.c1_sims.get()
    if not csv_path or not sims_path or csv_path == "Select Bot CSV file" or sims_path == "Select Extracted Excel file":
        messagebox.showwarning("Warning", "Select both files."); return
    app.btn_c1_match.config(state="disabled")
    app.c1_status.set("Fetching Method from Shakti...")
    
    def worker():
        try:
            job = _extract_job_from_csv(csv_path)
            method = "item"
            skoda_user = ""
            if app.api and job:
                skoda_user, reason = app.api.get_skoda_user_by_job_no(job)
                if not skoda_user:
                    app.root.after(0, lambda r=reason: messagebox.showerror("Error", f"Cannot proceed.\n\n{r}"))
                    app.root.after(0, lambda: app.btn_c1_match.config(state="normal"))
                    app.root.after(0, lambda r=reason: app.c1_status.set(f"Failed: {r.split(':')[0]}"))
                    return
                if skoda_user in ["Ranjit (PUNE)", "Ashish (CSN)"]:
                    method = "hs"
                else:
                    method = "item"
            
            def update_ui():
                app.c1_method.set(method)
                disp = "HS Method" if method == "hs" else "Item Method"
                user_str = skoda_user if skoda_user else "None"
                app.c1_method_display.set(f"Method: {disp} (User: {user_str})")
                _toggle_c1_method(app)
                
                try:
                    is_hs = (method == "hs")
                    data, unused, _, _ = match_csv_with_sims(csv_path, sims_path, is_hs=is_hs)
                    
                    if method == "hs":
                        # Deduplicate by CTH for HS Method
                        unique_data = []
                        seen_cth = set()
                        for item in data:
                            cth = clean_cth(item["cth"])
                            if cth not in seen_cth:
                                seen_cth.add(cth)
                                unique_data.append(item)
                        data = unique_data
                        
                        # For HS Method, build the full pool of ALL SIMS codes from the Excel
                        import pandas as pd
                        df_sims_full = pd.read_excel(sims_path, keep_default_na=False)
                        all_sims_codes = []
                        for _, r in df_sims_full.iterrows():
                            sim = str(r.get('SIM Number', '')).strip()
                            if sim and "Error" not in sim and sim != "Not Found":
                                all_sims_codes.append(sim)
                        # Remove codes already auto-assigned to the unique set
                        used_in_unique = {item["sim"] for item in data if item["sim"]}
                        unused = [s for s in all_sims_codes if s not in used_in_unique]
                        
                    app.c1_display = data
                    app.c1_unused_pool = unused
                    if hasattr(app, "c1_combo_unused"):
                        app.c1_combo_unused.config(values=unused)
                        if unused: app.c1_combo_unused.current(0)
                        else: app.c1_combo_unused.set("")

                    _refresh_tab3_tree(app)
                    _update_c1_status(app)
                    if unused:
                        messagebox.showwarning("Extra Certificates", "Please check CSV it has less items or please check whether you have uploaded any extra certificate.\n\nThere are unused certificates remaining.")
                except Exception as e:
                    messagebox.showerror("Error", str(e))
                finally:
                    app.btn_c1_match.config(state="normal")
            
            app.root.after(0, update_ui)
        except Exception as e:
            app.root.after(0, lambda: messagebox.showerror("Error", str(e)))
            app.root.after(0, lambda: app.btn_c1_match.config(state="normal"))
            
    threading.Thread(target=worker, daemon=True).start()

from extractor_logic import extract_payment_slip_data

def _push_c1(app):
    method = app.c1_method.get()
    job = _extract_job_from_csv(app.c1_csv.get())
    
    if not job:
        messagebox.showerror("Error", "Could not extract Job Number from CSV filename.\nExpected format: IR55553.csv"); return
    
    if not app.c1_display:
        messagebox.showwarning("Warning", "Run Match first."); return
        
    miss = sum(1 for x in app.c1_display if x["missing"])
    if miss > 0:
        messagebox.showerror("Error", f"Cannot push. {miss} items are still missing SIMS codes."); return
        
    if method == "item":
        extra = len(getattr(app, 'c1_unused_pool', []))
        if extra > 0:
            messagebox.showerror("Error", f"Cannot push. Please check CSV it has less items or please check whether you have uploaded any extra certificate.\n\n{extra} extra unused certificates found."); return
    
    if not app.c1_slips:
        messagebox.showerror("Error", "Please upload at least one Payment Slip."); return

    app.btn_c1_push.config(state="disabled")

    def worker():
        try:
            # 1. Process Slips and Verify Amount
            slips_data = []
            total_paid = 0.0
            for path in app.c1_slips:
                data = extract_payment_slip_data(path)
                slips_data.append(data)
                total_paid += data["Amount"]
            
            # Payment amount check — only enforced for Item Method
            if method == "item":
                item_count = len(app.c1_display)
                expected_total = item_count * 750
                
                if abs(total_paid - expected_total) > 0.01:
                    app.root.after(0, lambda: messagebox.showerror("Payment Mismatch", 
                        f"Payment Mismatch Found!\n\n"
                        f"Total Items: {item_count}\n"
                        f"Expected Total: {expected_total} (750 x {item_count})\n"
                        f"Actual Paid: {total_paid}\n\n"
                        f"Push aborted. Please check your payment slips."))
                    return

            # 2. Push to Shakti (runs for BOTH Item Method and HS Method)
            rid = app.api.get_job_record_id(job)
            if rid:
                is_hs = (method == "hs")
                payload = build_check1_payload(job, app.c1_display, slips_data, is_hs=is_hs)
                ok, msg = app.api.update_job_record(rid, payload)
                if ok:
                    app.api.trigger_sims_tracker_refresh()
                app.root.after(0, lambda: messagebox.showinfo("Shakti", msg if ok else f"Failed: {msg}"))
            else:
                app.root.after(0, lambda: messagebox.showerror("Error", f"No SIMS Tracker record found for Job {job}."))

        except Exception as e:
            err_msg = str(e)
            app.root.after(0, lambda m=err_msg: messagebox.showerror("Error", m))
        finally:
            app.root.after(0, lambda: app.btn_c1_push.config(state="normal"))

    threading.Thread(target=worker, daemon=True).start()


# ======================================================================
#  TAB 4: Check 2 — Docs Team
# ======================================================================
def build_tab4(parent, app):
    app.c2_method = tk.StringVar(value="item")
    app.c2_job = tk.StringVar()
    app.c2_mbl = tk.StringVar()
    app.c2_csv = tk.StringVar()
    app.c2_sims = tk.StringVar()
    app.c2_status = tk.StringVar(value="Ready.")
    app.c2_display = []
    app.c2_unused_pool = []

    form = ttk.LabelFrame(parent, text=" Check 2 — Docs Team (Verification) ", padding=15)
    form.pack(fill="x", padx=20, pady=5)
    form.columnconfigure(1, weight=1)

    # Method Selection
    app.c2_method_display = tk.StringVar(value="Method: Auto-Detecting on Match...")
    c2_method_frame = ttk.Frame(form)
    c2_method_frame.grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 10))
    ttk.Label(c2_method_frame, textvariable=app.c2_method_display, font=("Segoe UI", 10, "bold"), foreground=BRAND_BLUE).pack(side="left", padx=5)

    # Job & MBL row
    jm_frame = ttk.Frame(form)
    jm_frame.grid(row=1, column=0, columnspan=3, sticky="ew", pady=5)
    ttk.Label(jm_frame, text="Job Number:").pack(side="left", padx=5)
    e_c2_job = ttk.Entry(jm_frame, textvariable=app.c2_job, width=15)
    e_c2_job.pack(side="left", padx=5)
    _add_placeholder(e_c2_job, app.c2_job, "e.g. 55553")
    
    ttk.Label(jm_frame, text="MBL:").pack(side="left", padx=(20, 5))
    e_c2_mbl = ttk.Entry(jm_frame, textvariable=app.c2_mbl, width=25)
    e_c2_mbl.pack(side="left", padx=5)
    _add_placeholder(e_c2_mbl, app.c2_mbl, "Enter MBL number")

    ttk.Label(form, text="Item Report (CSV):").grid(row=2, column=0, sticky="w", pady=5, padx=5)
    e_c2_csv = ttk.Entry(form, textvariable=app.c2_csv)
    e_c2_csv.grid(row=2, column=1, sticky="ew", pady=5)
    _add_placeholder(e_c2_csv, app.c2_csv, "Select your CSV file which you make for logisys upload")
    ttk.Button(form, text="Browse", command=lambda: _browse_any_c2_csv(app)).grid(row=2, column=2, padx=5)

    ttk.Label(form, text="SIMS Extracted (Excel):").grid(row=3, column=0, sticky="w", pady=5, padx=5)
    e_c2_sims = ttk.Entry(form, textvariable=app.c2_sims)
    e_c2_sims.grid(row=3, column=1, sticky="ew", pady=5)
    _add_placeholder(e_c2_sims, app.c2_sims, "Select SIMS Extracted Excel file from Module 3")
    ttk.Button(form, text="Browse", command=lambda: _browse_any(app.c2_sims, [("Excel", "*.xlsx")])).grid(row=3, column=2, padx=5)

    # --- Manual Assignment Area (Item Method only) ---
    app.c2_assign_frame = ttk.Frame(form)
    app.c2_assign_frame.grid(row=4, column=0, columnspan=3, sticky="ew", pady=10)
    
    ttk.Label(app.c2_assign_frame, text="Fix CTH / Assign:").pack(side="left", padx=5)
    app.c2_combo_unused = ttk.Combobox(app.c2_assign_frame, state="readonly", width=30)
    app.c2_combo_unused.pack(side="left", padx=5)
    
    app.btn_c2_assign = ttk.Button(app.c2_assign_frame, text="ASSIGN", command=lambda: _assign_sim_code_c2(app), state="disabled")
    app.btn_c2_assign.pack(side="left", padx=5)
    
    app.btn_c2_undo = ttk.Button(app.c2_assign_frame, text="UNDO", command=lambda: _undo_assign_sim_code_c2(app), state="disabled")
    app.btn_c2_undo.pack(side="left", padx=5)
    
    app.c2_hint_label = ttk.Label(app.c2_assign_frame, text="(Select a red row)", font=("Segoe UI", 8, "italic"))
    app.c2_hint_label.pack(side="left", padx=5)

    pv = ttk.LabelFrame(parent, text=" Preview ", padding=5)
    pv.pack(fill="both", expand=True, padx=20, pady=5)

    cols = ("Model", "CTH", "SQC Qty", "SIMS Code")
    app.c2_tree = ttk.Treeview(pv, columns=cols, show="headings", height=8)
    for c in cols: app.c2_tree.heading(c, text=c)
    app.c2_tree.column("Model", width=200)
    app.c2_tree.column("CTH", width=100)
    app.c2_tree.column("SQC Qty", width=100)
    app.c2_tree.column("SIMS Code", width=200)
    app.c2_tree.tag_configure("missing", background="#ffcccc")
    sb = ttk.Scrollbar(pv, orient="vertical", command=app.c2_tree.yview)
    app.c2_tree.configure(yscrollcommand=sb.set)
    sb.pack(side="right", fill="y")
    app.c2_tree.pack(fill="both", expand=True)
    _add_copy_menu(app.c2_tree)

    app.c2_tree.bind("<<TreeviewSelect>>", lambda e: _on_tree_select_c2(app))

    bf = ttk.Frame(parent)
    bf.pack(fill="x", padx=20, pady=5)
    ttk.Label(bf, textvariable=app.c2_status, font=("Segoe UI", 9, "italic"), foreground=TEXT_LIGHT).pack(side="left")
    app.btn_c2_push = ttk.Button(bf, text="PUSH CHECK 2 & LOGISYS CSV", style="Primary.TButton", command=lambda: _push_c2(app), state="disabled")
    app.btn_c2_push.pack(side="right", padx=5)
    ttk.Button(bf, text="MATCH & VERIFY", style="Primary.TButton", command=lambda: _match_c2(app)).pack(side="right", padx=5)
    ttk.Button(bf, text="CLEAR", command=lambda: _clear_tab4(app)).pack(side="right", padx=5)

    # Initialize UI state
    _toggle_c2_method(app)


def _toggle_c2_method(app):
    pass


def _clear_tab4(app):
    app.c2_method.set("item")
    app.c2_job.set("")
    app.c2_mbl.set("")
    app.c2_csv.set("")
    app.c2_sims.set("")
    app.c2_status.set("Ready.")
    app.c2_display = []
    app.c2_unused_pool = []
    app.c2_combo_unused.config(values=[])
    app.c2_combo_unused.set("")
    app.btn_c2_assign.config(state="disabled")
    app.btn_c2_undo.config(state="disabled")
    _refresh_tab4_tree(app)
    app.btn_c2_push.config(state="disabled")
    _toggle_c2_method(app)

def _on_tree_select_c2(app):
    sel = app.c2_tree.selection()
    if not sel:
        app.btn_c2_assign.config(state="disabled")
        app.btn_c2_undo.config(state="disabled")
        return
    idx = app.c2_tree.index(sel[0])
    item = app.c2_display[idx]
    if item["missing"]:
        app.btn_c2_assign.config(state="normal" if app.c2_unused_pool else "disabled")
        app.btn_c2_undo.config(state="disabled")
        app.c2_hint_label.config(text="(Ready to assign)")
    elif item["manually_assigned"]:
        app.btn_c2_assign.config(state="disabled")
        app.btn_c2_undo.config(state="normal")
        app.c2_hint_label.config(text="(Manual - Undo enabled)")
    else:
        app.btn_c2_assign.config(state="disabled")
        app.btn_c2_undo.config(state="disabled")
        app.c2_hint_label.config(text="(Auto-matched)")


def _assign_sim_code_c2(app):
    sel = app.c2_tree.selection()
    if not sel: return
    idx = app.c2_tree.index(sel[0])
    code = app.c2_combo_unused.get()
    if not code: return
    app.c2_display[idx]["sim"] = code
    app.c2_display[idx]["missing"] = False
    app.c2_display[idx]["manually_assigned"] = True
    app.c2_unused_pool.remove(code)
    app.c2_combo_unused.config(values=app.c2_unused_pool)
    app.c2_combo_unused.set(app.c2_unused_pool[0] if app.c2_unused_pool else "")
    _refresh_tab4_tree(app)
    _update_c2_status(app)


def _undo_assign_sim_code_c2(app):
    sel = app.c2_tree.selection()
    if not sel: return
    idx = app.c2_tree.index(sel[0])
    item = app.c2_display[idx]
    if not item["manually_assigned"]: return
    code = item["sim"]
    app.c2_unused_pool.append(code)
    app.c2_unused_pool.sort()
    app.c2_combo_unused.config(values=app.c2_unused_pool)
    item["sim"] = ""
    item["missing"] = True
    item["manually_assigned"] = False
    _refresh_tab4_tree(app)
    _update_c2_status(app)


def _refresh_tab4_tree(app):
    for i in app.c2_tree.get_children(): app.c2_tree.delete(i)
    app.c2_display.sort(key=lambda x: x["missing"], reverse=True)
    for d in app.c2_display:
        tag = ("missing",) if d["missing"] else ()
        app.c2_tree.insert("", "end", values=(d["model"], d["cth"], d["sqc_qty"], d["sim"]), tags=tag)


def _update_c2_status(app):
    job = app.c2_job.get().strip()
    miss = sum(1 for x in app.c2_display if x["missing"])
    extra = len(getattr(app, 'c2_unused_pool', []))
    job_label = f" (Job: {job})" if job else ""
    app.c2_status.set(f"Verified {len(app.c2_display)} items. Missing: {miss} | Extra Certs: {extra}{job_label}")
    
    method = app.c2_method.get()
    can_push = len(app.c2_display) > 0 and miss == 0
    if method == "item" and extra > 0:
        can_push = False
        
    if can_push:
        app.btn_c2_push.config(state="normal")
    else:
        app.btn_c2_push.config(state="disabled")


def _match_c2(app):
    csv_path = app.c2_csv.get()
    sims_path = app.c2_sims.get()
    if not csv_path or not sims_path or csv_path == "Select Bot CSV file" or sims_path == "Select Extracted Excel file":
        messagebox.showwarning("Warning", "Select both files."); return
    job = app.c2_job.get().strip()
    if not job or job == "e.g. 55553":
        messagebox.showwarning("Warning", "Please enter Job Number first to detect method."); return

    app.c2_status.set("Fetching Method from Shakti...")
    
    def worker():
        try:
            method = "item"
            skoda_user = ""
            if app.api and job:
                skoda_user, reason = app.api.get_skoda_user_by_job_no(job)
                if not skoda_user:
                    app.root.after(0, lambda r=reason: messagebox.showerror("Error", f"Cannot proceed.\n\n{r}"))
                    app.root.after(0, lambda r=reason: app.c2_status.set(f"Failed: {r.split(':')[0]}"))
                    return
                if skoda_user in ["Ranjit (PUNE)", "Ashish (CSN)"]:
                    method = "hs"
                else:
                    method = "item"
            
            def update_ui():
                app.c2_method.set(method)
                disp = "HS Method" if method == "hs" else "Item Method"
                user_str = skoda_user if skoda_user else "None"
                app.c2_method_display.set(f"Method: {disp} (User: {user_str})")
                _toggle_c2_method(app)
                
                try:
                    is_hs = (method == "hs")
                    data, unused, _, _ = match_csv_with_sims(csv_path, sims_path, is_hs=is_hs)
                    
                    if method == "hs":
                        # Deduplicate: keep only the first item per unique CTH
                        unique_data = []
                        seen_cth = set()
                        for item in data:
                            cth = clean_cth(item["cth"])
                            if cth not in seen_cth:
                                seen_cth.add(cth)
                                unique_data.append(item)
                        data = unique_data
                        # For HS Method, build the full pool of ALL SIMS codes from the Excel
                        import pandas as pd
                        df_sims_full = pd.read_excel(sims_path, keep_default_na=False)
                        all_sims_codes = []
                        for _, r in df_sims_full.iterrows():
                            sim = str(r.get('SIM Number', '')).strip()
                            if sim and "Error" not in sim and sim != "Not Found":
                                all_sims_codes.append(sim)
                        # Remove codes already auto-assigned to the unique set
                        used_in_unique = {item["sim"] for item in data if item["sim"]}
                        unused = [s for s in all_sims_codes if s not in used_in_unique]
                    
                    app.c2_display = data
                    app.c2_unused_pool = unused
                    app.c2_combo_unused.config(values=unused)
                    if unused: app.c2_combo_unused.current(0)
                    else: app.c2_combo_unused.set("")
                    _refresh_tab4_tree(app)
                    _update_c2_status(app)
                    if unused:
                        messagebox.showwarning("Extra Certificates", "Please check CSV it has less items or please check whether you have uploaded any extra certificate.\n\nThere are unused certificates remaining.")
                except Exception as e:
                    messagebox.showerror("Error", str(e))
            app.root.after(0, update_ui)
        except Exception as e:
            app.root.after(0, lambda: messagebox.showerror("Error", str(e)))
            
    threading.Thread(target=worker, daemon=True).start()


def _push_c2(app):
    job = app.c2_job.get().strip()
    mbl = app.c2_mbl.get().strip()
    csv_file = app.c2_csv.get()
    
    if not job or job == "e.g. 55553" or not mbl or mbl == "Enter MBL number":
        messagebox.showerror("Error", "Please enter valid Job Number and MBL."); return
    
    # Validation: 5 digit job number
    if not job.isdigit() or len(job) != 5:
        messagebox.showerror("Error", "Job number must be exactly 5 digits."); return
        
    if not app.c2_display:
        messagebox.showwarning("Warning", "No 72, 73, or 86 items found in this CSV to push."); return
    
    miss = sum(1 for x in app.c2_display if x["missing"])
    if miss > 0:
        messagebox.showerror("Error", f"Cannot push. {miss} items are still missing SIMS codes."); return
        
    method = app.c2_method.get()
    if method == "item":
        extra = len(getattr(app, 'c2_unused_pool', []))
        if extra > 0:
            messagebox.showerror("Error", f"Cannot push. Please check CSV it has less items or please check whether you have uploaded any extra certificate.\n\n{extra} extra unused certificates found."); return

    app.btn_c2_push.config(state="disabled")
    
    def worker():
        try:
            # 1. Shakti Update
            is_hs = (app.c2_method.get() == "hs")
            payload = build_check2_payload(app.c2_display, is_hs=is_hs)
            rid = app.api.get_job_record_id_with_mbl(job, mbl)
            shakti_msg = "Skipped"
            if rid:
                ok, msg = app.api.update_job_record(rid, payload)
                if ok:
                    app.api.trigger_sims_tracker_refresh()
                shakti_msg = msg if ok else f"Failed: {msg}"
            else:
                ok = False
                shakti_msg = f"Job {job} record not found or MBL mismatch."

            # 2. Logisys CSV (ONLY if Shakti push is successful)
            logisys_path_msg = "Not generated due to Shakti failure."
            if ok:
                out_dir = os.path.dirname(app.c2_csv.get())
                logisys_path = os.path.join(out_dir, f"{job}_Logisys_Ready.csv")
                # Pass HS flag to generate appropriate columns
                create_logisys_csv(app.c2_csv.get(), logisys_path, app.c2_display, is_hs=is_hs)
                logisys_path_msg = os.path.basename(logisys_path)
            
            final_msg = f"Check 2 Complete!\n\nShakti: {shakti_msg}\nLogisys CSV: {logisys_path_msg}"
            app.root.after(0, lambda: messagebox.showinfo("Success", final_msg))
            
        except Exception as e:
            err_msg = str(e)
            app.root.after(0, lambda m=err_msg: messagebox.showerror("Error", m))
        finally:
            app.root.after(0, lambda: app.btn_c2_push.config(state="normal"))

    threading.Thread(target=worker, daemon=True).start()


# ── Shared helpers ──
def _browse_any_c2_csv(app):
    p = filedialog.askopenfilename(filetypes=[("CSV", "*.csv")])
    if p:
        app.c2_csv.set(p)

def _browse_file(var, fallback_dir=None, ftypes=None):
    if ftypes is None:
        ftypes = [("Excel files", "*.xlsx *.xls")]
    p = filedialog.askopenfilename(filetypes=ftypes)
    if p:
        var.set(p)
        # Always update fallback_dir if it's the invoice being selected
        if fallback_dir: fallback_dir.set(os.path.dirname(p))

def _browse_any(var, ftypes):
    p = filedialog.askopenfilename(filetypes=ftypes)
    if p: var.set(p)

def _browse_dir(var):
    p = filedialog.askdirectory()
    if p: var.set(p)
