# Privacy

This plugin collects **no telemetry, analytics, or usage data**. There is no
account, registration, or API key.

## What the MCP server sends, and where

The bundled `agentcore-docs` MCP server runs locally on your machine (stdio —
no network listener). It makes outbound HTTPS requests only to fetch public
documentation:

| Destination | What is sent | When |
|---|---|---|
| `docs.aws.amazon.com` | HTTP GET requests for public documentation pages and manifests | On startup (index) and when a tool fetches a page |
| `aws.amazon.com` | HTTP GET for the public AgentCore FAQ page | When the `faq` source is enabled |
| `raw.githubusercontent.com` / `github.com` | HTTP GET for the public AgentCore SDK docs | When the `sdk` source is enabled |
| `pkg.go.dev` | HTTP GET for the public CDK Go reference | When the `cdk_go` source is enabled |

Your **search queries never leave your machine** — searching runs against a
locally built index, and only the resulting page URLs are fetched. Fetched
pages are cached in memory (never written to disk) and discarded when the
server process exits.

These are ordinary requests to public websites, governed by
[AWS's privacy notice](https://aws.amazon.com/privacy/) and GitHub's privacy
policy respectively.

## What the draw.io diagram server sends, and where

The `drawio` MCP server (the official [`@drawio/mcp`](https://www.npmjs.com/package/@drawio/mcp)
package) is fetched from the npm registry on first use via `npx` and then runs
locally over stdio. To display a diagram it opens the draw.io web editor at
`https://app.diagrams.net/`, passing the **diagram content** (the mxGraph XML /
Mermaid you asked it to render) in the URL. That means the architecture you
diagram is sent to the draw.io editor to render it in your browser.

If you don't want diagram content to reach `app.diagrams.net`, either point the
server at a self-hosted draw.io instance by setting `DRAWIO_BASE_URL` in the
server's `env` block, or don't accept the diagram step (the skills always print
the design as text/Mermaid regardless). draw.io is a third party governed by its
own [privacy policy](https://www.drawio.com/privacy).

## What the skills do

The skills are instructions for your AI assistant. When you use them, your
assistant may (with your approval, per your Claude Code permission settings)
run AWS CLI commands against **your** AWS account using **your** locally
configured credentials. Nothing is proxied through any third party, and this
plugin never reads, stores, or transmits your AWS credentials.
