import { describe, it, expect, vi, beforeEach } from "vitest";
import { searchEntries, buildComponentOverview, type DocEntry, type ComponentSummary } from "../src/doc-index.js";

// --- Unit tests for search and component overview (no network, no LLM) ---

const MOCK_ENTRIES: DocEntry[] = [
  {
    url: "https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/harness.html",
    title: "AgentCore Harness overview",
    description: "Managed agent loop via configuration",
    sourceId: "docs",
    component: "harness",
    tags: ["harness", "docs", "overview"],
  },
  {
    url: "https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/harness-tools.html",
    title: "Harness tools configuration",
    description: "Tools are declarative. Six tool types supported.",
    sourceId: "docs",
    component: "harness",
    tags: ["harness", "docs", "tools", "mcp"],
  },
  {
    url: "https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/memory.html",
    title: "AgentCore Memory overview",
    description: "Short-term and long-term memory for context-aware agents",
    sourceId: "docs",
    component: "memory",
    tags: ["memory", "docs", "overview"],
  },
  {
    url: "https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/runtime-getting-started.html",
    title: "Get started with AgentCore Runtime",
    description: "Tutorials to get started with Runtime",
    sourceId: "docs",
    component: "runtime",
    tags: ["runtime", "docs", "getting-started", "deploy"],
  },
  {
    url: "https://docs.aws.amazon.com/bedrock-agentcore/latest/APIReference/API_CreateGateway.html",
    title: "CreateGateway",
    description: "Creates a gateway for Amazon Bedrock Agent.",
    sourceId: "api_control_plane",
    component: "gateway",
    tags: ["gateway", "api_control_plane", "deploy"],
  },
  {
    url: "https://docs.aws.amazon.com/boto3/latest/reference/services/bedrock-agentcore-control/client/create_gateway.html",
    title: "create_gateway",
    description: "boto3 bedrock-agentcore-control client method",
    sourceId: "boto3_control_plane",
    component: "boto3_control_plane",
    tags: ["boto3_control_plane", "boto3", "sdk", "python", "create"],
  },
  {
    url: "https://aws.amazon.com/bedrock/agentcore/faqs/",
    title: "What is Amazon Bedrock AgentCore?",
    description: "Amazon Bedrock AgentCore is a platform to build, connect, and optimize AI agents at scale.",
    sourceId: "faq",
    component: "faq",
    tags: ["faq", "general"],
  },
  {
    url: "https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/using-any-agent-framework.html",
    title: "Use any agent framework with Runtime",
    description: "Examples for Strands, LangGraph, CrewAI, Google ADK, OpenAI",
    sourceId: "docs",
    component: "runtime",
    tags: ["runtime", "docs", "strands", "langgraph"],
  },
];

describe("searchEntries", () => {
  it("returns results matching query terms in title", () => {
    const results = searchEntries(MOCK_ENTRIES, "harness tools");
    expect(results.length).toBeGreaterThan(0);
    expect(results[0].title).toBe("Harness tools configuration");
  });

  it("returns results matching exact phrase in title", () => {
    const results = searchEntries(MOCK_ENTRIES, "CreateGateway");
    expect(results.length).toBeGreaterThan(0);
    expect(results[0].title).toBe("CreateGateway");
  });

  it("matches against description", () => {
    const results = searchEntries(MOCK_ENTRIES, "declarative");
    expect(results.length).toBeGreaterThan(0);
    expect(results[0].title).toBe("Harness tools configuration");
  });

  it("matches against tags", () => {
    const results = searchEntries(MOCK_ENTRIES, "langgraph");
    expect(results.length).toBeGreaterThan(0);
    expect(results[0].component).toBe("runtime");
  });

  it("filters by sourceId", () => {
    const results = searchEntries(MOCK_ENTRIES, "gateway", { sourceId: "boto3_control_plane" });
    expect(results.length).toBe(1);
    expect(results[0].sourceId).toBe("boto3_control_plane");
  });

  it("respects maxResults", () => {
    const results = searchEntries(MOCK_ENTRIES, "agentcore", { maxResults: 2 });
    expect(results.length).toBeLessThanOrEqual(2);
  });

  it("returns empty array for no matches", () => {
    const results = searchEntries(MOCK_ENTRIES, "xyznonexistent");
    expect(results).toEqual([]);
  });

  it("scores exact title match higher than partial", () => {
    const results = searchEntries(MOCK_ENTRIES, "AgentCore Memory overview");
    expect(results[0].title).toBe("AgentCore Memory overview");
  });

  it("sourceId filter 'all' returns from all sources", () => {
    const results = searchEntries(MOCK_ENTRIES, "gateway", { sourceId: "all" });
    const sources = new Set(results.map(r => r.sourceId));
    expect(sources.size).toBeGreaterThan(1);
  });

  it("handles single-character query terms by filtering them out", () => {
    // Single char terms are excluded (< 2 chars), so only single-char query returns nothing
    const results = searchEntries(MOCK_ENTRIES, "q");
    expect(results).toEqual([]);
  });
});

