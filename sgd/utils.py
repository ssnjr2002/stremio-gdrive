import json
import requests

from sgd.cache import Pickle


def hr_size(size):
    """Bytes to human readable:
    https://stackoverflow.com/a/43690506"""
    for unit in ["B", "KiB", "MiB", "GiB", "TiB"]:
        if size < 1024.0:
            break
        size /= 1024.0
    return f"{size:.2f}{unit}"


def safe_get(list_, idx, default=""):
    try:
        return list_[idx]
    except IndexError:
        return default


def num_extract(string):
    num_chars = [ch if ch.isdigit() else ' ' for ch in string]
    return ''.join(num_chars).split()


def is_year(string):
    try:
        if (1850 <= int(string) <= 2050) and len(str(string)) == 4:
            return True
        return False
    except ValueError:
        return False


def sanitize(string, valid_chars=". "):
    """Return alphanumeric input with certain non alphanumeric chars intact"""
    chars = [ch if ch.isalnum() or ch in valid_chars else " " for ch in string]
    # Join -> split -> join to have just a single space b/w words
    return " ".join("".join(chars).split()).lower()


def req_wrapper(url, time_out=3):
    timeout = requests.exceptions.Timeout
    conn_err = requests.exceptions.ConnectionError

    cached_session = Pickle("requests_session.pickle")

    if cached_session.contents:
        req_session = cached_session.contents
    else:
        req_session = requests.session()
        req_session.headers = {
            "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36"
        }

    try:
        result = req_session.get(f"https://{url}", timeout=time_out).text
        cached_session.contents = req_session
        cached_session.save()
        return result
    except (timeout, conn_err):
        return ""


def req_api(url, key="meta"):
    try:
        r = req_wrapper(url)
        # imbd wont return proper json sometimes so:
        return json.loads(r[r.find("{") :].rstrip(")")).get(key)
    except json.decoder.JSONDecodeError:
        return dict()
