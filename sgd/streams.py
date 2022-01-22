import os
import urllib
from sgd.ptn import parse_title
from sgd.utils import sanitize, hr_size


class Streams:
    def __init__(self, gdrive, stream_meta):
        self.results = []
        self.gdrive = gdrive
        self.strm_meta = stream_meta
        self.get_url = self.get_proxy_url
        self.proxy_url = os.environ.get("CF_PROXY_URL")

        if not self.proxy_url:
            self.get_url = self.get_gapi_url
            self.acc_token = gdrive.get_acc_token()

        for item in gdrive.results:
            self.item = item
            self.parsed = parse_title(item.get("name"))
            self.construct_stream()

            if self.is_semi_valid_title(self.constructed):
                if self.strm_meta.type == "movie":
                    if self.is_valid_year(self.constructed):
                        self.results.append(self.constructed)
                else:
                    self.results.append(self.constructed)

        self.results.sort(key=self.best_res, reverse=True)

    def is_valid_year(self, movie):
        movie_year = str(movie["sortkeys"].get("year", "0"))
        return movie_year == self.strm_meta.year

    def is_semi_valid_title(self, item):
        item_title = sanitize(str(item["sortkeys"].get("title")), "")
        if item_title:
            return any(
                sanitize(title, "") in item_title for title in self.strm_meta.titles
            )
        return False

    def get_title(self):
        file_name = self.item.get("name")
        file_size = hr_size(int(self.item.get("size")))
        drive_id = self.item.get("driveId")
        drive_name = self.gdrive.drive_names.contents.get(drive_id, "MyDrive")

        str_format = "🎥;%codec 🌈;%bitDepth;bit 🔊;%audio 👤;%encoder"
        suffix = self.parsed.get_str(str_format)
        return f"{file_name}\n💾 {file_size} ☁️ {drive_name}\n{suffix}"

    def get_proxy_url(self):
        file_id = self.item.get("id")
        file_name = urllib.parse.quote(self.item.get("name")) or "file_name.vid"
        self.constructed["behaviorHints"]["proxyHeaders"] = {
            "request": {"Server": "Stremio"}
        }
        return f"{self.proxy_url}/load/{file_id}/{file_name}"

    def get_gapi_url(self):
        file_id = self.item.get("id")
        file_name = urllib.parse.quote(self.item.get("name")) or "file_name.vid"
        self.constructed["behaviorHints"]["proxyHeaders"] = {
            "request": {"Authorization": f"Bearer {self.acc_token}"}
        }
        return f"https://www.googleapis.com/drive/v3/files/{file_id}?alt=media&file_name={file_name}"

    def construct_stream(self):
        self.constructed = {}
        self.constructed["behaviorHints"] = {}
        self.constructed["behaviorHints"]["notWebReady"] = "true"
        resolution = self.parsed.sortkeys.get("res", "1")
        self.constructed["behaviorHints"]["bingeGroup"] = f"gdrive-{resolution}"

        self.constructed["url"] = self.get_url()
        self.constructed["name"] = self.parsed.get_str(f"GDrive %resolution %quality")
        self.constructed["title"] = self.get_title()
        self.constructed["sortkeys"] = self.parsed.sortkeys

        return self.constructed

    def best_res(self, item):
        MAX_RES = 2160
        sortkeys = item.pop("sortkeys")
        resolution = sortkeys.get("res")

        try:
            res_map = {
                "hd": 720,
                "1280x720": 720,
                "1280x720p": 720,
                "1920x1080": 1080,
                "fhd": 1080,
                "uhd": 2160,
                "4k": 2160,
            }
            sort_int = res_map.get(resolution.lower()) or int(resolution[:-1])
        except (TypeError, AttributeError):
            sort_int = 1

        ptn_name = sanitize(sortkeys.get("title", ""), "")
        name_match = any(
            ptn_name.endswith(sanitize(title, "")) for title in self.strm_meta.titles
        )
        if not name_match:
            sort_int -= MAX_RES

        if self.strm_meta.type == "series":
            listify = lambda x: [x] if isinstance(x, int) or not x else x

            se_list = listify(sortkeys.get("se"))
            ep_list = listify(sortkeys.get("ep"))
            invalid_se = int(self.strm_meta.se) not in se_list
            invalid_ep = int(self.strm_meta.ep) not in ep_list

            if invalid_se or invalid_ep:
                sort_int -= MAX_RES * 2

        return sort_int
