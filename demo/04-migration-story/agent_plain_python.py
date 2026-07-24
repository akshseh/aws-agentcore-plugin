import boto3

bedrock = boto3.client("bedrock-runtime")


def handle_request(user_message):
    response = bedrock.converse(
        modelId="anthropic.claude-sonnet-4-20250514",
        messages=[{"role": "user", "content": [{"text": user_message}]}],
    )
    return response["output"]["message"]["content"][0]["text"]
