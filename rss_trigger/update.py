import os
import requests
import json
import logging
import time
from reader import make_reader
from reader.exceptions import FeedNotFoundError, ParseError

logging.basicConfig(level="INFO", format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

with make_reader(f'{os.environ.get("RSS_STORAGE_PATH")}/rss.db.sqlite') as reader:
    try:
        reader.get_feed(os.environ.get("RSS_URL"))
    except FeedNotFoundError as e:
        log.info(f'Feed was not known {os.environ.get("RSS_URL")}. Adding it...')
        reader.add_feed(os.environ.get("RSS_URL"))
    log.info(f'Looking for new trafo results on {os.environ.get("RSS_URL")}.')
    while True:
        try:
            reader.update_feeds()
            break
        except ParseError as e:
            seconds = int(os.environ.get("RSS_SLEEP_TIME", "1"))
            time.sleep(seconds)
            log.info(f'Service {os.environ.get("RSS_URL")} is not available yet. Sleeping for {seconds}s')
    for entry in reader.get_entries(read=False):
        rss_json_link = entry.link.replace('.html', '.json')
        rss_json_response = requests.get(rss_json_link)
        if rss_json_response.status_code >= 400:
            log.error(f'Problem with connection to {rss_json_link}')
        log.info(f'Successfully read {rss_json_link}')
        rss_json_list = json.loads(rss_json_response.text)
        job_json_link = None
        oereb_xtf_link = None
        for file_link in rss_json_list:
            if '.job.json' in file_link:
                job_json_link = file_link
            if '.OeREBKRMtrsfr_V2_0.xtf' in file_link:
                oereb_xtf_link = file_link
        if job_json_link and oereb_xtf_link:
            job_json_response = requests.get(job_json_link)
            if job_json_response.status_code >= 400:
                log.error(f'Problem with connection to {job_json_link}')
            job_json_dict = json.loads(job_json_response.text)
            log.info(f'Successfully read {job_json_link}')
            if not job_json_dict['successful']:
                log.info(f'Not a successful job in {job_json_link}. Skippingt this...')
                reader.mark_entry_as_read(entry)
                continue
            oereb_xtf_response = requests.get(oereb_xtf_link)
            if oereb_xtf_response.status_code >= 400:
                log.error(f'Problem with connection to {oereb_xtf_link}')
            log.info(f'Successfully read {oereb_xtf_link}')
            target_path = os.path.join(
                os.environ.get('GIT_REPO_PATH'),
                f'{job_json_dict["theme_code"]}-{job_json_dict["model"]}-{job_json_dict["target_basket_id"]}.xtf'
            )
            with open(target_path, "w+") as fh:
                fh.write(oereb_xtf_response.text)
            log.info(f'Successfully wrote {target_path}')
            reader.mark_entry_as_read(entry)
        else:
            reader.mark_entry_as_read(entry)
            log.info(f'Skipping because its an old trafo and we do not have what we need')
