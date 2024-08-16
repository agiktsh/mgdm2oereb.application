import json
import os
import uuid

import yaml
import logging
import base64
import zipfile
import requests
import time
import datetime
from lxml import etree as ET
from email import utils
from pygeoapi.process.base import BaseProcessor, ProcessorExecuteError
from pygeoapi.util import JobStatus


class JobFile(object):

    def __init__(self, name, job_id, job_folder, web_folder, theme_code, timestamp, target_basket_id):
        """

        Args:
            name (str): The last part of the name which identifies a file.
            job_id (str): The id string which makes the file name unique.
            job_folder (str): An absolute folder path where the job files should be stored while processing
                (folder must exist).
            web_folder (str): An absolute folder path where the file should be stored for final publishing
                (folder must exist).
            theme_code (str): The theme code which is used as a part of the name.
            timestamp (datetime.datetime): The timestamp when this job was created.
            target_basket_id (str): The id bfs of a municipality which might be used as part of the name
                (default: None).
        """
        self.name = name
        self.job_id = job_id
        self.job_folder = job_folder
        self.web_folder = web_folder
        self.theme_code = theme_code
        self.target_basket_id = target_basket_id
        self.time_string = timestamp.strftime('%Y-%m-%d_%H%M%S%s')
        self.runtime_content = None
        self.runtime_path = None
        self.result_content = None
        self.result_path = None

    def write_file(self, path, content):
        with open(path, mode="wb+") as file_handler:
            file_handler.write(content)

    def file_name(self):
        if self.target_basket_id:
            return ".".join([
                self.time_string,
                self.theme_code,
                self.target_basket_id,
                self.job_id,
                self.name
            ])
        else:
            return ".".join([
                self.time_string,
                self.theme_code,
                self.job_id,
                self.name
            ])

    def save_runtime_file(self, content):
        """
        Args:
            content (buffer): The content which should be saved to the file.
        Returns:
            str: The absolute file system path to the persisted file.
        """
        path = os.path.join(
            self.job_folder,
            self.file_name()
        )
        self.write_file(path, content)
        self.runtime_content = content
        self.runtime_path = path
        return path

    def save_result_file(self, content):
        """
        Args:
            content (buffer): The content which should be saved to the file.
        Returns:
            str: The absolute file system path to the persisted file.
        """
        path = os.path.join(
            self.web_folder,
            self.file_name()
        )
        self.write_file(path, content)
        self.result_content = content
        self.result_path = path
        return path


