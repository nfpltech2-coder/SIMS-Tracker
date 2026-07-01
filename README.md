# SIMS Application Tracker

The **SIMS Application Tracker** is a Python-based desktop application designed to streamline the extraction, mapping, and pushing of SIMS (Steel Import Monitoring System) certificates for DHL/Skoda logistics workflows.

## Features
- **PDF Extraction**: Automatically parses complex SIMS certificate PDFs and extracts key tabular data into structured Excel formats.
- **Smart Matching Engine**: 
  - Supports **Item Method**: Matches line items using the quantity-based formula `CTH / (SQC_Qty / 1000)`.
  - Supports **HS Method**: Matches line items solely by CTH (no quantity calculations).
  - Uses robust **CTH Normalization**: Cleans whitespace, trailing `.0` (from floats), and all periods/dots to ensure formats like `7208.51.10` and `72085110.0` match correctly.
- **Zoho Shakti API Integration**: Pushes matched data, missing items, and status updates directly to Zoho Shakti.
- **Payment Verification**: Extracts and validates payment amounts from receipt PDFs to ensure exact matching (`750 * Item Count`).
- **Logisys CSV Export**: Enriches the original Item Report CSV by appending two new columns (`SIMS Code` and `SIMS Category`) to all rows, preserving all original columns and rows exactly as they were in the input file.

## Setup Instructions
1. Install Python 3.10+.
2. Run application: `python main.py`

## User Guide
See `USER_GUIDE.md` for a complete walkthrough of the application's interface and troubleshooting steps.
