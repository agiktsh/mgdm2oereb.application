# =================================================================
#
# Authors: Tom Kralidis <tomkralidis@gmail.com>
#          Norman Barker <norman.barker@gmail.com>
#
# Copyright (c) 2022 Tom Kralidis
#
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation
# files (the "Software"), to deal in the Software without
# restriction, including without limitation the rights to use,
# copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following
# conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
# OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.
#
# =================================================================

"""Flask module providing the route paths to the api"""
import json
import os
import logging
from datetime import datetime, timezone
from http import HTTPStatus
from typing import Union, Any, Tuple

import click

from flask import Flask, Blueprint, make_response, request, send_from_directory

from pygeoapi.api import API, APIRequest, gzip, pre_process, SYSTEM_LOCALE, FORMAT_TYPES, F_JSON, F_HTML
from pygeoapi.util import get_mimetype, yaml_load, get_api_rules, JobStatus, render_j2_template, \
    DATETIME_FORMAT, to_json, json_serial

logger = logging.getLogger(__name__)


class CustomApi(API):



    @gzip
    @pre_process
    def get_jobs(self, request: Union[APIRequest, Any],
                 job_id=None) -> Tuple[dict, int, str]:
        """
        Get process jobs

        :param request: A request object
        :param job_id: id of job

        :returns: tuple of headers, status code, content
        """

        if not request.is_valid():
            return self.get_format_exception(request)
        headers = request.get_response_headers(SYSTEM_LOCALE,
                                               **self.api_headers)
        if self.manager:
            if job_id is None:
                jobs = sorted(self.manager.get_jobs(),
                              key=lambda k: k['job_start_datetime'],
                              reverse=True)
            else:
                jobs = [self.manager.get_job(job_id)]
        else:
            logger.debug('Process management not configured')
            jobs = []

        serialized_jobs = {
            'jobs': [],
            'links': [{
                'href': f"{self.base_url}/jobs?f={F_HTML}",
                'rel': request.get_linkrel(F_HTML),
                'type': FORMAT_TYPES[F_HTML],
                'title': 'Jobs list as HTML'
            }, {
                'href': f"{self.base_url}/jobs?f={F_JSON}",
                'rel': request.get_linkrel(F_JSON),
                'type': FORMAT_TYPES[F_JSON],
                'title': 'Jobs list as JSON'
            }]
        }
        for job_ in jobs:
            job2 = {
                'processID': job_['process_id'],
                'jobID': job_['identifier'],
                'status': job_['status'],
                'message': job_['message'],
                'progress': job_['progress'],
                'parameters': job_.get('parameters'),
                'job_start_datetime': job_['job_start_datetime'],
                'job_end_datetime': job_['job_end_datetime']
            }

            # TODO: translate
            if JobStatus[job_['status']] in (
                    JobStatus.successful, JobStatus.running, JobStatus.accepted, JobStatus.failed):

                job_result_url = f"{self.base_url}/jobs/{job_['identifier']}/results"  # noqa

                job2['links'] = [{
                    'href': f'{job_result_url}?f={F_HTML}',
                    'rel': 'about',
                    'type': FORMAT_TYPES[F_HTML],
                    'title': f'results of job {job_id} as HTML'
                }, {
                    'href': f'{job_result_url}?f={F_JSON}',
                    'rel': 'about',
                    'type': FORMAT_TYPES[F_JSON],
                    'title': f'results of job {job_id} as JSON'
                }]

                if job_['mimetype'] not in (FORMAT_TYPES[F_JSON],
                                            FORMAT_TYPES[F_HTML]):
                    job2['links'].append({
                        'href': job_result_url,
                        'rel': 'about',
                        'type': job_['mimetype'],
                        'title': f"results of job {job_id} as {job_['mimetype']}"  # noqa
                    })

            serialized_jobs['jobs'].append(job2)

        if job_id is None:
            j2_template = 'jobs/index.html'
        else:
            serialized_jobs = serialized_jobs['jobs'][0]
            j2_template = 'jobs/job.html'

        if request.format == F_HTML:
            data = {
                'jobs': serialized_jobs,
                'now': datetime.now(timezone.utc).strftime(DATETIME_FORMAT)
            }
            response = render_j2_template(self.tpl_config, j2_template, data,
                                          request.locale)
            return headers, HTTPStatus.OK, response

        return headers, HTTPStatus.OK, to_json(serialized_jobs,
                                               self.pretty_print)

    @gzip
    @pre_process
    def get_job_result(self, request: Union[APIRequest, Any],
                       job_id) -> Tuple[dict, int, str]:
        """
        Get result of job (instance of a process)

        :param request: A request object
        :param job_id: ID of job

        :returns: tuple of headers, status code, content
        """

        if not request.is_valid():
            return self.get_format_exception(request)
        headers = request.get_response_headers(SYSTEM_LOCALE,
                                               **self.api_headers)
        job = self.manager.get_job(job_id)

        if not job:
            msg = 'job not found'
            return self.get_exception(HTTPStatus.NOT_FOUND, headers,
                                      request.format, 'NoSuchJob', msg)

        status = JobStatus[job['status']]

        if status == JobStatus.running:
            msg = 'job still running'
            return self.get_exception(
                HTTPStatus.NOT_FOUND, headers,
                request.format, 'ResultNotReady', msg)

        elif status == JobStatus.accepted:
            # NOTE: this case is not mentioned in the specification
            msg = 'job accepted but not yet running'
            return self.get_exception(
                HTTPStatus.NOT_FOUND, headers,
                request.format, 'ResultNotReady', msg)
        mimetype, job_output = self.manager.get_job_result(job_id)

        if mimetype not in (None, FORMAT_TYPES[F_JSON]):
            headers['Content-Type'] = mimetype
            content = job_output
        else:
            if request.format == F_JSON:
                content = json.dumps(job_output, sort_keys=True, indent=4,
                                     default=json_serial)
            else:
                # HTML
                data = {
                    'job': {'id': job_id},
                    'result': job_output
                }
                content = render_j2_template(
                    self.config, 'jobs/results/index.html',
                    data, request.locale)

        return headers, HTTPStatus.OK, content


