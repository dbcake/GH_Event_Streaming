KC="/opt/bitnami/kafka/bin/kafka-console-consumer.sh"

echo "Starting Kafka consumer..."
"$KC" --topic ingestion-topic --bootstrap-server localhost:9092