class Mgdm2OerebTransformatorBase(BaseProcessor):
    """MGDM2OEREB Processor for documents from oereblex"""

    def __init__(self, processor_def):
        """
        Initialize object
        :param processor_def: provider definition
        :returns: mgdm2oereb_service.process.Mgdm2OerebTransformator
        """
        from mgdm2oereb_service.app import RESULTS_PATH
        self.absolute_result_dir = RESULTS_PATH
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
        self.data_path = os.environ.get(
            'MGDM2OEREB_DATA',
            '/data'
        )
        self.job_dir = os.environ.get(
            'MGDM2OEREB_JOB',
            '/job'
        )
        self.job_path = self.create_working_dir(self.job_id, self.logger, self.job_dir)
        self.mgdm2oereb_xsl_path = os.path.join(
            os.environ.get('MGDM2OEREB_PATH', '/mgdm2oereb'),
            'xsl'
        )
        self.zip_file_name = 'input.zip'
        self.input_xtf_file_name = 'input.xtf'
        self.result_xtf_file_name = os.environ.get('MGDM2OEREB_RESULT_XTF_NAME', 'OeREBKRMtrsfr_V2_0.xtf')
        self.output_log_file_name = 'output.ili.log'
        self.input_log_file_name = 'input.ili.log'
        self.rss_snippet_file_name = "rss.xml"
        self.json_snippet_file_name = "job.json"
        self.catalog_file_name = "supplement_catalog.xtf"
        self.municipality_id = None
        self.timestamp = datetime.datetime.now()

    def create_job_file(self, name, theme_code, target_basket_id):
        return JobFile(
            name,
            self.job_id,
            self.job_path,
            self.data_path,
            theme_code,
            self.timestamp,
            target_basket_id
        )

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
        """
        Simple wrapper to provide a uuid4 string.

        Returns:
            str: The string encapsulating the freshly made UUID4
        """
        return str(uuid.uuid4())

    @staticmethod
    def create_working_dir(uid, logger, root='/job'):
        """
        Creates a working directory under `root`

        Args:
            uid (str): The uuid4 which is used to create a unique directory.
            logger (logging.Logger): The logger instance.
            root (str): The root folder of the working directory. Needs write permissions! (default='/data'
        Returns:
            str: The path of the created directory.
        """
        working_dir = os.path.join(root, "working_{}".format(uid))
        os.makedirs(working_dir, exist_ok=True)
        logger.info('Created working dir {}'.format(working_dir))
        return working_dir

    @staticmethod
    def decode_input_file(input_file_string):
        """
        Parses a base64 encoded string to a binary. It is used to decode the uploaded data.

        Args:
            input_file_string (str): A base64 encoded string.
        Returns:
            binary or string: The decoded element (binary or str).
        """
        return base64.b64decode(bytes(input_file_string, 'utf-8'))

    @staticmethod
    def unzip_input_file(zip_file_path, target_dir):
        """
        Inflates a zip to a target dir.

        Args:
            zip_file_path (str): The path of to the zip file.
            target_dir (str): The path to the directory where the zip should be extracted.
        Returns:
            str: The valid path of the extracted XTF which was contained in the zip.
        """

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
            with open(os.path.join(target_dir, xtf_file_name), mode="rb") as xtf_file:
                return xtf_file.read()

    @staticmethod
    def validate(xtf_content, ilivalidator_service_url, result_xtf_file_name, sleep_time_ms=1000,
                 all_objects_accessible=True):
        """
        Uses the external ILI validator service to validate an XTF.

        Args:
            xtf_content (bin): The XTF content which should be validated (not the file!).
            ilivalidator_service_url (str): The URI to the validation service.
            result_xtf_file_name (str): The file name corresponding to xtf_content (for logging reasons).
            sleep_time_ms (int): Validation runs async. So we need to check when our job was ready. This
                defines the wait time in milliseconds for next ready check. (default=1000)
            all_objects_accessible (bool): If the switch should be on or off.
        Returns:
            (bool, bytes): The status (failed True/False) and the validation log content as binary encoded
                as delivered by service.
        Raises:
            ProcessorExecuteError
        """
        VERSION='1'

        files = {
            'file': (result_xtf_file_name, xtf_content)
        }
        create_job_response = requests.post(
            f'{ilivalidator_service_url}/api/v{VERSION}/upload',
            files=files
        )

        if create_job_response.status_code == 201:
            # job was created successfully
            job_status = create_job_response.json()
            status_url = f'{ilivalidator_service_url}{job_status["statusUrl"]}'
            last_log = None

            while True:
                status_response = requests.get(status_url)
                body = status_response.json()
                if last_log != body["status"]:
                    # logging.info(body)
                    last_log = body["status"]
                if body["status"] in ["completedWithErrors", "completed"]:
                    ili_log_path = body['logUrl']
                    logging.info(ili_log_path)
                    response = requests.get(f'{ilivalidator_service_url}{ili_log_path}')
                    log_content = response.text
                    # logging.info(log_content)
                    return "...validation failed" in log_content, bytes(log_content, 'utf-8')
                elif body["status"] in ["processing", "enqueued"]:
                    time.sleep(sleep_time_ms / 1000)
                else:
                    logging.error("unknown status")
                    raise AttributeError(
                        "unknown STATUS of ilivalidator service {}".format(body["status"])
                    )
        elif create_job_response.status_code == 400:
            return True, bytes(
                f'Some error happened: P code was {create_job_response.status_code}', 'utf-8'
            )
        elif create_job_response.status_code == 413:
            return True, bytes(
                f'File was too large. See details: P code was {create_job_response.status_code}', 'utf-8'
            )
        else:
            return True, bytes(
                f'could not talk to ilivalidator HTTP code was {create_job_response.status_code}', 'utf-8'
            )


    @staticmethod
    def download_catalogue(catalogue_url):
        """
        Downloads a file from an URL assuming it to be the catalogue.

        Args:
            catalogue_url (str): The URI to the catalogue.
        Returns:
            bin: The catalog content as binary encoded as delivered by service.
        Raised:
            ProcessorExecuteError
        """
        catalogue_request = requests.get(catalogue_url)
        if catalogue_request.status_code == 200:
            catalogue_content = catalogue_request.text
            encoding = requests.utils.get_encoding_from_headers(catalogue_request.headers)
            return catalogue_content.encode(encoding=encoding)
        raise ProcessorExecuteError('Catalogue could not be downloaded. Response was:\n{}'.format(
            catalogue_request.text
        ))

    @staticmethod
    def transform(xsl_trafo_path, xtf_path, params):
        """
        Executes a transformation of a given XML with a given XSL. The transformation receives XSL string
        parameters.

        Args:
            xsl_trafo_path (str): The local file path where the XSL is located.
            xtf_path (str): The local file path where the XML is located.
            params (dict): The params which are applied as XSL string parameters to the transformation.
        Returns:
            bin: The transformed result XML encoded as binary.
        """
        xsl = ET.parse(xsl_trafo_path)
        transform = ET.XSLT(xsl)
        xml = ET.parse(xtf_path)

        result = transform(xml, **{k: ET.XSLT.strparam(v) for k, v in params.items()})
        return result

    def create_rss_snippet(self, theme_code, model, target_basket_id, output_validation_failed):
        published_string = "failed and was NOT published" if output_validation_failed == JobStatus.failed.value else "was successful and is published now"
        return f"""
        <item>
          <guid isPermaLink="true">mgdm2oereb_results/{self.job_id}/index.html</guid>
          <title>Transformation {output_validation_failed} (theme: {theme_code}, model: {model})</title>
          <description>The MGDM2OERB Trafo from MGDM {model} to OeREBKRM_V2_0 for {theme_code} (Basket ID: {target_basket_id}) {published_string}.</description>
          <link>mgdm2oereb_results/{self.job_id}/index.html</link>
          <pubDate>{utils.format_datetime(self.timestamp)}</pubDate>
        </item>
        """.encode(encoding="utf-8")

    def create_json_snippet(self, theme_code, model, target_basket_id, output_validation_failed):
        return bytes(json.dumps(
            {
                "job_id": self.job_id,
                "theme_code": theme_code,
                "target_basket_id": target_basket_id,
                "model": model,
                "time_stamp": self.timestamp.isoformat(),
                "successful": not output_validation_failed == JobStatus.failed.value
            },
            indent=4
        ), 'utf-8')
