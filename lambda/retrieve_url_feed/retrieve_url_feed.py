import os
import json
import boto3


def lambda_handler(event, context):

    if "DEBUG" in os.environ:
        print(json.dumps(event))

    qsp = event.get("queryStringParameters", {})
    if not qsp:
        qsp = {}
    body = event.get("body", "")
    if not body:
        body = ""
    headers = event.get("headers", {})

    details = {
        **qsp,
        **{"body": body},
        **headers,
    }
    if body:
        details["body"] = body

    return_dict = {
        "statusCode": 200,
        "headers": {"Content-Type": "text/plain"},
        "body": "Hello, CDK! You have hit "
        + event["path"]
        + "\nDetails = "
        + json.dumps(details)
        + "\n",
    }

    print(json.dumps(return_dict))

    return return_dict
