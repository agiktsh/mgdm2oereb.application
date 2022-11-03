import os
import logging
import uuid
import json
import time
import base64
import zipfile
import requests
import subprocess
from lxml import etree as ET
from pygeoapi.process.base import BaseProcessor, ProcessorExecuteError

LOGGER = logging.getLogger(__name__)

MGDM2OEREB_PATH = '/mgdm2oereb'
MGDM2OEREB_OEREBLEX_TRAFO_PY = 'oereblex.download.py'
RESULT_XTF_NAME = "OeREBKRMtrsfr_V2_0.xtf"
RESULT_OEREBLEX_XML_NAME = 'oereblex.xml'


#: Process metadata and description
PROCESS_METADATA = {
    'version': '0.2.0',
    'id': 'mgdm2oereb',
    'title': {
        'en': 'MGDM2OEREB',
        'fr': 'MGDM2OEREB',
        'de': 'MGDM2OEREB-oereblex'
    },
    'description': {
        'en': 'The process which will execute the transformation.',
    },
    'keywords': ['openoereb', 'ÖREB', 'INTERLIS', 'XSLT', ''],
    'links': [{
        'type': 'text/html',
        'rel': 'about',
        'title': 'information',
        'href': 'https://example.org/process',
        'hreflang': 'en-US'
    }],
    'inputs': {
        'zip_file': {
            'title': 'ZIP-File',
            'description': 'The ZIP file encapsulating the data which will be transformed.',
            'schema': {
                'type': 'string'
            },
            'minOccurs': 1,
            'maxOccurs': 1,
            'metadata': None,  # TODO how to use?
            'keywords': ['input']
        },
        'theme_code': {
            'title': 'Theme Code',
            'description': 'The theme code regarding to https://models.geo.admin.ch/V_D/OeREB/OeREBKRM_V2_0_Themen.xml (e.g. ch.Planungszonen)',
            'schema': {
                'type': 'string'
            },
            'minOccurs': 1,
            'maxOccurs': 1,
            'metadata': None,
            'keywords': ['message']
        },
        'model_name': {
            'title': 'Model Name',
            'description': 'The fully qualified model name regarding to the INTERLIS data you want to transform (e.g. Planungszonen_V1_1 or KbS_V1_5.)',
            'schema': {
                'type': 'string'
            },
            'minOccurs': 1,
            'maxOccurs': 1,
            'metadata': None,
            'keywords': ['message']
        },
        'catalog': {
            'title': 'Supplement Catalog',
            'description': 'The name of the catalog which will be used to pick the additional data from. (e.g. ch.sh.OeREBKRMkvs_supplement.xml)',
            'schema': {
                'type': 'string'
            },
            'minOccurs': 1,
            'maxOccurs': 1,
            'metadata': None,
            'keywords': ['message']
        }
    },
    'outputs': {
        'result': {
            'title': 'Transformed File',
            'description': 'The link to the transformed data.',
            'schema': {
                'type': 'object',
                'contentMediaType': 'application/json'
            }
        }
    },
    'example': {
        'inputs': {
            'zip_file': "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",
            'theme_code': 'ch.Planungszonen',
            'model_name': 'Planungszonen_V1_1',
            'catalog': 'ch.sh.OeREBKRMkvs_supplement.xml'
        }
    }
}


