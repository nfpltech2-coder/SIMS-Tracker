# SIMS Application Tracker

The **SIMS Application Tracker** is a Python-based desktop application designed to streamline the extraction, mapping, and pushing of SIMS (Steel Import Monitoring System) certificates for DHL/Skoda logistics workflows.

## Features
- **PDF Extraction**: Automatically parses complex SIMS certificate PDFs and extracts key tabular data into structured Excel formats.
- **Smart Matching Engine**: 
  - Supports **Item Method** (1:1 mapping based on SQC quantity and CTH).
  - Supports **HS Method** (Deduplicated mapping based solely on CTH for specific Skoda Users like Ranjit and Ashish).
- **Zoho Shakti API Integration**: Pushes matched data, missing items, and status updates directly to Zoho Shakti.
- **Payment Verification**: Extracts and validates payment amounts from receipt PDFs to ensure exact matching (`750 * Item Count`).
- **Logisys CSV Export**: Automatically formats data for downstream ingestion into the Logisys system.

## Setup Instructions
1. Install Python 3.10+.
2. Activate virtual environment: `.\venv\Scripts\activate`
3. Install requirements: `pip install -r requirements.txt`
4. Run application: `python main.py`

## User Guide
See `USER_GUIDE.md` for a complete walkthrough of the application's interface and troubleshooting steps.
