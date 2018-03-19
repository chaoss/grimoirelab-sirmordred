import logging

from elasticsearch import Elasticsearch, helpers

from mordred.config import Config
from mordred.task_collection import TaskRawDataCollection
from mordred.task_enrich import TaskEnrich
from mordred.task_projects import TaskProjects

DEBUG_LOG_FORMAT = "[%(asctime)s - %(name)s - %(levelname)s] - %(message)s"
logging.basicConfig(level=logging.DEBUG, format=DEBUG_LOG_FORMAT)

RAW = True
ENRICH = False

REINDEX = True
OLD_INDEX = "test_slack-raw"
NEW_INDEX = "test_slack-raw2"

CONF_FILE = "settings/local.cfg"
SECTION = "slack"

MAPPINGS = '''
         {
            "mappings": {
                "items": {
                    "dynamic": true,
                    "properties": {
                        "data": {
                            "properties": {
                                "attachments": {
                                    "dynamic":false,
                                    "properties": {}
                                }
                            }
                        }
                    }
                }
            }
        }
        '''


def get_raw():
    config = Config(CONF_FILE)
    backend_section = SECTION
    task = TaskRawDataCollection(config, backend_section=backend_section)
    TaskProjects(config).execute()
    task.execute()
    logging.info("Loading raw data finished!")


def get_enrich():
    config = Config(CONF_FILE)
    TaskProjects(config).execute()
    backend_section = SECTION
    task = TaskEnrich(config, backend_section=backend_section)
    task.execute()
    logging.info("Loading raw data finished!")


def reindex(old_index, new_index):
    es = Elasticsearch()

    if es.indices.exists(index=new_index):
        logging.warning("New index %s not created, one with the same name already exists!" % new_index)
        return

    es.indices.create(index=new_index, body=MAPPINGS)

    page = es.search(
        index=old_index,
        scroll="1m",
        search_type="scan",
        size=1000,
        body={"query": {"match_all": {}}}
    )

    sid = page['_scroll_id']
    scroll_size = page['hits']['total']

    if scroll_size == 0:
        logging.warning("No data found!")
        return

    while scroll_size > 0:
        page = es.scroll(scroll_id=sid, scroll='1m')
        sid = page['_scroll_id']
        scroll_size = len(page['hits']['hits'])

        new_insert_data = []

        for item in page['hits']['hits']:
            item['_index'] = new_index
            item['_source'] = item['_source']

            new_insert_data.append(item)

        es.indices.refresh(index=new_index)
        helpers.bulk(es, new_insert_data, raise_on_error=True)

    logging.info("Reindex from %s to %s finished!" % (old_index, new_index))


if __name__ == '__main__':
    if RAW:
        get_raw()

    if ENRICH:
        get_enrich()

    if REINDEX:
        reindex(OLD_INDEX, NEW_INDEX)
