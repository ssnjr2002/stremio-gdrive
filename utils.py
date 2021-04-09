import os
import PTN
import json
from datetime import datetime
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials


class meta:
    def __init__(self, name):
        self.ptn_parsed_dict = PTN.parse(name, standardise=False)
        self.metas2get = ['resolution', 'codec',
                          'bitDepth', 'audio', 'quality', 'encoder']

        for obj in self.metas2get:
            current_obj_value = self.ptn_parsed_dict.get(obj)
            if self.ptn_parsed_dict.get(obj):
                setattr(self, obj, current_obj_value)

    def get_string(self, format):
        self.formatted = ''

        def get_val(x, y):
            formatted = ''
            for word in x.split(y):
                if len(word) and word[0] == '%':
                    string = getattr(self, word[1:], '')
                    if string:
                        formatted += f'{string} '
                    elif not string and y == ';':
                        return ''
                else:
                    formatted += f'{word} '
            return formatted

        for segment in format.split():
            if len(segment.split(';')) > 1:
                self.formatted += get_val(segment, ';')
            else:
                self.formatted += get_val(segment, ' ')
        return self.formatted


class gdrive:
    def __init__(self):
        self.cf_proxy_url = None
        self.token = json.loads(os.environ.get('TOKEN'))

        with open('token.json', 'w') as token_json:
            json.dump(self.token, token_json)

        creds = Credentials.from_authorized_user_file('token.json')
        self.drive_instance = build('drive', 'v3', credentials=creds)

    def drive_q(self, raw_query):
        out = ''
        for word in raw_query.split():
            if out:
                out += ' and '
            out += f'name contains "{word}"'
        return out

    def file_list(self, file_fields):
        return self.drive_instance.files().list(
            q=self.query + " and trashed=false and mimeType contains 'video/'",
            fields=f'files({file_fields})',
            pageSize=self.max_results,
            supportsAllDrives=True,
            includeItemsFromAllDrives=True,
            orderBy='quotaBytesUsed desc',
            corpora='allDrives'
        ).execute()

    def get_drive_names(self):
        def callback(request_id, response, exception):
            self.drive_names[response.get('id')] = response.get('name')

        self.drive_names = {}
        batch = self.drive_instance.new_batch_http_request()
        drives = self.drive_instance.drives()

        for result in self.results:
            driveid = result.get('driveId')
            if not driveid:
                result['driveId'] = 'MyDrive'
                self.drive_names['MyDrive'] = 'MyDrive'
                continue
            batch_inst = drives.get(driveId=driveid, fields='name, id')
            batch.add(batch_inst, callback=callback)
        
        batch.execute()
        return self.drive_names

    def search(self, query):
        self.results = []
        self.query = self.drive_q(query)
        self.max_results = 200

        response = self.file_list(
            'id, name, size, driveId, md5Checksum')

        if response:
            unique_ids = []
            for obj in response['files']:
                unique_id = f"{obj.get('md5Checksum')}__{obj.get('driveId')}"
                if unique_id not in unique_ids:
                    obj.pop('md5Checksum')
                    unique_ids.append(unique_id)
                    self.results.append(obj)

            self.get_drive_names()
        return self.results

    def get_streams(self, query):
        def get_stream_name():
            return m.get_string(f'GDrive \n;%quality \n;%resolution')

        def get_title():
            m.get_string('🎥;%codec 🌈;%bitDepth;bit 🔊;%audio 👤;%encoder')
            return f"{name}\n💾 {gib_size:.3f} GiB ☁️ {drive_name}\n{m.formatted}"

        def get_url():
            return f"{self.cf_proxy_url}/load/{file_id}"

        out = []
        start_time = datetime.now()
        self.search(query)

        for obj in self.results:
            gib_size, name, file_id = int(obj['size']) / 1073741824, obj['name'], obj['id']
            drive_name = self.drive_names[obj['driveId']]

            m = meta(name)
            out.append({'name': get_stream_name(),
                        'title': get_title(), 'url': get_url()})

        time_taken = (datetime.now() - start_time).total_seconds()
        print(f'Fetched stream(s) in {time_taken:.3f}s')
        return out
