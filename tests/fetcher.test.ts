import { describe, it, expect, beforeEach } from "vitest";
import { fetchRawUrl, fetchDocPage, clearCache } from "../src/fetcher.js";

describe("fetcher", () => {
  beforeEach(() => {
    clearCache();
  });

  describe("fetchRawUrl", () => {
    it("fetches a real URL and returns content", async () => {
      const content = await fetchRawUrl("https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/llms.txt");
      expect(content.length).toBeGreaterThan(100);
      expect(content).toContain("AgentCore");
    });

    it("follows redirects", async () => {
      // AWS docs often redirect http → https
      const content = await fetchRawUrl("https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/llms.txt");
      expect(content).toBeTruthy();
    });

    it("throws on invalid hostname", async () => {
      await expect(
        fetchRawUrl("https://this-host-does-not-exist-xyz99.invalid/page")
      ).rejects.toThrow();
    });

    it("throws on invalid hostname", async () => {
      await expect(
        fetchRawUrl("https://this-domain-does-not-exist-xyz123.com/page")
      ).rejects.toThrow();
    });
  });

  describe("fetchDocPage", () => {
    it("fetches and converts HTML to markdown", async () => {
      const content = await fetchDocPage("https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/harness.html");
      expect(content.length).toBeGreaterThan(100);
      // Should not contain raw HTML tags
      expect(content).not.toMatch(/<script/i);
      expect(content).not.toMatch(/<style/i);
    });

    it("caches results on second call", async () => {
      const url = "https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/memory.html";
      const start1 = Date.now();
      const content1 = await fetchDocPage(url);
      const duration1 = Date.now() - start1;

      const start2 = Date.now();
      const content2 = await fetchDocPage(url);
      const duration2 = Date.now() - start2;

      expect(content1).toBe(content2);
      // Cached call should be near-instant (< 5ms)
      expect(duration2).toBeLessThan(5);
    });

    it("clearCache causes re-fetch", async () => {
      const url = "https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/harness.html";
      await fetchDocPage(url);

      // Verify cached version is instant
      const cachedStart = Date.now();
      await fetchDocPage(url);
      const cachedDuration = Date.now() - cachedStart;
      expect(cachedDuration).toBeLessThan(5);

      // Clear and verify it fetches again
      clearCache();
      const start = Date.now();
      await fetchDocPage(url);
      const duration = Date.now() - start;
      // Re-fetch should be slower than cache hit
      expect(duration).toBeGreaterThan(cachedDuration);
    });
  });
});
