import os
import subprocess
from typing import Callable
from dataclasses import dataclass, field
from mgdm2oereb_service.pygeoapi_plugins.process.mgdm2oereb import \
    Mgdm2OerebTransformatorBase, JobFile
from pygeoapi.util import JobStatus


@dataclass
class Parameters:
    zip_file: str = field()
    target_basket_id: str = field()
    theme_code: str = field()
    model_name: str = field()
    catalog: str = field()
    input_validation: bool = field()


@dataclass
class OereblexParameters(Parameters):
    oereblex_host: str = field()
    oereblex_canton: str = field()
    dummy_office_name: str = field()
    dummy_office_url: str = field()


@dataclass
class JobFiles:
    input_zip_file: JobFile
    input_xtf_file: JobFile
    input_log_file: JobFile
    output_log_file: JobFile
    trafo_result_file: JobFile
    rss_snippet_file: JobFile
    json_snippet_file: JobFile
    catalog_file: JobFile


@dataclass
class OereblexJobFiles(JobFiles):
    oereblex_trafo_result_file: JobFile


@dataclass
class TaskOrder:
    tasks: list[Callable[[Parameters | OereblexParameters, JobFiles | OereblexJobFiles, dict, str], dict]]


class Mgdm2OerebTransformator(Mgdm2OerebTransformatorBase):
    mimetype = 'text/json'
    
    def format_exception(self, e: Exception) -> str:
        if hasattr(e, 'message'):
            return str(e.message)
        else:
            return str(e)

    def extract_parameters(self, data: dict) -> Parameters:
        return Parameters(**data)

    def check_params(self, data: dict) -> Parameters | OereblexParameters:
        input_validation = data.get('input_validation', False) in [True, 'true', 1, '1', 'True']
        data['input_validation'] = input_validation
        params = self.extract_parameters(data)
        self.logger.info('All params are there. Starting with the process.')
        return params

    def prepare_job_files(self, parameters: Parameters) -> JobFiles:
        return JobFiles(
            input_zip_file=self.create_job_file(
                self.zip_file_name,
                parameters.theme_code,
                parameters.target_basket_id
            ),
            input_xtf_file=self.create_job_file(
                self.input_xtf_file_name,
                parameters.theme_code,
                parameters.target_basket_id
            ),
            input_log_file=self.create_job_file(
                self.input_log_file_name,
                parameters.theme_code,
                parameters.target_basket_id
            ),
            output_log_file=self.create_job_file(
                self.output_log_file_name,
                parameters.theme_code,
                parameters.target_basket_id
            ),
            trafo_result_file=self.create_job_file(
                self.result_xtf_file_name,
                parameters.theme_code,
                parameters.target_basket_id
            ),
            rss_snippet_file=self.create_job_file(
                self.rss_snippet_file_name,
                parameters.theme_code,
                parameters.target_basket_id
            ),
            json_snippet_file=self.create_job_file(
                self.json_snippet_file_name,
                parameters.theme_code,
                parameters.target_basket_id
            ),
            catalog_file=self.create_job_file(
                self.catalog_file_name,
                parameters.theme_code,
                parameters.target_basket_id
            )
        )

    def obtain_task_order(self):
        return TaskOrder(
            tasks=[
                self.task_handle_input_zip,
                self.task_handle_input_validation,
                self.task_handle_catalogue,
                self.task_handle_trafo,
                self.task_handle_output_validation,
                self.task_handle_rss_snippet,
                self.task_handle_json_snippet
            ]
        )

    def task_handle_input_zip(
            self,
            parameters: Parameters | OereblexParameters,
            job_files: JobFiles | OereblexJobFiles,
            result: dict,
            task_name: str
    ) -> dict:
        input_zip_file_path = job_files.input_zip_file.save_runtime_file(
            self.decode_input_file(parameters.zip_file)
        )
        try:
            input_xtf_content = self.unzip_input_file(
                input_zip_file_path,
                self.job_path
            )
            self.logger.info('Input-Zip extracted')
        except Exception as e:
            return {
                'status': JobStatus.failed.value,
                'msg': self.format_exception(e),
                'task': task_name,
                'step': 'unzip'
            }
        try:
            job_files.input_xtf_file.save_runtime_file(
                input_xtf_content
            )
            job_files.input_xtf_file.save_result_file(input_xtf_content)
            self.logger.info('Input-XTF Created')
            return {
                f"{task_name}_status": JobStatus.successful.value,
                "input_xtf": f"/{self.absolute_result_dir}/{job_files.input_xtf_file.file_name()}"
            }
        except Exception as e:
            return {
                'status': JobStatus.failed.value,
                'msg': self.format_exception(e),
                'task': task_name,
                'step': 'save input xtf'
            }

    def task_handle_input_validation(
            self,
            parameters: Parameters | OereblexParameters,
            job_files: JobFiles | OereblexJobFiles,
            result: dict,
            task_name: str
    ) -> dict:
        if parameters.input_validation:
            if job_files.input_xtf_file.result_content:
                input_validation_failed, input_validation_result = self.validate(
                    job_files.input_xtf_file.result_content,
                    self.ilivalidator_service_url,
                    self.result_xtf_file_name,
                    all_objects_accessible=False
                )
                job_files.input_log_file.save_runtime_file(
                    input_validation_result
                )
                job_files.input_log_file.save_result_file(input_validation_result)
                self.logger.info('Input-Validation done')
                if input_validation_failed:
                    return {
                        'status': JobStatus.failed.value,
                        'msg': 'Validation of input file failed.',
                        'task': task_name
                    }
                return {
                    f"{task_name}_status": JobStatus.successful.value,
                    "input_validation_log": f"/{self.absolute_result_dir}/{job_files.input_log_file.file_name()}"
                }
            else:
                return {
                    'status': JobStatus.failed.value,
                    'msg': 'No XTF Content at runtime for some reason.',
                    'task': task_name
                }
        else:
            return {}

    def task_handle_catalogue(
            self,
            parameters: Parameters | OereblexParameters,
            job_files: JobFiles | OereblexJobFiles,
            result: dict,
            task_name: str
    ) -> dict:
        try:
            catalog_content = self.download_catalogue(parameters.catalog)
            job_files.catalog_file.save_runtime_file(
                catalog_content
            )
            job_files.catalog_file.save_result_file(catalog_content)
            self.logger.info('Catalogue created')
            return {
                f"{task_name}_status": JobStatus.successful.value,
                "used_catalog": f"/{self.absolute_result_dir}/{job_files.catalog_file.file_name()}"
            }
        except Exception as e:
            return {
                'status': JobStatus.failed.value,
                'msg': self.format_exception(e),
                'task': task_name
            }

    def task_handle_trafo(
            self,
            parameters: Parameters | OereblexParameters,
            job_files: JobFiles | OereblexJobFiles,
            result: dict,
            task_name: str
    ) -> dict:
        trafo_params = {
            "catalog": job_files.catalog_file.result_path,
            "theme_code": parameters.theme_code,
            "model": parameters.model_name,
            "target_basket_id": parameters.target_basket_id,
            'xsl_path': self.mgdm2oereb_xsl_path
        }
        try:
            xsl_trafo_path = os.path.join(
                self.mgdm2oereb_xsl_path,
                '{}.trafo.xsl'.format(parameters.model_name)
            )
            trafo_result_content = self.transform(
                xsl_trafo_path,
                job_files.input_xtf_file.result_path,
                trafo_params
            )
            job_files.trafo_result_file.save_runtime_file(
                trafo_result_content
            )
            job_files.trafo_result_file.save_result_file(trafo_result_content)
            return {
                f"{task_name}_status": JobStatus.successful.value,
                "transformation_result": f"/{self.absolute_result_dir}/{job_files.trafo_result_file.file_name()}"
            }
        except Exception as e:
            return {
                'status': JobStatus.failed.value,
                'msg': self.format_exception(e),
                'task': task_name
            }

    def task_handle_output_validation(
            self,
            parameters: Parameters | OereblexParameters,
            job_files: JobFiles | OereblexJobFiles,
            result: dict,
            task_name: str
    ) -> dict:
        output_validation_failed, output_validation_result = self.validate(
            job_files.trafo_result_file.result_content,
            self.ilivalidator_service_url,
            self.result_xtf_file_name,
            all_objects_accessible=True
        )
        job_files.output_log_file.save_runtime_file(
            output_validation_result
        )
        job_files.output_log_file.save_result_file(output_validation_result)
        if output_validation_failed:
            return {
                'status': JobStatus.failed.value,
                'msg': 'Validation of output file failed.',
                'task': task_name,
                "output_validation_log": f"/{self.absolute_result_dir}/{job_files.output_log_file.file_name()}"
            }
        return {
            f"{task_name}_status": JobStatus.successful.value,
            "output_validation_log": f"/{self.absolute_result_dir}/{job_files.output_log_file.file_name()}"
        }

    def task_handle_rss_snippet(
            self,
            parameters: Parameters | OereblexParameters,
            job_files: JobFiles | OereblexJobFiles,
            result: dict,
            task_name: str
    ) -> dict:
        rss_snippet_content = self.create_rss_snippet(
            parameters.theme_code,
            parameters.model_name,
            parameters.target_basket_id,
            result[f"{self.task_handle_output_validation.__name__}_status"]
        )
        job_files.rss_snippet_file.save_runtime_file(
            rss_snippet_content
        )
        job_files.rss_snippet_file.save_result_file(rss_snippet_content)
        return {
            f"{task_name}_status": JobStatus.successful.value,
            "rss_snippet": f"/{self.absolute_result_dir}/{job_files.rss_snippet_file.file_name()}"
        }

    def task_handle_json_snippet(
            self,
            parameters: Parameters | OereblexParameters,
            job_files: JobFiles | OereblexJobFiles,
            result: dict,
            task_name: str
    ) -> dict:
        json_snippet_content = self.create_json_snippet(
            parameters.theme_code,
            parameters.model_name,
            parameters.target_basket_id,
            result[f"{self.task_handle_output_validation.__name__}_status"]
        )
        job_files.json_snippet_file.save_runtime_file(
            json_snippet_content
        )
        job_files.json_snippet_file.save_result_file(json_snippet_content)
        return {
            f"{task_name}_status": JobStatus.successful.value,
            "rss_snippet": f"/{self.absolute_result_dir}/{job_files.json_snippet_file.file_name()}"
        }

    def execute(self, data):
        result = {}
        try:
            parameters = self.check_params(data)
            result.update({
                "theme_code": parameters.theme_code,
                "target_basket_id": parameters.target_basket_id
            })
        except Exception as e:
            result.update({
                'status': JobStatus.failed.value,
                'msg': f'Error in passed Params: {e}',
                'task': 'checking parameters'
            })
            return self.mimetype, result

        try:
            job_files = self.prepare_job_files(parameters)
        except Exception as e:
            result.update({
                'status': JobStatus.failed.value,
                'msg': f'Error while preparing Job Files: {e}',
                'task': 'preparing job files'
            })
            return self.mimetype, result

        task_order = self.obtain_task_order()
        for task in task_order.tasks:
            task_result = task(
                parameters,
                job_files,
                result.copy(),
                task.__name__
            )
            result.update(task_result)
            if task_result.get('status', False):
                if task_result['status'] == JobStatus.failed.value:
                    # we break the loop and stop since a task in the row was failing.
                    return self.mimetype, result


        result.update({
            "rss_snippet": f"/{self.absolute_result_dir}/{job_files.rss_snippet_file.file_name()}",
            "json_snippet": f"/{self.absolute_result_dir}/{job_files.json_snippet_file.file_name()}"
        })
        self.logger.info(result)
        return self.mimetype, result


