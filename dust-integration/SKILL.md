---
name: dust-integration
description: Integrate Dust capabilities across API, SDK, and MCP workflows. Use when tasks involve connecting to Dust services, configuring the Dust MCP server, building Dust-backed features, troubleshooting Dust integrations, or translating product requirements into Dust API/SDK implementation steps.
---

# Dust Integration

Use this skill to implement or troubleshoot Dust API, SDK, and MCP integrations.

## Use the provided MCP server config

Use this MCP configuration exactly unless the user requests a different server:

```json
{
  "mcpServers": {
    "dust-tt": {
      "url": "https://docs.dust.tt/mcp"
    }
  }
}
```

## Core workflow

1. Confirm the target integration surface: `API`, `SDK`, `MCP`, or a combination.
2. Capture constraints: runtime, language, auth model, and deployment target.
3. Apply the MCP configuration when MCP tools are required.
4. Implement the smallest end-to-end path first, then expand features.
5. Validate behavior with a real request/response loop when credentials and environment allow.
6. Document any environment prerequisites and fallback behavior.

## API and SDK implementation checklist

- Verify required secrets and environment variables are present before coding.
- Keep auth and transport configuration isolated from business logic.
- Add explicit error handling for network failures, auth failures, and malformed responses.
- Normalize Dust responses into typed/internal structures before downstream usage.
- Add a minimal smoke test or runnable example for the integration path.

## MCP usage guidance

- Register the `dust-tt` server in the active MCP config.
- Prefer MCP for discovery, docs lookup, and tool-driven workflows.
- If MCP is unavailable, fall back to direct API/SDK integration and note that fallback.

## Troubleshooting order

1. Configuration mismatch (wrong URL, bad env, wrong workspace context).
2. Authentication issues (missing/invalid secrets).
3. Network reachability and timeout handling.
4. Payload shape mismatches between caller and Dust endpoint/tool.
5. Version or capability mismatch between intended feature and available Dust surface.

## Output expectations

When implementing Dust integration tasks, always provide:

- Exact files changed.
- Required env vars/secrets.
- Verification steps run (or blockers if execution is not possible).
- Any assumptions that might affect production behavior.
