import os
import time
import sys
import json
import logging
import requests
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Load environment variables from the directory next to the exe
if getattr(sys, 'frozen', False):
    _env_dir = Path(sys._MEIPASS)
else:
    _env_dir = Path(__file__).resolve().parent
load_dotenv(_env_dir / ".env")

class ShaktiCreatorAPI:
    """Handles authentication and pushing/updating records to Shakti (Zoho) Creator API."""
    
    def __init__(self):
        self.client_id = os.getenv("ZOHO_CLIENT_ID")
        self.client_secret = os.getenv("ZOHO_CLIENT_SECRET")
        self.refresh_token = os.getenv("ZOHO_REFRESH_TOKEN")
        self.account_owner = os.getenv("ZOHO_ACCOUNT_OWNER")
        self.app_link_name = os.getenv("ZOHO_APP_LINK_NAME")
        
        # Link names per new requirement audit
        self.form_link_name = os.getenv("ZOHO_FORM_LINK_NAME", "SIMS_Tracker")
        self.report_link_name = os.getenv("ZOHO_REPORT_LINK_NAME", "SIMS_Tracker_Report")
        
        # Pre-Alert form/report for MBL lookup
        self.pre_alert_form = os.getenv("ZOHO_PRE_ALERT_FORM", "Book_Pre_Alert")
        self.pre_alert_report = os.getenv("ZOHO_PRE_ALERT_REPORT", "Book_Pre_Alert_Report")
        
        self.auth_domain = os.getenv("ZOHO_AUTH_DOMAIN", "accounts.zoho.in")
        self.api_domain = os.getenv("ZOHO_API_DOMAIN", "creator.zoho.in")
        
        self.access_token = None
        self.token_fetched_at = 0.0

    def ensure_valid_token(self) -> bool:
        """Checks if a valid token exists and has not expired. Refreshes if needed."""
        now = time.time()
        # Zoho access tokens expire after 1 hour (3600 seconds).
        # We refresh it after 50 minutes (3000 seconds) to be 100% safe.
        if self.access_token and (now - self.token_fetched_at < 3000):
            return True
        return self._get_access_token()

    def is_configured(self) -> bool:
        """Check if minimum required credentials are set in .env."""
        return all([
            self.client_id, self.client_secret, self.refresh_token,
            self.account_owner, self.app_link_name, self.form_link_name
        ])

    def _get_access_token(self) -> bool:
        """Fetch a new OAuth2 Access Token using the Refresh Token."""
        url = f"https://{self.auth_domain}/oauth/v2/token"
        params = {
            "refresh_token": self.refresh_token,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "refresh_token"
        }
        try:
            response = requests.post(url, params=params)
            response.raise_for_status()
            data = response.json()
            if "access_token" in data:
                self.access_token = data["access_token"]
                self.token_fetched_at = time.time()
                logger.info("Shakti Access Token refreshed successfully.")
                return True
            else:
                logger.error(f"Failed to get access token: {data}")
                return False
        except Exception as e:
            logger.error(f"Error fetching Shakti access token: {e}")
            return False

    def create_job_record(self, job_no: str) -> tuple[bool, str]:
        """Tab 1: Create the initial job record with 'Pending' status."""
        if not self.is_configured():
            return False, "Shakti credentials not configured in .env file."
        if not self.ensure_valid_token():
            return False, "Failed to authenticate with Shakti."
            
        url = f"https://{self.api_domain}/api/v2/{self.account_owner}/{self.app_link_name}/form/{self.form_link_name}"
        headers = {
            "Authorization": f"Zoho-oauthtoken {self.access_token}",
            "Content-Type": "application/json"
        }
        
        # Push just the Job Number and Status
        payload = {
            "data": {
                "Job_Number": job_no,
                "SIMS_Filing_Status": "Pending"
            }
        }

        try:
            response = requests.post(url, headers=headers, json=payload)
            resp_data = response.json()
            
            msg = resp_data.get('message', '')
            code = str(resp_data.get('code', ''))
            
            if code == "3000" or "Added Successfully" in msg:
                return True, "Job successfully created in Shakti!"
            
            return False, f"Shakti API Error: {msg if msg else 'Code ' + code}"
                
        except requests.exceptions.RequestException as e:
            return False, f"Network error: {str(e)}"

    def get_job_record_id_with_mbl(self, job_no: str, expected_mbl: str) -> Optional[str]:
        """Find SIMS Tracker record ID and strictly verify the MBL matches expected_mbl."""
        if not self.ensure_valid_token():
            return None
        
        # Step 1: Find Pre-Alert by Job_No
        url = (f"https://{self.api_domain}/api/v2/{self.account_owner}/{self.app_link_name}"
               f"/report/{self.pre_alert_report}?criteria=(Job_No == {job_no})")
        headers = {"Authorization": f"Zoho-oauthtoken {self.access_token}"}
        
        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                data_list = response.json().get('data', [])
                if data_list and len(data_list) > 0:
                    mbl = str(data_list[0].get('MAWB_MBL', '')).strip()
                    if mbl and mbl.upper() == expected_mbl.strip().upper():
                        # Step 2: Find SIMS Tracker by MBL
                        record_id, _ = self._find_sims_record_by_mbl(mbl)
                        return record_id
                    elif mbl:
                        raise Exception(f"MBL Mismatch! Pre-Alert has MBL: {mbl}, but you entered: {expected_mbl}")
            return None
        except Exception as e:
            raise Exception(f"Failed to fetch Job Record: {str(e)}")

    def get_job_record_id(self, job_no: str) -> Optional[str]:
        """Find SIMS Tracker record ID by searching Pre-Alert Job_No → MBL → SIMS Tracker."""
        if not self.ensure_valid_token():
            return None
        
        # Step 1: Find Pre-Alert by Job_No
        url = (f"https://{self.api_domain}/api/v2/{self.account_owner}/{self.app_link_name}"
               f"/report/{self.pre_alert_report}?criteria=(Job_No == {job_no})")
        headers = {"Authorization": f"Zoho-oauthtoken {self.access_token}"}
        
        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                data_list = response.json().get('data', [])
                if data_list and len(data_list) > 0:
                    mbl = data_list[0].get('MAWB_MBL', '')
                    if mbl:
                        # Step 2: Find SIMS Tracker by MBL
                        record_id, _ = self._find_sims_record_by_mbl(str(mbl))
                        return record_id
            return None
        except Exception as e:
            raise Exception(f"Failed to fetch Job Record: {str(e)}")

    def get_record_data(self, record_id: str) -> Optional[Dict]:
        """Fetch full record data including subforms like Missing_Items."""
        if not self.ensure_valid_token():
            return None

        url = (f"https://{self.api_domain}/api/v2/{self.account_owner}/{self.app_link_name}"
               f"/report/{self.report_link_name}/{record_id}")
        headers = {"Authorization": f"Zoho-oauthtoken {self.access_token}"}

        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                return response.json().get('data', {})
            return None
        except Exception as e:
            logger.error(f"Failed to fetch record data: {e}")
            return None

    def update_job_record(self, record_id: str, data_payload: dict) -> tuple[bool, str]:
        """Tab 3: Updates the matched job record with new status and Subform items using PATCH."""
        if not self.is_configured():
            return False, "Shakti credentials not configured."
        if not self.ensure_valid_token():
            return False, "Failed to authenticate with Shakti."
            
        url = f"https://{self.api_domain}/api/v2/{self.account_owner}/{self.app_link_name}/report/{self.report_link_name}/{record_id}"
        headers = {
            "Authorization": f"Zoho-oauthtoken {self.access_token}",
            "Content-Type": "application/json"
        }

        # The payload is exactly the subforms and updated status fields
        payload = {
            "data": data_payload["data"]
        }

        try:
            response = requests.patch(url, headers=headers, json=payload)
            resp_data = response.json()
            
            msg = resp_data.get('message', '')
            code = str(resp_data.get('code', ''))
            
            if code == "3000" or "Updated Successfully" in msg:
                return True, "Successfully updated Job and pushed items to Shakti!"
            
            # Check for nested subform or form-level errors
            results = resp_data.get("result", [])
            err_details = []
            if results and isinstance(results, list):
                for res in results:
                    if res.get("code") != 3000:
                        err_details.append(str(res.get("error", "Unknown error")))
            elif resp_data.get("error"):
                err_details.append(str(resp_data.get("error")))
                
            detailed_err = " | ".join(err_details) if err_details else msg
            
            # Save exact error to file for debugging
            import json
            with open("shakti_error_log.txt", "w") as f:
                json.dump(resp_data, f, indent=4)
                
            return False, f"Shakti API Error: Code {code} - {detailed_err} (See shakti_error_log.txt)"
                
        except requests.exceptions.RequestException as e:
            return False, f"Network error: {str(e)}"

    def trigger_sims_tracker_refresh(self):
        """Hits the public Zoho refresh URL to trigger backend automation logic."""
        url = "https://www.zohoapis.in/creator/custom/nisarg_nagarkot182/SIMS_Tracker_for_Tool?publickey=wqwQgrYUj9wSPVWWKmASj9148"
        try:
            # We use a timeout to avoid hanging the UI thread if the trigger is slow
            requests.get(url, timeout=10)
            print("SIMS Tracker Refresh Triggered Successfully.")
        except Exception as e:
            print(f"Failed to trigger SIMS Tracker Refresh: {str(e)}")

    def find_pre_alert_by_mbl(self, mbl: str) -> Optional[str]:
        """Search Book Pre-Alert by MAWB_MBL and return its record ID."""
        if not self.ensure_valid_token():
            return None
        
        url = (f"https://{self.api_domain}/api/v2/{self.account_owner}/{self.app_link_name}"
               f"/report/{self.pre_alert_report}?criteria=(MAWB_MBL == \"{mbl}\")")
        headers = {"Authorization": f"Zoho-oauthtoken {self.access_token}"}
        
        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                data_list = response.json().get('data', [])
                if data_list and len(data_list) > 0:
                    return str(data_list[0].get('ID'))
            return None
        except Exception as e:
            logger.error(f"Pre-Alert lookup failed: {e}")
            return None

    def get_skoda_user_by_mbl(self, mbl: str) -> tuple[Optional[str], str]:
        """Fetch Skoda_User from Pre-Alert using MBL.
        Returns (skoda_user, error_reason). error_reason is empty on success.
        """
        if not self.ensure_valid_token():
            logger.error("Skoda User lookup failed: Auth token refresh failed.")
            return None, "AUTH_FAILED: Could not authenticate with Shakti. Check .env credentials."
        
        url = (f"https://{self.api_domain}/api/v2/{self.account_owner}/{self.app_link_name}"
               f"/report/{self.pre_alert_report}?criteria=(MAWB_MBL == \"{mbl}\")")
        headers = {"Authorization": f"Zoho-oauthtoken {self.access_token}"}
        
        try:
            response = requests.get(url, headers=headers)
            logger.info(f"Skoda User by MBL '{mbl}': HTTP {response.status_code}")
            if response.status_code == 200:
                data_list = response.json().get('data', [])
                if data_list and len(data_list) > 0:
                    raw_value = data_list[0].get('Skoda_User')
                    user = str(raw_value).strip() if raw_value else ""
                    logger.info(f"Skoda User raw value: {repr(raw_value)} -> '{user}'")
                    if user:
                        return user, ""
                    return None, "EMPTY_FIELD: Pre-Alert record found but Skoda_User field is blank."
                return None, f"NO_RECORD: No Pre-Alert record found for MBL '{mbl}'."
            elif response.status_code == 401:
                return None, "AUTH_EXPIRED: Shakti token expired or invalid. Restart the app."
            else:
                return None, f"API_ERROR: Shakti returned HTTP {response.status_code}."
        except Exception as e:
            logger.error(f"Skoda User lookup failed: {e}")
            return None, f"NETWORK_ERROR: {e}"

    def get_skoda_user_by_job_no(self, job_no: str) -> tuple[Optional[str], str]:
        """Fetch Skoda_User from Pre-Alert using Job_No.
        Returns (skoda_user, error_reason). error_reason is empty on success.
        """
        if not self.ensure_valid_token():
            logger.error("Skoda User lookup failed: Auth token refresh failed.")
            return None, "AUTH_FAILED: Could not authenticate with Shakti. Check .env credentials."
        
        url = (f"https://{self.api_domain}/api/v2/{self.account_owner}/{self.app_link_name}"
               f"/report/{self.pre_alert_report}?criteria=(Job_No == {job_no})")
        headers = {"Authorization": f"Zoho-oauthtoken {self.access_token}"}
        
        try:
            response = requests.get(url, headers=headers)
            logger.info(f"Skoda User by Job '{job_no}': HTTP {response.status_code}")
            if response.status_code == 200:
                data_list = response.json().get('data', [])
                if data_list and len(data_list) > 0:
                    raw_value = data_list[0].get('Skoda_User')
                    user = str(raw_value).strip() if raw_value else ""
                    logger.info(f"Skoda User raw value: {repr(raw_value)} -> '{user}'")
                    if user:
                        return user, ""
                    return None, "EMPTY_FIELD: Pre-Alert record found but Skoda_User field is blank."
                return None, f"NO_RECORD: No Pre-Alert record found for Job No '{job_no}'."
            elif response.status_code == 401:
                return None, "AUTH_EXPIRED: Shakti token expired or invalid. Restart the app."
            else:
                return None, f"API_ERROR: Shakti returned HTTP {response.status_code}."
        except Exception as e:
            logger.error(f"Skoda User lookup failed: {e}")
            return None, f"NETWORK_ERROR: {e}"

    def update_pre_alert_job_no(self, pre_alert_id: str, job_no: str) -> tuple[bool, str]:
        """Update the Job_No field on a Book Pre-Alert record."""
        if not self.ensure_valid_token():
            return False, "Auth failed"
        
        url = (f"https://{self.api_domain}/api/v2/{self.account_owner}/{self.app_link_name}"
               f"/report/{self.pre_alert_report}/{pre_alert_id}")
        headers = {
            "Authorization": f"Zoho-oauthtoken {self.access_token}",
            "Content-Type": "application/json"
        }
        payload = {"data": {"Job_No": int(job_no)}}
        
        try:
            response = requests.patch(url, headers=headers, json=payload)
            resp_data = response.json()
            code = str(resp_data.get('code', ''))
            if code == "3000":
                return True, "Pre-Alert Job_No updated!"
            # Surface the full error for debugging
            msg = resp_data.get('message', '')
            # Check for nested errors (Zoho sometimes puts errors in 'result')
            result = resp_data.get('result', [])
            if result and isinstance(result, list):
                nested = result[0].get('error', '') if result else ''
                if nested:
                    msg = f"{msg} | {nested}"
            if not msg:
                msg = f"API Response: {resp_data}"
            return False, msg
        except Exception as e:
            return False, str(e)

    def create_job_with_pre_alert(self, job_no: str, mbl: str, missing_items: list) -> tuple[bool, str]:
        """Update Pre-Alert Job_No if empty, otherwise verify it matches job_no, and push Missing Items to SIMS Tracker."""
        if not self.is_configured():
            return False, "Shakti credentials not configured."
        if not self.ensure_valid_token():
            return False, "Auth failed."
        
        if not mbl:
            return False, "MBL is required."
        
        # --- STEP 1: Find Pre-Alert by MBL and check/verify Job_No ---
        pre_alert_id = self.find_pre_alert_by_mbl(mbl)
        if not pre_alert_id:
            return False, f"No Pre-Alert record found with MBL: {mbl}"
        
        # Check if Pre-Alert already has a Job_No
        existing_job = self._get_pre_alert_job_no(pre_alert_id)
        if existing_job:
            # Verify that the existing Job Number matches the user input
            if str(existing_job).strip() != str(job_no).strip():
                return False, f"MBL {mbl} already has Job Number '{existing_job}' in Pre-Alert, but you entered '{job_no}'."
            logger.info(f"Job Number '{job_no}' matches existing Pre-Alert Job Number. Skipping update step.")
        else:
            # --- STEP 2: Update Job_No on Pre-Alert (Fallback for backward compatibility if empty) ---
            pa_ok, pa_msg = self.update_pre_alert_job_no(pre_alert_id, job_no)
            if not pa_ok:
                return False, f"Failed to update Pre-Alert: {pa_msg}"
        
        # --- STEP 3: Find SIMS Tracker record linked to this MBL ---
        record_id, _ = self._find_sims_record_by_mbl(mbl)
        if not record_id:
            return False, f"Pre-Alert verified but no SIMS Tracker record found for MBL: {mbl}"
        
        # --- STEP 4: Push only Missing Items + Status to SIMS Tracker (NO Job_Number) ---
        url = (f"https://{self.api_domain}/api/v2/{self.account_owner}/{self.app_link_name}"
               f"/report/{self.report_link_name}/{record_id}")
        headers = {
            "Authorization": f"Zoho-oauthtoken {self.access_token}",
            "Content-Type": "application/json"
        }
        
        status = "Pending" if missing_items else "No SIMS"
        payload = {
            "data": {
                "SIMS_Filing_Status": status,
                "Missing_Items": missing_items
            }
        }
        
        try:
            response = requests.patch(url, headers=headers, json=payload)
            resp_data = response.json()
            code = str(resp_data.get('code', ''))
            msg = resp_data.get('message', '')
            if code == "3000" or "Updated Successfully" in msg:
                return True, f"Job {job_no} → Pre-Alert verified & items pushed to SIMS Tracker!"
            return False, f"SIMS Tracker update failed: {msg if msg else 'Code ' + code}"
        except Exception as e:
            return False, f"Network error: {e}"

    def _get_pre_alert_job_no(self, pre_alert_id: str) -> Optional[str]:
        """Fetch the existing Job_No from a Pre-Alert record."""
        if not self.ensure_valid_token():
            return None
        
        url = (f"https://{self.api_domain}/api/v2/{self.account_owner}/{self.app_link_name}"
               f"/report/{self.pre_alert_report}/{pre_alert_id}")
        headers = {"Authorization": f"Zoho-oauthtoken {self.access_token}"}
        
        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                data = response.json().get('data', {})
                job_no = data.get('Job_No', '')
                if job_no and str(job_no).strip() not in ['', '0', 'None', 'null']:
                    return str(job_no).strip()
            return None
        except Exception:
            return None

    def _find_sims_record_by_mbl(self, mbl: str) -> tuple[Optional[str], Optional[str]]:
        """Search SIMS Tracker report by MBL. Returns (record_id, existing_job_number)."""
        if not self.ensure_valid_token():
            return None, None
        
        # Search using the lookup field's MAWB_MBL
        url = (f"https://{self.api_domain}/api/v2/{self.account_owner}/{self.app_link_name}"
               f"/report/{self.report_link_name}"
               f"?criteria=(Pre_Alert_Ref.MAWB_MBL == \"{mbl}\")")
        headers = {"Authorization": f"Zoho-oauthtoken {self.access_token}"}
        
        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                data_list = response.json().get('data', [])
                if data_list and len(data_list) > 0:
                    record = data_list[0]
                    rid = str(record.get('ID'))
                    existing_job = record.get('Job_Number', '')
                    # Return existing job as truthy only if it's non-empty
                    if existing_job and str(existing_job).strip() not in ['', 'None', 'null']:
                        return rid, str(existing_job).strip()
                    return rid, None
            return None, None
        except Exception as e:
            logger.error(f"SIMS Tracker MBL lookup failed: {e}")
            return None, None
