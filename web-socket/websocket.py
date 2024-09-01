import asyncio
import websockets
import json
from confluent_kafka import Producer, Consumer, KafkaError
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

producer = Producer({
    'bootstrap.servers': 'kafka:9092'
})
consumer = Consumer({
    'bootstrap.servers': 'kafka:9092',
    'auto.offset.reset': 'earliest',
    'enable.auto.commit': True,
    'group.id': 'websocket-group'
})
consumer.subscribe(["real_estate_response_topic"])

async def produce_message(message):
    """Produce a message to Kafka."""
    producer.produce("real_estate_topic", message)
    producer.flush()

async def consume_messages(websocket):
    """Consume messages from Kafka and send them over WebSocket."""
    logging.info("Starting to consume messages from Kafka")
    while True:
        try:
            msg = consumer.poll(1.0)  # Poll Kafka for messages
            if msg is None:
                logging.debug("No message received from Kafka, sleeping for 1 second")
                await asyncio.sleep(1)
                continue
            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    logging.debug("End of partition reached")
                    continue
                else:
                    print(f"Kafka error: {msg.error()}")
                    break

            # When a message is received via WebSocket, produce it to Kafka
            message = msg.value().decode('utf-8')
            logging.info(f"Message received from Kafka: {message}")
            await websocket.send(message)
            logging.info(f"Message sent to WebSocket client: {message}")
        except Exception as e:
            logging.error(f"Exception in consume_messages: {e}")
            break


async def handler(websocket, path):
    """Handle incoming WebSocket connections."""
    logging.info(f"New WebSocket connection from {websocket.remote_address}")

    # Start Kafka consumer task
    consumer_task = asyncio.create_task(consume_messages(websocket))

    try:
        async for message in websocket:
            # When a message is received via WebSocket, produce it to Kafka
            logging.info(f"Received message: {message}")
            await produce_message(message)
    finally:
        consumer_task.cancel()
        logging.info(f"WebSocket connection closed for {websocket.remote_address}")


async def main():
    async with websockets.serve(handler, "0.0.0.0", 6789):
        await asyncio.Future()  # Run forever

if __name__ == "__main__":
    asyncio.run(main())