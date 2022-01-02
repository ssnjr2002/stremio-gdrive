import PTN


class parse_title:
    def __init__(self, name):
        ptn_dict = PTN.parse(name)
        key_list = [
            "resolution",
            "codec",
            "season",
            "episode",
            "bitDepth",
            "audio",
            "quality",
            "encoder",
            "title",
            "year",
            "remux",
        ]

        for key in key_list:
            setattr(self, key, ptn_dict.get(key))

        # Write REMUX instead of Blu-Ray
        self.quality = "REMUX" if self.remux else self.quality

        self.sortkeys = {
            "se": self.season,
            "ep": self.episode,
            "res": self.resolution,
            "title": self.title,
            "year": self.year,
        }

    def get_val(self, x, y):
        formatted = ""

        for word in x.split(y):
            if len(word) and word[0] == "%":
                string = getattr(self, word[1:], "")
                if string:
                    formatted += f"{string} "
                elif not string and y == ";":
                    return ""
            else:
                formatted += f"{word} "
        return formatted

    def get_str(self, format):
        self.formatted = ""

        for segment in format.split():
            if len(segment.split(";")) > 1:
                self.formatted += self.get_val(segment, ";")
            else:
                self.formatted += self.get_val(segment, " ")
        return self.formatted
