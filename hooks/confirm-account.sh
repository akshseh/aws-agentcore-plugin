#!/bin/bash
# PreToolUse hook: before any mutating AgentCore command, surface which AWS
# account and region it will hit. Deploying to the wrong account/region is the
# most common self-inflicted AgentCore failure. Non-mutating commands pass
# through untouched; if anything here fails, we allow rather than break the user.

INPUT=$(cat)

COMMAND=$(node -e "
  try {
    const d = JSON.parse(require('fs').readFileSync(0, 'utf-8'));
    process.stdout.write(String(d.tool_input?.command ?? ''));
  } catch {}
" <<< "$INPUT" 2>/dev/null) || exit 0

# Only mutating operations: agentcore deploy/destroy, or control-plane
# create/update/delete via the AWS CLI. Dry-runs pass through.
if ! echo "$COMMAND" | grep -qE '(^|[;&|[:space:]])agentcore[[:space:]]+(deploy|destroy)|aws[[:space:]]+bedrock-agentcore-control[[:space:]]+(create|update|delete)-'; then
  exit 0
fi
if echo "$COMMAND" | grep -q -- '--dry-run'; then
  exit 0
fi

IDENTITY=$(aws sts get-caller-identity --output text --query '[Account,Arn]' 2>/dev/null)
REGION="${AWS_REGION:-${AWS_DEFAULT_REGION:-$(aws configure get region 2>/dev/null)}}"

if [ -z "$IDENTITY" ]; then
  REASON="Mutating AgentCore command, and AWS credentials could not be verified (aws sts get-caller-identity failed). Confirm credentials before proceeding."
else
  ACCOUNT=$(echo "$IDENTITY" | awk '{print $1}')
  ARN=$(echo "$IDENTITY" | awk '{print $2}')
  REASON="Mutating AgentCore command targeting AWS account ${ACCOUNT} (${ARN}), region ${REGION:-unset}. Confirm this is the intended account and region."
fi

node -e "
  console.log(JSON.stringify({
    hookSpecificOutput: {
      hookEventName: 'PreToolUse',
      permissionDecision: 'ask',
      permissionDecisionReason: process.argv[1]
    }
  }));
" "$REASON"
exit 0
