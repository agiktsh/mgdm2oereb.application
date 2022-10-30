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
    'id': 'mgdm2oereb-oereblex',
    'title': {
        'en': 'MGDM2OEREB-oereblex',
        'fr': 'MGDM2OEREB-oereblex',
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
        },
        'oereblex_host': {
            'title': 'ÖREBlex host',
            'description': 'The host which is used in the data (e.g. oereblex.sh.ch).',
            'schema': {
                'type': 'string'
            },
            'minOccurs': 1,
            'maxOccurs': 1,
            'metadata': None,
            'keywords': ['message']
        },
        'oereblex_canton': {
            'title': 'ÖREBlex Canton',
            'description': 'The shortened version of the cantons name (e.g. sh).',
            'schema': {
                'type': 'string'
            },
            'minOccurs': 1,
            'maxOccurs': 1,
            'metadata': None,
            'keywords': ['message']
        },
        'dummy_office_name': {
            'title': 'Dummy office name',
            'description': 'ÖREBlex delivers documents without responsible offices. This name is used in this case.',
            'schema': {
                'type': 'string'
            },
            'minOccurs': 1,
            'maxOccurs': 1,
            'metadata': None,
            'keywords': ['message']
        },
        'dummy_office_url': {
            'title': 'Dummy office url',
            'description': 'ÖREBlex delivers documents without responsible offices. This url is used in this case.',
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
            'zip_file': """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
SwUGAAAAAAEAAQBYAAAAWhAAAAAA""",
            'theme_code': 'ch.Planungszonen',
            'model_name': 'Planungszonen_V1_1',
            'catalog': 'ch.sh.OeREBKRMkvs_supplement.xml',
            'oereblex_host': 'oereblex.sh.ch',
            'oereblex_canton': 'sh',
            'dummy_office_name': 'AGI SH',
            'dummy_office_url': 'https://sh.ch/CMS/Webseite/Kanton-Schaffhausen/Beh-rde/Verwaltung/Volkswirtschaftsdepartement/Amt-f-r-Geoinformation-3854-DE.html'
        }
    }
}


class Mgdm2OerebTransformatorOereblex(BaseProcessor):
    """MGDM2OEREB Processor for documents from oereblex"""

    def __init__(self, processor_def):
        """
        Initialize object
        :param processor_def: provider definition
        :returns: mgdm2oereb_service.process.Mgdm2OerebTransformator
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
        oereblex_host = data.get('oereblex_host', None)
        oereblex_canton = data.get('oereblex_canton', None)
        dummy_office_name = data.get('dummy_office_name', None)
        dummy_office_url = data.get('dummy_office_url', None)

        if zip_file is None:
            raise ProcessorExecuteError('Cannot process without a zip_file')
        if theme_code is None:
            raise ProcessorExecuteError('Cannot process without a theme_code')
        if model_name is None:
            raise ProcessorExecuteError('Cannot process without a model_name')
        if catalog is None:
            raise ProcessorExecuteError('Cannot process without a catalog')
        if oereblex_host is None:
            raise ProcessorExecuteError('Cannot process without a oereblex_host')
        if oereblex_canton is None:
            raise ProcessorExecuteError('Cannot process without a oereblex_canton')
        if dummy_office_name is None:
            raise ProcessorExecuteError('Cannot process without a dummy_office_name')
        if dummy_office_url is None:
            raise ProcessorExecuteError('Cannot process without a dummy_office_url')
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
        result_oereblex_xml_path = os.path.join(working_dir_path, RESULT_OEREBLEX_XML_NAME)
        xsl_trafo_path = os.path.join(
            mgdm2oereb_xsl_path,
            '{}.oereblex.trafo.xsl'.format(model_name)
        )
        envars = {
            "GEOLINK_LIST_TRAFO_PATH": os.path.join(
                mgdm2oereb_xsl_path,
                "{}.oereblex.geolink_list.xsl".format(model_name)
            ),
            "XTF_PATH": xtf_path,
            "RESULT_FILE_PATH": result_oereblex_xml_path,
            "OEREBLEX_HOST": oereblex_host,
            "DUMMY_OFFICE_NAME": dummy_office_name,
            "DUMMY_OFFICE_URL": dummy_office_url,
        }
        envars.update(os.environ)
        path_to_python_file = os.path.join(mgdm2oereb_xsl_path, MGDM2OEREB_OEREBLEX_TRAFO_PY)
        call_args = ["python3", path_to_python_file]

        try:
            sub = subprocess.run(
                call_args,
                env=envars,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            )
            result = sub.stdout.decode("utf-8")
            logging.info(result)
        except subprocess.CalledProcessError as e:
            result = e.output
            logging.error(result)
            raise e

        xsl = ET.parse(xsl_trafo_path)
        transform = ET.XSLT(xsl)
        xml = ET.parse(xtf_path)
        params = {
            "catalog": os.path.join(MGDM2OEREB_PATH, 'catalogs', catalog),
            "theme_code": theme_code,
            "model": model_name,
            "oereblex_output": result_oereblex_xml_path,
            "oereblex_host": oereblex_host
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
