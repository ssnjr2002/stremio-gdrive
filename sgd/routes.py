from sgd import app, gdrive
from sgd.meta import MetadataNotFound, CachedMeta
from sgd.streams import Streams
from flask import jsonify, abort
from datetime import datetime


MANIFEST = {
    "id": "ssnjr.stremio.googledrive",
    "version": "1.0.9",
    "name": "GDrive",
    "description": "This plugin fetches content from goolag drive.",
    "logo": "https://fonts.gstatic.com/s/i/productlogos/drive_2020q4/v8/web-512dp/logo_drive_2020q4_color_1x_web_512dp.png",
    "resources": ["stream"],
    "types": ["movie", "series"],
    "catalogs": [],
}


def respond_with(data):
    resp = jsonify(data)
    resp.headers["Access-Control-Allow-Origin"] = "*"
    resp.headers["Access-Control-Allow-Headers"] = "*"
    resp.headers["X-Robots-Tag"] = "noindex"
    return resp


@app.route("/")
def init():
    return "Addon is alive."


@app.route("/manifest.json")
def addon_manifest():
    return respond_with(MANIFEST)


@app.route("/stream/<stream_type>/<stream_id>.json")
def addon_stream(stream_type, stream_id):
    if stream_type not in MANIFEST["types"] or stream_id[:2] != "tt":
        abort(404)
    try:
        start_time = datetime.now()

        stream_meta = CachedMeta(stream_type, stream_id)
        gdrive.search(stream_meta)
        streams = Streams(gdrive, stream_meta)

        time_taken = (datetime.now() - start_time).total_seconds()
        print(
            f"Fetched {len(streams.results)} stream(s) in "
            f"{time_taken:.3f}s for ({stream_id}) {gdrive.query}"
        )
        return respond_with({"streams": streams.results})

    except MetadataNotFound as e:
        print(f"ERROR: {e}")
        abort(404)
