/**
 * HTTP fetcher with TTL-based in-memory cache.
 *
 * Responsible for all network I/O in the MCP server:
 *   - fetchRawUrl: Fetches raw content (used for llms.txt, README, boto3 index, FAQ pages)
 *   - fetchDocPage: Fetches HTML doc pages, converts to Markdown, caches with TTL
 *
 * Cache behavior:
 *   - In-memory Map<url, {content, timestamp}>
 *   - TTL configurable via AGENTCORE_CACHE_TTL_MINUTES (default: 60)
 *   - Expired entries re-fetched transparently on next access
 *   - Cache lost on process restart (intentional — guarantees freshness)
 */

import https from "node:https";
import http from "node:http";

interface CacheEntry {
  content: string;
  timestamp: number;
}

const cache = new Map<string, CacheEntry>();
const DEFAULT_TTL_MS = 60 * 60 * 1000;

function getCacheTTL(): number {
  const envTtl = process.env.AGENTCORE_CACHE_TTL_MINUTES;
  if (envTtl) {
    return parseInt(envTtl, 10) * 60 * 1000;
  }
  return DEFAULT_TTL_MS;
}

export function clearCache(): void {
  cache.clear();
}

/**
 * Fetch raw content from a URL. Follows redirects, times out at 15s.
 */
export function fetchRawUrl(url: string): Promise<string> {
  return new Promise((resolve, reject) => {
    const client = url.startsWith("https") ? https : http;
    const req = client.get(url, { headers: { "User-Agent": "AgentCore-Assistant/3.0" } }, (res) => {
      if (res.statusCode && res.statusCode >= 300 && res.statusCode < 400 && res.headers.location) {
        fetchRawUrl(res.headers.location).then(resolve).catch(reject);
        return;
      }
      if (res.statusCode && res.statusCode >= 400) {
        reject(new Error(`HTTP ${res.statusCode} for ${url}`));
        return;
      }
      const chunks: Buffer[] = [];
      res.on("data", (chunk) => chunks.push(chunk));
      res.on("end", () => resolve(Buffer.concat(chunks).toString("utf-8")));
      res.on("error", reject);
    });
    req.on("error", reject);
    req.setTimeout(15000, () => {
      req.destroy();
      reject(new Error(`Timeout fetching ${url}`));
    });
  });
}

/**
 * Convert raw HTML to readable Markdown.
 * Extracts the main content area and strips navigation/scripts.
 */
function htmlToMarkdown(html: string): string {
  let content = html;

  const mainMatch = content.match(/<div id="main-col-body"[^>]*>([\s\S]*?)<\/div>\s*<div/);
  if (mainMatch) {
    content = mainMatch[1];
  } else {
    const articleMatch = content.match(/<main[^>]*>([\s\S]*?)<\/main>/);
    if (articleMatch) content = articleMatch[1];
  }

  content = content.replace(/<script[\s\S]*?<\/script>/gi, "");
  content = content.replace(/<style[\s\S]*?<\/style>/gi, "");
  content = content.replace(/<h1[^>]*>([\s\S]*?)<\/h1>/gi, "\n# $1\n");
  content = content.replace(/<h2[^>]*>([\s\S]*?)<\/h2>/gi, "\n## $1\n");
  content = content.replace(/<h3[^>]*>([\s\S]*?)<\/h3>/gi, "\n### $1\n");
  content = content.replace(/<h4[^>]*>([\s\S]*?)<\/h4>/gi, "\n#### $1\n");
  content = content.replace(/<pre[^>]*><code[^>]*>([\s\S]*?)<\/code><\/pre>/gi, "\n```\n$1\n```\n");
  content = content.replace(/<pre[^>]*>([\s\S]*?)<\/pre>/gi, "\n```\n$1\n```\n");
  content = content.replace(/<code[^>]*>([\s\S]*?)<\/code>/gi, "`$1`");
  content = content.replace(/<strong[^>]*>([\s\S]*?)<\/strong>/gi, "**$1**");
  content = content.replace(/<b[^>]*>([\s\S]*?)<\/b>/gi, "**$1**");
  content = content.replace(/<em[^>]*>([\s\S]*?)<\/em>/gi, "*$1*");
  content = content.replace(/<li[^>]*>([\s\S]*?)<\/li>/gi, "- $1\n");
  content = content.replace(/<a[^>]*href="([^"]*)"[^>]*>([\s\S]*?)<\/a>/gi, "[$2]($1)");
  content = content.replace(/<p[^>]*>([\s\S]*?)<\/p>/gi, "\n$1\n");
  content = content.replace(/<br\s*\/?>/gi, "\n");
  content = content.replace(/<[^>]+>/g, "");
  content = content.replace(/&lt;/g, "<");
  content = content.replace(/&gt;/g, ">");
  content = content.replace(/&amp;/g, "&");
  content = content.replace(/&quot;/g, '"');
  content = content.replace(/&#39;/g, "'");
  content = content.replace(/&nbsp;/g, " ");
  content = content.replace(/\n{3,}/g, "\n\n");
  content = content.trim();

  return content;
}

/**
 * Fetch a documentation page, convert to Markdown, and cache.
 * Returns cached content if within TTL, otherwise re-fetches.
 */
export async function fetchDocPage(url: string): Promise<string> {
  const ttl = getCacheTTL();

  const cached = cache.get(url);
  if (cached && (Date.now() - cached.timestamp) < ttl) {
    return cached.content;
  }

  const html = await fetchRawUrl(url);
  const markdown = htmlToMarkdown(html);

  cache.set(url, { content: markdown, timestamp: Date.now() });

  return markdown;
}
