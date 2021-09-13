import json
import requests
from string import punctuation


class MetadataNotFound(Exception):
    pass


class Meta:
    def __init__(self, stream_type, stream_id):
        self.id = stream_id
        self.type = stream_type
        self.full_id = stream_id
        alnum = lambda x: ''.join(filter(str.isalnum, x)).lower()
        del_punc = lambda x: x.translate(str.maketrans('', '', punctuation))

        if self.type == 'series':
            id_split = self.id.split(':')
            self.id = id_split[0]
            self.ep = str(id_split[-1]).zfill(2)
            self.se = str(id_split[-2]).zfill(2)

        meta = self.get(
            f'v2.sg.media-imdb.com/suggests/t/{self.id}.json', 'd')
        
        if meta:
            self.set_meta(self.id, meta[0], year='y', name='l')
        else:  # fallback to cinemeta just for keks
            meta = self.get(
                f'v3-cinemeta.strem.io/meta/{self.type}/{self.id}.json')
            if meta:
                self.set_meta(self.id, meta)

        if meta:
            self.slug = del_punc(self.name)
            if self.name != self.slug:
                self.names = [self.name, self.slug]
            else:
                self.names = [self.slug]
            self.alnum_names = set(alnum(name) for name in self.names)
        else:
            raise MetadataNotFound(
                f"Couldn't find metadata for {type} {id} !")

    def get(self, url, key='meta'):
        try:
            r = requests.get(f'https://{url}', timeout=5).text
            # imbd wont return proper json sometimes so:
            return json.loads(r[r.index('{'):].rstrip(')')).get(key)
        except (requests.exceptions.Timeout, JSONDecodeError):
            return None

    def set_meta(self, id, meta, year='year', name='name'):
        fix_ch = lambda x: x.replace("'", "\\'").replace(":", "").lower()
        self.name = fix_ch(meta.get(name))
        self.year = str(meta.get(year)).split('–')[0]
