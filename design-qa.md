# Design QA — IPAC Login

- Source visual truth path: conversation attachment, “IPAC CRM login” reference supplied on 2026-07-30.
- Generated supporting asset: `frontend/public/login-ipac-background.png`.
- Implementation screenshot path: unavailable.
- Source viewport: 1776 × 886 px, assumed 1× density from the supplied reference.
- Intended desktop comparison viewport: 1776 × 886 CSS px at device scale factor 1.
- Intended mobile validation viewport: 390 × 844 CSS px at device scale factor 1; no mobile source mock was supplied.
- State: unauthenticated login, password hidden, “Recordarme” unchecked.

## Full-view comparison evidence

Blocked. The source reference is visible in the conversation, but no supported browser-rendered screenshot of the current implementation could be captured. The in-app browser is unavailable in this session and the connected Chrome control is not installed.

## Focused-region comparison evidence

Not performed because browser-rendered evidence is missing. The form, feature cards, help strip, desktop composition, and separate mobile experience still require visual inspection at their target viewports.

## Required fidelity surfaces

- Fonts and typography: Inter Variable is bundled and the target hierarchy is implemented, but visual weight, wrapping, and optical alignment are not browser-verified.
- Spacing and layout rhythm: desktop uses a full-viewport 53/47 split and mobile mounts a separate full-screen composition; visual spacing and overflow remain unverified.
- Colors and visual tokens: the navy, blue, white, and gold palette follows the reference; browser rendering and contrast remain unverified.
- Image quality and asset fidelity: the generated navy background is present as a real raster asset and Heroicons are used for UI icons; crop and sharpness remain unverified in the browser.
- Copy and content: institutional copy, Argentine support email, and Argentine phone number are implemented.

## Findings

- [P0] Browser-rendered evidence is unavailable.
  - Location: desktop and mobile login views.
  - Evidence: build and component tests pass, but there is no implementation screenshot or browser console capture.
  - Impact: layout, visual fidelity, overflow, and interaction polish cannot receive a valid design-QA pass.
  - Fix: capture the unauthenticated login at 1776 × 886 and 390 × 844, compare both with the supplied reference and intended mobile direction, then resolve any P1/P2 differences.

## Primary interactions tested

- Desktop form submission payload.
- Mobile form submission payload.
- Independent desktop and mobile component structures.
- Persistent versus session-only authentication token behavior.
- Production build and automated unit/component tests.

Browser-level keyboard flow, password visibility control, help links, responsive component switching, network requests, and console errors were not captured.

## Comparison history

- Pass 1: blocked before visual comparison because implementation capture is unavailable.

## Implementation checklist

- Capture the desktop login at 1776 × 886.
- Capture the mobile login at 390 × 844.
- Test password visibility, “Recordarme”, help links, loading, invalid credentials, and successful login.
- Inspect browser console errors.
- Compare reference and implementation together and fix all P0/P1/P2 differences.

## Follow-up polish

- Evaluate the generated background crop at ultrawide desktop sizes.
- Confirm the mobile help block remains above the fold on shorter devices.

final result: blocked
