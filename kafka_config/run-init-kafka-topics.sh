#!/bin/sh

/scripts/init-kafka-topics.sh &
/scripts/run_kafka_consumer_1.sh &
/scripts/run_kafka_producer.sh &

exit 0