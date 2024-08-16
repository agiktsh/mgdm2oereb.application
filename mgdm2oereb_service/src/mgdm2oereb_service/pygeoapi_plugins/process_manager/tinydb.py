
import io
import json
import logging
from datetime import datetime
from typing import Tuple, Any

from pygeoapi.process.base import BaseProcessor
from pygeoapi.util import JobStatus, DATETIME_FORMAT
from pygeoapi.process.manager.tinydb_ import TinyDBManager


logger = logging.getLogger(__name__)


class CustomTinyDBManager(TinyDBManager):

    def get_job_result(self, job_id):
        """
                Get a job's status, and actual output of executing the process
                :param jobid: job identifier
                :returns: `tuple` of mimetype and raw output
                """

        job_result = self.get_job(job_id)
        if not job_result:
            # job does not exist
            return None

        location = job_result.get('location', None)
        mimetype = job_result.get('mimetype', None)

        if not location:
            # Job data was not written for some reason
            # TODO log/raise exception?
            return (None,)
        with io.open(location, 'r', encoding='utf-8') as filehandler:
            result = filehandler.read()
        logger.error(result)
        return mimetype, result

    def _execute_handler_sync(self, p: BaseProcessor, job_id: str,
                              data_dict: dict) -> Tuple[str, Any, JobStatus]:
        """
        Synchronous execution handler

        If the manager has defined `output_dir`, then the result
        will be written to disk
        output store. There is no clean-up of old process outputs.

        :param p: `pygeoapi.process` object
        :param job_id: job identifier
        :param data_dict: `dict` of data parameters

        :returns: tuple of MIME type, response payload and status
        """

        process_id = p.metadata['id']
        current_status = JobStatus.accepted

        job_metadata = {
            'identifier': job_id,
            'process_id': process_id,
            'job_start_datetime': datetime.utcnow().strftime(
                DATETIME_FORMAT),
            'job_end_datetime': None,
            'status': current_status.value,
            'location': None,
            'mimetype': None,
            'message': 'Job accepted and ready for execution',
            'progress': 5
        }

        self.add_job(job_metadata)

        try:
            if self.output_dir is not None:
                filename = f"{p.metadata['id']}-{job_id}"
                job_filename = self.output_dir / filename
            else:
                job_filename = None

            current_status = JobStatus.running
            jfmt, outputs = p.execute(data_dict)

            self.update_job(job_id, {
                'status': current_status.value,
                'message': 'Writing job output',
                'progress': 95
            })

            if self.output_dir is not None:
                logger.debug(f'writing output to {job_filename}')
                mode = 'w'
                data = json.dumps(outputs, sort_keys=True, indent=4)
                encoding = 'utf-8'
                with job_filename.open(mode=mode, encoding=encoding) as fh:
                    fh.write(data)
            if outputs.get('status', False):
                current_status = JobStatus[outputs['status']]
                message = outputs['msg']
            else:
                current_status = JobStatus.successful
                message = 'Job complete'

            job_update_metadata = {
                'job_end_datetime': datetime.utcnow().strftime(
                    DATETIME_FORMAT),
                'status': current_status.value,
                'location': str(job_filename),
                'mimetype': jfmt,
                'message': message,
                'progress': 100
            }

            self.update_job(job_id, job_update_metadata)

        except Exception as err:
            # TODO assess correct exception type and description to help users
            # NOTE, the /results endpoint should return the error HTTP status
            # for jobs that failed, ths specification says that failing jobs
            # must still be able to be retrieved with their error message
            # intact, and the correct HTTP error status at the /results
            # endpoint, even if the /result endpoint correctly returns the
            # failure information (i.e. what one might assume is a 200
            # response).

            current_status = JobStatus.failed
            code = 'InvalidParameterValue'
            outputs = {
                'code': code,
                'description': 'Error updating job'
            }
            logger.error(err)
            job_metadata = {
                'job_end_datetime': datetime.utcnow().strftime(
                    DATETIME_FORMAT),
                'status': current_status.value,
                'location': None,
                'mimetype': None,
                'message': f'{code}: {outputs["description"]}'
            }

            jfmt = 'application/json'

            self.update_job(job_id, job_metadata)

        return jfmt, outputs, current_status

    def __repr__(self):
        return '<CustomTinyDBManager> {}'.format(self.name)
