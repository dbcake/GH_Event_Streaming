"""Get Public Events data from GitHub"""

import json
import os
import time

from ghapi.all import GhApi
from kafka import (
    KafkaProducer,
    producer,
)

# Import Secret from ENV variables
secret_key = os.environ.get('GITHUB_TOKEN')

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
    json_object = json.dumps(dict) 
    return json_object


def fetch_data():
    fetched = api.fetch_events (n_pages=5, pause=0.3, per_page=10, types=None,
                        incl_bot=False, username=None, org=None, owner=None,
                        repo=None)
    start_time = time.time()
    max_duration = 6  # Run for 60 seconds
    for row in fetched:
        # Check time elapsed
        time_elapsed = time.time() - start_time
        # Dump the json out as string
        print(f"\n -------------------- {str(round(time_elapsed,1))} s --------------------\n ")
        print( json.dumps(filter_data(row)))
        # Produce the string
        # produce_kafka_string(json_as_string)
        if time_elapsed > max_duration:
            print(f"\n Stopping data collection after {max_duration} seconds.")
            break

fetch_data()
# def produce_kafka_string(json_as_string):
#     # Create producer
#     producer = KafkaProducer(bootstrap_servers='kafka:9092',acks=1)
    
#     # Write the string as bytes because Kafka needs it this way
#     producer.send('ingestion-topic', bytes(json_as_string, 'utf-8'))
#     producer.flush() 
