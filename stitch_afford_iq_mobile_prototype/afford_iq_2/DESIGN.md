---
name: Afford IQ
colors:
  surface: '#0f131d'
  surface-dim: '#0f131d'
  surface-bright: '#353944'
  surface-container-lowest: '#0a0e18'
  surface-container-low: '#171b26'
  surface-container: '#1c1f2a'
  surface-container-high: '#262a35'
  surface-container-highest: '#313540'
  on-surface: '#dfe2f1'
  on-surface-variant: '#bcc9cd'
  inverse-surface: '#dfe2f1'
  inverse-on-surface: '#2c303b'
  outline: '#869397'
  outline-variant: '#3d494c'
  surface-tint: '#4cd7f6'
  primary: '#4cd7f6'
  on-primary: '#003640'
  primary-container: '#06b6d4'
  on-primary-container: '#00424f'
  inverse-primary: '#00687a'
  secondary: '#c0c1ff'
  on-secondary: '#1000a9'
  secondary-container: '#3131c0'
  on-secondary-container: '#b0b2ff'
  tertiary: '#4edea3'
  on-tertiary: '#003824'
  tertiary-container: '#1bbd85'
  on-tertiary-container: '#00452e'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#acedff'
  primary-fixed-dim: '#4cd7f6'
  on-primary-fixed: '#001f26'
  on-primary-fixed-variant: '#004e5c'
  secondary-fixed: '#e1e0ff'
  secondary-fixed-dim: '#c0c1ff'
  on-secondary-fixed: '#07006c'
  on-secondary-fixed-variant: '#2f2ebe'
  tertiary-fixed: '#6ffbbe'
  tertiary-fixed-dim: '#4edea3'
  on-tertiary-fixed: '#002113'
  on-tertiary-fixed-variant: '#005236'
  background: '#0f131d'
  on-background: '#dfe2f1'
  surface-variant: '#313540'
typography:
  display-xl:
    fontFamily: Plus Jakarta Sans
    fontSize: 56px
    fontWeight: '700'
    lineHeight: 64px
    letterSpacing: -0.03em
  display-xl-mobile:
    fontFamily: Plus Jakarta Sans
    fontSize: 38px
    fontWeight: '700'
    lineHeight: 46px
    letterSpacing: -0.025em
  headline-lg:
    fontFamily: Plus Jakarta Sans
    fontSize: 36px
    fontWeight: '700'
    lineHeight: 44px
    letterSpacing: -0.025em
  headline-lg-mobile:
    fontFamily: Plus Jakarta Sans
    fontSize: 28px
    fontWeight: '700'
    lineHeight: 36px
    letterSpacing: -0.02em
  headline-md:
    fontFamily: Plus Jakarta Sans
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
    letterSpacing: -0.02em
  headline-sm:
    fontFamily: Plus Jakarta Sans
    fontSize: 20px
    fontWeight: '600'
    lineHeight: 28px
    letterSpacing: -0.015em
  title-md:
    fontFamily: Plus Jakarta Sans
    fontSize: 16px
    fontWeight: '600'
    lineHeight: 24px
    letterSpacing: -0.01em
  body-lg:
    fontFamily: Plus Jakarta Sans
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 26px
    letterSpacing: 0em
  body-md:
    fontFamily: Plus Jakarta Sans
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 22px
    letterSpacing: 0em
  label-md:
    fontFamily: Plus Jakarta Sans
    fontSize: 12px
    fontWeight: '600'
    lineHeight: 16px
    letterSpacing: 0.04em
  label-sm:
    fontFamily: Plus Jakarta Sans
    fontSize: 11px
    fontWeight: '500'
    lineHeight: 14px
    letterSpacing: 0.05em
  mono-metric:
    fontFamily: Plus Jakarta Sans
    fontSize: 15px
    fontWeight: '600'
    lineHeight: 20px
    letterSpacing: -0.01em
rounded:
  sm: 0.5rem
  DEFAULT: 1rem
  md: 1.5rem
  lg: 2rem
  xl: 3rem
  full: 9999px
