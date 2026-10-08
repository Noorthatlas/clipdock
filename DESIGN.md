---
name: ClipDock
description: Minimal cool-gray and navy export desk with system task typography.
colors:
  ink: "#172b3b"
  muted: "#556474"
  navy: "#183956"
  line: "#dce2e8"
  canvas: "#f1f3f6"
  sheet: "#fff"
  export-surface: "#fcfdfe"
  workspace-border: "#d5dde5"
  control-border: "#c4ced8"
  primary-hover: "#244e70"
  inspect-surface: "#f8fafc"
  button-hover: "#f0f5fa"
  button-hover-border: "#6d8daa"
  disabled-surface: "#e9edf1"
  disabled-text: "#637181"
  disabled-border: "#e0e5ea"
  selected-surface: "#f4f8fc"
  selected-border: "#4f7699"
  selected-disabled-surface: "#f6f8fa"
  selected-disabled-border: "#b9c7d4"
  focus: "#3c73a7"
  focus-soft: "#dce7f2"
  progress: "#315b7f"
  progress-track: "#e4ebf1"
  error-text: "#8d3038"
  error-surface: "#fdf4f4"
  error-border: "#efced2"
  success-text: "#285b4b"
typography:
  headline:
    fontFamily: '-apple-system,BlinkMacSystemFont,"Segoe UI",Arial,sans-serif'
    fontSize: "clamp(30px,3.6vw,43px)"
    fontWeight: 650
    lineHeight: 1.15
    letterSpacing: "-.035em"
  title:
    fontSize: "18px"
    fontWeight: 650
    letterSpacing: "-.015em"
  body:
    fontFamily: '-apple-system,BlinkMacSystemFont,"Segoe UI",Arial,sans-serif'
    fontSize: "15px"
    lineHeight: 1.5
  label:
    fontSize: "13px"
    fontWeight: 600
rounded:
  control: "6px"
  workspace: "10px"
  compact-workspace: "8px"
  progress: "3px"
spacing:
  inline: "9px"
  compact-gap: "10px"
  heading-gap: "12px"
  mobile-pane: "24px 20px"
  source-pane: "30px 32px"
  export-pane: "30px 30px"
components:
  button-primary:
    backgroundColor: "{colors.navy}"
    textColor: "{colors.sheet}"
    typography: "{typography.label}"
    rounded: "{rounded.control}"
    padding: "10px 17px"
    width: "100%"
  button-primary-hover:
    backgroundColor: "{colors.primary-hover}"
  button-inspect:
    backgroundColor: "{colors.inspect-surface}"
    textColor: "{colors.navy}"
    rounded: "{rounded.control}"
    padding: "10px 17px"
    width: "100%"
  button-disabled:
    backgroundColor: "{colors.disabled-surface}"
    textColor: "{colors.disabled-text}"
  url-control:
    backgroundColor: "{colors.sheet}"
    rounded: "{rounded.control}"
    padding: "0 13px"
    height: "48px"
  workspace:
    backgroundColor: "{colors.sheet}"
    rounded: "{rounded.workspace}"
  format-selected:
    backgroundColor: "{colors.selected-surface}"
    textColor: "{colors.navy}"
    rounded: "{rounded.control}"
    padding: "15px 14px"
---

# Design System: ClipDock

## Overview

The built identity is the user-approved **minimal export desk**: cool-gray canvas, white working sheet, navy controls, fine seams, and system sans typography. It is a task interface rather than a marketing composition. There is no separate display font, generated imagery, or supplied brand asset; the wordmark pairs text with a Lucide outline icon.

This document records source truth, not a production feature certification. Evidence: `frontend/src/app/globals.css`, `layout.tsx`, `page.tsx`, `frontend/src/components/desk.tsx`, `frontend/src/lib/security.ts`, and `frontend/next.config.ts`; approved direction comes from `PRODUCT.md` and `SURFACE.md`. The surface's Operate mode and task sequence remain in `SURFACE.md` rather than becoming global design tokens. The context helper failed to recognize these existing UI files; direct source inspection is authoritative here.

**Key Characteristics:**
- Restrained light-only surfaces and readable ink-blue hierarchy.
- A single bordered workspace, not a collection of floating cards.
- Native form semantics, explicit permission, and state-dependent actions.
- Spanish interface copy; honest empty, error, progress, and disconnected states.

## Colors

### Primary

Navy identifies the wordmark, permission checkbox accent, inspection action text, and enabled preparation/download button. Primary hover deepens the filled action. The progress blue also fills the selected radio indicator. This is one restrained blue family, not multiple decorative accents.

### Neutral

Canvas surrounds the white sheet; the export surface is subtly cooler than the source pane. Ink carries main content and muted carries supporting labels. Line supplies pane seams and summary rules; workspace and control borders use their own slightly stronger strokes. Disabled controls retain legible text instead of relying on opacity.

### Semantic states

