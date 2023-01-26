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

    ssm_client = boto3.client("ssm")

    resp = ssm_client.get_parameter(
        Name=os.environ["BUCKET_SSM_PARAM"], WithDecryption=True
    )
    bucket_ssm_param = json.loads(resp["Parameter"]["Value"])

    s3 = boto3.resource("s3")
    feed_object = s3.Object(
        bucket_ssm_param["bucket_name"], bucket_ssm_param["object_key"]
    )

    if "md5" in qsp:
        pass  # return the MD5 hash / e_tag

    # details = {
    #     **qsp,
    #     **{"body": body},
    #     **headers,
    #     **bucket_ssm_param
    # }
    # if body:
    #     details["body"] = body

    # https://botocore.amazonaws.com/v1/documentation/api/latest/reference/response.html
    response = feed_object.get()

    return_dict = {
        "statusCode": 200,
        "headers": {
            "Content-Type": "text/plain",
        },
        "body": (response["Body"]).read().decode()
        # "body": "Hello, CDK! You have hit "
        # + event["path"]
        # + "\nDetails = "
        # + json.dumps(details, indent=2)
        # + "\n",
    }

    # print(json.dumps(return_dict))

    return return_dict