spacing:
  gutter: 1.5rem
  gutter-mobile: 1rem
  margin: 2.5rem
  margin-mobile: 1rem
  space-xs: 0.375rem
  space-sm: 0.75rem
  space-md: 1.25rem
  space-lg: 2rem
  space-xl: 3rem
---

## Brand & Style

This design system expresses high-conviction financial intelligence through a synthesis of **tactile glassmorphism** and **soft-edge skeuomorphic elevation**. It balances modern fintech precision with deep, sensory craftsmanship.

### Target Audience & Personality
- **Audience**: High-earning digital natives, private investors, and wealth builders who expect institutional-grade clarity delivered with consumer-grade polish.
- **Tone**: Discerning, luminous, calculated, architectural, calm.
- **Emotional Response**: Complete financial clarity, weightless control, and a feeling of handling an expensive, physical precision instrument carved out of sapphire and optical crystal.

### Design Movement: Optical Tactility
The visual language rejects flat corporate austerity in favor of frosted optical layers, ambient backlight refractions, and embossed micro-surfaces. Key characteristics include:
- Multi-layered frosted glass plates (`backdrop-filter: blur(24px)`) positioned over organic, slow-moving radial light sources.
- Dual-light directional specular highlights: top and left borders receive razor-thin white light (`rgba(255, 255, 255, 0.45)`), while bottom and right edges drop into diffused atmospheric indigo tints.
- Physical extrusion cues on actionable pills and inputs using subtle dual inner-shadows (embossed and debossed forms) rather than flat strokes.

## Colors

The palette operates on a deep atmospheric canvas where rich luminous primaries shine through semi-opaque glass substrates.

### Color Archetype & Usage
- **Neutral Canvas (`#0B0F19`)**: A deep cosmic obsidian foundation. It provides the required contrast for white frosted glass layers and colored radial lights. It prevents pure-black OLED clipping while preserving cinematic depth.
- **Primary — Cyan Glaze (`#06B6D4`)**: Used for live metrics, active tracking lines, primary focus boundaries, and high-clarity data nodes.
- **Secondary — Indigo Prism (`#6366F1`)**: Used for structural focal points, balance graphs, gradient glow blends, and forward momentum actions.
- **Tertiary — Radiant Emerald (`#10B981`)**: Dedicated to positive alpha, compounding growth, purchasing power surplus, and valid state indicators.

### Atmospheric Gradients & Environmental Glows
Surface luminosity does not rely on solid card colors, but on underlying radial blur patches:
- **Atmospheric Glow Alpha**: `radial-gradient(circle at top left, rgba(99, 102, 241, 0.18) 0%, transparent 65%)`
- **Atmospheric Glow Beta**: `radial-gradient(circle at bottom right, rgba(6, 182, 212, 0.14) 0%, transparent 60%)`
- **Atmospheric Glow Gamma**: `radial-gradient(circle at center, rgba(16, 185, 129, 0.08) 0%, transparent 50%)`

### Glass Surface System
- **Base Panel**: `rgba(15, 23, 42, 0.55)` with `backdrop-filter: blur(20px)` and `border: 1px solid rgba(255, 255, 255, 0.12)`.
- **Raised Interactive Glass**: `rgba(255, 255, 255, 0.07)` with `backdrop-filter: blur(28px)` and specular border `rgba(255, 255, 255, 0.28)`.
- **Text & Foreground**: Highest hierarchy text uses `#FFFFFF` (100%), secondary metrics use `rgba(241, 245, 249, 0.72)`, and tertiary labels use `rgba(148, 163, 184, 0.55)`.

## Typography

Typography in this design system uses **Plus Jakarta Sans** across all levels. The typeface offers a clean geometric core with subtly sculpted terminals, lending warmth to cold financial tables without sacrificing structural integrity.

