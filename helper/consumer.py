import json
from kafka import KafkaConsumer

if __name__ == '__main__':
    # Kafka Consumer
    consumer = KafkaConsumer(
        'real_estate_response_topic',
        bootstrap_servers='localhost:9093',
        auto_offset_reset='earliest'
    )
    for message in consumer:
        print(json.loads(message.value))