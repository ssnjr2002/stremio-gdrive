import os
import requests
from flask import Flask, jsonify, abort
from utils import gdrive, MetadataNotFound

MANIFEST = {
    "id": "ssnjr.stremio.googledrive",
    "version": "1.0.7",
    "name": "GDrive",
    "description": "This plugin fetches content from goolag drive.",
    "logo": "https://fonts.gstatic.com/s/i/productlogos/drive_2020q4/v8/web-512dp/logo_drive_2020q4_color_1x_web_512dp.png",
    "resources": ["stream"],
    "types": ["movie", "series"],
    "catalogs": []
}

app = Flask(__name__)
gd = gdrive()
gd.cf_proxy_url = os.environ.get('CF_PROXY_URL')


def respond_with(data):
    resp = jsonify(data)
    resp.headers['Access-Control-Allow-Origin'] = '*'
    resp.headers['Access-Control-Allow-Headers'] = '*'
    resp.headers['X-Robots-Tag'] = 'noindex'
    return resp


@app.route('/')
def init():
    return 'Addon is alive.'


@app.route('/manifest.json')
def addon_manifest():
    return respond_with(MANIFEST)


@app.route('/stream/<type>/<id>.json')
def addon_stream(type, id):
    if type not in MANIFEST['types'] or id[:2] != 'tt':
        abort(404)
    try:
        return respond_with({'streams': gd.get_streams(type, id)})
    except MetadataNotFound as e:
        print(f'ERROR: {e}')
        abort(404)


if __name__ == '__main__':
    app.run(debug=True)
