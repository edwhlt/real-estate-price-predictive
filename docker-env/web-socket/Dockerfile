# Use Python base image
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Copy the WebSocket server code
COPY websocket.py .

# Install required Python packages
RUN pip install websockets confluent_kafka asyncio

# Expose port for WebSocket server
EXPOSE 6789

# Command to run the WebSocket server
CMD ["python", "websocket.py"]
