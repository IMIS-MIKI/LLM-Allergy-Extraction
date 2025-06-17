import os
import json
import re
from datetime import datetime
from src.logging_config import logger
from src.main_allergy import run_llm_allergy

from dotenv import load_dotenv
from kafka.consumer import KafkaConsumer
from kafka.producer import KafkaProducer
from pydantic import BaseModel

load_dotenv(verbose=True)


class Task(BaseModel):
    text: str
    patient_id: str
    metadata: dict


def get_modus_props():
    in_topic = os.environ['INCOMING_TOPIC_NAME']
    out_topic = os.environ['OUTGOING_TOPIC_NAME']
    consumer_group = os.environ['CONSUMER_GROUP']
    max_poll_records = int(os.environ['MAX_POLL_RECORDS'])
    bootstrap_servers = os.environ['BOOTSTRAP_SERVER']
    ollama_model = os.environ['OLLAMA_MODEL']
    return in_topic, out_topic, consumer_group, bootstrap_servers, max_poll_records, ollama_model


def safe_json_deserializer(x):
    try:
        # Decode from bytes
        s = x.decode("utf-8")
        
        # Replace raw control characters with spaces (or escape them)
        s = re.sub(r'(?<!\\)[\n\r\t]', ' ', s)

        return json.loads(s)
    except Exception as e:
        print(f"JSON decode error: {e}")
        return {}

def send_error(message, bootstrap_servers, error):
    logger.exception(error)
    logger.error('Failed: ' + str(message))
    producer = KafkaProducer(value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                             bootstrap_servers=bootstrap_servers)
    res = dict()
    res['date_created'] = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    res['message'] = message[6]
    res['error'] = str(error)

    producer.send(topic=os.environ['ERROR_TOPIC_NAME'], value=res)
    producer.flush()


def start_consumer():
    in_topic, out_topic, consumer_group, bootstrap_servers, max_poll_records, ollama_model = get_modus_props()

    logger.info("Start Allergy Extraction Service")

    try:
        consumer = KafkaConsumer(
            bootstrap_servers=bootstrap_servers,
            auto_offset_reset="latest",
            enable_auto_commit=True,
            group_id=consumer_group,
            max_poll_records=max_poll_records,
            value_deserializer=safe_json_deserializer,
            max_poll_interval_ms=60 * 60 * 1000
        )

        logger.info("Successfully created consumer")

    except Exception as error:
        logger.exception('Exception occurred ' + str(error.__module__))
        exit()

    consumer.subscribe([in_topic])

    for message in consumer:
        try:
            payload = None
            res = None
            consumer.commit()

            payload = message[6]

            try:
                Task(**payload)
            except:
                raise ValueError('Incoming task JSON is not conformant.')
            
            metadata = payload['metadata']
            text = payload['text']
            patient_id = payload['patient_id']

            # Here comes your processing
            start = datetime.now()
            fhir_bundle_dict = run_llm_allergy(ollama_model, text, patient_id)
            end = datetime.now()

            # Note might be empty if no allergies are found
            if not fhir_bundle_dict:
                continue

            res = dict()
            res['response'] = fhir_bundle_dict
            res['metadata'] = metadata
            res['metadata']['duration'] = str(end - start)

            logger.debug('Response: ' + str(res))

            # https://forum.confluent.io/t/what-should-i-use-as-the-key-for-my-kafka-message/312
            producer = KafkaProducer(value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                                     bootstrap_servers=bootstrap_servers)
            producer.send(topic=out_topic, value=res)
            producer.flush()

        except Exception as error:
            if payload:
                logger.error('Payload: ' + str(payload))
            else:
                logger.error('Original Message: ' + str(message.value))
            if res:
                logger.error('Response: ' + str(res))
            logger.exception("Exception occurred")
            send_error(message, bootstrap_servers, error)
