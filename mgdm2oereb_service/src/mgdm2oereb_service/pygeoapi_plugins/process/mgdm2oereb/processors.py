import os
import subprocess
from mgdm2oereb_service.pygeoapi_plugins.process.mgdm2oereb import \
    Mgdm2OerebTransformatorBase
from pygeoapi.process.base import ProcessorExecuteError
from mgdm2oereb_service import RESULTS_PATH


class Mgdm2OerebTransformator(Mgdm2OerebTransformatorBase):

    def execute(self, data):
        mimetype = 'text/json'
        zip_file = data.get('zip_file', None)
        target_basket_id = data.get('target_basket_id', None)
        theme_code = data.get('theme_code', None)
        model_name = data.get('model_name', None)
        catalog = data.get('catalog', None)
        result = {
            "theme_code": theme_code,
            "target_basket_id": target_basket_id
        }

        if zip_file is None:
            return mimetype, result
            raise ProcessorExecuteError('Cannot process without a zip_file')
        if theme_code is None:
            raise ProcessorExecuteError('Cannot process without a theme_code')
        if model_name is None:
            raise ProcessorExecuteError('Cannot process without a model_name')
        if catalog is None:
            raise ProcessorExecuteError('Cannot process without a catalog')
        self.logger.info('All params are there. Starting with the process.')
        input_zip_file = self.create_job_file(
            self.zip_file_name,
            theme_code,
            target_basket_id
        )
        input_xtf_file = self.create_job_file(
            self.input_xtf_file_name,
            theme_code,
            target_basket_id
        )
        input_log_file = self.create_job_file(
            self.input_log_file_name,
            theme_code,
            target_basket_id
        )
        output_log_file = self.create_job_file(
            self.output_log_file_name,
            theme_code,
            target_basket_id
        )
        trafo_result_file = self.create_job_file(
            self.result_xtf_file_name,
            theme_code,
            target_basket_id
        )
        rss_snippet_file = self.create_job_file(
            self.rss_snippet_file_name,
            theme_code,
            target_basket_id
        )

        json_snippet_file = self.create_job_file(
            self.json_snippet_file_name,
            theme_code,
            target_basket_id
        )

        input_zip_file_path = input_zip_file.save_runtime_file(
            self.decode_input_file(zip_file)
        )
        try:
            input_xtf_content = self.unzip_input_file(
                input_zip_file_path,
                self.job_path
            )
        except Exception as e:
            result.update({'error': e})
            return mimetype, result
        try:
            input_xtf_file_path = input_xtf_file.save_runtime_file(
                input_xtf_content
            )
            input_xtf_file.save_result_file(input_xtf_content)
            result.update({"input_xtf": f"/{RESULTS_PATH}/{input_xtf_file.file_name()}"})
        except Exception as e:
            result.update({'error': e})
            return mimetype, result
        input_validation_failed, input_validation_result = self.validate(
            input_xtf_content,
            self.ilivalidator_service_url,
            self.result_xtf_file_name,
            all_objects_accessible=False
        )
        input_log_file_path = input_log_file.save_runtime_file(
            input_validation_result
        )
        input_log_file.save_result_file(input_validation_result)
        result.update({"input_validation_log": f"/{RESULTS_PATH}/{input_log_file.file_name()}"})
        if input_validation_failed:
            result.update({'error': 'Validation of input file failed.'})
            return mimetype, result

        xsl_trafo_path = os.path.join(
            self.mgdm2oereb_xsl_path,
            '{}.trafo.xsl'.format(model_name)
        )
        try:
            catalog_content = self.download_catalogue(catalog)
            catalog_file = self.create_job_file(
                self.catalog_file_name,
                theme_code,
                target_basket_id
            )
            catalog_file_path = catalog_file.save_runtime_file(
                catalog_content
            )
            catalog_file.save_result_file(catalog_content)
            result.update({"used_catalog": f"/{RESULTS_PATH}/{catalog_file.file_name()}"})
        except Exception as e:
            result.update({'error': e})
            return mimetype, result
        trafo_params = {
            "catalog": catalog_file_path,
            "theme_code": theme_code,
            "model": model_name,
            "target_basket_id": target_basket_id,
            'xsl_path': self.mgdm2oereb_xsl_path
        }
        try:
            trafo_result_content = self.transform(
                xsl_trafo_path,
                input_xtf_file_path,
                trafo_params
            )
            trafo_result_file_path = trafo_result_file.save_runtime_file(
                trafo_result_content
            )
            trafo_result_file.save_result_file(trafo_result_content)
            result.update({"transformation_result": f"/{RESULTS_PATH}/{trafo_result_file.file_name()}"})
        except Exception as e:
            result.update({'error': e})
            return mimetype, result

        output_validation_failed, output_validation_result = self.validate(
            trafo_result_content,
            self.ilivalidator_service_url,
            self.result_xtf_file_name,
            all_objects_accessible=True
        )
        output_log_file_path = output_log_file.save_runtime_file(
            output_validation_result
        )
        output_log_file.save_result_file(output_validation_result)
        result.update({"output_validation_log": f"/{RESULTS_PATH}/{output_log_file.file_name()}"})
        if output_validation_failed:
            result.update({'error': 'Validation of output file failed.'})

        rss_snippet_content = self.create_rss_snippet(
            theme_code,
            model_name,
            target_basket_id,
            output_validation_failed
        )
        rss_snippet_file_path = rss_snippet_file.save_runtime_file(
            rss_snippet_content
        )

        json_snippet_content = self.create_json_snippet(
            theme_code,
            model_name,
            target_basket_id,
            output_validation_failed
        )
        json_snippet_file_path = json_snippet_file.save_runtime_file(
            json_snippet_content
        )

        # save files to be available for web access (aka publishing)

        rss_snippet_file.save_result_file(rss_snippet_content)
        json_snippet_file.save_result_file(json_snippet_content)

        result.update({
            "rss_snippet": f"/{RESULTS_PATH}/{rss_snippet_file.file_name()}",
            "json_snippet": f"/{RESULTS_PATH}/{json_snippet_file.file_name()}"
        })
        self.logger.info(result)
        return mimetype, result


