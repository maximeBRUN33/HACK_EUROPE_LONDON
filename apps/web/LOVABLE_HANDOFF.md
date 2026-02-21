# Lovable Handoff (Start Now)

Lovable should be used now, in parallel with backend implementation.

## Why now

- Backend APIs exist for the full vertical slice.
- UI routes/components exist and can be imported into Lovable for rapid refinement.
- This is the best time to harden visual quality and interaction behavior before adding more backend complexity.

## Immediate Lovable workflow

1. Use Plan mode to lock route and component contracts:
   - `/repos`
   - `/atlas/:runId`
   - `/lineage/:runId`
   - `/risk/:runId`
2. Import the current `apps/web` codebase.
3. Request Lovable to refine:
   - graph canvas interaction polish
   - evidence drawer behavior
   - mobile responsiveness
   - typography and spacing consistency
4. Run Lovable Browser Testing on these journeys:
   - register repo -> run scan -> open graph
   - select high-risk node -> inspect details
   - ask copilot -> inspect citations

## Prompt to use in Lovable

```text
Refine this React app into a premium graph-first engineering intelligence UI.
Keep existing API contracts and routes. Improve visual hierarchy, graph readability,
node interaction clarity, and responsive behavior. Preserve dark theme and cyan/amber/coral accents.
Add polished transitions for graph node selection and panel updates.
Do not break existing fetch contracts in src/lib/api.ts.
```

## Non-negotiables

- Keep latency low and avoid heavy client libraries unless needed.
- Do not remove evidence/citation visibility.
- Keep keyboard-accessible interactions.