if 'PYGEOAPI_CONFIG' not in os.environ:
    raise RuntimeError('PYGEOAPI_CONFIG environment variable not set')

with open(os.environ.get('PYGEOAPI_CONFIG'), encoding='utf8') as fh:
    CONFIG = yaml_load(fh)

API_RULES = get_api_rules(CONFIG)

STATIC_FOLDER = 'static'
if 'templates' in CONFIG['server']:
    STATIC_FOLDER = CONFIG['server']['templates'].get('static', 'static')

APP = Flask(__name__, static_folder=STATIC_FOLDER, static_url_path='/static')
APP.url_map.strict_slashes = API_RULES.strict_slashes

BLUEPRINT = Blueprint(
    'pygeoapi',
    __name__,
    static_folder=STATIC_FOLDER,
    url_prefix=API_RULES.get_url_prefix('flask')
)

# CORS: optionally enable from config.
if CONFIG['server'].get('cors', False):
    try:
        from flask_cors import CORS
        CORS(APP)
    except ModuleNotFoundError:
        print('Python package flask-cors required for CORS support')

APP.config['JSONIFY_PRETTYPRINT_REGULAR'] = CONFIG['server'].get(
    'pretty_print', True)

api_ = CustomApi(CONFIG)

OGC_SCHEMAS_LOCATION = CONFIG['server'].get('ogc_schemas_location')

