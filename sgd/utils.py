import requests


def hr_size(size):
    """Bytes to human readable:
    https://stackoverflow.com/a/43690506"""
    for unit in ["B", "KiB", "MiB", "GiB", "TiB"]:
        if size < 1024.0:
            break
        size /= 1024.0
    return f"{size:.2f}{unit}"


def sanitize(string):
    """Return alphanumeric input with certain non alphanumeric chars intact"""
    valid_chars = ". "
    chars = [ch if ch.isalnum() or ch in valid_chars else " " for ch in string]
    # Joining twice to have just a single space b/w words
    return " ".join("".join(chars).split()).lower()


def req_wrapper(url, time_out=3):
    timeout = requests.exceptions.Timeout
    conn_err = requests.exceptions.ConnectionError

    req_session = requests.session()
    req_session.headers = {
        "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36"
    }

    try:
        return req_session.get(f"https://{url}", timeout=time_out).text
    except (timeout, conn_err):
        return ""


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
