import streamlit as st
import pandas as pd
from datetime import datetime
from utils.google_oauth_io import (
    get_oauth_creds,
    get_drive_service,
    upload_to_drive_folder,
    append_df_to_gsheet
)

st.title("Payroll Upload")
def run():
    current_user = st.session_state.get("user", {}).get("username", "system")
    SHEET_ID = "1BJd1ezT7UL3ka1XGYSQ25ZBYmXpw0jUh9UxAPTZ2ngA"
    WORKSHEET = "transactions"
    FOLDER_ID = "1Eo9LrUw0M76R4HJ5tTGpZ61E3kR0tAD8"

    uploaded = st.file_uploader("Upload Payroll Worksheet", type=["xlsx","xls","csv"])

    if uploaded:
        if uploaded.name.endswith(".csv"):
            df = pd.read_csv(uploaded)
        else:
            df = pd.read_excel(uploaded)

        st.dataframe(df.head(20), use_container_width=True)

        if st.button("Save & Append"):
            creds = get_oauth_creds()
            drive_service = get_drive_service(creds)

            # A) Upload raw file to Drive folder
            stamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            fname = f"{stamp}_{uploaded.name}_{current_user}"
            file_id = upload_to_drive_folder(drive_service, uploaded.getvalue(), fname, FOLDER_ID)

            # Add audit columns
            df["uploaded_by"] = current_user
            df["uploaded_at"] = datetime.utcnow().isoformat()

            # B) Append to master sheet
            n = append_df_to_gsheet(creds, SHEET_ID, WORKSHEET, df)

            if n is None:
                st.success(f"Uploaded to Drive (file id: {file_id}). Data appended successfully.")
            else:
                st.success(f"Uploaded to Drive (file id: {file_id}) and appended {n:,} rows.")


    # from googleapiclient.discovery import build
    # from utils.google_oauth_io import get_oauth_creds

    # SHEET_ID = "1BJd1ezT7UL3ka1XGYSQ25ZBYmXpw0jUh9UxAPTZ2ngA"

    # creds = get_oauth_creds()
    # drive = build("drive", "v3", credentials=creds)

    # meta = drive.files().get(fileId=SHEET_ID, fields="id,name,owners,permissions").execute()
    # print(meta)
