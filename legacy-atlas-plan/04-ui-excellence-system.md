# Legacy Atlas UI Excellence System

## 1) Design Intent

The UI should feel like a precision instrument, not a dashboard template.

Visual direction:

- "Operational Renaissance": structured, elegant, and information-dense without clutter.
- Blend archival map metaphors with modern engineering control panels.

## 2) Experience Goals

1. Comprehension in under 30 seconds.
2. Trust through evidence visibility.
3. Delight through purposeful motion and visual hierarchy.
4. Speed under stress during live demo.

## 3) Information Architecture

Primary screens:

1. Repository Mission Control
2. Process Atlas (interactive workflow graph)
3. Data Lineage Navigator
4. Risk Observatory
5. Copilot and Evidence Console

Screen choreography:

- Landing opens on Mission Control summary cards.
- Main CTA enters Process Atlas.
- Node click opens right evidence drawer with code references and risk chips.
- Copilot can pin insights directly onto graph nodes.

## 4) Visual Language

Typography:

- Display: Space Grotesk (headlines)
- Body: IBM Plex Sans (readability)
- Code and metrics: JetBrains Mono

Color system (no purple default):

- `--bg-deep`: #07111A
- `--bg-surface`: #0F1E2B
- `--ink-high`: #EAF2F8
- `--ink-mid`: #A8BCCF
- `--accent-cyan`: #37D5D6
- `--accent-amber`: #FFC247
- `--accent-coral`: #FF6F61
- `--risk-low`: #2FBF71
- `--risk-mid`: #FFB020
- `--risk-high`: #FF5C5C

Shape and spacing:

- Rounded corners: 14px primary cards, 10px secondary.
- Grid: 12-column desktop, 4-column mobile.
- Base spacing unit: 8px.

## 5) Motion Principles

Motion must encode meaning, not decoration.

1. Graph reveal:
   Stagger node appearance by dependency depth.
2. Evidence drawer:
   220ms slide and fade to preserve context.
3. Risk overlays:
   Smooth heat interpolation (250ms) when filters change.
4. Copilot citations:
   Pulse highlight to corresponding graph node on hover.

## 6) Signature Interaction Patterns

1. Trace Lens:
   Hold a key to temporarily isolate all inbound and outbound paths from selected node.
2. Risk Fog:
   Background dims while high-risk nodes glow with severity halo.
3. Data Pulse:
   Animate lineage edges to show record flow direction.
4. Time Diff Slider:
   Compare two analysis runs with morphing node clusters.

## 7) Content and Copy Rules

Tone:

- Expert and concise.
- No generic AI language.

Rules:

1. Every insight must have an "Evidence" affordance.
2. Risk labels must include cause and impact.
3. Copilot answers must return citations by default.

## 8) Performance Budgets

Hard budgets:

1. First meaningful paint: < 1.8s (desktop demo environment).
2. Graph interaction latency: < 120ms for neighborhood expansions.
3. Copilot first token latency: < 2.5s with cached context.

Techniques:

1. Virtualized side panels.
2. Graph level-of-detail rendering.
3. Response streaming for copilot.
4. Cached query results for common drill paths.

## 9) Accessibility and Resilience

1. WCAG AA contrast compliance.
2. Keyboard shortcuts for graph navigation and focus changes.
3. Reduced-motion mode fallback.
4. Empty and error states with clear recovery actions.

## 10) Lovable Execution Pattern

1. Use Plan mode to define screen architecture, style tokens, and interaction contracts.
2. Generate baseline UI.
3. Apply manual refinements for signature interactions and motion.
4. Run browser testing on:
   - Graph drill-down
   - Risk filtering
   - Copilot citation jumps

## 11) UI Review Checklist (Before Demo)

1. Can a new viewer identify top risk module within 15 seconds?
2. Can one click move from risk to exact code evidence?
3. Is motion smooth and informative on laptop hardware?
4. Are typography and spacing consistent across all pages?

