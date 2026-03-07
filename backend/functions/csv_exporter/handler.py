import json


def handler(event, context):
    print("Event received:")
    print(json.dumps(event))

    return {
        "statusCode": 200,
        "body": json.dumps("CSV exporter placeholder")
    }