### Typesetting Rules
- **Monospace Alternates for Currencies**: All numerical readouts, account balances, and percentage shifts must activate tabular figures (`font-feature-settings: "tnum" 1, "ss01" 1`) to eliminate tabular jitter during live data updates.
- **Optical Tracking Adjustments**: Headline tiers use progressive negative tracking (`-0.03em` down to `-0.015em`) to compress geometric presence, giving headlines a laser-cut, architectural density.
- **Label Transformations**: `label-md` and `label-sm` should be styled in uppercase when introducing data fields or metrics to reinforce the micro-pill hierarchy.

## Layout & Spacing

The layout is built upon an 8pt spatial grid with generous breathing room. This negative space allows the translucent glass plates and colored ambient glows to interact without visual crowding.

### Grid and Form Factors
- **Desktop (1200px+)**: 12-column layout with a 1360px maximum container width. Gutter is `1.5rem` (`24px`), section margin is `2.5rem` (`40px`). Multi-panel analytics sit side-by-side without visual conflict due to low card-edge opacity.
- **Tablet (768px – 1199px)**: 8-column layout. Gutter scales to `1.25rem` (`20px`), margins drop to `1.5rem` (`24px`). Tertiary sidebar panels collapse into expandable frosted sheets.
- **Mobile (< 768px)**: 4-column layout. Gutter shrinks to `1rem` (`16px`), outer margins use `1rem` (`16px`). Dashboard glass cards collapse to a singular column stack, expanding edge-to-edge with the canvas margin.

### Spatial Rhythms
- **Internal Card Padding**: Primary dashboard cards strictly utilize `space-lg` (`2rem`) padding to ensure content does not collide with light-refracting edge borders.
- **Micro Gaps**: Use `space-xs` (`6px`) between financial status pills and label descriptions; use `space-sm` (`12px`) between inputs and micro-labels.

## Elevation & Depth

Visual hierarchy uses a refined hybrid approach: **tactile neumorphic extrusion** layered inside **optical glass refractions**. Rather than dark, flat drop shadows, surfaces gain depth through specular border highlights and colored ambient underglows.

### The Prism-Glass Stacking Model

1. **Canvas Level (Ground Zero)**:
   - Deep obsidian background with dual atmospheric radial glows.
   - Non-interactive, pure substrate.

2. **Sub-Level (Recessed Cavities & Input Beds)**:
   - Neumorphic debossed state.
   - Background: `rgba(4, 7, 14, 0.6)`.
   - Box-Shadow: `inset 0 2px 4px rgba(0, 0, 0, 0.4), inset 0 0 12px rgba(0, 0, 0, 0.3)`.
   - Border: `1px solid rgba(255, 255, 255, 0.05)`.

3. **Level 1 (Standard Panel Glass)**:
   - Frosted content cards, transaction records, analytical groups.
   - Background: `rgba(17, 24, 39, 0.45)`.
   - Backdrop-Filter: `blur(24px) saturate(140%)`.
   - Border: `1px solid rgba(255, 255, 255, 0.12)`. Top border accented with a directional gradient: `linear-gradient(90deg, rgba(255, 255, 255, 0.35) 0%, rgba(255, 255, 255, 0.05) 100%)`.
   - Outer Shadow: `0 16px 36px -8px rgba(0, 0, 0, 0.4)`.

4. **Level 2 (Tactile Floating Controls & Actionable Modals)**:
   - Buttons, active modals, contextual popovers.
   - Background: `linear-gradient(135deg, rgba(255, 255, 255, 0.14) 0%, rgba(255, 255, 255, 0.03) 100%)`.
   - Backdrop-Filter: `blur(32px)`.
   - Dual Shadow:
     - Outer: `0 20px 40px -10px rgba(0, 0, 0, 0.5), 0 0 25px -4px rgba(6, 182, 212, 0.2)`.
     - Inner Specular (Top-Left): `inset 0 1px 1px rgba(255, 255, 255, 0.4)`.
     - Inner Occlusion (Bottom-Right): `inset 0 -1px 2px rgba(0, 0, 0, 0.3)`.

## Shapes

The design system uses a pill-centric, hyper-ergonomic geometry (`roundedness: 3`) that counterbalances analytical finance charts with soft, comfortable tactile points.

