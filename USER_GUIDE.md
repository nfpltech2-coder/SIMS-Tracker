# SIMS Application Tracker - User Guide

## Introduction
The SIMS Application Tracker automates the processing of SIMS (Steel Import Monitoring System) certificates and matches them against daily status reports and invoice data. It pushes missing items and matches to Zoho Shakti and generates logisys-ready CSVs.

## How to Use

### 1. Launching the App
Simply double-click the `SIMS_Tracker.exe` file. The application will launch a graphical interface.

### 2. The Workflow (Step-by-Step)

#### Module 1: File Selection & Job Details
1. **Job Number**: Enter a 5-digit job number (e.g. 55553). This will be pushed to Shakti.
2. **MBL**: Enter the MAWB/MBL. 
3. **Master Sheet**: Select the DHL Master Sheet (Excel/CSV).
4. **Extracted Invoice**: Select the invoice extracted via Invoice Parsers.
5. **Output Directory**: Select where to save output files.
6. **PROCESS & CREATE JOB**: Click to process. The system detects if it's "Item Method" or "HS Method" based on the Skoda User from Shakti.

#### Module 2: SIMS PDF Extraction
1. **Select SIMS Certificate PDF Files**: Select the PDFs to extract from.
2. **Output Directory / File Name**: Specify where to save the extracted Excel file.
3. **START EXTRACTION**: Converts the PDFs into a combined Excel spreadsheet of SIMS certificates.

#### Module 3: Check 1 — Docs Support
1. **CSV (from Module 1)**: Select the CSV generated from Module 1.
2. **SIMS Extracted (Excel)**: Select the Excel file generated from Module 2.
3. **Payment Receipts (PDF)**: Select payment receipt PDFs.
4. **MATCH & PREVIEW**: Matches the items against the SIMS codes. For HS Method, the "Fix CTH/Assign" section is hidden as codes are bulk-assigned based on CTH.
5. **Fix CTH / Assign**: (Item Method Only) Select missing items from the table and manually assign an unused SIMS code.
6. **PUSH CHECK 1**: Submits the matched records to Shakti.

#### Module 4: Check 2 — Docs Team
1. **Job Number & MBL**: Enter the 5-digit Job Number and the exact MBL.
2. **Item Report (CSV)**: Select the logisys-ready CSV.
3. **SIMS Extracted (Excel)**: Select the extracted Excel from Module 2.
4. **MATCH & VERIFY**: Verifies all items have SIMS codes. For HS Method, manual assignment is hidden.
5. **Fix CTH / Assign**: (Item Method Only) Manually assign missing codes.
6. **PUSH CHECK 2 & LOGISYS CSV**: Submits final verifications to Shakti and generates the `_Logisys_Ready.csv`.

## Interface Reference

| Control / Input | Description | Expected Format |
| :--- | :--- | :--- |
| Job Number | Links to Zoho Shakti | 5 digits (e.g. 55553) |
| MBL | Search key for Pre-Alert records | Exact MBL String |
| Master Sheet | Export from DHL system | .xls, .xlsx, .csv |
| Extracted Invoice | Result of parsing step | .xls, .xlsx, .csv |
| SIMS PDFs | Raw SIMS Certificates | .pdf |
| Payment Receipts | Proof of payment for validation | .pdf |

## Troubleshooting & Validations

If you see an error, check this table:

| Message | What it means | Solution |
| :--- | :--- | :--- |
| **"Job number must be exactly 5 digits."** | Invalid job number length. | Check your entry and try again. |
| **"Skoda User is empty in Shakti for this MBL. Cannot proceed."** | The API found the record but the user field is blank. | Update the Pre-Alert record in Zoho Shakti with a valid Skoda User. |
| **"Payment Mismatch Found!"** | The total amount from receipts doesn't match the expected `750 * Item Count`. | Verify you uploaded all receipts or check item count (Item Method only). |
| **"Cannot push. X items are still missing SIMS codes."** | Some items failed auto-matching. | Use the "Fix CTH / Assign" area to manually assign codes, or add the missing certificate. |
| **"Extra unused certificates found."** | There are leftover certificates in the pool. | Ensure you aren't uploading extra PDFs or missing items in the CSV. |
