import os
import json
import boto3


def lambda_handler(event, context):

    if "DEBUG" in os.environ:
        print(json.dumps(event))

    qsp = event.get("queryStringParameters", {})
    if not qsp:
        qsp = {}

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
        # return the MD5 hash / e_tag

        e_tag = feed_object.e_tag
        # delete the leading and trailing quotes
        e_tag = e_tag.replace(r'"', "")

        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "text/plain",
            },
            "body": e_tag,
        }

    # https://botocore.amazonaws.com/v1/documentation/api/latest/reference/response.html
    response = feed_object.get()

    return_dict = {
        "statusCode": 200,
        "headers": {
            "Content-Type": "text/plain",
        },
        "body": (response["Body"]).read().decode(),
    }

    return return_dict
