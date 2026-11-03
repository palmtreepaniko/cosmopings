---
system: Impeccable Design Standards
project: Cosmopings Dispatcher & Portfolio
version: 2.0.0
anti_slop_rules:
  - no-purple-gradients
  - no-glassmorphism-blur
  - no-gradient-text
  - no-dark-glows
  - no-side-tab-cards
  - no-repetitive-icon-grids
  - no-gratuitous-canvas-starfields
tokens:
  color:
    canvas_bg: "#090a0d"
    surface_1: "#101318"
    surface_2: "#161a22"
    border_subtle: "#1f242e"
    border_focus: "#374151"
    text_primary: "#f3f4f6"
    text_secondary: "#9ca3af"
    text_tertiary: "#6b7280"
    accent_live: "#e11d48"
    accent_melody: "#f59e0b"
    accent_status: "#10b981"
  typography:
    family_display: "'Bricolage Grotesque', -apple-system, sans-serif"
    family_sans: "'Plus Jakarta Sans', system-ui, -apple-system, sans-serif"
    family_mono: "'JetBrains Mono', 'IBM Plex Mono', monospace"
---

# Cosmopings Design System (`DESIGN.md`)

Designed according to **Impeccable** (`impeccable.style`) guidelines to eliminate AI-generated visual tropes ("AI Slop") in favor of an authentic, functional broadcast engineering console.

## 1. Core Visual Intent
Cosmopings is not a generic SaaS landing page. It is a specialized, real-time dispatch utility that monitors YouTube for creator **Mira** (`@possiblymira`) and routes live notifications to Discord channels.
The interface must feel like an **authoritative, high-precision broadcast monitor**:
- Information-dense, scannable data layouts.
- Functional color coding (Broadcast Scarlet `#e11d48`, Melody Amber `#f59e0b`, Terminal Green `#10b981`).
- Crisp, high-contrast typography with deliberate scale.
- Zero decorative filler (no floating particles, no violet gradient washes, no unearned card nesting).

## 2. Typography Rules
- **Display Headings (`h1`, `h2`)**: Set in `Bricolage Grotesque`. Tight tracking (`-0.03em`), solid crisp off-white (`#f3f4f6`). Headings communicate purpose directly without poetic fluff.
- **Data & Telemetry (`code`, `.mono`, tables)**: Set in `JetBrains Mono`. Used for video IDs, timestamps, cycle counters, latency figures, and Discord channel mappings.
- **Body & Explanatory Prose**: Set in `Plus Jakarta Sans`. Calibrated line-height (`1.65`) for effortless reading rhythm.

## 3. Structural Rules & Anti-Slop Safeguards
- **No Side-Tab Borders**: Cards use uniform, crisp 1px borders (`#1f242e`) without thick left-accent bars.
- **No Background Blurs**: Pure, high-performance solid surfaces (`#101318`, `#161a22`).
- **No Gradient Text**: Solid contrast color for maximum accessibility and readability.
- **Direct Utility**: Includes a real interactive health-check inspector and live dispatch table pulling directly from `posted.json`.
