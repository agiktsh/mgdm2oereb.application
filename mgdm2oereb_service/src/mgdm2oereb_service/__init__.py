import pygeoapi
import os
import glob
pygeoapi.plugin.PLUGINS['process_manager']['CustomTinyDB'] = 'mgdm2oereb_service.pygeoapi_plugins.process_manager.tinydb.CustomTinyDBManager'
pygeoapi.plugin.PLUGINS['process']['Mgdm2Oereb'] = 'mgdm2oereb_service.pygeoapi_plugins.process.mgdm2oereb.processors.Mgdm2OerebTransformator'
pygeoapi.plugin.PLUGINS['process']['Mgdm2OerebOereblex'] = 'mgdm2oereb_service.pygeoapi_plugins.process.mgdm2oereb.processors.Mgdm2OerebTransformatorOereblex'
from markupsafe import escape
from lxml import etree
from flask import Flask, send_file, render_template, request
from pygeoapi.flask_app import BLUEPRINT
from pygeoapi.flask_app import STATIC_FOLDER
from urllib.parse import urlparse

parser = etree.XMLParser(remove_blank_text=True)

RESULTS_PATH = "mgdm2oereb_results"

app = Flask(__name__, static_folder=STATIC_FOLDER, static_url_path='/static')

app.register_blueprint(BLUEPRINT, url_prefix='/oapi')


def upgrade_url_to_https(url):
    o = urlparse(url)
    o._replace(scheme='https')
    return o.geturl()

@app.route(f'/{RESULTS_PATH}/<path:file_name>')
def mgdm2oereb_results_xtf(file_name):
    if file_name.endswith('.log'):
        mimetype = "text/plain"
    elif file_name.endswith('.xtf'):
        mimetype = "text/xml"
    elif file_name.endswith('.xml'):
        mimetype = "text/xml"
    else:
        mimetype = None
    return send_file(
        f'/data/{file_name}',
        mimetype=mimetype,
        download_name=file_name
    )

@app.route(f'/{RESULTS_PATH}/<path:uid>/index.html')
def mgdm2oereb_results_index(uid):
    file_paths = glob.glob(f"/data/*{uid}*")
    file_paths.sort()
    content = []
    for file_path in file_paths:
        content.append(f"/{RESULTS_PATH}/{os.path.basename(file_path)}")
    return render_template("index.html", content=content)


@app.route("/published_feed")
def pubished_feed():
    content = []
    file_paths = glob.glob("/data/*.rss.xml")
    file_paths.sort()
    if request.headers.get('X-Forwarded-Proto') == 'https':
        url = upgrade_url_to_https(request.host_url)
        base_url = upgrade_url_to_https(request.base_url)
    else:
        url = request.host_url
        base_url = request.base_url

    for file_path in file_paths:
        with open(file_path, mode="r") as file_handler:
            root = etree.fromstring(file_handler.read())
            for link in root.xpath('//link'):
                link.text = f'{url}{link.text}'
            for guid in root.xpath('//guid'):
                guid.text = f'{url}{guid.text}'
            content.append(etree.tostring(root, pretty_print=True).decode())
    return render_template(
        "feed.xml",
        content=content,
        content_type='application/rss+xml',
        url=base_url
    )
