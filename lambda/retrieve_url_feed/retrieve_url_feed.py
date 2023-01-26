import os
import json
import boto3
from botocore.exceptions import ClientError

# https://docs.aws.amazon.com/apigateway/latest/developerguide/limits.html#http-api-quotas
# the maximum payload size is 10MB
MAX_PAYLOAD_SIZE = 10 * (2**20)


def lambda_handler(event, context):

    if "DEBUG" in os.environ:
        print(json.dumps(event))

    qsp = event.get("queryStringParameters", {})
    if not qsp:
        qsp = {}

    filename = qsp.get("filename", None)
    if not filename:
        message = "expected ?filename= parameter in URL"
        print(message)
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "text/plain",
            },
            "body": message,
        }

    ssm_client = boto3.client("ssm")

    resp = ssm_client.get_parameter(
        Name=os.environ["BUCKET_SSM_PARAM"], WithDecryption=True
    )
    bucket_ssm_param = json.loads(resp["Parameter"]["Value"])

    s3 = boto3.resource("s3")
    feed_object = s3.Object(
        bucket_ssm_param["bucket_name"],
        filename
        # bucket_ssm_param["object_key"]
    )

    # Get the e_tag first. If there is any problem getting the file,
    # an exception will be thrown. Handle it gracefully.

    try:
        e_tag = feed_object.e_tag

    except ClientError as exc:
        message = (
            f"error retrieving s3://{feed_object.bucket_name}/{feed_object.key}: {exc}"
        )
        print(message)
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "text/plain",
            },
            "body": message,
        }

    if "md5" in qsp:
        # return the MD5 hash / e_tag

        # delete the leading and trailing quotes
        # e_tag = e_tag.replace(r'"', "")
        e_tag = json.loads(e_tag)

        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "text/plain",
            },
            "body": e_tag,
        }

    if feed_object.content_length > MAX_PAYLOAD_SIZE:
        message = (
            f"s3://{feed_object.bucket_name}/{feed_object.key}"
            + f" is {feed_object.content_length} bytes, which exceeds "
            + f" the maximum size of {MAX_PAYLOAD_SIZE} bytes"
        )
        print(message)
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "text/plain",
            },
            "body": message,
        }

    # https://botocore.amazonaws.com/v1/documentation/api/latest/reference/response.html

    # add logic to check object size. error if too big.
    response = feed_object.get()

    return_dict = {
        "statusCode": 200,
        "headers": {"Content-Type": feed_object.content_type},  # "text/plain",
        "body": (response["Body"]).read().decode(),
    }

    return return_dict


if __name__ == "__main__":
    import pdb

    event = {}
    # with open(sys.argv[1], 'r') as fp:
    #     event = json.load(fp)

    response = lambda_handler(event=event, context={})
    print(response)