if (OGC_SCHEMAS_LOCATION is not None and
        not OGC_SCHEMAS_LOCATION.startswith('http')):
    # serve the OGC schemas locally

    if not os.path.exists(OGC_SCHEMAS_LOCATION):
        raise RuntimeError('OGC schemas misconfigured')

    @BLUEPRINT.route('/schemas/<path:path>', methods=['GET'])
    def schemas(path):
        """
        Serve OGC schemas locally

        :param path: path of the OGC schema document

        :returns: HTTP response
        """

        full_filepath = os.path.join(OGC_SCHEMAS_LOCATION, path)
        dirname_ = os.path.dirname(full_filepath)
        basename_ = os.path.basename(full_filepath)

        # TODO: better sanitization?
        path_ = dirname_.replace('..', '').replace('//', '')
        return send_from_directory(path_, basename_,
                                   mimetype=get_mimetype(basename_))


def get_response(result: tuple):
    """
    Creates a Flask Response object and updates matching headers.

    :param result: The result of the API call.
                   This should be a tuple of (headers, status, content).

    :returns: A Response instance.
    """

    headers, status, content = result
    response = make_response(content, status)

    if headers:
        response.headers = headers
    return response


@BLUEPRINT.route('/')
def landing_page():
    """
    OGC API landing page endpoint

    :returns: HTTP response
    """
    return get_response(api_.landing_page(request))


@BLUEPRINT.route('/openapi')
def openapi():
    """
    OpenAPI endpoint

    :returns: HTTP response
    """
    with open(os.environ.get('PYGEOAPI_OPENAPI'), encoding='utf8') as ff:
        if os.environ.get('PYGEOAPI_OPENAPI').endswith(('.yaml', '.yml')):
            openapi_ = yaml_load(ff)
        else:  # JSON string, do not transform
            openapi_ = ff.read()

    return get_response(api_.openapi(request, openapi_))


@BLUEPRINT.route('/conformance')
def conformance():
    """
    OGC API conformance endpoint

    :returns: HTTP response
    """
    return get_response(api_.conformance(request))


@BLUEPRINT.route('/collections')
@BLUEPRINT.route('/collections/<path:collection_id>')
def collections(collection_id=None):
    """
    OGC API collections endpoint

    :param collection_id: collection identifier

    :returns: HTTP response
    """
    return get_response(api_.describe_collections(request, collection_id))


@BLUEPRINT.route('/collections/<path:collection_id>/queryables')
def collection_queryables(collection_id=None):
    """
    OGC API collections querybles endpoint

    :param collection_id: collection identifier

    :returns: HTTP response
    """
    return get_response(api_.get_collection_queryables(request, collection_id))


@BLUEPRINT.route('/collections/<path:collection_id>/items',
                 methods=['GET', 'POST', 'OPTIONS'],
                 provide_automatic_options=False)
@BLUEPRINT.route('/collections/<path:collection_id>/items/<path:item_id>',
                 methods=['GET', 'PUT', 'DELETE', 'OPTIONS'],
                 provide_automatic_options=False)
def collection_items(collection_id, item_id=None):
    """
    OGC API collections items endpoint

    :param collection_id: collection identifier
    :param item_id: item identifier

    :returns: HTTP response
    """

    if item_id is None:
        if request.method == 'GET':  # list items
            return get_response(
                api_.get_collection_items(request, collection_id))
        elif request.method == 'POST':  # filter or manage items
            if request.content_type is not None:
                if request.content_type == 'application/geo+json':
                    return get_response(
                        api_.manage_collection_item(request, 'create',
                                                    collection_id))
                else:
                    return get_response(
                        api_.post_collection_items(request, collection_id))
        elif request.method == 'OPTIONS':
            return get_response(
                api_.manage_collection_item(request, 'options', collection_id))

    elif request.method == 'DELETE':
        return get_response(
            api_.manage_collection_item(request, 'delete',
                                        collection_id, item_id))
    elif request.method == 'PUT':
        return get_response(
            api_.manage_collection_item(request, 'update',
                                        collection_id, item_id))
    elif request.method == 'OPTIONS':
        return get_response(
            api_.manage_collection_item(request, 'options',
                                        collection_id, item_id))
    else:
        return get_response(
            api_.get_collection_item(request, collection_id, item_id))


