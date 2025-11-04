import json
import boto3
from botocore.exceptions import ClientError

iam = boto3.client("iam")

def lambda_handler(event, context):
    try:
        # Parse incoming event
        body = event.get("body", event)
        if isinstance(body, str):
            body = json.loads(body)

        policy = body.get("policy")
        if not policy:
            return {"statusCode": 400, "body": json.dumps({"error": "Missing 'policy'"})}

        # Extract statements (ensure array form)
        statements = policy.get("Statement", [])
        if isinstance(statements, dict):
            statements = [statements]

        all_results = []

        # Loop through each SID / Statement
        for stmt in statements:
            sid = stmt.get("Sid", "NoSid")
            actions = stmt.get("Action")
            resources = stmt.get("Resource")

            # Normalize to lists
            if isinstance(actions, str):
                actions = [actions]
            if isinstance(resources, str):
                resources = [resources]

            # Run one simulation per statement
            response = iam.simulate_custom_policy(
                PolicyInputList=[json.dumps(policy)],
                ActionNames=actions,
                ResourceArns=resources
            )

            # Collect evaluation results with SID context
            results = response.get("EvaluationResults", [])
            for r in results:
                r["Sid"] = sid
            all_results.extend(results)

        # Combine everything into one clean response
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"EvaluationResults": all_results}, default=str)
        }

    except ClientError as e:
        return {"statusCode": 500, "body": json.dumps({"aws_error": e.response["Error"]["Message"]})}
    except Exception as e:
        return {"statusCode": 400, "body": json.dumps({"error": str(e)})}
