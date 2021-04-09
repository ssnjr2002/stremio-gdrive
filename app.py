import os
import requests
from utils import gdrive
from flask import Flask, jsonify, abort

MANIFEST = {
    "id": "ssnjr.stremio.googledrive",
    "version": "1.0.2",
    "name": "GDrive",
    "description": "This plugin fetches content from goolag drive.",
    "logo": "https://fonts.gstatic.com/s/i/productlogos/drive_2020q4/v8/web-512dp/logo_drive_2020q4_color_1x_web_512dp.png",
    "resources": ["stream"],
    "types": ["movie", "series"],
    "catalogs": []
}


app = Flask(__name__)


def respond_with(data):
    resp = jsonify(data)
    resp.headers['Access-Control-Allow-Origin'] = '*'
    resp.headers['Access-Control-Allow-Headers'] = '*'
    resp.headers['X-Robots-Tag'] = 'noindex'
    return resp


@app.route('/')
def init():
    return respond_with({'status': 200})


@app.route('/manifest.json')
def addon_manifest():
    return respond_with(MANIFEST)


@app.route('/stream/<type>/<id>.json')
def addon_stream(type, id):
    if type not in MANIFEST['types']:
        abort(404)

    def query_gen(type, id):
        if type == 'series':
            id, se, ep = id.split(':')
            series_suffix = f"S{int(se):02d}E{int(ep):02d}"

        meta_url = f"https://v3-cinemeta.strem.io/meta/{type}/{id}.json"
        meta = requests.get(meta_url).json().get('meta')
        name = ' '.join(meta['slug'].split('/')[-1].split('-')[0:-1])
        year = meta['year'].split('–')[0]

        return f'{name} {series_suffix}' if type == 'series' else f'{name} {year}'

    search_q = query_gen(type=type, id=id)
    streams = gd.get_streams(search_q)

    app.logger.info(f'{search_q}: ({len(streams)})')
    return respond_with({'streams': streams})


if __name__ == '__main__':
    gd = gdrive()
    gd.cf_proxy_url = os.environ.get('CF_PROXY_URL')

    port = os.environ.get('PORT')
    app.run(threaded=True, debug=True, host="0.0.0.0", port=port)
