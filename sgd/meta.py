import lxml
import cchardet
import sgd.utils as ut
from bs4 import BeautifulSoup
from sgd.cache import Json


class MetadataNotFound(Exception):
    pass


class IMDb:
    def __init__(self):
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
        """
        Scrape metadata from imdb aka page. Includes local
        names to get more results
        """
        imdb_html = ut.req_wrapper(self.imdb_html_url, time_out=5)
        soup = BeautifulSoup(imdb_html, "lxml")
        table = soup.find("table", attrs={"class": "akas-table-test-only"})
        r_title_block = soup.find(
            "div", attrs={"class": "subpage_title_block__right-column"}
        )

        if r_title_block:
            h3_itemprop = r_title_block.find("h3", attrs={"itemprop": "name"})
            h4_itemprop = r_title_block.find("h4", attrs={"itemprop": "name"})

            title = ""
            if h4_itemprop:
                # Only appears in some pages like tt1672218
                title = ut.sanitize(h4_itemprop.find("a").text) + " "

            if h3_itemprop:
                title += ut.sanitize(h3_itemprop.find("a").text)
                self.titles.append(title)
                # Extract start year from span text
                span_text = h3_itemprop.find("span").text.strip()
                years = list(filter(ut.is_year, ut.num_extract(span_text)))
                self.year = min(years) if years else None

        if table:
            table_rows = table.find_all("tr")
            table_data = [tr.find_all("td") for tr in table_rows]

            titles = set()
            first_title = ut.safe_get(self.titles, 0)

            for td in table_data:
                title = ut.sanitize(ut.safe_get(td, 1).text)
                if title and title != first_title:
                    # Dont use titles which are just nums with 
                    # less than 3 digits
                    if not (title.isdigit() and len(title) < 3):
                        titles.add(title)

            limit = 29  # To "ease" gdrive batch api's suffering
            self.titles += list(titles)[:limit]

        if self.titles:
            if self.type == "series" or self.year:
                return True
        return False

    def get_meta_from_imdb_sg(self):
        """Obtain metadata from imdb suggestions api"""
        meta = ut.req_api(self.imdb_sg_url, key="d")
        if meta:
            self.set_meta(meta[0], year="y", name="l")
            return True
        return False

    def get_meta_from_cinemeta(self):
        """Obtain metadata from cinemeta v3 api"""
        meta = ut.req_api(self.cinemeta_url)
        if meta:
            self.set_meta(meta)
            return True
        return False

    def set_meta(self, meta, year="year", title="name"):
        self.titles.append(ut.sanitize(meta.get(title, "")))
        self.year = str(meta.get(year, "")).split("–")[0]


class Meta(IMDb):
    def __init__(self, stream_type, stream_id):
        self.titles = []
        self.year = None
        self.ep = 0
        self.se = 0

        self.id_split = stream_id.split(":")
        self.type = stream_type
        self.stream_type = stream_type

        self.id = self.id_split[0]
        if stream_type == "series":
            self.ep = str(self.id_split[-1]).zfill(2)
            self.se = str(self.id_split[-2]).zfill(2)

        cached = Json(f"{self.id}.json")
        if not cached.contents:
            IMDb.__init__(self)
            cached.contents.update(self.__dict__)
            cached.save()
        else:
            # Refresh se:ep to prevent series' from searching last cached
            # se:ep instead of current se:ep
            cached.contents["se"] = self.se
            cached.contents["ep"] = self.ep
            self.__dict__.update(cached.contents)
            self.fetch_dest = "CACHE"

        print(f"Fetched metadata for {self.id} from {self.fetch_dest}:")
        print(f"Titles ({len(self.titles)}) -> {self.titles}")
        print(f"Year: {self.year}")
