import os
import subprocess
from mgdm2oereb_service.pygeoapi_plugins.process.mgdm2oereb import \
    Mgdm2OerebTransformatorBase
from pygeoapi.process.base import ProcessorExecuteError


class Mgdm2OerebTransformator(Mgdm2OerebTransformatorBase):

    def execute(self, data):
        mimetype = 'text/json'
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
        self.logger.info('All params are there. Starting with the process.')
        with open(self.zip_path, 'wb') as input_file:
            input_file.write(self.decode_input_file(zip_file))
        xtf_path = self.unzip_input_file(self.zip_path, self.job_path)
        with open(xtf_path, mode="rb") as fh:
            input_validation = self.validate(
                fh,
                self.ilivalidator_service_url,
                self.result_xtf_file_name,
                os.path.join(self.job_path, self.input_log_file)
            )
        xsl_trafo_path = os.path.join(
            self.mgdm2oereb_xsl_path,
            '{}.trafo.xsl'.format(model_name)
        )
        catalog_path = self.download_catalogue(catalog, self.job_path)
        trafo_params = {
            "catalog": catalog_path,
            "theme_code": theme_code,
            "model": model_name
        }
        self.transform(
            xsl_trafo_path,
            xtf_path,
            self.result_xtf_path,
            trafo_params
        )

        with open(self.result_xtf_path, "rb") as fh:

            validation_result = self.validate(
                fh,
                self.ilivalidator_service_url,
                self.result_xtf_file_name,
                os.path.join(self.job_path, self.output_log_file)
            )
        result = {
            "transformation_result": os.path.join("/mgdm2oereb_results", self.job_id, self.result_xtf_file_name),
            "input_validation_log": os.path.join("/mgdm2oereb_results", self.job_id, self.input_log_file),
            "output_validation_log": os.path.join("/mgdm2oereb_results", self.job_id, self.output_log_file)
        }
        self.logger.info(result)
        return mimetype, result


class Mgdm2OerebTransformatorOereblex(Mgdm2OerebTransformatorBase):

    def __init__(self, processor_def):

        super().__init__(processor_def)
        self.result_oereblex_xml_path = os.path.join(
            self.job_path,
            os.environ.get('MGDM2OEREB_RESULT_OEREBLEX_XML_NAME', 'oereblex.xml')
        )
        self.mgdm2oereb_oereblex_python_trafo_path = os.path.join(
            self.job_path,
            os.environ.get('MGDM2OEREB_OEREBLEX_TRAFO_PY', 'oereblex.download.py')
        )

    def execute(self, data):
        mimetype = 'text/json'
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
        self.logger.info('All params are there. Starting with the process.')
        with open(self.zip_path, 'wb') as input_file:
            input_file.write(self.decode_input_file(zip_file))
        xtf_path = self.unzip_input_file(self.zip_path, self.job_path)
        with open(xtf_path, mode="rb") as fh:
            input_validation = self.validate(
                fh,
                self.ilivalidator_service_url,
                self.result_xtf_file_name,
                os.path.join(self.job_path, self.input_log_file)
            )
        xsl_trafo_path = os.path.join(
            self.mgdm2oereb_xsl_path,
            '{}.trafo.xsl'.format(model_name)
        )
        mgdm2oereb_oereblex_geolink_list_path = os.path.join(
            self.mgdm2oereb_xsl_path,
            "{}.oereblex.geolink_list.xsl".format(model_name)
        )
        self.run_oereblex_trafo(
            mgdm2oereb_oereblex_geolink_list_path,
            xtf_path,
            self.result_oereblex_xml_path,
            oereblex_host,
            dummy_office_name,
            dummy_office_url,
            self.logger
        )
        catalog_path = self.download_catalogue(catalog, self.job_path)
        trafo_params = {
            "catalog": catalog_path,
             "theme_code": theme_code,
            "model": model_name,
            "oereblex_output": self.result_oereblex_xml_path,
            "oereblex_host": oereblex_host
        }
        result = self.transform(
            xsl_trafo_path,
            xtf_path,
            self.result_xtf_path,
            trafo_params
        )

        with open(self.result_xtf_path, "rb") as fh:
            validation_result = self.validate(
                fh,
                self.ilivalidator_service_url,
                self.result_xtf_file_name,
                os.path.join(self.job_path, self.output_log_file)
            )

        return mimetype, {
            "transformation_result": os.path.join(self.job_id, self.result_xtf_file_name),
            "input_validation_log": os.path.join(self.job_id, self.input_log_file),
            "output_validation_log": os.path.join(self.job_id, self.output_log_file)
        }

    def run_oereblex_trafo(self, mgdm2oereb_oereblex_geolink_list_path, xtf_path, result_oereblex_xml_path,
                           oereblex_host, dummy_office_name, dummy_office_url, logger):
        envars = {
            "GEOLINK_LIST_TRAFO_PATH": mgdm2oereb_oereblex_geolink_list_path,
            "XTF_PATH": xtf_path,
            "RESULT_FILE_PATH": result_oereblex_xml_path,
            "OEREBLEX_HOST": oereblex_host,
            "DUMMY_OFFICE_NAME": dummy_office_name,
            "DUMMY_OFFICE_URL": dummy_office_url,
        }
        envars.update(os.environ)
        call_args = ["python3", self.mgdm2oereb_oereblex_python_trafo_path]
        try:
            sub = subprocess.run(
                call_args,
                env=envars,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            )
            result = sub.stdout.decode("utf-8")
            logger.info(result)
        except subprocess.CalledProcessError as e:
            result = e.output
            logger.error(result)
            raise e