class Mgdm2OerebTransformatorOereblex(Mgdm2OerebTransformator):

    # TODO: Implement switch "input_validation": true as parameter like it is implemented in the non oereblex
    # trafo

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

    def extract_parameters(self, data: dict) -> OereblexParameters:
        return OereblexParameters(**data)

    def prepare_job_files(self, parameters: OereblexParameters) -> OereblexJobFiles:
        return OereblexJobFiles(
            input_zip_file=self.create_job_file(
                self.zip_file_name,
                parameters.theme_code,
                parameters.target_basket_id
            ),
            input_xtf_file=self.create_job_file(
                self.input_xtf_file_name,
                parameters.theme_code,
                parameters.target_basket_id
            ),
            input_log_file=self.create_job_file(
                self.input_log_file_name,
                parameters.theme_code,
                parameters.target_basket_id
            ),
            output_log_file=self.create_job_file(
                self.output_log_file_name,
                parameters.theme_code,
                parameters.target_basket_id
            ),
            trafo_result_file=self.create_job_file(
                self.result_xtf_file_name,
                parameters.theme_code,
                parameters.target_basket_id
            ),
            rss_snippet_file=self.create_job_file(
                self.rss_snippet_file_name,
                parameters.theme_code,
                parameters.target_basket_id
            ),
            json_snippet_file=self.create_job_file(
                self.json_snippet_file_name,
                parameters.theme_code,
                parameters.target_basket_id
            ),
            catalog_file=self.create_job_file(
                self.catalog_file_name,
                parameters.theme_code,
                parameters.target_basket_id
            ),
            oereblex_trafo_result_file=self.create_job_file(
                self.result_oereblex_xml_file_name,
                parameters.theme_code,
                parameters.target_basket_id
            )
        )

    def obtain_task_order(self):
        return TaskOrder(
            tasks=[
                self.task_handle_input_zip,
                self.task_handle_input_validation,
                self.task_handle_oereblex,
                self.task_handle_catalogue,
                self.task_handle_trafo,
                self.task_handle_output_validation,
                self.task_handle_rss_snippet,
                self.task_handle_json_snippet
            ]
        )

    def task_handle_oereblex(
            self,
            parameters: Parameters | OereblexParameters,
            job_files: JobFiles | OereblexJobFiles,
            result: dict,
            task_name: str
    ) -> dict:
        try:
            mgdm2oereb_oereblex_geolink_list_path = os.path.join(
                self.mgdm2oereb_xsl_path,
                "{}.oereblex.geolink_list.xsl".format(parameters.model_name)
            )

            oereblex_trafo_result = self.run_oereblex_trafo(
                mgdm2oereb_oereblex_geolink_list_path,
                job_files.input_xtf_file.result_path,
                self.result_oereblex_xml_path,
                parameters.oereblex_host,
                parameters.dummy_office_name,
                parameters.dummy_office_url,
                self.logger
            )

            job_files.oereblex_trafo_result_file.save_runtime_file(
                oereblex_trafo_result
            )
            return {
                f"{task_name}_status": JobStatus.successful.value,
                "oereblex_trafo_result": f"/{self.absolute_result_dir}/{job_files.oereblex_trafo_result_file.file_name()}"
            }
        except Exception as e:
            return {'status': JobStatus.failed.value, 'msg': self.format_exception(e), 'task': task_name}

    def task_handle_trafo(
            self,
            parameters: OereblexParameters,
            job_files: OereblexJobFiles,
            result: dict,
            task_name: str
    ) -> dict:
        try:
            trafo_params = {
                "catalog": job_files.catalog_file.result_path,
                "theme_code": parameters.theme_code,
                "model": parameters.model_name,
                "oereblex_output": job_files.oereblex_trafo_result_file.result_path,
                "oereblex_host": parameters.oereblex_host,
                "target_basket_id": parameters.target_basket_id,
                'xsl_path': self.mgdm2oereb_xsl_path
            }
            xsl_trafo_path = os.path.join(
                self.mgdm2oereb_xsl_path,
                '{}.trafo.xsl'.format(parameters.model_name)
            )
            trafo_result_content = self.transform(
                xsl_trafo_path,
                job_files.input_xtf_file.result_path,
                trafo_params
            )
            job_files.trafo_result_file.save_runtime_file(
                trafo_result_content
            )
            job_files.trafo_result_file.save_result_file(trafo_result_content)
            return {
                f"{task_name}_status": JobStatus.successful.value,
                "transformation_result": f"/{self.absolute_result_dir}/{job_files.trafo_result_file.file_name()}"
            }
        except Exception as e:
            return {'status': JobStatus.failed.value, 'msg': self.format_exception(e), 'task': task_name}

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

