import json
import boto3
from botocore.exceptions import ClientError

iam = boto3.client("iam")

def lambda_handler(event, context):
    try:
        # Read body (assume JSON sent in POST)
        body = event.get("body")
        if isinstance(body, str):
            body = json.loads(body)
        policy = body.get("policy")

        if not policy:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Request must include 'policy' JSON"})
            }

        # Run the IAM Policy Simulator
        response = iam.simulate_custom_policy(
            PolicyInputList=[json.dumps(policy)],
            ActionNames=[
                "s3:ListBucket",
                "s3:GetObject",
                "s3:DescribeJob"
            ],
            ResourceArns=["*"]
        )

        # Return raw simulator output (JSON-encoded)
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(response, default=str)
        }

    except ClientError as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"aws_error": e.response["Error"]["Message"]})
        }
    except Exception as e:
        return {
            "statusCode": 400,
            "body": json.dumps({"error": str(e)})
        }
