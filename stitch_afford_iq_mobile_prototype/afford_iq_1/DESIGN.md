---
name: Afford IQ
colors:
  surface: '#faf8ff'
  surface-dim: '#d2d9f4'
  surface-bright: '#faf8ff'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f2f3ff'
  surface-container: '#eaedff'
  surface-container-high: '#e2e7ff'
  surface-container-highest: '#dae2fd'
  on-surface: '#131b2e'
  on-surface-variant: '#464555'
  inverse-surface: '#283044'
  inverse-on-surface: '#eef0ff'
  outline: '#777587'
  outline-variant: '#c7c4d8'
  surface-tint: '#4d44e3'
  primary: '#3525cd'
  on-primary: '#ffffff'
  primary-container: '#4f46e5'
  on-primary-container: '#dad7ff'
  inverse-primary: '#c3c0ff'
  secondary: '#006c49'
  on-secondary: '#ffffff'
  secondary-container: '#6cf8bb'
  on-secondary-container: '#00714d'
  tertiary: '#684000'
  on-tertiary: '#ffffff'
  tertiary-container: '#885500'
  on-tertiary-container: '#ffd4a4'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#e2dfff'
  primary-fixed-dim: '#c3c0ff'
  on-primary-fixed: '#0f0069'
  on-primary-fixed-variant: '#3323cc'
  secondary-fixed: '#6ffbbe'
  secondary-fixed-dim: '#4edea3'
  on-secondary-fixed: '#002113'
  on-secondary-fixed-variant: '#005236'
  tertiary-fixed: '#ffddb8'
  tertiary-fixed-dim: '#ffb95f'
  on-tertiary-fixed: '#2a1700'
  on-tertiary-fixed-variant: '#653e00'
  background: '#faf8ff'
  on-background: '#131b2e'
  surface-variant: '#dae2fd'
typography:
  display-hero:
    fontFamily: Plus Jakarta Sans
    fontSize: 36px
    fontWeight: '700'
    lineHeight: 44px
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Plus Jakarta Sans
    fontSize: 28px
    fontWeight: '700'
    lineHeight: 36px
    letterSpacing: -0.02em
  headline-md:
    fontFamily: Plus Jakarta Sans
    fontSize: 22px
    fontWeight: '600'
    lineHeight: 28px
    letterSpacing: -0.01em
  headline-sm:
    fontFamily: Plus Jakarta Sans
    fontSize: 18px
    fontWeight: '600'
    lineHeight: 24px
  body-lg:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  body-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  body-sm:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '400'
    lineHeight: 16px
  label-lg:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '600'
    lineHeight: 20px
    letterSpacing: 0.01em
  label-md:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '500'
    lineHeight: 16px
    letterSpacing: 0.02em
  label-sm:
    fontFamily: Inter
    fontSize: 10px
    fontWeight: '600'
    lineHeight: 14px
    letterSpacing: 0.04em
  currency-display:
    fontFamily: Plus Jakarta Sans
    fontSize: 32px
    fontWeight: '700'
    lineHeight: 40px
    letterSpacing: -0.03em
  currency-md:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '600'
    lineHeight: 24px
    letterSpacing: -0.01em
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  gutter: 1rem
  margin: 1rem
  space-xs: 0.25rem
  space-sm: 0.5rem
  space-md: 1rem
  space-lg: 1.5rem
  space-xl: 2rem
---

## Brand & Style
This design system represents a calm, privacy-first personal financial copilot designed specifically for Indian college students and early-career earners navigating discretionary spending, rent, UPI outlays, and initial credit decisions.

The design movement merges **Modern Fintech Craft** with **Calm Intelligence**. Rather than anxiety-inducing warning banners or gamified credit scores, the interface operates like an analytical personal ledger: balanced, confident, and discreet. Visual weight relies on crisp surfaces, deep slate contrast, tactile container grouping, and quiet on-device AI markers that signal security rather than cloud surveillance.

### Emotional Response
- **Reassurance & Discretion:** Explicit cues that financial telemetry remains strictly on-device.
- **Clarity over Impulse:** Clean purchase-verdict visual language that prevents buyer remorse without judgment.
- **Tactile Trust:** Deliberate hierarchy, precise numeric data formatting (Indian numbering format and ₹ currency notation), and ergonomic tap targets tailored for single-handed mobile usage.

## Colors
The palette balances rational slate neutrals with decisive semantic indicators for instant decision-making:

- **Primary Intelligence Accent (`#4F46E5` / `#6366F1`):** Represents on-device intelligence, computational privacy, and active synthesis. Used for active navigation tabs, smart evaluation pills, and machine-inferred suggestions.
- **Verdict Safe / Afford (`#10B981`):** Used strictly for clear affordability outcomes ("Safe to buy", "Within monthly buffer", zero-debt risk).
- **Verdict Caution / Defer (`#F59E0B`):** Warm ochre indicating liquid cash stress, upcoming rent/EMI obligations, or a recommendation to pause.
- **Verdict Risk / Restrict (`#EF4444`):** Soft coral-red reserving judgment for severe balance depletion, impending overdraft, or high-risk BNPL commitments.
- **Surface & Neutral Hierarchy:** Rooted in Slate (`#0F172A`). Light mode deploys an ultra-soft cool off-white base (`#F8FAFC`) layered with pure white cards (`#FFFFFF`) and hairline border definitions (`#E2E8F0`). Dark mode reverses this with `#090D16` canvas, `#131B2E` cards, and `#1E293B` dividers.

## Typography
The system utilizes **Plus Jakarta Sans** for headlines and high-impact decision metrics, conveying modern clarity and approachable geometric structure. **Inter** is assigned to analytical body copy, metadata labels, lists, and tabular data due to its neutral grotesque proportions and high legibility at micro-sizes.

