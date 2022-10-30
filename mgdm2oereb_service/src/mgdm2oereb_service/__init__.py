import pygeoapi
pygeoapi.plugin.PLUGINS['process_manager']['CustomTinyDB'] = 'mgdm2oereb_service.pygeoapi_plugins.tinydb.CustomTinyDBManager'
pygeoapi.plugin.PLUGINS['process']['Mgdm2Oereb'] = 'mgdm2oereb_service.process.Mgdm2OerebTransformator'
pygeoapi.plugin.PLUGINS['process']['Mgdm2OerebOereblex'] = 'mgdm2oereb_service.process_oereblex.Mgdm2OerebTransformatorOereblex'
from markupsafe import escape
from flask import Flask, send_file
from pygeoapi.flask_app import BLUEPRINT
from pygeoapi.flask_app import STATIC_FOLDER

app = Flask(__name__, static_folder=STATIC_FOLDER, static_url_path='/static')

app.register_blueprint(BLUEPRINT, url_prefix='/oapi')


@app.route('/mgdm2oereb_results/<path:job_result_id>')
def mgdm2oereb_results(job_result_id):
    return send_file(
        '/tmp/working_{}/OeREBKRMtrsfr_V2_0.xtf'.format(escape(job_result_id)),
        mimetype='text/xml',
        as_attachment=True,
        download_name='OeREBKRMtrsfr_V2_0.xtf'
    )
