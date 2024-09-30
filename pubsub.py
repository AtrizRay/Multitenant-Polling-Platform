import redis
import logging

# Setup Redis connection
redis_client = redis.StrictRedis(host='localhost', port=6379, db=0)

# Configure logging
logging.basicConfig(level=logging.INFO)

def publish(channel, message):
    # Log the publish action
    logging.info(f"Publishing message to channel '{channel}': {message}")
    redis_client.publish(channel, message)

def subscribe(channel):
    pubsub = redis_client.pubsub()
    pubsub.subscribe(channel)
    
    # Log the subscription action
    logging.info(f"Subscribed to channel '{channel}'")
    
    return pubsub
