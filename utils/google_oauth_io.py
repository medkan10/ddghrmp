import os
import io
import pandas as pd

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import gspread

# ------------------------------------------------------------
# 1. OAUTH CREDS (Drive + Sheets + Offline refresh token)
# ------------------------------------------------------------
SCOPES = [
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/spreadsheets",
]


def get_oauth_creds():
    token_path = "token.json"

    # If token exists → reuse it
    if os.path.exists(token_path):
        return Credentials.from_authorized_user_file(token_path, SCOPES)

    # Otherwise → authenticate fresh
    flow = InstalledAppFlow.from_client_secrets_file(
        "client_secrets.json", SCOPES
    )

    creds = flow.run_local_server(
        port=0,
        access_type="offline",
        prompt="consent"
    )

    # Save token
    with open(token_path, "w") as f:
        f.write(creds.to_json())

    return creds


# ------------------------------------------------------------
# 2. GET DRIVE SERVICE (uses SAME creds as Sheets)
# ------------------------------------------------------------
def get_drive_service(creds):
    return build("drive", "v3", credentials=creds)


# ------------------------------------------------------------
# 3. UPLOAD FILE TO GOOGLE DRIVE FOLDER
# ------------------------------------------------------------
def upload_to_drive_folder(drive_service, file_bytes, filename, folder_id):
    media = MediaIoBaseUpload(
        io.BytesIO(file_bytes),
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        resumable=True
    )

    metadata = {
        "name": filename,
        "parents": [folder_id]
    }

    uploaded = drive_service.files().create(
        body=metadata,
        media_body=media,
        fields="id, name, webViewLink"
    ).execute()

    return uploaded["id"]


# ------------------------------------------------------------
# 4. APPEND DATAFRAME TO GOOGLE SHEET
# ------------------------------------------------------------
# def append_df_to_gsheet(creds, sheet_id, worksheet_name, df: pd.DataFrame):
#     gc = gspread.authorize(creds)
#     sh = gc.open_by_key(sheet_id)
#     ws = sh.worksheet(worksheet_name)

#     rows = df.fillna("").astype(str).values.tolist()
#     ws.append_rows(rows, value_input_option="USER_ENTERED")

#     return len(rows)

def append_df_to_gsheet(creds, sheet_id, worksheet_name, df):
    gc = gspread.authorize(creds)
    ws = gc.open_by_key(sheet_id).worksheet(worksheet_name)

    existing = ws.get_all_values()
    if len(existing) == 0:
        ws.append_row(df.columns.tolist(), value_input_option="USER_ENTERED")

    ws.append_rows(df.fillna("").astype(str).values.tolist(),
                   value_input_option="USER_ENTERED")