class Mgdm2OerebTransformator(BaseProcessor):
    """MGDM2OEREB Processor for documents from oereblex"""

    def __init__(self, processor_def):
        """
        Initialize object
        :param processor_def: provider definition
        :returns: mgdm2oereb_service.process_oereblex.Mgdm2OerebTransformatorOereblex
        """
        super().__init__(processor_def, PROCESS_METADATA)
        self._ilivalidator_service_url = os.environ.get(
            'ILIVALIDATOR_SERVICE',
            'http://ilivalidator-service:8080/rest/jobs'
        )

    def execute(self, data):
        mimetype = 'text/xml'
        zip_file = data.get('zip_file', None)
        theme_code = data.get('theme_code', None)
        model_name = data.get('model_name', None)
        catalog = data.get('catalog', None)

        if zip_file is None:
            raise ProcessorExecuteError('Cannot process without a zip_file')
        if theme_code is None:
            raise ProcessorExecuteError('Cannot process without a theme_code')
        if model_name is None:
            raise ProcessorExecuteError('Cannot process without a model_name')
        if catalog is None:
            raise ProcessorExecuteError('Cannot process without a catalog')
        LOGGER.info('All params are there. Starting with the process.')
        uuid_string = str(uuid.uuid4())
        working_dir_path = self.create_working_dir(uuid_string)
        mgdm2oereb_xsl_path = os.path.join(MGDM2OEREB_PATH, 'xsl')
        zip_path = os.path.join(working_dir_path, 'input.zip')

        with open(zip_path, 'wb') as input_file:
            input_file.write(self.decode_input_file(zip_file))
        xtf_path = self.unzip_input_file(zip_path, working_dir_path)
        with open(xtf_path, mode="rb") as fh:
            input_validation = self.validate(fh)
        result_xtf_path = os.path.join(working_dir_path, RESULT_XTF_NAME)
        xsl_trafo_path = os.path.join(
            mgdm2oereb_xsl_path,
            '{}.trafo.xsl'.format(model_name)
        )

        xsl = ET.parse(xsl_trafo_path)
        transform = ET.XSLT(xsl)
        xml = ET.parse(xtf_path)
        params = {
            "catalog": os.path.join(MGDM2OEREB_PATH, 'catalogs', catalog),
            "theme_code": theme_code,
            "model": model_name
        }
        result = transform(xml, **{k: ET.XSLT.strparam(v) for k, v in params.items()})

        with open(result_xtf_path, "wb") as fh:
            fh.write(result)

        with open(result_xtf_path, "rb") as fh:
            validation_result = self.validate(fh)

        return mimetype, bytes(result)

    def create_working_dir(self, uid: str):
        """
        Creates a working directory under /tmp

        Args:
            uid (str): The uuid4 which is used to create a unique directory.
        Returns:
            str: The path of the created directory.
        """

        working_dir = "/tmp/working_{}".format(uid)
        os.mkdir(working_dir)
        LOGGER.info('Created working dir {}'.format(working_dir))
        return working_dir

    def decode_input_file(self, input_file_string: str):
        b = base64.b64decode(bytes(input_file_string, 'utf-8'))
        return b

    def unzip_input_file(self, zip_file_path: str, target_dir: str):
        if not zipfile.is_zipfile(zip_file_path):
            raise ProcessorExecuteError('The sent file was not a valid zip.')
        with zipfile.ZipFile(zip_file_path, "r") as zip_ref:
            count_xtf = 0
            xtf_index = None
            for i, name in enumerate(zip_ref.namelist()):
                if name.endswith('.xtf'):
                    count_xtf += 1
                    xtf_index = i
            if count_xtf == 0:
                raise ProcessorExecuteError('The sent zip does not contain an XTF.')
            if count_xtf > 1:
                raise ProcessorExecuteError('The sent zip container more than 1 XTF.')
            xtf_file_name = zip_ref.namelist()[xtf_index]
            zip_ref.extract(xtf_file_name, path=target_dir)
            return os.path.join(target_dir, xtf_file_name)

    def validate(self, xtf_content):

        files = {
            'file': (RESULT_XTF_NAME, xtf_content),
        }

        create_job_response = requests.post(
            self._ilivalidator_service_url,
            files=files
        )
        status_url = create_job_response.headers["Operation-Location"]
        while True:
            status_response = requests.get(status_url)
            body = json.loads(status_response.text)
            logging.error(body)
            if body["status"] == "SUCCEEDED":
                return body
            elif body["status"] == "PROCESSING":
                time.sleep(float(status_response.headers["Retry-After"])/1000)
            elif body["status"] == "ENQUEUED":
                time.sleep(1000/1000)
            else:
                raise AttributeError("unknown STATUS of ilivalidator service {}".format(body["status"]))

    def __repr__(self):
        return '<Mgdm2OerebTransformator> {}'.format(self.name)
