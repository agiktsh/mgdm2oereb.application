
import io
from pygeoapi.util import JobStatus
from pygeoapi.process.manager.tinydb_ import TinyDBManager


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
        job_status = JobStatus[job_result['status']]

        if not job_status == JobStatus.successful:
            # Job is incomplete
            return (None,)
        if not location:
            # Job data was not written for some reason
            # TODO log/raise exception?
            return (None,)

        with io.open(location, 'r', encoding='utf-8') as filehandler:
            result = filehandler.read()

        return mimetype, result

    def __repr__(self):
        return '<CustomTinyDBManager> {}'.format(self.name)