describe("buildComponentOverview", () => {
  const mockComponent: ComponentSummary = {
    name: "memory",
    sectionTitle: "AgentCore Memory: Add memory to your agent",
    sectionUrl: "https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/memory.html",
    sourceId: "docs",
    subPages: [
      { title: "How it works", description: "AgentCore Memory provides APIs for storing and retrieving memory." },
      { title: "Get started", description: "Install dependencies and implement memory features." },
      { title: "Short-term memory", description: "" },
      { title: "Long-term memory", description: "" },
      { title: "Memory strategies", description: "Add memory strategies to your memory resource." },
    ],
  };

  it("includes section title as heading", () => {
    const overview = buildComponentOverview(mockComponent);
    expect(overview).toContain("## AgentCore Memory: Add memory to your agent");
  });

  it("includes source ID", () => {
    const overview = buildComponentOverview(mockComponent);
    expect(overview).toContain("**Source:** docs");
  });

  it("includes documentation URL", () => {
    const overview = buildComponentOverview(mockComponent);
    expect(overview).toContain("**Documentation:** https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/memory.html");
  });

  it("includes page count", () => {
    const overview = buildComponentOverview(mockComponent);
    expect(overview).toContain("**Pages:** 5");
  });

  it("lists described pages under Key topics", () => {
    const overview = buildComponentOverview(mockComponent);
    expect(overview).toContain("**Key topics:**");
    expect(overview).toContain("**How it works** — AgentCore Memory provides APIs");
    expect(overview).toContain("**Get started** — Install dependencies");
  });

  it("lists undescribed pages under Additional topics when few described", () => {
    const overview = buildComponentOverview(mockComponent);
    expect(overview).toContain("Short-term memory");
    expect(overview).toContain("Long-term memory");
  });

  it("handles component with no described pages", () => {
    const comp: ComponentSummary = {
      name: "boto3",
      sectionTitle: "Boto3 Client",
      sectionUrl: "https://example.com",
      sourceId: "boto3_data_plane",
      subPages: [
        { title: "invoke_harness", description: "" },
        { title: "create_event", description: "" },
      ],
    };
    const overview = buildComponentOverview(comp);
    expect(overview).toContain("invoke_harness");
    expect(overview).toContain("create_event");
  });

  it("truncates long lists with '...and N more'", () => {
    const comp: ComponentSummary = {
      name: "large",
      sectionTitle: "Large Component",
      sectionUrl: "https://example.com",
      sourceId: "docs",
      subPages: Array.from({ length: 20 }, (_, i) => ({
        title: `Topic ${i}`,
        description: `Description for topic ${i}`,
      })),
    };
    const overview = buildComponentOverview(comp);
    expect(overview).toContain("...and 8 more");
  });
});