### Formatting & Locality Rules
- **Indian Rupee (₹) Presentation:** Always render ₹ with an explicit tabular figure font feature (`font-feature-settings: "tnum"`). Use the Indian numbering system for values equal to or above one lakh (e.g., `₹1,24,500` instead of `₹124,500`).
- **Privacy Badging:** Micro-labels like `STORED LOCALLY` or `AUTO-DETECTED SMS` must be rendered in `label-sm`, all-caps, with a `+0.04em` letter spacing for crisp rendering on high-density OLED mobile displays.

## Layout & Spacing
This design system is built phone-first with a vertical stack rhythm tuned for one-handed reach on viewports between 360px and 430px wide.

### Layout Philosophy
- **Fluid Vertical Viewport:** Content is bound by a maximum width of 480px centered on larger displays, maintaining an authentic mobile shell.
- **Margins & Safe Zones:** Canvas padding uses `margin` (`1rem` / 16px) on mobile viewports, scaling to `1.5rem` on larger tablets. Bottom margins automatically accommodate floating action buttons and safe-area inset bars (`env(safe-area-inset-bottom) + 64px`).
- **Vertical Rhythm:**
  - Compact grouping (icon to text): `space-xs` (4px) to `space-sm` (8px).
  - Internal card padding: `space-md` (16px) to `space-lg` (24px).
  - Inter-card structural stacking: `space-md` (16px).
  - Decision block separation: `space-xl` (32px).

## Elevation & Depth
Depth is created through tonal layering and low-contrast surface outlines rather than aggressive drop shadows, preserving an uncluttered and focused environment.

### Surface Tiers
1. **Base Layer (L0):** `#F8FAFC` (Canvas).
2. **Surface Layer (L1):** `#FFFFFF`, bound by a 1px structural stroke (`#E2E8F0` or `#F1F5F9`).
3. **Elevated Card / Modal (L2):** `#FFFFFF` paired with an ambient diffuse shadow (`0 10px 25px -5px rgba(15, 23, 42, 0.04), 0 8px 10px -6px rgba(15, 23, 42, 0.02)`) and a 1px border.
4. **Overlay / Bottom Sheet (L3):** `#FFFFFF` over a 40% alpha slate backdrop blur (`rgba(15, 23, 42, 0.40)` with `backdrop-filter: blur(8px)`).

### Privacy & Intelligence Depth
Cards driven by local intelligence feature a gentle inner ring: a subtle 1px border tinted in `#6366F1` at 20% opacity, paired with an ultra-light tint background (`rgba(99, 102, 241, 0.03)`), distinguishing verified local processing from regular static containers.

## Shapes
The system applies a consistent rounded language across touch targets:

- **Primary Cards & Modals (`rounded-2xl` / 16px–24px):** Standard containers, verdict summaries, and merchant insight modules use a smooth 16px (`rounded-lg` token) or 24px (`rounded-xl` token) radius.
- **Buttons & Interactive Touch Points (`rounded-xl` / 12px–14px):** Generously curved edges for effortless tap targeting.
- **Pills & Status Indicators:** Full pill (`9999px` border-radius) for all decision tags, security markers, and category chips.

## Components

### Buttons
- **Primary CTA:** Deep slate or Indigo solid (`#0F172A` or `#4F46E5`), text `#FFFFFF`, height 52px, border-radius 14px, typography `label-lg`. Haptic touch feedback state scales down to `0.98`.
- **Secondary / Ghost CTA:** Clean white fill with a 1px border in `#E2E8F0`, slate text (`#1E293B`).
- **Verdict Action Buttons:** When triggering affordability evaluations, display contextual safe green (`#10B981`) or cautionary ochre tones with solid contrast.

### Badges & Intelligence Pills
- **Badge Types:**
  - *Stored Locally:* Slate-50 background (`#F1F5F9`), slate-600 label (`#475569`), leading closed-lock glyph.
  - *Auto-Detected:* Indigo-50 background (`#EEF2FF`), indigo-600 label (`#4F46E5`), leading sparkle glyph.
  - *Afford Verdict Pills:*
    - **Safe / Can Afford:** Emerald-50 background, Emerald-700 label (`#047857`), solid green dot.
    - **Wait / Consider:** Amber-50 background, Amber-800 label (`#92400E`), solid amber dot.
    - **High Risk:** Red-50 background, Red-700 label (`#B91C1C`), solid red dot.

### Affordability Decision Card
- The centerpiece component. White surface, 16px padding, rounded-2xl with a 1px border.
- Top row: Context metadata (`₹4,999 on Flipkart`, `Electronics`) paired with the `Auto-Detected` pill.
- Center: Verdict headline (`Safe to spend`, `Will reduce month-end buffer to ₹1,800`) set in `headline-md`.
- Bottom: Mini visual runway bar showing projected balance before and after purchase.

### Input Fields & Amount Entry
- Large-format amount entry featuring a static `₹` symbol in Slate-400 and user input in `display-hero`.
- Standard inputs: 48px height, 12px corner radius, `#FFFFFF` surface, border `#CBD5E1`. Focused state: 2px border `#4F46E5` with zero offset shadow.

### Bottom Navigation Bar
- Docked to bottom, height 64px + safe area padding.
- Four core destinations: *Check*, *Activity*, *Budgets*, *Vault (Settings/Privacy)*.
- Active state indicated with indigo tint icon + small 4px indigo dot below; inactive tabs in Slate-400. Backdrop features high-transmission blur (`rgba(255, 255, 255, 0.85)`).