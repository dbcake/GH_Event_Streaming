"""Get Public Events data from GitHub"""

import json
import os
import time
from datetime import datetime

# import app.write_logs as wl
import elasticsearch

# from elasticsearch import Elasticsearch, exceptions
from ghapi.all import GhApi  # type: ignore
from kafka import (  # type: ignore
    KafkaConsumer,
    KafkaProducer,
    producer,
)

# initialize elasticsearch client
# try:
#     es = Elasticsearch("http://localhost:9200")
# except:
es = elasticsearch.Elasticsearch("http://elasticsearch:9200")


# def create_index():
#     request_body = {
#         "settings": {"number_of_shards": 1, "number_of_replicas": 1},
#         "mappings": {
#             "properties": {
#                 "process": {"type": "text"},
#                 "date": {"format": "yyyy-MM-dd", "type": "date"},
#                 "processing_time": {"type": "double"},
#                 "records": {"type": "integer"},
#                 "run": {"type": "integer"},
#                 "msg": {"type": "text"},
#             }
#         },
#     }
#     es.indices.create(index="data-ingest", body=request_body)



def es_create_index_if_not_exists(es, index_name):
    """Create the given ElasticSearch index and ignore error if it already exists"""
    request_body = {
        "settings": {"number_of_shards": 1, "number_of_replicas": 1},
        "mappings": {
            "properties": {
                "process": {"type": "text"},
                "date_time": {"type": "date_nanos"},
                "processing_time": {"type": "double"},
                "records": {"type": "integer"},
                "run": {"type": "integer"},
                "msg": {"type": "text"},
            }
        },
    }
    try:
        es.indices.create(index=index_name, body=request_body)
    except elasticsearch.exceptions.RequestError as ex:
        if ex.error == 'resource_already_exists_exception':
            print ("----------   Index already exists.   ----------")
            pass # Index already exists. Ignore.
        else: # Other exception - raise it
            raise ex

# Create "data-ingest" index
es_create_index_if_not_exists(es, "data-ingest")



def log_info(process, status, date_time, processing_time, records, run, msg):
    # create logs for etl process run 1
    info_json = {
        "process": process,
        "status": status,
        "date_time": date_time,
        "processing_time": processing_time,
        "records": records,
        "run": run,
        "msg": msg
    }
    print("----------   LOG   ----------")
    response = es.index(index="data-ingest", document=info_json)
    print(f"Log response: {response}")


# Import Secret from ENV variables
if os.environ.get('GITHUB_TOKEN'):
    # Running locally, token in .zshrc
    secret_key = os.environ.get('GITHUB_TOKEN')
else:
    # Running as a container
    with open('/run/secrets/gh_password') as f:
        secret_key=f.read()


# print(f"---- token: {secret_key[:20]}")
# Create API
api = GhApi(owner='D', repo='dbcake', token=secret_key)

# Query events
events= api.list_events (per_page=5, page=1, username=None, org=None,
                    owner=None, repo=None)


def filter_data(row):
    dict = {
        'id': row['id'], 
        'type': row['type'], 
        'actor_login': row['actor']['login'],
        'repo_name': row['repo']['name'], 
        'created_at': row['created_at']
    }
    json_str = json.dumps(dict) 
    return json_str


def cont_fetch():
    """Continuously fetch data from the API"""
    # Call the API
    fetched = api.fetch_events (n_pages=10, pause=0.5, per_page=30, types=None,
                        incl_bot=False, username=None, org=None, owner=None,
                        repo=None)
    start_time = time.time()
    max_duration = 5  # Run for 60 seconds
    datetime.now().strftime("%d-%b-%YT%H:%M:%S.%f0000Z")
    # Log
    log_info("fetch", "starting", datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f000Z"), 0, 0, run, "fetching started")

    for row in fetched:
        # Check time elapsed
        time_elapsed = time.time() - start_time
        # Dump the json out as string
        print(f"\n -------------------- {str(round(time_elapsed,4))} s --------------------\n ")
        print( json.dumps(filter_data(row)))
        # Produce the string
        # produce_kafka_string(json_as_string)
        log_info("fetch", "processing", datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f000Z"), 0, 0, run, "sending event")

        if time_elapsed > max_duration:
            print(f"\n Stopping data collection after {max_duration} seconds.")
            break

    log_info("fetch", "stopping", datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f000Z"), time_elapsed, 0, run, "fetching ended")

def get_paginated_data(number_of_pages=10, result_per_page=30):
    """Query all pages of the api and collect results in a list"""
    start_time = time.time()
    log_info("fetch", "starting", datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f000Z"), 0, 0, run, "fetching started")
    data = []
    all_result_num= 0
    # cycle through the pages
    for num in range(1, number_of_pages+1):
        # call the api
        results=api.list_events (per_page=result_per_page, page=num, username=None,
                                org=None, owner=None, repo=None)
        # print(num)
        page_result_num = 0
        for result in results:
            json_str = filter_data(result)
            data.append(json_str)
            produce_kafka_string(json_str)
            page_result_num+=1
        all_result_num += page_result_num
        # print(page_result_num)
        # No need to continue after the not full page
        if page_result_num != result_per_page:
            break
    time_elapsed = time.time() - start_time
    log_info("fetch", "processing", datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f000Z"), time_elapsed, all_result_num, run, "sending event")
        
    print (f"Records for run {run}: {all_result_num}")
    time_elapsed = time.time() - start_time
    log_info("fetch", "stopping", datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f000Z"), time_elapsed, all_result_num, run, "fetching ended")
    #print(data)
    return data

def produce_kafka_string(json_as_string):
    # Create producer
    producer = KafkaProducer(bootstrap_servers='kafka:9092',acks=1)
    
    # Write the string as bytes because Kafka needs it this way
    producer.send('ingestion-topic', bytes(json_as_string, 'utf-8'))
    producer.flush() 

# cont_fetch()
run = 0 
while True:
    print( f"Run: {run}")
    #print( f"Run: {run}", json.dumps( ) )
    get_paginated_data()
    run+=1

    time.sleep(60)
