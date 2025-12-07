"""
RabbitMQ Message Queue Service
Handles message routing and queuing
"""

import pika
import json
import logging
from typing import Dict, Any, Callable
import threading

logger = logging.getLogger(__name__)

class RabbitMQService:
    def __init__(self, host='localhost', port=5672, username='guest', password='guest'):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.connection = None
        self.channel = None
        self.exchange = 'credit_card_exchange'
        self.knowledge_queue = 'knowledge_base_queue'
        self.action_queue = 'action_api_queue'
        
    def connect(self):
        try:
            credentials = pika.PlainCredentials(self.username, self.password)
            parameters = pika.ConnectionParameters(
                host=self.host,
                port=self.port,
                credentials=credentials
            )
            self.connection = pika.BlockingConnection(parameters)
            self.channel = self.connection.channel()
            
            self.channel.exchange_declare(exchange=self.exchange, exchange_type='direct', durable=True)
            
            self.channel.queue_declare(queue=self.knowledge_queue, durable=True)
            self.channel.queue_declare(queue=self.action_queue, durable=True)
            
            self.channel.queue_bind(
                exchange=self.exchange,
                queue=self.knowledge_queue,
                routing_key='knowledge'
            )
            
            self.channel.queue_bind(
                exchange=self.exchange,
                queue=self.action_queue,
                routing_key='action'
            )
            
            logger.info("Connected to RabbitMQ")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {str(e)}")
            return False
    
    def publish_message(self, routing_key: str, message: Dict[str, Any]):
        try:
            if not self.channel or self.channel.is_closed:
                self.connect()
            
            self.channel.basic_publish(
                exchange=self.exchange,
                routing_key=routing_key,
                body=json.dumps(message),
                properties=pika.BasicProperties(
                    delivery_mode=2,
                )
            )
            logger.info(f"Message published to {routing_key} queue")
            return True
        except Exception as e:
            logger.error(f"Failed to publish message: {str(e)}")
            return False
    
    def consume_messages(self, queue_name: str, callback: Callable):
        def on_message(channel, method, properties, body):
            try:
                message = json.loads(body.decode('utf-8'))
                callback(message)
                channel.basic_ack(delivery_tag=method.delivery_tag)
            except Exception as e:
                logger.error(f"Error processing message: {str(e)}")
                try:
                    channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
                except:
                    pass
        
        connection = None
        try:
            credentials = pika.PlainCredentials(self.username, self.password)
            parameters = pika.ConnectionParameters(
                host=self.host,
                port=self.port,
                credentials=credentials
            )
            connection = pika.BlockingConnection(parameters)
            channel = connection.channel()
            
            channel.exchange_declare(exchange=self.exchange, exchange_type='direct', durable=True)
            channel.queue_declare(queue=queue_name, durable=True)
            
            if queue_name == self.knowledge_queue:
                channel.queue_bind(
                    exchange=self.exchange,
                    queue=queue_name,
                    routing_key='knowledge'
                )
            elif queue_name == self.action_queue:
                channel.queue_bind(
                    exchange=self.exchange,
                    queue=queue_name,
                    routing_key='action'
                )
            
            channel.basic_qos(prefetch_count=1)
            channel.basic_consume(
                queue=queue_name,
                on_message_callback=on_message
            )
            
            logger.info(f"Started consuming from {queue_name}")
            channel.start_consuming()
        except KeyboardInterrupt:
            if connection and not connection.is_closed:
                connection.close()
        except Exception as e:
            logger.error(f"Error consuming messages from {queue_name}: {str(e)}")
            if connection and not connection.is_closed:
                try:
                    connection.close()
                except:
                    pass
    
    def close(self):
        if self.connection and not self.connection.is_closed:
            self.connection.close()

