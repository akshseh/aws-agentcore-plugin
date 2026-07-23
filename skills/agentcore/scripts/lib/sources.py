"""
Data source definitions for the AgentCore skill CLI.

Each source represents an independent documentation corpus that can be
enabled/disabled via the AGENTCORE_SOURCES environment variable.
All sources are fetched dynamically at runtime — no static content.

Source types:
    "llms_txt"      Standard llms.txt manifest (Markdown with [title](url): description)
    "boto3_index"   boto3 HTML index page with method links
    "faq_page"      AWS FAQ page with Q&A sections
    "github_readme" GitHub repo README for SDK reference
    "single_page"   A single HTML page (e.g., CDK docs) indexed as one searchable entry
"""

import os

ALL_SOURCES = [
    {
        "id": "docs",
        "name": "AgentCore Developer Guide",
        "description": "Official developer guide covering all AgentCore components — Runtime, Harness, Memory, Gateway, Identity, Browser, Code Interpreter, Observability, Policy, Evaluations, and more.",
        "type": "llms_txt",
        "indexUrl": "https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/llms.txt",
        "baseUrl": "https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/",
    },
    {
        "id": "api_data_plane",
        "name": "Data Plane API Reference",
        "description": "API reference for runtime operations — invoking agents, memory CRUD, browser sessions, code interpreter, identity tokens, evaluations, and A/B tests.",
        "type": "llms_txt",
        "indexUrl": "https://docs.aws.amazon.com/bedrock-agentcore/latest/APIReference/llms.txt",
        "baseUrl": "https://docs.aws.amazon.com/bedrock-agentcore/latest/APIReference/",
    },
    {
        "id": "api_control_plane",
        "name": "Control Plane API Reference",
        "description": "API reference for resource management — creating, updating, deleting agent runtimes, harnesses, gateways, memory stores, identity providers, policies, and evaluators.",
        "type": "llms_txt",
        "indexUrl": "https://docs.aws.amazon.com/bedrock-agentcore-control/latest/APIReference/llms.txt",
        "baseUrl": "https://docs.aws.amazon.com/bedrock-agentcore-control/latest/APIReference/",
    },
    {
        "id": "boto3_data_plane",
        "name": "Boto3 Data Plane SDK Reference",
        "description": "Python boto3 client reference for bedrock-agentcore data plane — invoke agents, memory operations, browser sessions, code interpreter, identity tokens, evaluations.",
        "type": "boto3_index",
        "indexUrl": "https://docs.aws.amazon.com/boto3/latest/reference/services/bedrock-agentcore.html",
        "baseUrl": "https://docs.aws.amazon.com/boto3/latest/reference/services/",
    },
    {
        "id": "boto3_control_plane",
        "name": "Boto3 Control Plane SDK Reference",
        "description": "Python boto3 client reference for bedrock-agentcore-control — create, update, delete, and list agent runtimes, harnesses, gateways, memory stores, identity providers, policies, and evaluators.",
        "type": "boto3_index",
        "indexUrl": "https://docs.aws.amazon.com/boto3/latest/reference/services/bedrock-agentcore-control.html",
        "baseUrl": "https://docs.aws.amazon.com/boto3/latest/reference/services/",
    },
    {
        "id": "sdk",
        "name": "AgentCore Python SDK",
        "description": "The bedrock-agentcore Python package — BedrockAgentCoreApp for Runtime deployment, MemoryClient, framework integrations (Strands, LangGraph, CrewAI, Google ADK, OpenAI), AG-UI and A2A protocol support.",
        "type": "github_readme",
        "indexUrl": "https://raw.githubusercontent.com/aws/bedrock-agentcore-sdk-python/main/README.md",
        "baseUrl": "https://github.com/aws/bedrock-agentcore-sdk-python",
    },
    {
        "id": "cloudformation",
        "name": "CloudFormation Template Reference",
        "description": "AWS CloudFormation resource types and properties for AgentCore — define agent runtimes, gateways, memory stores, identity providers, browsers, code interpreters, and policies as infrastructure-as-code.",
        "type": "llms_txt",
        "indexUrl": "https://docs.aws.amazon.com/AWSCloudFormation/latest/TemplateReference/AWS_BedrockAgentCore/llms.txt",
        "baseUrl": "https://docs.aws.amazon.com/AWSCloudFormation/latest/TemplateReference/",
    },
    {
        "id": "cdk_typescript",
        "name": "AWS CDK (TypeScript) Reference",
        "description": "AWS CDK L1 construct library for AgentCore in TypeScript — CfnAgentRuntime, CfnGateway, CfnMemory, CfnBrowser, CfnCodeInterpreter, and all related constructs with code examples.",
        "type": "single_page",
        "indexUrl": "https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.aws_bedrockagentcore-readme.html",
        "baseUrl": "https://docs.aws.amazon.com/cdk/api/v2/docs/",
    },
    {
        "id": "cdk_python",
        "name": "AWS CDK (Python) Reference",
        "description": "AWS CDK construct library for AgentCore in Python — aws_cdk.aws_bedrockagentcore module with all resource classes and property definitions.",
        "type": "single_page",
        "indexUrl": "https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_bedrockagentcore.html",
        "baseUrl": "https://docs.aws.amazon.com/cdk/api/v2/python/",
    },
    {
        "id": "cdk_java",
        "name": "AWS CDK (Java) Reference",
        "description": "AWS CDK construct library for AgentCore in Java — software.amazon.awscdk.services.bedrockagentcore package with all resource classes.",
        "type": "single_page",
        "indexUrl": "https://docs.aws.amazon.com/cdk/api/v2/java/software/amazon/awscdk/cfnpropertymixins/services/bedrockagentcore/package-summary.html",
        "baseUrl": "https://docs.aws.amazon.com/cdk/api/v2/java/",
    },
    {
        "id": "cdk_dotnet",
        "name": "AWS CDK (.NET) Reference",
        "description": "AWS CDK construct library for AgentCore in .NET — Amazon.CDK.AWS.BedrockAgentCore namespace with all resource classes.",
        "type": "single_page",
        "indexUrl": "https://docs.aws.amazon.com/cdk/api/v2/dotnet/api/Amazon.CDK.AWS.BedrockAgentCore.html",
        "baseUrl": "https://docs.aws.amazon.com/cdk/api/v2/dotnet/",
    },
    {
        "id": "cdk_go",
        "name": "AWS CDK (Go) Reference",
        "description": "AWS CDK construct library for AgentCore in Go — awsbedrockagentcore package with all resource structs and interfaces.",
        "type": "single_page",
        "indexUrl": "https://pkg.go.dev/github.com/aws/aws-cdk-go/awscdk/v2@v2.260.0/awsbedrockagentcore",
        "baseUrl": "https://pkg.go.dev/",
    },
    {
        "id": "faq",
        "name": "AgentCore FAQs",
        "description": "Frequently asked questions about AgentCore — general concepts, pricing, supported frameworks/models/regions, and per-service capabilities.",
        "type": "faq_page",
        "indexUrl": "https://aws.amazon.com/bedrock/agentcore/faqs/",
        "baseUrl": "https://aws.amazon.com/bedrock/agentcore/faqs/",
    },
]


def get_enabled_sources():
    """Get enabled sources based on the AGENTCORE_SOURCES env var.

    AGENTCORE_SOURCES format:
        - Not set or "all" -> all sources enabled
        - Comma-separated list of IDs -> only those enabled (e.g., "docs,api_data_plane,faq")
        - Prefix with "-" to disable specific ones (e.g., "-faq,-boto3" keeps the rest)
    """
    env_sources = (os.environ.get("AGENTCORE_SOURCES") or "").strip()

    if not env_sources or env_sources == "all":
        return list(ALL_SOURCES)

    parts = [p.strip().lower() for p in env_sources.split(",")]

    exclusions = [p[1:] for p in parts if p.startswith("-")]
    if exclusions:
        return [s for s in ALL_SOURCES if s["id"] not in exclusions]

    return [s for s in ALL_SOURCES if s["id"] in parts]


def get_all_source_ids():
    return [s["id"] for s in ALL_SOURCES]
