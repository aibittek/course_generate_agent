---
name: "clean-tech-ui"
description: "Generates light-theme web pages with a clean tech aesthetic: white cards, soft shadows, blue-cyan-teal accent palette, card-based layouts. Invoke when user asks for science/tech tutorials, course pages, or any educational web content with a bright, approachable, non-repressive visual style."
---

# Clean Tech UI

A design system for generating light-theme, science-technology style web pages. Optimized for educational/tutorial content (course catalogs, experiment guides, knowledge bases) where readability and approachability matter more than dramatic visuals.

## Design DNA

**Keywords**: bright, clean, structured, approachable, trustworthy, tech-forward
**Anti-patterns**: dark backgrounds, heavy neon glow, dense gradients, purple-on-dark, brutalist raw

## Color System

```css
:root {
  /* Backgrounds */
  --bg-base: #f8fafc;        /* page background, soft off-white */
  --bg-card: #ffffff;         /* card surfaces */
  --bg-soft: #f1f5f9;         /* subtle fill, code blocks, tags */
  --bg-tint: #eef4ff;         /* light blue tint for code badges, eyebrows */

  /* Borders */
  --border: #e2e8f0;          /* default card/border */
  --border-hover: #94a3b8;   /* hover state */

  /* Accent palette (blue → cyan → teal = tech trust) */
  --accent-blue: #2563eb;     /* primary actions, links, active states */
  --accent-cyan: #0891b2;     /* secondary highlight, icon backgrounds */
  --accent-teal: #0d9488;     /* success, alternative accent */
  --accent-indigo: #4f46e5;   /* deep accent for variety */
  --accent-amber: #d97706;    /* warning, difficulty stars */
  --accent-rose: #e11d48;     /* danger, occupied/obstacle indicators */
  --accent-violet: #7c3aed;   /* tertiary, AI/ML tag color */

  /* Text */
  --text-primary: #0f172a;    /* headings, important text */
  --text-body: #334155;       /* body text */
  --text-secondary: #64748b;  /* descriptions, labels */
  --text-muted: #94a3b8;      /* meta, footnotes, placeholder */
}
```

### Color Usage Rules

| Element | Color | Notes |
|---------|-------|-------|
| Page background | `--bg-base` | Soft off-white with subtle radial gradients (blue/teal at 4-5% opacity) |
| Cards | `--bg-card` | Pure white, 1px `--border`, soft shadow on hover |
| Primary CTA / links | `--accent-blue` | Never use for body text |
| Section icons | `--accent-cyan` / `--accent-teal` | Alternate for visual variety |
| Difficulty / warning | `--accent-amber` | Use sparingly |
| Danger / occupied | `--accent-rose` | Maps, alerts, occupied grid cells |
| AI / ML concepts | `--accent-violet` | For LLM/voice/model content |

## Typography

```css
--font-sans: 'PingFang SC', 'Noto Sans SC', 'Microsoft YaHei', 'Segoe UI', system-ui, sans-serif;
--font-mono: 'Cascadia Code', 'JetBrains Mono', 'Fira Code', Consolas, monospace;
```

**Hierarchy**:
- Hero h1: 44px / 800 weight / gradient text (blue→cyan→teal)
- Section h2: 22px / 700
- Card h3: 18px / 700
- Body: 14-17px / 400 / `--text-body`
- Code/meta: 12-13px / monospace / `--text-muted`

## Component Patterns

### Course/Content Card
- White bg, 1px border, 14px radius
- 3px gradient top bar (blue→cyan), `scaleX(0)` → reveals on hover
- Lift on hover: `translateY(-4px)` + `box-shadow: 0 8px 24px rgba(37,99,235,0.10)`
- Clickable → expandable (experiment list slides down via `max-height` transition)

### Tag Pill
- 12px text, 3px×10px padding, 100px radius
- `--bg-soft` fill, `--border` border, `--text-secondary` color

### Stats Bar
- Horizontal flex row, white bg, bordered
- Each stat: 36px bold number in `--accent-blue` + 14px label

### Tech Stack Pills
- Centered flex-wrap, 8px gap
- 6px color dot + 13px text
- Hover: border→`--accent-blue`, text→`--accent-blue`

### Code Badge
- `--font-mono`, 12px, `--accent-blue` text on `--bg-tint` bg, 6px radius

### Info Tip
- Left 3px border accent (blue=info, amber=warning)
- `5%` opacity tinted background, 16px padding

### Flow Chart
- Horizontal step boxes connected by arrows
- Each step: `--bg-soft` bg, border, hover→glow

## Shadow System

```css
--shadow-sm: 0 1px 3px rgba(0,0,0,0.04), 0 1px 2px rgba(0,0,0,0.03);
--shadow-md: 0 4px 12px rgba(0,0,0,0.05), 0 2px 4px rgba(0,0,0,0.03);
--shadow-lg: 0 12px 32px rgba(0,0,0,0.06), 0 4px 8px rgba(0,0,0,0.03);
--shadow-glow: 0 8px 24px rgba(37,99,235,0.10);  /* hover glow on cards */
```

## Motion

- **Transition**: `0.28s cubic-bezier(0.4, 0, 0.2, 1)` for all interactive states
- **Card hover**: translateY(-4px) + shadow-glow + top bar scaleX(1)
- **Scroll reveal**: IntersectionObserver → fade-in (opacity 0→1, translateY 16px→0, 0.5s)
- **Pulse**: keyframe for logo dot (opacity 1→0.35→1, 2.5s infinite)

## Page Background Texture

```css
background-image:
  radial-gradient(ellipse 60% 40% at 50% -5%, rgba(37,99,235,0.05), transparent),
  radial-gradient(ellipse 50% 35% at 100% 5%, rgba(13,148,136,0.04), transparent);
```

## Layout Structure

```
[Sticky Topbar — white blur, 60px]
[Hero — centered, max 820px]
[Stats Bar — horizontal row]
[Category Section — header + course grid]
[Tech Stack — centered pills]
[Footer — centered, border-top]
```

**Card grid**: `repeat(auto-fill, minmax(340px, 1fr))` with 20px gap
**Max content width**: 1200px, 40px padding
**Mobile**: single column, reduced padding, stacked stats

## When to Use This Skill

- Science/tech educational content (course catalogs, experiment guides)
- Tutorial pages needing principle animations + structured layouts
- Any page where the user said "简约科技风" / "clean tech" / "bright and approachable"
- When the user explicitly wants light background (not dark/repressive)
- Course/learning platforms with card-based content browsing

## When NOT to Use

- Dark-themed dashboards or monitoring tools
- Marketing landing pages with dramatic hero animations
- Mobile-first apps with bottom navigation
- When user explicitly requests dark mode or high-contrast dark theme
