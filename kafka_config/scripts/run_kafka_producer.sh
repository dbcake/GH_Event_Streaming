KP="/opt/bitnami/kafka/bin/kafka-console-producer.sh"

echo "Starting Kafka producer..."
"$KP" --topic ingestion-topic --bootstrap-server localhost:9092