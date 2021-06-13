import os
import re
import PTN
import json
import requests
from datetime import datetime
from string import punctuation
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


class MetadataNotFound(Exception):
    pass


class meta_provider:
    def __init__(self, type, id):
        self.id = id
        self.type = type
        self.cm_url = 'v3-cinemeta.strem.io'
        self.imdbsg_url = 'v2.sg.media-imdb.com'
        self.fix_char = lambda x: x.replace("'", "\\'").replace(":", "").lower()
        self.re_punc = lambda x: x.translate(str.maketrans('', '', punctuation))

        meta = None
        id_split = id.split(':')

        if self.type == 'series':
            self.id = id_split[0]
            self.ep = str(id_split[-1]).zfill(2)
            self.se = str(id_split[-2]).zfill(2)

        meta = self.get(self.imdbsg_url, 'd')
        if meta:
            self.set_meta(self.id, meta[0], year='y', name='l')
        else:  # fallback to cinemeta just for keks
            meta = self.get(self.cm_url)
            if meta:
                self.set_meta(self.id, meta)

        if meta:
            self.slug = self.re_punc(self.name)
            self.names = [self.name,
                          self.slug] if self.name != self.slug else [self.slug]
        else:
            raise MetadataNotFound(f"Couldn't find metadata for {id}!")

    def get(self, url, keyname='meta'):
        url += f"/meta/{self.type}/{self.id}.json" if not url.startswith(
                "v2.sg.media-imdb") else f"/suggests/t/{self.id}.json"
        try:
            r = requests.get(f'https://{url}', timeout=5).text
            # imbd wont return proper json sometimes so:
            return json.loads(r[r.index('{'):].rstrip(')')).get(keyname)
        except requests.exceptions.Timeout:
            print(f"ERROR: FAILED TO FETCH META ({id})!")
            return None

    def set_meta(self, id, meta, year='year', name='name'):
        self.year = str(meta.get(year)).split('–')[0]
        self.name = self.fix_char(meta.get(name))

class gdrive:
    def __init__(self):
        self.page_size = 1000
        self.cf_proxy_url = None
        self.streams_cache = {}
        self.token = json.loads(os.environ.get('TOKEN'))

        with open('token.json', 'w') as token_json:
            json.dump(self.token, token_json)

        creds = Credentials.from_authorized_user_file('token.json')
        self.drive_instance = build('drive', 'v3', credentials=creds)

    def get_query(self, type, id):
        def qgen(string, chain='or', method='fullText', 
                 splitter=', ', quotes=False):
            out = ''
            for word in string.split(splitter):
                if out:
                    out += f" {chain} "
                if quotes:
                    out += f"{method} contains '\"{word}\"'"
                else:
                    out += f"{method} contains '{word}'"
            return out

        mp = meta_provider(type, id)
        self.mp = mp  # need this for se_ep check later

        if type == 'series':
            return ['(' + \
                    qgen('^%$'.join(mp.names), splitter='^%$', quotes=True) + \
                    ") and (" + qgen(
                    f's{mp.se} e{mp.ep}, ' + \
                    f's{int(mp.se)} e{int(mp.ep)}, ' + \
                    f'season {int(mp.se)} episode {int(mp.ep)}, ' + \
                    f'"{int(mp.se)} x {int(mp.ep)}", ' + \
                    f'"{int(mp.se)} x {mp.ep}"') + ')']

        elif type == 'movie':
            def query(name):
                return "name contains '" + \
                        f"*{name} {mp.year}".replace(" ", "*") + "' or (" + \
                        qgen(f"{name} {mp.year}", chain='and', method='name',
                            splitter=' ') + ")"
            return [query(name) for name in mp.names]

    def file_list(self, file_fields):
        out = []
        for q in self.query:
            out += self.drive_instance.files().list(
                    q=f"{q} and trashed=false and mimeType contains 'video/'",
                    fields=f'files({file_fields})',
                    pageSize=self.page_size,
                    supportsAllDrives=True,
                    includeItemsFromAllDrives=True,
                    corpora='allDrives').execute()['files']
        return out

    def get_drive_names(self):
        def callback(request_id, response, exception):
            if response:
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
            self.drive_names[driveid] = driveid
            batch_inst = drives.get(driveId=driveid, fields='name, id')
            batch.add(batch_inst, callback=callback)

        batch.execute()
        return self.drive_names

    def search(self, query):
        self.query = query
        self.results = []

        response = self.file_list(
            'id, name, size, driveId, md5Checksum')

        if response:
            unique_ids = {}
            for obj in response:
                unique_id = f"{obj.get('md5Checksum')}__{obj.get('driveId')}"
                if not unique_ids.get(unique_id):
                    try:
                        obj.pop('md5Checksum')
                    except KeyError:
                        print(f"WARN, Checksum not found: {obj}")
                    unique_ids[unique_id] = True
                    self.results.append(obj)

            self.get_drive_names()
            self.results.sort(
                key=(lambda dic: int(dic.get('size'))), reverse=True)

        return self.results

    def correct_se_ep(self, id, obj):
        id = id.split(':')[1:]
        seep = re.compile(
            r"(?ix)(\d+)[^a-zA-Z]*?(?:ep|e|x|episode)[^a-zA-Z]*?(\d+)")
        try:
            se, ep = seep.findall(obj['name'])[0]
            if int(se) == int(self.mp.se) and int(self.mp.ep) == int(id[1]):
                return True
        except (ValueError, IndexError):
            return False
        return False

    def get_streams(self, type, id):
        def get_name():
            return m.get_string(f'GDrive \n;%quality \n;%resolution')

        def get_title():
            m.get_string('🎥;%codec 🌈;%bitDepth;bit 🔊;%audio 👤;%encoder')
            return f"{name}\n💾 {gib_size:.3f} GiB ☁️ " \
                   f"{drive_name}\n{m.formatted}"

        def get_url():
            return f"{self.cf_proxy_url}/load/{file_id}"

        start_time = datetime.now()
        out = []
        self.search(self.get_query(type, id))

        for obj in self.results:
            if type == "series" and not self.correct_se_ep(id, obj):
                continue
            gib_size = int(obj['size']) / 1073741824
            name, file_id = obj['name'], obj['id']
            drive_name = self.drive_names[obj['driveId']]

            m = meta(name)
            out.append(
                {'name': get_name(), 'title': get_title(), 'url': get_url()})

        noresult = [{
            'name': 'GDrive 404', 
            'title': 'No results found!', 
            'externalUrl': '/'}]

        time_taken = (datetime.now() - start_time).total_seconds()
        print(f'Fetched {len(out)} stream(s) in {time_taken:.3f}s',
              f'for ({id}) {self.query}')

        return out if len(out) else noresult
