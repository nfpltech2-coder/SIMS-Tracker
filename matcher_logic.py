"""
Matching Logic for Tab 3 (Check 1).
Matches SIMS extracted data against CSV using Merged to Compare keys.
"""
import os
import decimal
import pandas as pd
from typing import List, Dict, Tuple, Optional

from extractor_logic import format_qty_for_merge


# ======================================================================
#  CHECK 1: CSV (from Tab 1) + SIMS Excel (from Tab 2)
#  Docs Support team matches the CSV items with SIMS extracted data.
# ======================================================================

def clean_excel_formula(val):
    """Removes Excel formula wrappers like '="VALUE"'."""
    s = str(val).strip()
    if s.startswith('="') and s.endswith('"'):
        return s[2:-1]
    return val

def match_csv_with_sims(
    csv_path: str,
    sims_path: str,
    is_hs: bool = False
) -> Tuple[List[Dict], List[str], pd.DataFrame, pd.DataFrame]:
    """
    Matches CSV (Inv No, CTH, Model, SQC_Qty) with SIMS Excel.
    If is_hs is True, matches only on CTH.
    Returns: (display_data, unused_sims, df_csv, df_sims)
    """
    df_csv = pd.read_csv(csv_path, keep_default_na=False)
    df_sims = pd.read_excel(sims_path, keep_default_na=False)
    
    # Cleanup formulas
    for df in [df_csv, df_sims]:
        for col in df.select_dtypes(include=['object']):
            df[col] = df[col].apply(clean_excel_formula)

    # Filter CSV for 72/73/86 only
    df_csv['CTH_str'] = df_csv['CTH'].astype(str).str.strip()
    df_csv = df_csv[df_csv['CTH_str'].str.startswith(('72', '73', '86'))].copy()
    if 'CTH_str' in df_csv.columns: del df_csv['CTH_str']

    # Build merged key for CSV: CTH/SQC_Qty (Divide by 1000 to match SIMS MT) or just CTH for HS
    def calc_csv_merged(row):
        cth = str(row.get('CTH', '')).strip().split('.')[0]
        if is_hs:
            return cth
        raw_qty = row.get('SQC_Qty', 0)
        try:
            processed_qty = float(str(raw_qty).replace(',', '')) / 1000
        except (ValueError, TypeError):
            processed_qty = raw_qty
        return f"{cth}/{format_qty_for_merge(processed_qty)}"

    df_csv['Merged to Compare'] = df_csv.apply(calc_csv_merged, axis=1)

    # Build SIMS pool: {merged_key: [(sim_number, sim_date), ...]}
    sims_pool = {}
    all_sims = []
    for _, r in df_sims.iterrows():
        # SIMS Extracted Excel typically names the CTH column 'HS Code'
        cth_sims = str(r.get('HS Code', r.get('CTH', ''))).strip().split('.')[0]
        if is_hs:
            key = cth_sims
        else:
            key = str(r.get('Merged to Compare', '')).strip()
            
        sim = str(r.get('SIM Number', '')).strip()
        raw_date = r.get('SIMS Date')
        # Ensure date is a string or datetime object we can handle later
        if key and sim and "Error" not in sim and sim != "Not Found":
            sims_pool.setdefault(key, []).append((sim, raw_date))
            all_sims.append(sim)

    display_data = []
    used_sims = []
    for _, r in df_csv.iterrows():
        key = str(r.get('Merged to Compare', ''))
        sim_code = ""
        sim_date = None
        if key in sims_pool and sims_pool[key]:
            if is_hs:
                # For HS Method, a single SIMS code covers all items with the same CTH.
                # Don't pop it from the pool so other rows with this CTH can use it too.
                sim_code, sim_date = sims_pool[key][0]
                if sim_code not in used_sims:
                    used_sims.append(sim_code)
            else:
                sim_code, sim_date = sims_pool[key].pop(0)
                used_sims.append(sim_code)

        display_data.append({
            "inv_no": str(r.get('Inv No', '')),
            "model": str(r.get('Model', '')),
            "cth": str(r.get('CTH', '')),
            "sqc_qty": str(r.get('SQC_Qty', '')),
            "sim": sim_code,
            "sim_date": sim_date,
            "missing": not bool(sim_code),
            "manually_assigned": False,
        })

    # Identify unused sims
    unused_sims = [s for s in all_sims if s not in used_sims]

    # Sort: missing items first
    display_data.sort(key=lambda x: x["missing"], reverse=True)
    return display_data, unused_sims, df_csv, df_sims


from datetime import datetime

