---
name: deploy
description: Deploy an AgentCore agent to AWS and troubleshoot deployment/runtime failures — agentcore deploy, CDK/CloudFormation infrastructure, environments and endpoints, CI/CD, and diagnosing errors. Triggers on "deploy", "ship", "launch to AWS", "deploy fails", "invoke errors", "AccessDeniedException", "ThrottlingException", "Too many tokens", "CDK bootstrap", "works locally but fails deployed". Use for anything between working-locally and running-in-AWS. Not for writing agent code — use build. Slow-but-working performance issues route here only if deploy-config-related; code fixes route to build.
allowed-tools:
  - mcp__plugin_aws-agentcore_agentcore-docs__list_agentcore_components
  - mcp__plugin_aws-agentcore_agentcore-docs__search_agentcore_docs
  - mcp__plugin_aws-agentcore_agentcore-docs__fetch_agentcore_doc
  - mcp__agentcore__list_agentcore_components
  - mcp__agentcore__search_agentcore_docs
  - mcp__agentcore__fetch_agentcore_doc
  - mcp__plugin_aws-agentcore_drawio__open_drawio_xml
  - mcp__plugin_aws-agentcore_drawio__open_drawio_mermaid
  - mcp__plugin_aws-agentcore_drawio__open_drawio_csv
  - mcp__plugin_aws-agentcore_drawio__search_shapes
  - mcp__plugin_aws-agentcore_drawio__list_pages
  - mcp__plugin_aws-agentcore_drawio__get_page
  - mcp__plugin_aws-agentcore_drawio__set_page
  - mcp__drawio__open_drawio_xml
  - mcp__drawio__open_drawio_mermaid
  - mcp__drawio__open_drawio_csv
  - mcp__drawio__search_shapes
  - mcp__drawio__list_pages
  - mcp__drawio__get_page
  - mcp__drawio__set_page
  - Read
  - Grep
  - Glob
  - Bash(agentcore --version)
  - Bash(agentcore * --help)
  - Bash(agentcore status*)
  - Bash(agentcore logs*)
  - Bash(agentcore deploy --dry-run*)
  - Bash(aws sts get-caller-identity*)
  - Bash(cdk diff*)
---

# AgentCore Deployer

Get the agent from working-locally to running-in-AWS, and fix it when it breaks.

## Ground rules

1. **CLI for dev, IaC as source of truth for production.** `agentcore deploy` (CDK under the hood) is the right loop for PoC and iteration. For production, resources belong in the org's IaC (CDK/CloudFormation/Terraform) in CI/CD — verify current CloudFormation/CDK resource coverage live (`cloudformation` and `cdk_*` sources in `search_agentcore_docs`) before promising a construct exists.
2. **Verify before you diagnose.** Read the actual error (`agentcore logs`, CloudWatch, CDK output) before proposing a fix. A signal that pattern-matches a known failure may have a different cause.
3. **Confirm account and region before any create/deploy.** Run `aws sts get-caller-identity` and check `agentcore/aws-targets.json` — deploying to the wrong account/region is the most common self-inflicted failure. Region mismatch between config, credentials, and model access breaks late and confusingly.
4. **Present mutating commands before running them.** `agentcore deploy --dry-run` / `cdk diff` first; never run destructive commands (`agentcore destroy`) without explicit user confirmation.

## Deploy workflow

1. **Preflight**: `agentcore --version` (offer `agentcore update` if stale) · AWS credentials valid · target account/region confirmed · model access enabled in that region (Bedrock console/API — verify, don't assume) · for VPC deployments, subnets are in supported AZ IDs (fetch the live AZ table from the `agentcore-vpc` doc; check with `aws ec2 describe-subnets --query 'Subnets[].AvailabilityZoneId'`).
2. **Dry-run**: `agentcore deploy --dry-run` (or `cdk diff`) and review with the user.
3. **Deploy**: `agentcore deploy`. First deploy may CDK-bootstrap the account and take minutes; memory resources can sit in CREATING for a few minutes — that's normal, don't re-run.
4. **Verify**: `agentcore status`, then a real invocation (`agentcore invoke --prompt "..."`), then check traces/logs (`agentcore logs`, CloudWatch). A deploy isn't done until an invoke succeeds.
5. **Environments**: use named endpoints pinned to versions (`prod`, `staging`); never point production clients at latest. Multi-env: separate targets/accounts, promote by repointing endpoints.

### Diagram the deployment topology (optional)

When it clarifies a multi-environment or multi-account setup, offer a deployment-topology diagram via the `drawio` MCP tools — accounts/regions, endpoints pinned to versions (`prod`/`staging`), the VPC/network boundary, and the CI/CD promotion flow. Render with `open_drawio_mermaid`, or `open_drawio_xml` with `search_shapes` for branded AWS icons (don't guess style strings). Skip silently for a simple single-account deploy or if the user didn't ask; if the draw.io server isn't available, say so and continue — never block the deploy on the diagram.

## Troubleshooting

Always start from the real error text. Common failure classes to check against (verify current fixes in live docs — `runtime-troubleshooting` and the code-deploy `common-issues` pages):

| Symptom | Usual cause | First check |
|---|---|---|
| `AccessDeniedException` on model call | Model access not enabled in region, missing inference-profile ARNs in execution role, or cross-region profile needs multiple ARNs | Bedrock model access page for the target region; execution role policy resources |
| `ThrottlingException: Too many tokens` | Account-level token quota (can be stuck at zero on new accounts, sometimes shown as "not adjustable") | Service Quotas console for Bedrock token quotas; if zero/not-adjustable, an AWS Support case for account verification is usually required |
| Deploy silently fails at role step | Deployer lacks `iam:PassRole` for the execution role, or a managed-policy PassRole scope (e.g. role-name patterns) doesn't match | PassRole permission for the exact role ARN; check CloudTrail for the denied `iam:PassRole`; verify current managed-policy scoping in live docs |
| CDK bootstrap errors | Account never bootstrapped / bootstrap role missing | `cdk bootstrap` in target account+region |
| VPC resource creation fails | Subnet in unsupported AZ | AZ **IDs** (not names) vs. live supported-AZ table |
| Works in `agentcore dev`, fails deployed | Local/deployed gap: memory or gateway URL exists only after deploy; env vars differ | Config references to undeployed resources |
| Invoke hangs/timeouts | Long-running work over sync invoke; execution limits | Async patterns, lifecycle settings, `agentcore logs --since 30m --level error` |

If the error doesn't match, search the docs for the exact error string before theorizing.

## Production deployment checklist (gate before first prod deploy)

Run `/aws-agentcore:production-readiness` for the full review. Blockers at the deploy layer: least-privilege execution role (not CLI-generated), trust policy with `aws:SourceAccount`/`aws:SourceArn`, endpoint pinning, observability alarms live, IaC (not CLI state) owning the resources, and a rollback plan (previous version + endpoint repoint).