### Radius Assignments
- **Primary Action Buttons & Status Pills**: Complete Pill (`9999px` / `rounded-full`). These mimic polished beach pebbles, inviting touch on both mobile and desktop interfaces.
- **Large Frosted Panels & Cards**: `rounded-xl` (`2rem` / `32px`). Generous rounding emphasizes the fluid optical distortion beneath the glass boundaries.
- **Data Inputs & Form Modules**: Medium pill curvature (`1rem` / `16px`). Provides an enclosed, reservoir-like visual feel for inserted numbers.
- **Micro-Indicators & Avatars**: Soft circular contours (`rounded-full`).

## Components

### Buttons
- **Primary Tactile Button**:
  - Gradient face: `linear-gradient(135deg, #06B6D4 0%, #6366F1 100%)`.
  - Inner tactile highlight: `inset 0 1px 1px rgba(255, 255, 255, 0.5)`.
  - Outer ambient glow: `0 8px 24px -2px rgba(6, 182, 212, 0.35)`.
  - Radius: Pill (`9999px`).
  - Text: White, bold, `title-md`, subtle text drop shadow `0 1px 2px rgba(0, 0, 0, 0.3)`.
  - Hover: Scale `1.02`, glow expands to `0 12px 32px rgba(99, 102, 241, 0.5)`.
  - Active: Scale `0.98`, inner shadow switches to debossed: `inset 0 2px 4px rgba(0, 0, 0, 0.4)`.
- **Secondary Glass Button**:
  - Background: `rgba(255, 255, 255, 0.05)`.
  - Border: `1px solid rgba(255, 255, 255, 0.2)`.
  - Backdrop-Filter: `blur(16px)`.
  - Inner highlight: `inset 0 1px 0 rgba(255, 255, 255, 0.25)`.
  - Hover: Background rises to `rgba(255, 255, 255, 0.1)`, border brightens to `rgba(255, 255, 255, 0.4)`.

### Cards & Panels
- Constructed with multi-stop border gradients simulating directional crystal facets:
  - Top border: `rgba(255, 255, 255, 0.35)`.
  - Lateral borders: `rgba(255, 255, 255, 0.1)`.
  - Bottom border: `rgba(255, 255, 255, 0.03)`.
- Backing: `rgba(15, 23, 42, 0.6)`.
- Inner content separation uses hairline gradients (`rgba(255, 255, 255, 0.06)`) rather than solid divider lines.

### Inputs & Fields
- **Affordability Scenario Sliders & Fields**:
  - Cavity-style base: debossed into the canvas using `box-shadow: inset 0 2px 6px rgba(0, 0, 0, 0.5)`.
  - Background: `rgba(8, 12, 22, 0.7)`.
  - Focus Ring: `0 0 0 1px #06B6D4, 0 0 16px rgba(6, 182, 212, 0.35)`.
  - Range Sliders: Rail is debossed (`4px` height). The slider thumb is an embossed pill badge with an emerald/cyan core and a crisp white specular edge.

### Chips & Badges
- **Affordability Pill Indicator (Surplus / Deficit)**:
  - Positive: `rgba(16, 185, 129, 0.12)` background, `border: 1px solid rgba(16, 185, 129, 0.35)`. Text `#34D399`. Outer glow: `0 0 10px rgba(16, 185, 129, 0.15)`.
  - Caution/Deficit: `rgba(244, 63, 94, 0.12)` background, `border: 1px solid rgba(244, 63, 94, 0.35)`. Text `#FB7185`.

### Checkboxes & Radio Controls
- Base: Inset circular or rounded-pill well.
- Checked State: Liquid fill using primary cyan with a luminous center dot. An outer radial glow lights up the immediate frosted area around the control.

### Lists & Transaction Rows
- Rows sit on transparent surfaces and reveal an elevated glass skin on hover: `background: rgba(255, 255, 255, 0.04)`.
- Smooth transition (`200ms ease-out`) with an extruded left accent bar colored in Indigo or Cyan to denote selection.