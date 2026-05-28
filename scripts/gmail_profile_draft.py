#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Create Gmail drafts for LabMFA profile requests.

The script intentionally creates drafts instead of sending messages. This keeps
the final send action inside Gmail, where the recipient and content can be
reviewed before delivery.
"""

import argparse
import base64
import json
import mimetypes
import os
import sys
from email.message import EmailMessage
from pathlib import Path

SCOPES = ['https://www.googleapis.com/auth/gmail.compose']
DEFAULT_CONFIG_DIR = Path.home() / '.config/labmfa'
DEFAULT_CREDENTIALS = DEFAULT_CONFIG_DIR / 'gmail-credentials.json'
DEFAULT_TOKEN = DEFAULT_CONFIG_DIR / 'gmail-token.json'


def load_google_client(credentials_path, token_path):
    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build
    except ImportError as error:
        raise SystemExit(
            'Missing Gmail API dependencies. Install with:\n'
            '  python -m pip install --upgrade '
            'google-api-python-client google-auth-httplib2 '
            'google-auth-oauthlib\n'
            'Original import error: {}'.format(error)
        )

    credentials_path = Path(credentials_path).expanduser()
    token_path = Path(token_path).expanduser()

    if not credentials_path.exists():
        raise SystemExit(
            'Gmail OAuth credentials not found: {}\n'
            'Create a Desktop OAuth client in Google Cloud, enable the Gmail '
            'API, and save the downloaded JSON there. You can also set '
            'LABMFA_GMAIL_CREDENTIALS to another path.'.format(
                credentials_path)
        )

    creds = None
    if token_path.exists():
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                credentials_path, SCOPES)
            creds = flow.run_local_server(port=0)

        token_path.parent.mkdir(parents=True, exist_ok=True)
        token_path.write_text(creds.to_json(), encoding='utf-8')

    return build('gmail', 'v1', credentials=creds)


def build_message(payload):
    message = EmailMessage()
    message['From'] = payload['from']
    if payload.get('to'):
        message['To'] = payload['to']
    message['Subject'] = payload['subject']
    message.set_content(payload['body'])

    for attachment in payload.get('attachments', []):
        path = Path(attachment).expanduser()
        content_type, _ = mimetypes.guess_type(path)
        maintype, subtype = (
            content_type.split('/', 1)
            if content_type else ('application', 'octet-stream')
        )
        message.add_attachment(
            path.read_bytes(),
            maintype=maintype,
            subtype=subtype,
            filename=path.name,
        )

    raw = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
    return {'message': {'raw': raw}}


def create_draft(payload, credentials_path, token_path):
    service = load_google_client(credentials_path, token_path)
    return service.users().drafts().create(
        userId='me',
        body=build_message(payload),
    ).execute()


def main():
    parser = argparse.ArgumentParser(
        description='Create a Gmail draft with the LabMFA profile request.')
    parser.add_argument('--payload', required=True,
                        help='JSON payload produced by build.py')
    parser.add_argument(
        '--credentials',
        default=os.environ.get('LABMFA_GMAIL_CREDENTIALS',
                               str(DEFAULT_CREDENTIALS)),
        help='OAuth Desktop credentials JSON')
    parser.add_argument(
        '--token',
        default=os.environ.get('LABMFA_GMAIL_TOKEN', str(DEFAULT_TOKEN)),
        help='OAuth token cache JSON')
    args = parser.parse_args()

    payload = json.loads(Path(args.payload).read_text(encoding='utf-8'))
    draft = create_draft(payload, args.credentials, args.token)
    print('Gmail draft created: {}'.format(draft.get('id')))
    print('Open Gmail drafts: https://mail.google.com/mail/u/0/#drafts')


if __name__ == '__main__':
    main()
