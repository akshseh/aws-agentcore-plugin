import { describe, it, expect } from "vitest";
import { readFileSync } from "node:fs";
import path from "node:path";
import { htmlToMarkdown } from "../src/fetcher.js";

// Fixtures are trimmed captures of the *real* CDK reference pages this
// server fetches (Python/Sphinx, .NET/DocFX, Go/pkg.go.dev), each wrapped in
// the same surrounding nav/wrapper markup the live sites use. Regressions in
// container-selector priority (see src/fetcher.ts CONTENT_CONTAINERS) won't
// show up against synthetic HTML that only has one plausible container —
// these fixtures deliberately nest containers the way the real sites do.
function readFixture(name: string): string {
  return readFileSync(path.resolve(__dirname, "fixtures", name), "utf-8");
}

describe("htmlToMarkdown against real CDK reference page shapes", () => {
  it("extracts CDK Python (Sphinx role=main) content and excludes sidebar nav", () => {
    const md = htmlToMarkdown(readFixture("cdk-python-real.html"));

    expect(md).toContain("aws_cdk.aws_bedrockagentcore");
    expect(md).not.toContain("other-service-1");
    expect(md).not.toContain("other-service-2");
    expect(md).not.toMatch(/<div|<nav|<footer/);
  });

  it("extracts CDK .NET (DocFX article#_content) and excludes the outer sidenav wrapper", () => {
    const md = htmlToMarkdown(readFixture("cdk-dotnet-real.html"));

    // Regression guard: the outer <div role="main"> on DocFX pages also
    // matches the Sphinx selector, so without ordering article#_content
    // first, extraction stops at that wrapper and leaks the ToC toggle.
    expect(md).not.toContain("Show / Hide Table of Contents");
    expect(md).not.toContain("sidetoc");
    expect(md).toContain("Namespace Amazon.CDK.AWS.BedrockAgentCore");
  });

  it("extracts CDK Go (pkg.go.dev UnitReadme-content) and excludes the surrounding import/nav noise", () => {
    const md = htmlToMarkdown(readFixture("cdk-go-real.html"));

    expect(md).not.toContain("unrelated-import-x");
    expect(md).not.toContain("breadcrumb noise");
    expect(md).toContain("Amazon Bedrock AgentCore Construct Library");
  });

  it("renders full FAQ content from the embedded JSON blob when fetch_agentcore_doc is used on the FAQ page", () => {
    // fetch_agentcore_doc runs full pages through htmlToMarkdown too (not
    // just search_agentcore_docs's index-building path in doc-index.ts).
    // Without this, the "full content" a user asks for is just empty
    // <h2>/<h3> shells and nav — this fixture is the same real capture
    // used by the FAQ parser test in parsers.test.ts.
    const md = htmlToMarkdown(readFixture("faq-real.html"));

    expect(md).toContain("## What is Amazon Bedrock AgentCore?");
    expect(md).toContain("platform to build, connect, and optimize AI agents at scale");
    expect(md).not.toMatch(/<h2|<h3|<script/);
  });

  it("converts an HTML table to a Markdown table instead of collapsing it to run-on text", () => {
    const html = `<main><table>
      <tr><th>Name</th><th>Description</th></tr>
      <tr><td>AddApiGatewayTargetOptions</td><td>Options for adding an <a href="x.html">API Gateway</a> target.</td></tr>
    </table></main>`;

    const md = htmlToMarkdown(html);

    expect(md).toContain("| Name | Description |");
    expect(md).toContain("| --- | --- |");
    expect(md).toContain("| AddApiGatewayTargetOptions | Options for adding an API Gateway (x.html) target. |");
  });
});
