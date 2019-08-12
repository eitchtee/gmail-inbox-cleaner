import os.path
import pickle
from datetime import datetime
from datetime import timedelta

from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# If modifying these scopes, delete the file gmail_api_auth.db.
SCOPES = ['https://www.googleapis.com/auth/gmail.modify']


def get_credentials():
    work_dir = os.path.dirname(os.path.realpath(__file__))
    google_api_path = os.path.normpath(
        '{}/credenciais/gmail_api.json'.format(work_dir))
    credencials_path = os.path.normpath(
        '{}/credenciais/gmail_api_auth.db'.format(work_dir))

    creds = None
    # The file gmail_api_auth.db stores the user's access and refresh tokens,
    # and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists(credencials_path):
        with open(credencials_path, 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                google_api_path, SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open(credencials_path, 'wb') as token:
            pickle.dump(creds, token)

    return creds


def main(remove_emails_older_than: int = 30):
    service = build('gmail', 'v1', credentials=get_credentials())

    # Call the Gmail API
    results_list = []
    results = service.users().messages().list(userId='me',
                                              labelIds=['INBOX'],
                                              maxResults=500, ).execute()
    results_list.append(results)

    if 'nextPageToken' in results.keys():
        appending = True
        while appending:
            npage_token = results['nextPageToken']
            results = service.users().messages().list(userId='me',
                                                      labelIds=['INBOX'],
                                                      maxResults=500,
                                                      pageToken=npage_token).execute()
            results_list.append(results)
            if 'nextPageToken' in results.keys():
                continue
            else:
                appending = False

    emails_ids = []
    for request in results_list:
        try:
            for thread in request['messages']:
                emails_ids.append(thread['id'])
        except KeyError:
            print('No e-mails.')
            return

    print('{} e-mails found on your inbox.\n'.format(
        len(emails_ids)))
    for email_id in emails_ids:
        msg = service.users().messages().get(id=email_id,
                                             userId='me').execute()
        msg_date = datetime.fromtimestamp(int(msg['internalDate']) / 1000)
        today = datetime.now()
        x_days_ago = today - timedelta(days=remove_emails_older_than)
        if 'STARRED' not in msg['labelIds'] and msg_date < x_days_ago:
            archive_run = service.users(). \
                messages(). \
                modify(userId='me',
                       id=email_id,
                       body={'removeLabelIds': ['INBOX', 'UNREAD'],
                             'addLabelIds': []}). \
                execute()
            print('{} marked as read and archived. '.format(email_id))
        # else:
        #     print('{} is marked as important or too young. Skipped.'.format(
        #     email_id))


if __name__ == '__main__':
    main()
