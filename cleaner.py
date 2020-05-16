import argparse
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
        '{}/gmail_api.json'.format(work_dir))
    credencials_path = os.path.normpath(
        '{}/gmail_api_auth.db'.format(work_dir))

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


def cleaner(args):
    remove_emails_older_than = args.age
    remove_starred = args.starred
    verbose = args.verbose
    archive = args.archive
    mark_as_read = args.mark_as_read
    label_filter = args.label_filter

    if remove_emails_older_than < 0:
        print("Age is below 0. Acting on all e-mails.")
        remove_emails_older_than = 0

    if not archive and not mark_as_read:
        print("Don't archive and don't mark as read both set to true. "
              "Nothing to do.")
        return

    print('Acting only on e-mails with one of the following labels: {}'.format(
        label_filter)) if verbose and label_filter else None

    print("Logging in...") if verbose else None

    service = build('gmail', 'v1', credentials=get_credentials())

    print("Logged...") if verbose else None
    print('Fetching e-mails...') if verbose else None

    labels_dict = {}
    if label_filter:
        # Builds a dictionary with labelIds and their respective names
        labels = service.users().labels().list(userId='me').execute()
        for label in labels['labels']:
            if label['type'] == 'user':
                labels_dict[label['id']] = label['name']

    # Call the Gmail API
    results_list = []
    results = service.users().messages().list(userId='me',
                                              labelIds=['INBOX'],
                                              maxResults=500, ).execute()
    results_list.append(results)

    # Queries for next results until there aren't any (results > 500)
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
            print('No e-mails found.')
            return

    print('--- {} e-mails found on your inbox.'.format(len(emails_ids)))

    labels_to_remove = []
    labels_to_remove.append('UNREAD') if mark_as_read else None
    labels_to_remove.append('INBOX') if archive else None

    actions_per_email = []
    actions_per_email.append('marked as read') \
        if 'UNREAD' in labels_to_remove else None
    actions_per_email.append('archieved') \
        if 'INBOX' in labels_to_remove else None

    count = 0
    for email_id in emails_ids:
        msg = service.users().messages().get(id=email_id,
                                             userId='me').execute()
        msg_date = datetime.fromtimestamp(int(msg['internalDate']) / 1000)
        today = datetime.now()
        x_days_ago = today - timedelta(days=remove_emails_older_than)

        try:
            # Get e-mail subject from the mensage payload.
            msg_subject = [i['value'] for i in msg['payload']['headers'] if
                           i['name'] == 'Subject'][0]
        except IndexError:
            # If subject is not present, use e-mail id.
            msg_subject = email_id

        if label_filter:
            # Checks if the e-email is marked with any of the filter_labels
            # Returns True once at least one match is found.
            label_filter_cond = False

            msg_labels = msg['labelIds']
            for label in msg_labels:
                label_name = labels_dict.get(label, None)
                if label_name in label_filter:
                    label_filter_cond = True
                    break
                else:
                    label_filter_cond = False
        else:
            label_filter_cond = True

        if remove_starred:
            remove_starred_cond = 'STARRED' not in msg['labelIds']
        else:
            remove_starred_cond = True

        if remove_emails_older_than > 0:
            remove_emails_older_than_cond = msg_date < x_days_ago
        else:
            remove_emails_older_than_cond = True

        if remove_starred_cond and \
                remove_emails_older_than_cond and \
                label_filter_cond:
            gmail_executor = service.users().messages(). \
                modify(userId='me',
                       id=email_id,
                       body={
                           'removeLabelIds': labels_to_remove,
                           'addLabelIds': []}).execute()
            print('"{}": {}'.format(msg_subject,
                                    ' and '.join(actions_per_email)))

            count += 1

        elif verbose:
            # Builds the verbose output for skipping an e-mail based on what
            # conditions were not met.
            conditions = []
            conditions.append('Starred') if not remove_starred_cond else None
            conditions.append('Too young') \
                if not remove_emails_older_than_cond else None
            conditions.append("Doesn't match filtered label") \
                if not label_filter_cond else None

            print('"{}" skipped due to:'
                  ' {}'.format(msg_subject, '; '.join(conditions)))

    # Builds the final count output based on which
    # actions the user requested to be done
    actions = []
    actions.append('marked as read') if mark_as_read else None
    actions.append('archieved') if archive else None
    print('---\n{} e-mails {}'.format(count, ' and '.join(actions)))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--age', type=int, default=30,
                        help='Act on e-mails older than x days. Defaults to '
                             '30.')
    parser.add_argument('--starred', dest='starred', action='store_true',
                        help="Keep starred e-mails.")
    parser.add_argument('--verbose', dest='verbose', action='store_true',
                        help="More output of the actions done by the cleaner.")
    parser.add_argument('--no_archive', dest='archive', action='store_false',
                        help="Don't archive e-mails that met the criteria.")
    parser.add_argument('--no_read', dest='mark_as_read', action='store_false',
                        help="Don't mark e-mails that met the criteria as "
                             "read.")
    parser.add_argument('--filter_label', dest='label_filter', action='append',
                        help="Only act on e-mails containing this label. "
                             "Add as many as you want. Defaults to all.", )
    parser.set_defaults(starred=False,
                        verbose=False,
                        archive=True,
                        mark_as_read=True,
                        label_filter=[], )
    args = parser.parse_args()
    cleaner(args)


if __name__ == '__main__':
    main()
