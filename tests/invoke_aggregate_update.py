import json
import os

TOKEN = ""
AGENT_ID = "164589663015689482"
ORG_ID = "7363803534221262848"
CHANNEL_NAME = "tag_values"
CHANNEL_NAME_MESSAGE = "dv-rpc"

schedule_payload = {
    "op": "on_schedule",
    "d": {
        "schedule_id": AGENT_ID,
        "organisation_id": ORG_ID,
    },
    "token": TOKEN,
}

aggregate_update_payload = {
    "op": "on_aggregate_update",
    "d": {
        "channel": {
            "agent_id": AGENT_ID,
            "name": CHANNEL_NAME,
        },
        "owner_id": AGENT_ID,
        "channel_name": CHANNEL_NAME,
        "author_id": ORG_ID,
        "organisation_id": ORG_ID,
        "request_data": {
            "data": {
                "digital_matter_processor-1": {"odometer_km": 5, "run_hours": 20.6}
            }
        },
        "aggregate": {
            "data": {
                "digital_matter_processor-1": {"odometer_km": 5, "run_hours": 20.6}
            },
            "attachments": [],
        },
    },
    "token": TOKEN,
}


message_create_payload = {
    "op": "on_message_create",
    "d": {
        "channel": {
            "agent_id": AGENT_ID,
            "name": CHANNEL_NAME_MESSAGE,
        },
        "owner_id": AGENT_ID,
        "channel_name": CHANNEL_NAME_MESSAGE,
        "author_id": ORG_ID,
        "organisation_id": ORG_ID,
        "message": {
            "id": "164885485443898671",
            "author_id": ORG_ID,
            "channel": {
                "agent_id": AGENT_ID,
                "name": CHANNEL_NAME_MESSAGE,
            },
            "data": {
                "app_key": "maintenance_manager_1",
                "method": "record_service",
                "request": {
                    "engine_hours": 20.7,
                    "machine_odometer": 5,
                    "service_dt": 1775001139307,
                },
                "type": "rpc",
                # "type": "rpc",
                # "app_key": "maintenance_manager_1",
                # "method": "set_machine_hours",
                # "request": 10,
            },
            "attachments": [],
        },
    },
    "token": TOKEN,
}

# data = json.loads(event["Records"][0]["Sns"]["Message"])
# subscription_id = event["Records"][0]["EventSubscriptionArn"]

sns_payload = {
    "Records": [
        {
            "Sns": {"Message": json.dumps(message_create_payload)},
            "EventSubscriptionArn": "arn:aws:sns:ap-southeast-2:484395055539:proc-ch-164589663015689482-dv-rpc-onmessagecreate:d6186047-7908-4ac0-8463-d1c065dbf0c8",
            "EventSource": "aws:sns",
        }
    ]
}

payload = sns_payload

os.environ["DOOVER_DATA_ENDPOINT"] = "https://data.staging.udoover.com/api"

from processor import handler

handler(payload, {})
