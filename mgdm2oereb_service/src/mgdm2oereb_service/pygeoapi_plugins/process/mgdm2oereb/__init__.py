import json
import os
import uuid
import yaml
import logging
import base64
import zipfile
import requests
import time
from lxml import etree as ET
from pygeoapi.process.base import BaseProcessor, ProcessorExecuteError


class Mgdm2OerebTransformatorBase(BaseProcessor):
    """MGDM2OEREB Processor for documents from oereblex"""

    def __init__(self, processor_def):
        """
        Initialize object
        :param processor_def: provider definition
        :returns: mgdm2oereb_service.process.Mgdm2OerebTransformator
        """
        with open(os.environ.get('MGDM2OEREB_TRAFO_CONFIG'), "r") as stream:
            try:
                self.configuration = yaml.safe_load(stream)[self.__class__.__name__]
            except yaml.YAMLError as exc:
                print(exc)
        super().__init__(processor_def, self.configuration)
        self.ilivalidator_service_url = os.environ.get(
            'ILIVALIDATOR_SERVICE',
            'http://ilivalidator-service:8080/rest/jobs'
        )
        self.logger = logging.getLogger(__name__)
        self.job_id = self.create_uuid()
        self.job_path = self.create_working_dir(self.job_id, self.logger)
        self.mgdm2oereb_xsl_path = os.path.join(
            os.environ.get('MGDM2OEREB_PATH', '/mgdm2oereb'),
            'xsl'
        )
        self.zip_path = os.path.join(self.job_path, 'input.zip')
        self.result_xtf_file_name = os.environ.get('MGDM2OEREB_RESULT_XTF_NAME', 'OeREBKRMtrsfr_V2_0.xtf')
        self.result_xtf_path = os.path.join(
            self.job_path,
            self.result_xtf_file_name
        )
        self.output_log_file = 'output.ili.log'
        self.input_log_file = 'input.ili.log'

    def execute(self, data):
        raise NotImplementedError('This is a abstract base class and cant be used as is.')

    @staticmethod
    def create_xsl_trafo_path(self, mgdm2oereb_xsl_path, model_name):
        return os.path.join(
            mgdm2oereb_xsl_path,
            '{}.trafo.xsl'.format(model_name)
        )

    def __repr__(self):
        return '<{}> {} ({})'.format(
            self.__class__,
            self.configuration['id'],
            self.configuration['version']
        )

    @staticmethod
    def create_uuid():
        return str(uuid.uuid4())

    @staticmethod
    def create_working_dir(uid: str, logger):
        """
        Creates a working directory under /tmp

        Args:
            uid (str): The uuid4 which is used to create a unique directory.
            logger (logging.Logger): The logger instance.
        Returns:
            str: The path of the created directory.
        """

        working_dir = "/tmp/working_{}".format(uid)
        os.mkdir(working_dir)
        logger.info('Created working dir {}'.format(working_dir))
        return working_dir

    @staticmethod
    def decode_input_file(input_file_string: str):
        b = base64.b64decode(bytes(input_file_string, 'utf-8'))
        return b

    @staticmethod
    def unzip_input_file(zip_file_path: str, target_dir: str):
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

    @staticmethod
    def validate(xtf_content, ilivalidator_service_url, result_xtf_file_name, log_path, sleep_time_ms=1000):

        files = {
            'file': (result_xtf_file_name, xtf_content),
        }

        create_job_response = requests.post(
            ilivalidator_service_url,
            files=files
        )
        status_url = create_job_response.headers["Operation-Location"]
        while True:
            status_response = requests.get(status_url)
            body = json.loads(status_response.text)
            logging.info(body)
            if body["status"] == "SUCCEEDED":
                ili_log_path = body['logFileLocation']
                logging.info(ili_log_path)
                logging.info(log_path)
                log_content = requests.get(ili_log_path).text
                logging.info(log_content)
                with open(log_path, 'w') as fh:
                    fh.write(log_content)
                return log_path
            elif body["status"] == "PROCESSING":
                time.sleep(float(status_response.headers["Retry-After"])/1000)
            elif body["status"] == "ENQUEUED":
                time.sleep(sleep_time_ms/1000)
            else:
                raise AttributeError("unknown STATUS of ilivalidator service {}".format(body["status"]))

    @staticmethod
    def download_catalogue(catalogue_url, job_path, catalogue_file_name='supplement.xml'):
        catalogue_request = requests.get(catalogue_url)
        if catalogue_request.status_code == 200:
            catalogue_path = os.path.join(job_path, catalogue_file_name)
            with open(catalogue_path, 'w+') as fh:
                fh.write(catalogue_request.text)
            return catalogue_path
        raise ProcessorExecuteError('Catalogue could not be downloaded. Response was:\n{}'.format(
            catalogue_request.text
        ))

    @staticmethod
    def transform(xsl_trafo_path, xtf_path, result_xtf_path, params):
        xsl = ET.parse(xsl_trafo_path)
        transform = ET.XSLT(xsl)
        xml = ET.parse(xtf_path)

        result = transform(xml, **{k: ET.XSLT.strparam(v) for k, v in params.items()})
        with open(result_xtf_path, "wb") as fh:
            fh.write(result)
        return result
