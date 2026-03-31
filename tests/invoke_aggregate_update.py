import json
import os

TOKEN = ""
AGENT_ID = "164589663015689482"
ORG_ID = "7363803534221262848"
CHANNEL_NAME = "tag_values"
CHANNEL_NAME_MESSAGE = "ui_cmds"

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
            "id": "164874368382426401",
            "author_id": ORG_ID,
            "channel": {
                "agent_id": AGENT_ID,
                "name": CHANNEL_NAME_MESSAGE,
            },
            "data": {
                "type": "rpc",
                "app_key": "maintenance_manager_1",
                "method": "set_machine_hours",
                "request": 10,
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
            "EventSubscriptionArn": "arn:aws:sns:ap-southeast-2:484395055539:proc-ch-164589663015689482-tag_values-onmessagecreate:568b704f-51d1-41ca-b5e5-fd138b501d9a",
            "EventSource": "aws:sns",
        }
    ]
}

payload = sns_payload

os.environ["DOOVER_DATA_ENDPOINT"] = "https://data.staging.udoover.com/api"

from processor import handler

handler(payload, {})