class Mgdm2OerebTransformatorOereblex(Mgdm2OerebTransformatorBase):

    def __init__(self, processor_def):

        super().__init__(processor_def)
        self.result_oereblex_xml_file_name = os.environ.get(
            'MGDM2OEREB_RESULT_OEREBLEX_XML_NAME',
            'oereblex.xml'
        )
        self.result_oereblex_xml_path = os.path.join(
            self.job_path,
            self.result_oereblex_xml_file_name
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
        target_basket_id = data.get('target_basket_id', None)

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
        input_zip_file = self.create_job_file(
            self.zip_file_name,
            theme_code,
            target_basket_id
        )
        input_xtf_file = self.create_job_file(
            self.input_xtf_file_name,
            theme_code,
            target_basket_id
        )
        input_log_file = self.create_job_file(
            self.input_log_file_name,
            theme_code,
            target_basket_id
        )
        output_log_file = self.create_job_file(
            self.output_log_file_name,
            theme_code,
            target_basket_id
        )
        oereblex_trafo_result_file = self.create_job_file(
            self.result_oereblex_xml_file_name,
            theme_code,
            target_basket_id
        )
        trafo_result_file = self.create_job_file(
            self.result_xtf_file_name,
            theme_code,
            target_basket_id
        )
        rss_snippet_file = self.create_job_file(
            self.rss_snippet_file_name,
            theme_code,
            target_basket_id
        )

        json_snippet_file = self.create_job_file(
            self.json_snippet_file_name,
            theme_code,
            target_basket_id
        )

        input_zip_file_path = input_zip_file.save_runtime_file(
            self.decode_input_file(zip_file)
        )
        input_xtf_content = self.unzip_input_file(
            input_zip_file_path,
            self.job_path
        )
        input_xtf_file_path = input_xtf_file.save_runtime_file(
            input_xtf_content
        )

        input_validation_result = self.validate(
            input_xtf_content,
            self.ilivalidator_service_url,
            self.result_xtf_file_name,
            all_objects_accessible=False
        )

        input_log_file_path = input_log_file.save_runtime_file(
            input_validation_result
        )
        xsl_trafo_path = os.path.join(
            self.mgdm2oereb_xsl_path,
            '{}.trafo.xsl'.format(model_name)
        )
        mgdm2oereb_oereblex_geolink_list_path = os.path.join(
            self.mgdm2oereb_xsl_path,
            "{}.oereblex.geolink_list.xsl".format(model_name)
        )

        oereblex_trafo_result = self.run_oereblex_trafo(
            mgdm2oereb_oereblex_geolink_list_path,
            input_xtf_file_path,
            self.result_oereblex_xml_path,
            oereblex_host,
            dummy_office_name,
            dummy_office_url,
            self.logger
        )

        oereblex_trafo_result_file_path = oereblex_trafo_result_file.save_runtime_file(
            oereblex_trafo_result
        )
        catalog_content = self.download_catalogue(catalog)
        catalog_file = self.create_job_file(
            self.catalog_file_name,
            theme_code,
            target_basket_id
        )
        catalog_file_path = catalog_file.save_runtime_file(
            catalog_content
        )

        trafo_params = {
            "catalog": catalog_file_path,
            "theme_code": theme_code,
            "model": model_name,
            "oereblex_output": oereblex_trafo_result_file_path,
            "oereblex_host": oereblex_host,
            "target_basket_id": target_basket_id,
            'xsl_path': self.mgdm2oereb_xsl_path
        }
        trafo_result_content = self.transform(
            xsl_trafo_path,
            input_xtf_file_path,
            trafo_params
        )

        trafo_result_file_path = trafo_result_file.save_runtime_file(
            trafo_result_content
        )
        output_validation_result = self.validate(
            trafo_result_content,
            self.ilivalidator_service_url,
            self.result_xtf_file_name,
            all_objects_accessible=True
        )
        output_log_file_path = output_log_file.save_runtime_file(
            output_validation_result
        )

        rss_snippet_content = self.create_rss_snippet(
            theme_code,
            model_name,
            target_basket_id
        )

        rss_snippet_file_path = rss_snippet_file.save_runtime_file(
            rss_snippet_content
        )

        json_snippet_content = self.create_json_snippet(
            theme_code,
            model_name,
            target_basket_id
        )
        json_snippet_file_path = json_snippet_file.save_runtime_file(
            json_snippet_content
        )

        # save files to be available for web access (aka publishing)
        trafo_result_file.save_result_file(trafo_result_content)
        input_log_file.save_result_file(input_validation_result)
        output_log_file.save_result_file(output_validation_result)
        oereblex_trafo_result_file.save_result_file(oereblex_trafo_result)
        rss_snippet_file.save_result_file(rss_snippet_content)
        catalog_file.save_result_file(catalog_content)

        result = {
            "theme_code": theme_code,
            "target_basket_id": target_basket_id,
            "transformation_result": f"/{RESULTS_PATH}/{trafo_result_file.file_name()}",
            "input_validation_log": f"/{RESULTS_PATH}/{input_log_file.file_name()}",
            "used_catalog": f"/{RESULTS_PATH}/{catalog_file.file_name()}",
            "output_validation_log": f"/{RESULTS_PATH}/{output_log_file.file_name()}",
            "oereblex_trafo_result": f"/{RESULTS_PATH}/{oereblex_trafo_result_file.file_name()}",
            "rss_snippet": f"/{RESULTS_PATH}/{rss_snippet_file.file_name()}",
            "json_snippet": f"/{RESULTS_PATH}/{json_snippet_file.file_name()}"
        }
        self.logger.info(result)
        return mimetype, result

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
            return result
        except subprocess.CalledProcessError as e:
            result = e.output
            logger.error(result)
            raise e

