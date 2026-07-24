import { describe, it, expect, beforeEach, afterEach } from "vitest";
import { getEnabledSources, getAllSourceIds } from "../src/sources.js";

describe("sources", () => {
  const originalEnv = process.env.AGENTCORE_SOURCES;

  afterEach(() => {
    if (originalEnv === undefined) {
      delete process.env.AGENTCORE_SOURCES;
    } else {
      process.env.AGENTCORE_SOURCES = originalEnv;
    }
  });

  describe("getAllSourceIds", () => {
    it("returns all source IDs", () => {
      const ids = getAllSourceIds();
      expect(ids).toContain("docs");
      expect(ids).toContain("api_data_plane");
      expect(ids).toContain("api_control_plane");
      expect(ids).toContain("boto3_data_plane");
      expect(ids).toContain("boto3_control_plane");
      expect(ids).toContain("sdk");
      expect(ids).toContain("cloudformation");
      expect(ids).toContain("cdk_typescript");
      expect(ids).toContain("cdk_python");
      expect(ids).toContain("cdk_java");
      expect(ids).toContain("cdk_dotnet");
      expect(ids).toContain("cdk_go");
      expect(ids).toContain("faq");
      expect(ids.length).toBe(13);
    });
  });

  describe("getEnabledSources", () => {
    it("returns all sources when env var is not set", () => {
      delete process.env.AGENTCORE_SOURCES;
      const sources = getEnabledSources();
      expect(sources.length).toBe(13);
    });

    it("returns all sources when env var is 'all'", () => {
      process.env.AGENTCORE_SOURCES = "all";
      const sources = getEnabledSources();
      expect(sources.length).toBe(13);
    });

    it("filters to specified sources in inclusion mode", () => {
      process.env.AGENTCORE_SOURCES = "docs,faq";
      const sources = getEnabledSources();
      expect(sources.length).toBe(2);
      expect(sources.map(s => s.id)).toEqual(["docs", "faq"]);
    });

    it("excludes specified sources in exclusion mode", () => {
      process.env.AGENTCORE_SOURCES = "-boto3_data_plane,-boto3_control_plane,-sdk";
      const sources = getEnabledSources();
      expect(sources.length).toBe(10);
      const ids = sources.map(s => s.id);
      expect(ids).not.toContain("boto3_data_plane");
      expect(ids).not.toContain("boto3_control_plane");
      expect(ids).not.toContain("sdk");
      expect(ids).toContain("docs");
      expect(ids).toContain("faq");
      expect(ids).toContain("cloudformation");
      expect(ids).toContain("cdk_typescript");
    });

    it("handles whitespace in env var", () => {
      process.env.AGENTCORE_SOURCES = " docs , faq ";
      const sources = getEnabledSources();
      expect(sources.length).toBe(2);
    });

    it("is case-insensitive", () => {
      process.env.AGENTCORE_SOURCES = "DOCS,FAQ";
      const sources = getEnabledSources();
      expect(sources.length).toBe(2);
    });

    it("each source has required fields", () => {
      const sources = getEnabledSources();
      for (const source of sources) {
        expect(source.id).toBeTruthy();
        expect(source.name).toBeTruthy();
        expect(source.description).toBeTruthy();
        expect(source.type).toBeTruthy();
        expect(source.indexUrl).toMatch(/^https?:\/\//);
        expect(source.baseUrl).toMatch(/^https?:\/\//);
      }
    });
  });
});
