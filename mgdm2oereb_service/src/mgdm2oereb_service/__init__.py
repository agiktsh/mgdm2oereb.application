import pygeoapi
import os
import glob
pygeoapi.plugin.PLUGINS['process_manager']['CustomTinyDB'] = 'mgdm2oereb_service.pygeoapi_plugins.process_manager.tinydb.CustomTinyDBManager'
pygeoapi.plugin.PLUGINS['process']['Mgdm2Oereb'] = 'mgdm2oereb_service.pygeoapi_plugins.process.mgdm2oereb.processors.Mgdm2OerebTransformator'
pygeoapi.plugin.PLUGINS['process']['Mgdm2OerebOereblex'] = 'mgdm2oereb_service.pygeoapi_plugins.process.mgdm2oereb.processors.Mgdm2OerebTransformatorOereblex'
from markupsafe import escape
from flask import Flask, send_file, render_template
from pygeoapi.flask_app import BLUEPRINT
from pygeoapi.flask_app import STATIC_FOLDER

RESULTS_PATH = "mgdm2oereb_results"

app = Flask(__name__, static_folder=STATIC_FOLDER, static_url_path='/static')

app.register_blueprint(BLUEPRINT, url_prefix='/oapi')

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
    for file_path in file_paths:
        with open(file_path, mode="r") as file_handler:
            content.append(file_handler.read())
    return render_template("feed.xml", content=content, content_type='application/xml')