@BLUEPRINT.route('/collections/<path:collection_id>/coverage')
def collection_coverage(collection_id):
    """
    OGC API - Coverages coverage endpoint

    :param collection_id: collection identifier

    :returns: HTTP response
    """
    return get_response(api_.get_collection_coverage(request, collection_id))


@BLUEPRINT.route('/collections/<path:collection_id>/coverage/domainset')
def collection_coverage_domainset(collection_id):
    """
    OGC API - Coverages coverage domainset endpoint

    :param collection_id: collection identifier

    :returns: HTTP response
    """
    return get_response(api_.get_collection_coverage_domainset(
        request, collection_id))


@BLUEPRINT.route('/collections/<path:collection_id>/coverage/rangetype')
def collection_coverage_rangetype(collection_id):
    """
    OGC API - Coverages coverage rangetype endpoint

    :param collection_id: collection identifier

    :returns: HTTP response
    """
    return get_response(api_.get_collection_coverage_rangetype(
        request, collection_id))


@BLUEPRINT.route('/collections/<path:collection_id>/tiles')
def get_collection_tiles(collection_id=None):
    """
    OGC open api collections tiles access point

    :param collection_id: collection identifier

    :returns: HTTP response
    """
    return get_response(api_.get_collection_tiles(
        request, collection_id))


@BLUEPRINT.route('/collections/<path:collection_id>/tiles/<tileMatrixSetId>')
@BLUEPRINT.route('/collections/<path:collection_id>/tiles/<tileMatrixSetId>/metadata')  # noqa
def get_collection_tiles_metadata(collection_id=None, tileMatrixSetId=None):
    """
    OGC open api collection tiles service metadata

    :param collection_id: collection identifier
    :param tileMatrixSetId: identifier of tile matrix set

    :returns: HTTP response
    """
    return get_response(api_.get_collection_tiles_metadata(
        request, collection_id, tileMatrixSetId))


@BLUEPRINT.route('/collections/<path:collection_id>/tiles/\
<tileMatrixSetId>/<tileMatrix>/<tileRow>/<tileCol>')
def get_collection_tiles_data(collection_id=None, tileMatrixSetId=None,
                              tileMatrix=None, tileRow=None, tileCol=None):
    """
    OGC open api collection tiles service data

    :param collection_id: collection identifier
    :param tileMatrixSetId: identifier of tile matrix set
    :param tileMatrix: identifier of {z} matrix index
    :param tileRow: identifier of {y} matrix index
    :param tileCol: identifier of {x} matrix index

    :returns: HTTP response
    """
    return get_response(api_.get_collection_tiles_data(
        request, collection_id, tileMatrixSetId, tileMatrix, tileRow, tileCol))


@BLUEPRINT.route('/collections/<collection_id>/map')
@BLUEPRINT.route('/collections/<collection_id>/styles/<style_id>/map')
def collection_map(collection_id, style_id=None):
    """
    OGC API - Maps map render endpoint

    :param collection_id: collection identifier
    :param style_id: style identifier

    :returns: HTTP response
    """

    headers, status_code, content = api_.get_collection_map(
        request, collection_id, style_id)

    response = make_response(content, status_code)

    if headers:
        response.headers = headers

    return response


@BLUEPRINT.route('/processes')
@BLUEPRINT.route('/processes/<path:process_id>')
def get_processes(process_id=None):
    """
    OGC API - Processes description endpoint

    :param process_id: process identifier

    :returns: HTTP response
    """
    return get_response(api_.describe_processes(request, process_id))


@BLUEPRINT.route('/jobs')
@BLUEPRINT.route('/jobs/<job_id>',
                 methods=['GET', 'DELETE'])
