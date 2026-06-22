# Design System: Mutual Fund FAQ Assistant

## 1. Overview
This document serves as the foundational Design System for the **Mutual Fund FAQ Assistant**. The assistant is a strict, facts-only RAG chatbot scoped to ICICI Prudential Mutual Fund schemes (using Groww as a reference context). 

The visual language must communicate **trust, financial accuracy, compliance, and modern simplicity**. It should avoid aggressive "sales" aesthetics, opting instead for a clean, data-first presentation using glassmorphism, soft gradients, and clear typography.

---

## 2. Typography
We use a two-font system to balance approachability with data legibility, as defined in the project architecture.

* **Primary/Display Font:** `Outfit`
    * **Usage:** Headers, titles, example question cards, and the welcome message.
    * **Weights:** SemiBold (600), Bold (700)
* **Body Font:** `Inter`
    * **Usage:** Chat bubbles, input fields, citations, footers, and disclaimer text.
    * **Weights:** Regular (400), Medium (500)

---

## 3. Color Palette
The palette is inspired by modern financial platforms (like Groww) but muted to emphasize neutrality and compliance.

### Primary Accents
* **Growth Teal:** `#00B589` (Used for user chat bubbles, active states, and primary send buttons).
* **Deep Slate:** `#1E293B` (Used for header backgrounds, primary typography, and structural borders).

### Backgrounds & Surfaces
* **App Background:** `#F8FAFC` (Very soft slate/blue off-white to reduce eye strain).
* **Surface/Cards:** `#FFFFFF` (White with subtle shadow for chat bubbles and example cards).
* **Input Background:** `#F1F5F9` (Light gray/slate for the text input area).

### Typography Colors
* **Primary Text:** `#0F172A` (Near black for maximum readability in chat bubbles).
* **Secondary/Muted Text:** `#64748B` (Used for timestamps, footers, and placeholder text).
* **Links/Citations:** `#2563EB` (Standard trusted blue for citation URLs, with underline on hover).

### Compliance & Status
* **Disclaimer Banner Background:** `#FFFBEB` (Soft amber/warning).
* **Disclaimer Text:** `#B45309` (Deep amber).

---

## 4. UI Components

### 4.1. Disclaimer Banner
* **Style:** Full-width strip at the top of the interface or pinned just above the chat input.
* **Text:** `"⚠️ Facts-only. No investment advice."`
* **Visuals:** `#FFFBEB` background, `#B45309` text, `Inter` Medium 13px. Centered.

### 4.2. Example Question Cards (Chips)
* **Style:** Glassmorphism or soft-shadow cards displayed in the empty state.
* **Border:** 1px solid `#E2E8F0`.
* **Background:** `#FFFFFF` with a subtle hover effect (`#F8FAFC` and slight Y-axis lift).
* **Typography:** `Outfit` Medium, 14px, `#1E293B`.

### 4.3. Chat Bubbles
* **User Bubble:**
    * Alignment: Right.
    * Background: `#00B589` (Growth Teal).
    * Text: `#FFFFFF`, `Inter` Regular 15px.
    * Corners: Rounded (16px), but with a sharp bottom-right corner (2px).
* **Assistant Bubble:**
    * Alignment: Left.
    * Background: `#FFFFFF`.
    * Border: 1px solid `#E2E8F0`.
    * Shadow: `0 2px 4px rgba(0,0,0,0.02)`.
    * Text: `#0F172A`, `Inter` Regular 15px. Max 3 sentences.
    * Corners: Rounded (16px), sharp bottom-left corner (2px).

### 4.4. Assistant Response Footer & Citation
Every assistant response must contain a citation and a date footer.
* **Citation Links:** Displayed as distinct clickable links below the main text, separated by inline dividers (`|`) if multiple funds are selected. Font: `Inter` Medium 13px, `#2563EB`. Icon: Small external link icon next to each link.
* **Last Updated Footer:** Font: `Inter` Regular 12px, `#64748B`. Text: `Last updated from sources: <date>`. Displayed at the very bottom of the assistant bubble.

### 4.5. Chat Input Area
* **Style:** Floating pill or anchored bottom bar.
* **Input Field:** `#F1F5F9` background, no visible border, `Inter` Regular 15px.
* **Send Button:** Circular button, `#00B589` background, white send/arrow icon. Disabled state: `#CBD5E1`.

---

## 5. Layout & Spacing
* **Container:** Max-width 800px, centered on desktop, full-width on mobile.
* **Padding:** 24px global padding. 16px gap between chat bubbles.
* **Animations:** * Fade-in and slide-up for new messages (`200ms ease-out`).
    * Smooth pulse on the send button when input is active.

---

## 6. Implementation Status
The design system described in this document has been fully implemented in the React + Vite single-page application located under the `frontend/` directory. All design tokens, including color palettes, font weights, shadows, warning disclaimers, micro-animations, and viewport layout constraints, have been coded utilizing Tailwind CSS variables in strict alignment with this specification.