def build_check1_payload(job_no: str, display_data: List[Dict], payment_slips: List[Dict] = None, is_hs: bool = False) -> Dict:
    """Builds the Shakti payload for Check 1.
    
    Pushes all matched items to Job_Items subform.
    Does NOT touch Missing_Items — Zoho keeps them as-is from Tab 1.
    Identifies the latest SIMS Date among matched items.
    Includes Payment_Details subform if provided.
    """
    job_items = []
    all_dates = []
    for item in display_data:
        entry = {
            "Inv_No": "" if is_hs else item["inv_no"],
            "CTH": item["cth"],
            "Model": "" if is_hs else item["model"],
            "SQC_Qty": "" if is_hs else item["sqc_qty"],
            "SIMS_Code": item["sim"],
        }
        job_items.append(entry)
        if item.get("sim_date") and pd.notna(item["sim_date"]):
            try:
                # Ensure it's a datetime object
                if isinstance(item["sim_date"], datetime):
                    all_dates.append(item["sim_date"])
                else:
                    dt = pd.to_datetime(item["sim_date"])
                    if pd.notna(dt):
                        all_dates.append(dt)
            except:
                pass

    latest_date_str = ""
    if all_dates:
        latest_date = max(all_dates)
        latest_date_str = latest_date.strftime("%d-%b-%Y").upper() # Format for Zoho (e.g. 12-MAY-2026)

    # Build Payment Subform
    payment_entries = []
    if payment_slips:
        for p in payment_slips:
            payment_entries.append({
                "Date_field": p["Date"],
                "Amount": p["Amount"]
            })

    payload = {
        "data": {
            "Job_Number": job_no,
            "SIMS_Filing_Status": "Check 1 Done",
            "SIMS_Registration_Date": latest_date_str,
            "Job_Items": job_items,
        }
    }
    
    if payment_entries:
        payload["data"]["Payment_Details"] = payment_entries
        
    return payload


def build_check2_payload(display_data: List[Dict], is_hs: bool = False) -> Dict:
    """Builds the Shakti payload for Check 2 (Docs Team)."""
    items = []
    for item in display_data:
        items.append({
            "Inv_No": "" if is_hs else item["inv_no"],
            "CTH": item["cth"],
            "Model": "" if is_hs else item["model"],
            "SQC_Qty": "" if is_hs else item["sqc_qty"],
            "SIMS_Code": item["sim"],
        })

    return {
        "data": {
            "SIMS_Filing_Status": "Check 2 Done",
            "Job_Items_Check_2": items
        }
    }


def create_logisys_csv(input_csv_path: str, output_path: str, display_data: List[Dict], is_hs: bool = False):
    """Generates the Logisys ready upload CSV by enriching the original Item Report CSV.
    
    For HS Method (is_hs=True): Only outputs CTH, SIMS Code, SIMS Category — one row per unique CTH.
    For Item Method: Outputs all original columns plus SIMS Code, SIMS Category.
    """
    from collections import defaultdict

    if is_hs:
        # HS Method: build one row per unique CTH with its assigned SIMS code
        rows = []
        seen_cth = set()
        for d in display_data:
            cth = str(d.get("cth", "")).strip().split('.')[0]
            if cth in seen_cth:
                continue
            seen_cth.add(cth)
            sim = str(d.get("sim", "")).strip()
            rows.append({
                "CTH": cth,
                "SIMS Code": sim,
                "SIMS Category": "SIUNAPL" if sim else "",
            })
        df_out = pd.DataFrame(rows, columns=["CTH", "SIMS Code", "SIMS Category"])
        df_out.to_csv(output_path, index=False)
        return output_path

    # Item Method: enrich the original CSV with SIMS Code and SIMS Category
    # Use auto-delimiter detection to keep all original columns (e.g. BRAND)
    df_orig = None
    for sep in [',', ';', '\t']:
        try:
            temp_df = pd.read_csv(input_csv_path, sep=sep, keep_default_na=False, low_memory=False)
            if len(temp_df.columns) > 1:
                df_orig = temp_df
                break
        except:
            continue
    if df_orig is None:
        df_orig = pd.read_csv(input_csv_path, keep_default_na=False, low_memory=False)

    # Create a queue-based mapping dictionary using the exact 'Merged to Compare' logic
    sims_mapping = defaultdict(list)
    for d in display_data:
        if d.get("sim"):
            cth = str(d.get("cth", "")).strip().split('.')[0]
            raw_qty = d.get("sqc_qty", 0)
            try:
                processed_qty = float(str(raw_qty).replace(',', '')) / 1000
            except (ValueError, TypeError):
                processed_qty = raw_qty
            merged_key = f"{cth}/{format_qty_for_merge(processed_qty)}"
            sims_mapping[merged_key].append(d["sim"])

    # Assign SIMS Code row-by-row to consume the queue
    def assign_sims(row):
        cth_str = str(row.get('CTH', '')).strip()
        if not cth_str.startswith(('72', '73', '86')):
            return ""
        cth = cth_str.split('.')[0]
        raw_qty = row.get('SQC_Qty', 0)
        try:
            processed_qty = float(str(raw_qty).replace(',', '')) / 1000
        except (ValueError, TypeError):
            processed_qty = raw_qty
        merged_key = f"{cth}/{format_qty_for_merge(processed_qty)}"
        if merged_key in sims_mapping and sims_mapping[merged_key]:
            return sims_mapping[merged_key].pop(0)
        return ""

    df_orig['SIMS Code'] = df_orig.apply(assign_sims, axis=1)
    df_orig['SIMS Category'] = df_orig['SIMS Code'].apply(lambda x: "SIUNAPL" if str(x).strip() else "")

    df_orig.to_csv(output_path, index=False)
    return output_path
