"""Kafka handler for decoding service."""
import json
import sys
from pathlib import Path

# Add comfyui to path before importing
sys.path.insert(0, str(Path(__file__).parent / "comfyui"))

from confluent_kafka import Consumer, Producer
from config import Config
from service import decode_latent_to_image
from models import KafkaDecodingRequest, DecodingResponse
from utils import generate_request_id


def create_consumer():
    """Create Kafka consumer."""
    return Consumer({
        'bootstrap.servers': Config.kafka_bootstrap_servers,
        'group.id': Config.kafka_consumer_group,
        'auto.offset.reset': 'earliest',
        'enable.auto.commit': False
    })


def create_producer():
    """Create Kafka producer."""
    return Producer({
        'bootstrap.servers': Config.kafka_bootstrap_servers
    })


def consume_and_process():
    """Consume messages from Kafka and process them."""
    consumer = create_consumer()
    producer = create_producer()
    
    consumer.subscribe([Config.kafka_request_topic])
    
    print(f"Listening to topic: {Config.kafka_request_topic}")
    print(f"Publishing to topic: {Config.kafka_response_topic}")
    print("Waiting for messages...")
    
    try:
        while True:
            msg = consumer.poll(1.0)
            
            if msg is None:
                continue
            
            if msg.error():
                print(f"Consumer error: {msg.error()}")
                continue
            
            try:
                # Deserialize message
                message_data = json.loads(msg.value().decode('utf-8'))
                print(f"Received message: {message_data.get('request_id', 'unknown')}")
                
                # Parse message
                kafka_message = KafkaDecodingRequest(**message_data)
                
                # Process request
                result = decode_latent_to_image(
                    latent=kafka_message.latent,
                    vae_model_name=kafka_message.vae_model_name,
                    output_filename=kafka_message.output_filename,
                    output_dir=kafka_message.output_dir,
                    output_format=kafka_message.output_format,
                    request_id=kafka_message.request_id or generate_request_id(),
                    save_image=True
                )
                
                # Create response
                response = DecodingResponse(
                    status=result["status"],
                    request_id=result["request_id"],
                    image_file_path=result.get("image_file_path"),
                    image_shape=result.get("image_shape"),
                    file_size=result.get("file_size"),
                    error_code=result.get("error_code"),
                    error_message=result.get("error_message"),
                    metadata=result.get("metadata")
                )
                
                # Send response
                response_data = response.model_dump_json()
                producer.produce(
                    Config.kafka_response_topic,
                    key=kafka_message.request_id.encode('utf-8'),
                    value=response_data.encode('utf-8'),
                    callback=lambda err, msg: print(f"Message delivered: {msg.topic()}") if not err else print(f"Delivery failed: {err}")
                )
                producer.flush()
                
                print(f"Processed request: {result['request_id']}, Status: {result['status']}")
                
                # Commit offset
                consumer.commit(msg)
                
            except json.JSONDecodeError as e:
                print(f"Error decoding JSON message: {e}")
                # Send error response
                error_response = {
                    "status": "error",
                    "request_id": message_data.get('request_id', 'unknown'),
                    "error_code": "INVALID_JSON",
                    "error_message": str(e)
                }
                producer.produce(
                    Config.kafka_response_topic,
                    key=message_data.get('request_id', 'unknown').encode('utf-8'),
                    value=json.dumps(error_response).encode('utf-8')
                )
                producer.flush()
                
            except Exception as e:
                print(f"Error processing message: {e}")
                import traceback
                traceback.print_exc()
                
                # Send error response
                error_response = {
                    "status": "error",
                    "request_id": message_data.get('request_id', 'unknown'),
                    "error_code": type(e).__name__,
                    "error_message": str(e)
                }
                producer.produce(
                    Config.kafka_response_topic,
                    key=message_data.get('request_id', 'unknown').encode('utf-8'),
                    value=json.dumps(error_response).encode('utf-8')
                )
                producer.flush()
                
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        consumer.close()
        producer.flush()