Selected format cards use a pale blue surface and blue border; selected-but-disabled cards have separate quieter values. Errors use red text, pale red fill, and a red-tinted border. Ready-file status uses green text with a check icon. Focus has a stronger blue outline and a separate pale-blue URL-field treatment. These are state cues, not decorative palette expansion.

**The State Truth Rule.** A selected appearance does not imply availability: the initial MP4 card remains selected while disabled until media inspection supplies video qualities.

## Typography

The whole interface inherits the system sans stack in frontmatter. There are no downloaded font files or distinct serif/mono roles. Base body uses the recorded body style; form elements explicitly inherit it, then apply their own sizes.

- **Headline:** the sole page heading uses the fluid headline style, balanced wrapping, and tight tracking.
- **Pane title:** the title style is compact and moderately weighted. Restriction headings step down to (16px); subordinate restriction headings use (13px).
- **Media title:** (16px, weight 600), with anywhere wrapping and pretty text wrapping for unpredictable titles.
- **Intro:** (16px), reducing to (14px) on mobile with (1.6) line height and a (32ch) maximum width.
- **Labels/buttons:** the label style; format names use (14px, weight 650), and URL input text uses (14px).
- **Supporting copy:** generally (11–12px); permission footer and desktop platform caveat use (10px). Restriction paragraphs use (12px, 1.75), capped at (65ch).
- **Wordmark:** (23px, weight 650, -.035em), reducing to (21px) on mobile.
- **Numbers:** duration and job progress use tabular figures. Export summary values use weight (550).

No mathematical type-scale ratio is defined. Preserve these observed task roles rather than introducing an invented scale or extra display hierarchy.

## Layout

The header is (84px) tall with a centered (1200px) maximum-width inner container and (40px) horizontal padding. Main content shares that container width and uses (52px 40px 0) padding. The introduction is a bottom-aligned flex row with (24px) gap and (30px) space before the workspace.

The workspace is a clipped two-column grid: `minmax(0,1.55fr) minmax(0,1fr)`. Source and export panes use the frontmatter paddings. A fine vertical seam separates them. The export pane is a flex column, allowing its permission note to sit at the bottom via automatic top margin. The preview is (16:9), and media images use `object-fit: contain`, not cover cropping.

Below the desk, platform names form a wrapping text list with a conditional-availability caveat; they are not logo chips or navigation tabs. Restrictions use two equal columns with (60px) gap. Footer has a (1120px) maximum width, top rule, and modest inline text.

### Responsive conventions

- **At 1500px and wider:** main top padding becomes (64px).
- **At 1000px and narrower:** hide the intro permission note; use a `1.25fr / 1fr` desk; reduce both pane paddings to (25px). Platform caveat occupies its own row, restriction gap becomes (36px), and footer gets (40px) side margins.
- **At 700px and narrower:** header becomes (68px), inner padding (22px), main padding (32px 20px 0), and introduction spacing (24px). Workspace becomes one column with compact radius. Source precedes export; pane padding is (24px 20px), and the export seam moves from left to top.
- **Mobile formats:** retain two side-by-side cards within the stacked desk, with (10px) gap, (89px) minimum height, and (13px 11px) padding. Their radio indicators move to the upper right and shrink to (13px).
- **Mobile support/footer:** platform label spans a row, restrictions stack with (22px) gap, and footer wraps with its explanatory paragraph on a full-width last row. Disconnected copy uses anywhere wrapping.

These are CSS media-query boundaries, not framework preset breakpoints. Content containers use `min-width: 0` and wrapping where specified; do not restore fixed-width title or URL layouts.

## Elevation & Depth

Depth comes principally from background tone, fine borders, and pane seams. The workspace has one low-opacity structural shadow: `0 6px 24px #172b3b06`. Controls and the disconnected panel do not gain shadows on hover. Focus outlines communicate interaction, not elevation.

Motion is narrowly functional: URL border and button background/border transitions last (.15s); newly resolved media detail reveals with a (.3s) clip-path animation using `cubic-bezier(.16,1,.3,1)`. Job progress animates `transform` for (.4s) with the same easing; its full-width inner bar scales from the left using `scaleX(progress / 100)`, rather than changing layout width. Smooth anchor scrolling is enabled with (32px) scroll padding. Reduced-motion preference removes all animations/transitions and changes scrolling to automatic.

## Shapes

Controls, preview, format cards, and inline error use the control radius. The desktop sheet has the larger workspace radius; mobile sheet and disconnected panel use the compact radius. The progress track uses the progress radius. Most strokes are (1px). Radio indicators are circular, but the rest of the form remains crisp and rectangular rather than pill-shaped. Overflow clipping belongs to the sheet, preview, and progress track.

## Components

### Header and navigation

The wordmark links home; the help link scrolls to `#limites`. Help text is muted by default, then navy and underlined on hover. The keyboard-visible skip link is fixed at (12px, 12px), initially translated offscreen, and resolves on focus. There is no separate mobile navigation menu.