def get_jobs(job_id=None):
    """
    OGC API - Processes jobs endpoint

    :param job_id: job identifier

    :returns: HTTP response
    """

    if job_id is None:
        return get_response(api_.get_jobs(request))
    else:
        if request.method == 'DELETE':  # dismiss job
            return get_response(api_.delete_job(job_id))
        else:  # Return status of a specific job
            return get_response(api_.get_jobs(request, job_id))


@BLUEPRINT.route('/processes/<path:process_id>/execution', methods=['POST'])
def execute_process_jobs(process_id):
    """
    OGC API - Processes execution endpoint

    :param process_id: process identifier

    :returns: HTTP response
    """

    return get_response(api_.execute_process(request, process_id))


@BLUEPRINT.route('/jobs/<job_id>/results',
                 methods=['GET'])
def get_job_result(job_id=None):
    """
    OGC API - Processes job result endpoint

    :param job_id: job identifier

    :returns: HTTP response
    """
    return get_response(api_.get_job_result(request, job_id))


@BLUEPRINT.route('/jobs/<job_id>/results/<resource>',
                 methods=['GET'])
def get_job_result_resource(job_id, resource):
    """
    OGC API - Processes job result resource endpoint

    :param job_id: job identifier
    :param resource: job resource

    :returns: HTTP response
    """
    return get_response(api_.get_job_result_resource(
        request, job_id, resource))


@BLUEPRINT.route('/collections/<path:collection_id>/position')
@BLUEPRINT.route('/collections/<path:collection_id>/area')
@BLUEPRINT.route('/collections/<path:collection_id>/cube')
@BLUEPRINT.route('/collections/<path:collection_id>/radius')
@BLUEPRINT.route('/collections/<path:collection_id>/trajectory')
@BLUEPRINT.route('/collections/<path:collection_id>/corridor')
@BLUEPRINT.route('/collections/<path:collection_id>/instances/<instance_id>/position')  # noqa
@BLUEPRINT.route('/collections/<path:collection_id>/instances/<instance_id>/area')  # noqa
@BLUEPRINT.route('/collections/<path:collection_id>/instances/<instance_id>/cube')  # noqa
@BLUEPRINT.route('/collections/<path:collection_id>/instances/<instance_id>/radius')  # noqa
@BLUEPRINT.route('/collections/<path:collection_id>/instances/<instance_id>/trajectory')  # noqa
@BLUEPRINT.route('/collections/<path:collection_id>/instances/<instance_id>/corridor')  # noqa
def get_collection_edr_query(collection_id, instance_id=None):
    """
    OGC EDR API endpoints

    :param collection_id: collection identifier
    :param instance_id: instance identifier

    :returns: HTTP response
    """
    query_type = request.path.split('/')[-1]
    return get_response(api_.get_collection_edr_query(request, collection_id,
                                                      instance_id, query_type))


@BLUEPRINT.route('/stac')
def stac_catalog_root():
    """
    STAC root endpoint

    :returns: HTTP response
    """
    return get_response(api_.get_stac_root(request))


@BLUEPRINT.route('/stac/<path:path>')
def stac_catalog_path(path):
    """
    STAC path endpoint

    :param path: path

    :returns: HTTP response
    """
    return get_response(api_.get_stac_path(request, path))


APP.register_blueprint(BLUEPRINT)


@click.command()
@click.pass_context
@click.option('--debug', '-d', default=False, is_flag=True, help='debug')
def serve(ctx, server=None, debug=False):
    """
    Serve pygeoapi via Flask. Runs pygeoapi
    as a flask server. Not recommend for production.

    :param server: `string` of server type
    :param debug: `bool` of whether to run in debug mode

    :returns: void
    """

    # setup_logger(CONFIG['logging'])
    APP.run(debug=True, host=api_.config['server']['bind']['host'],
            port=api_.config['server']['bind']['port'])


if __name__ == '__main__':  # run locally, for testing
    serve()
