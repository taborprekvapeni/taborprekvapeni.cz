# -*- coding: utf-8 -*-


import times
from flask import render_template, abort, request, send_file

from taborprekvapeni import app
from taborprekvapeni.image import Image
from taborprekvapeni.cache import cached
from taborprekvapeni.templating import url_for
from taborprekvapeni.models import BasicInfo, HistoryText, PhotoAlbums


@app.context_processor
def redefine():
    return {'url_for': url_for}


@app.context_processor
def inject_info():
    info = BasicInfo()

    now = times.to_local(times.now(), 'Europe/Prague')
    starts_at = info['senior']['starts_at']
    ends_at = info['senior']['ends_at']

    return {
        'info': info,
        'volume_year': starts_at.year,
        'volume_no': starts_at.year - 1997,
        'is_past': now.date() > ends_at,
        'countdown': (starts_at - now.date()).days,
    }


@app.route('/')
@cached()
def index():
    return render_template('index.html')


@app.route('/informace')
@cached()
def info():
    return render_template('info.html')


@app.route('/kontakt-prihlaska')
@cached()
def contact():
    return render_template('contact.html')


@app.route('/tym-vedoucich')
@cached()
def team():
    return render_template('team.html')


@app.route('/historie-fotky/<int:year>')
@app.route('/historie-fotky')
@cached()
def history(year=None):
    all_texts = HistoryText.find_all()
    all_albums = PhotoAlbums()

    if year:
        text = HistoryText(year) or abort(404)
        albums = all_albums.get(year, [])
        return render_template('history_detail.html', year=year, text=text,
                               all_texts=all_texts, albums=albums)
    return render_template('history.html', all_texts=all_texts)


@app.route('/image')
def image_proxy():
    url = request.args.get('url') or abort(404)

    w = request.args.get('width')
    h = request.args.get('height')

    img = Image.from_url(url)
    img.rotate()

    if w and h:
        img.resize_crop(int(w), int(h))
    img.sharpen()

    return send_file(img.to_stream(), mimetype='image/jpeg')