### URL, permission, and inspection

The URL field is a (48px) flex control with a leading outline link icon. Its wrapper takes focus-within styling: (3px) soft outline, (1px) offset, and focus-color border; the inner input intentionally has no separate outline. Helper copy distinguishes an empty field, an unsupported URL, and a recognized platform. Recognition is not evidence that extraction will succeed.

Permission is a native (17px) checkbox and wrapping label, capped at (53ch). Inspection is full-width and quiet-toned, with an arrow when idle and `Analizando enlace…` while active. It is disabled unless permission and a recognized URL are present, and while inspection/export is running. Editing the URL or removing permission invalidates stale media, errors, progress, and download state.

### Buttons and focus

Buttons have minimum height (44px), (1px) stroke, and the documented padding. Quiet buttons use pale hover fill and a stronger border; filled actions use primary hover. Disabled buttons use the explicit disabled colors and a not-allowed cursor. Global button/link/input/select focus-visible is a (3px) focus-color outline at (3px) offset. Radio labels mirror that focus ring when their hidden native input receives focus.

### Preview and metadata

The empty preview centers a film icon, restrained heading, and short multiline guidance; during inspection, copy becomes `Buscando tu video` and a screen-reader status announces the lookup. Successful inspection can supply title, platform, and duration. A missing, rejected, or failed thumbnail shows `Miniatura no disponible` with an image-off icon and explicitly permits preparation without an image. Preview is never an autoplay video player.

Runtime thumbnails may be null. `safeThumbnail` and CSP restrict them to HTTPS CDN hosts listed in security source: `i.ytimg.com`, `img.youtube.com`, `i9.ytimg.com`, `pbs.twimg.com`, and `video.twimg.com`. Images use no-referrer requests. No supplied or generated marketing image is part of this design.

### Format cards, quality, and summary

Format cards are labels around native radios, grouped in a fieldset with legend; they have (78px) desktop minimum height and an outline icon, name, supporting description, and custom visible radio indicator. MP4 requires available video qualities; MP3 requires audio. Both lock during preparation. Selected treatment and disabled treatment are separate, including their combined state.

Quality is a native full-width (44px) select. Before inspection it displays `Disponible después de analizar`; afterwards it lists only returned qualities, using `Original` for zero. It is disabled for MP3, missing video qualities, or preparation. The two-row ruled summary shows `Por determinar` until media exists, not an invented quality. Changing format or quality clears the old download link.

### Processing, error, and completion

Preparation is enabled only for inspected media, confirmed permission, an available format, and no active operation. Inline errors use an alert role, icon, and actionable server/client message. Expired inspection clears media and asks for another inspection; network loss and timeout are errors, never ready-file states.

While busy, display queued/preparing text, a numeric percentage, and the narrow progress track. The track exposes progressbar role, label, and current/min/max values; displayed progress is clamped to (0–100). Completion appears only after a completed job returns a validated same-origin API download URL: green `Tu archivo está listo` status, navy download link, and a temporary-link reminder. The export explanation and permission disclaimer stay explicit; affirming permission is not automatic rights verification.

### Disconnected server

`page.tsx` validates `NEXT_PUBLIC_API_URL` before mounting the desk. Missing or invalid origin replaces the entire workspace with a white, bordered, compact-radius panel (`role="alert"`), alert icon, heading `El servidor aún no está conectado`, and copy saying download is unavailable until a valid media-server address is configured. It is not a disabled mock desk or simulated success.

The panel uses (38px) padding and (16px) gap on desktop, changing to (24px 20px) and (12px) gap on mobile. Its body uses (14px) muted text, then (12px) on mobile; mobile heading is (17px). Header, introduction, platform caveat, restrictions, and footer remain visible. With the deployment's intentionally unset API URL, this is the actual production-facing state; it does not verify the export flow in production.

## Do's and Don'ts

### Do:
- **Do** preserve the cool-gray/navy system sans identity and restrained bordered-sheet model.
- **Do** keep source-to-preview-to-settings order on mobile and retain native form semantics.
- **Do** use actual inspection data, validated download URLs, and explicit disabled/error/status treatments.
- **Do** retain focus visibility, reduced-motion behavior, thumbnail fallbacks, and long-title wrapping.
- **Do** show disconnected configuration as unavailable service, not as an operational desk.

### Don't:
- **Don't** add decorative brand assets, downloaded display fonts, autoplay previews, or unapproved imagery.
- **Don't** treat the six-platform list or URL recognition as a guarantee that every link works.
- **Don't** fabricate thumbnails, qualities, progress, readiness, or production download verification.
- **Don't** turn the permission checkbox into a claim that ownership or legal rights were verified.
- **Don't** replace the temporary-download warning or responsible-use restrictions with marketing assurance.

Development-only extension metadata is recorded in `development/design.json`; no `.impeccable` artifact or application source was changed for this extraction.
