import json
import requests
from bs4 import BeautifulSoup
from sgd.cache import Pickle
from sgd.utils import sanitize, req_wrapper, safe_get, num_extract, is_year


class MetadataNotFound(Exception):
    pass


class Meta:
    def __init__(self, stream_type, stream_id):
        self.id = stream_id
        self.type = stream_type
        self.ep = None
        self.se = None
        self.year = None
        self.titles = []

        if self.type == "series":
            id_split = self.id.split(":")
            self.id = id_split[0]
            self.ep = str(id_split[-1]).zfill(2)
            self.se = str(id_split[-2]).zfill(2)

        self.imdb_sg_url = f"v2.sg.media-imdb.com/suggests/t/{self.id}.json"
        self.cinemeta_url = f"v3-cinemeta.strem.io/meta/{self.type}/{self.id}.json"
        self.imdb_html_url = f"imdb.com/title/{self.id}/releaseinfo?ref_=tt_dt_aka"

        self.fetch_dest = "IMDB_HTML"
        if not self.get_meta_from_imdb_html():
            self.fetch_dest = "IMDB_SG_API"
            if not self.get_meta_from_imdb_sg():
                self.fetch_dest = "CINEMETA"
                if not self.get_meta_from_cinemeta():
                    self.fetch_dest = "NULL"
                    raise MetadataNotFound(
                        f"Couldn't find metadata for {self.type} {self.id}!"
                    )

    def get_meta_from_imdb_html(self):
        try:
            imdb_html = req_wrapper(self.imdb_html_url, time_out=5)
        except requests.exceptions.Timeout:
            return False

        soup = BeautifulSoup(imdb_html, "html.parser")
        table = soup.find("table", attrs={"class": "akas-table-test-only"})
        right_title_block = soup.find(
            "div", attrs={"class": "subpage_title_block__right-column"}
        )

        if right_title_block:
            h3_itemprop = right_title_block.find("h3", attrs={"itemprop": "name"})
            h4_itemprop = right_title_block.find("h4", attrs={"itemprop": "name"})

            title = ""
            if h4_itemprop:
                title = sanitize(h4_itemprop.find("a").text) + " "

            if h3_itemprop:
                title += sanitize(h3_itemprop.find("a").text)
                self.titles.append(title)
                span_text = h3_itemprop.find("span").text.strip()
                years = list(filter(is_year, num_extract(span_text)))
                self.year = min(years) if years else None

        if table:
            table_rows = table.find_all("tr")
            table_data = [tr.find_all("td") for tr in table_rows]
            titles = set(sanitize(safe_get(td, 1).text) for td in table_data)

            if safe_get(self.titles, 0):
                self.titles = list(titles)
            else:
                self.titles += list(titles)

        if self.titles:
            if self.type == "series" or self.year:
                return True
        return False

    def get_meta_from_imdb_sg(self):
        meta = self.req_api(self.imdb_sg_url, key="d")
        if meta:
            self.set_meta(meta[0], year="y", name="l")
            return True
        return False

    def get_meta_from_cinemeta(self):
        meta = self.req_api(self.cinemeta_url)
        if meta:
            self.set_meta(meta)
            return True
        return False

    def req_api(self, url, key="meta"):
        try:
            r = req_wrapper(url)
            # imbd wont return proper json sometimes so:
            return json.loads(r[r.find("{") :].rstrip(")")).get(key)
        except json.decoder.JSONDecodeError:
            return dict()

    def set_meta(self, meta, year="year", name="name"):
        self.titles.add(sanitize(meta.get(name, "")))
        self.year = str(meta.get(year, "")).split("–")[0]


def CachedMeta(stream_type, stream_id):
    meta = Pickle(f"{stream_id.split(':')[0]}.pickle")

    if not meta.contents:
        meta.contents = Meta(stream_type, stream_id)
        meta.save("Saving Metadata")
    else:
        meta.contents.fetch_dest = "CACHE"

    print(f"Fetched metadata for {meta.contents.id} from {meta.contents.fetch_dest}:")
    print(f"Titles ({len(meta.contents.titles)}): {meta.contents.titles}")
    print(f"Year: {meta.contents.year}")

    return meta.contents
