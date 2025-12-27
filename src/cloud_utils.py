import gspread
from oauth2client.service_account import ServiceAccountCredentials
import logging
import pandas as pd

logger = logging.getLogger(__name__)

def upload_to_sheets(dataframe, sheet_name, credentials_file, email_to_share=None):
    """
    Uploads a pandas DataFrame to a Google Sheet.
    Creates the sheet if it doesn't exist.
    """
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    
    try:
        creds = ServiceAccountCredentials.from_json_keyfile_name(credentials_file, scope)
        client = gspread.authorize(creds)
        
        # Open or Create
        try:
            sh = client.open(sheet_name)
            logger.info(f"Opened existing sheet: {sheet_name}")
        except gspread.SpreadsheetNotFound:
            sh = client.create(sheet_name)
            logger.info(f"Created new sheet: {sheet_name}")
            if email_to_share:
                sh.share(email_to_share, perm_type='user', role='writer')

        worksheet = sh.get_worksheet(0)
        
        # Clear existing
        worksheet.clear()
        
        # Update content
        # set_with_dataframe is deprecated/removed in some versions, using update.
        # list of lists
        val_matrix = [dataframe.columns.values.tolist()] + dataframe.values.tolist()
        worksheet.update(val_matrix)
        
        return f"https://docs.google.com/spreadsheets/d/{sh.id}"
        
    except Exception as e:
        logger.error(f"Google Sheets Upload Failed: {e}")
        raise e
