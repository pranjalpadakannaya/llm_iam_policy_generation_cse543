import json

def lambda_handler(event, context):
    try:
        # Parse input
        body = event.get("body", event)
        if isinstance(body, str):
            body = json.loads(body)

        # Expected (ground truth) actions
        gt_actions = set(body.get("expectedActions", []))

        # Predicted actions from simulator: e.g. ["s3:GetObject: allowed", "s3:PutObject: implicitDeny"]
        pred_results = body.get("predictedActions", [])

        # Extract only allowed actions (effective permissions granted by the LLM policy)
        pred_allowed = set()
        pred_denied = set()
        for item in pred_results:
            parts = item.split(":")
            if len(parts) < 3:
                continue
            action = parts[0].strip() + ":" + parts[1].strip()
            decision = parts[2].strip().lower()
            if "allowed" in decision:
                pred_allowed.add(action)
            else:
                pred_denied.add(action)

        # Compute intersections and differences
        intersection = gt_actions.intersection(pred_allowed)

        # Classification logic
        if pred_allowed == gt_actions:
            label = "equivalent"
        elif gt_actions.issubset(pred_allowed) and pred_allowed != gt_actions:
            label = "overpermissive"
        elif len(intersection) > 0 and len(pred_allowed) < len(gt_actions):
            label = "underpermissive"
        else:
            label = "uncomparable"


        # Build response
        response = {
            "expectedActions": list(gt_actions),
            "predAllowedActions": list(pred_allowed),
            "intersection": list(intersection),
            "classification": label
        }

        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(response)
        }

    except Exception as e:
        return {
            "statusCode": 400,
            "body": json.dumps({"error": str(e)})
        }
