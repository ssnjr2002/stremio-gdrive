import requests
from datetime import datetime, timedelta
from sgd.utils.cache import Pickle, Json
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials


class GoogleDrive:
    def __init__(self, token):
        self.token = token
        self.page_size = 1000
        self.acc_token = Pickle('acctoken.pickle')
        self.drive_names = Json('drivenames.json')
        
        creds = Credentials.from_authorized_user_info(self.token)
        self.drive_instance = build('drive', 'v3', credentials=creds)

    @staticmethod
    def qgen(string, chain='and', method='name', splitter=' '):
        out = ''
        for word in string.split(splitter):
            if out:
                out += f" {chain} "
            out += f"{method} contains '{word}'"
        return out

    def get_query(self, sm):
        if sm.type == 'series':
            return [f"({self.qgen(name)}) and (" + self.qgen(
                    f's{sm.se} e{sm.ep}, ' +  # sXX eXX
                    f's{int(sm.se)} e{int(sm.ep)}, ' +  # sX eX
                    f'season {int(sm.se)} episode {int(sm.ep)}, ' +  # season X episode X
                    f'"{int(sm.se)} x {int(sm.ep)}", ' +  # X x X
                    f'"{int(sm.se)} x {sm.ep}"',  # X x XX
                    chain='or', method='fullText', splitter=', '
                    ) + ')' for name in sm.names]

        elif sm.type == 'movie':
            return ["name contains '" +
                    f"*{name} {sm.year}".replace(" ", "*") + "' or (" +
                    self.qgen(f'{name} {sm.year}') + 
                    ")" for name in sm.names]

    def file_list(self, file_fields):
        def callb(request_id, response, exception):
            if response:
                output.extend(response.get('files'))

        if self.query:
            output = []
            files = self.drive_instance.files()
            batch = self.drive_instance.new_batch_http_request()
            for q in self.query:
                batch_inst = files.list(
                    q=f"{q} and trashed=false and mimeType contains 'video/'",
                    fields=f'files({file_fields})',
                    pageSize=self.page_size,
                    supportsAllDrives=True,
                    includeItemsFromAllDrives=True,
                    corpora='allDrives'
                    )
                batch.add(batch_inst, callback=callb)
            batch.execute()
            return output

    def get_drive_names(self):
        def callb(request_id, response, exception):
            if response:
                drive_id = response.get('id')
                drive_name = response.get('name')
                self.drive_names.contents[drive_id] = drive_name

        batch = self.drive_instance.new_batch_http_request()
        drives = self.drive_instance.drives()
        drive_ids = set(
            item['driveId'] for item in self.results if item.get('driveId')
        )

        for drive_id in drive_ids:
            cached_drive_name = self.drive_names.contents.get(drive_id)
            if not cached_drive_name:
                self.drive_names.contents[drive_id] = None
                batch_inst = drives.get(driveId=drive_id, fields='name, id')
                batch.add(batch_inst, callback=callb)

        batch.execute()
        self.drive_names.save()
        return self.drive_names.contents

    def search(self, stream_meta):
        self.results = []
        self.query = self.get_query(stream_meta)

        response = self.file_list(
            'id, name, size, driveId, md5Checksum')

        if response:
            unique_keys = set()

            def check_dupe(item):
                unique_key = item.get(
                    'driveId', 'MyDrive') + item.get('md5Checksum')
                if unique_key in unique_keys:
                    return False
                else:
                    unique_keys.add(unique_key)
                    return True

            self.results = sorted(
                filter(check_dupe, response),
                key=lambda item: int(item.get('size')), 
                reverse=True
            )

        self.get_drive_names()
        return self.results

    def get_acc_token(self):
        token_exipred = self.acc_token.contents.get(
            'expires_in', datetime.now()) <= datetime.now()

        if token_exipred or not self.acc_token.contents:
            body = {
                "client_id": self.token['client_id'],
                "client_secret": self.token['client_secret'],
                "refresh_token": self.token['refresh_token'],
                "grant_type": "refresh_token"
            }
            api_url = 'https://www.googleapis.com/oauth2/v4/token'
            oauth_resp = requests.post(api_url, json=body).json()
            oauth_resp['expires_in'] = timedelta(
                seconds=oauth_resp['expires_in']) + datetime.now()

            self.acc_token.contents = oauth_resp
            self.acc_token.save()

        expiry = self.acc_token.contents['expires_in']
        acc_token = self.acc_token.contents.get('access_token')
        print("Fetched access_token, will expire at", expiry)
        return acc_token
