# Phase 8 — Next.js Storefront Implementation Plan

> **For agentic workers:** Build task-by-task. Each task ends at a **visible checkpoint**
> (something to look at in the browser at http://localhost:3000). Frontend verification is
> visual + `next build` (typecheck/compile), not pytest.

**Goal:** A polished, clickable storefront — Main, Orders, Favorites, Chat, and auth — that
reads as the same brand family as mobileforyou (its exact design tokens + shadcn/ui-style
primitives) but is a fresh, clean Next 15 app wired to **our FastAPI** (no Supabase/i18n).

**Architecture:** `frontend/` = Next.js 15 App Router + React 19 + Tailwind v4. A typed
`lib/api.ts` talks to the backend and attaches the JWT `Bearer` from `localStorage`; a client
`AuthContext` holds session state; every page is a focused client component. Toaster feedback
on every action.

**Tech Stack:** Next 15, React 19, Tailwind v4, `class-variance-authority` + `clsx` +
`tailwind-merge` (the `cn` util), `lucide-react`, Radix (`@radix-ui/react-*` as needed).

## Global Constraints

- **Design tokens copied from mobileforyou** (`src/app/globals.css`): warm near-black `--ink`,
  indigo `--accent` (#2563eb), neutral surfaces/borders, signal colors. Same look & feel.
- **English + USD** everywhere. Prices formatted `$1,234.00`.
- **Auth:** JWT in `localStorage`, sent as `Authorization: Bearer`. Logged-out users browse;
  actions that need auth prompt a login.
- **Notify on every outcome** — a toast for success *and* failure (brief requirement).
- **API base URL** from `NEXT_PUBLIC_API_URL` (default `http://localhost:8000`).
- **Backend CORS** must allow `http://localhost:3000` (added in Task 7).
- Chat `session_id` = a `crypto.randomUUID()` persisted in `localStorage`.

---

### Task 1: Scaffold + design system + app shell

**Files:** `frontend/` (new app), `src/app/globals.css`, `src/lib/utils.ts`,
`src/components/ui/{Button,Card,Input,Badge,Spinner}.tsx`, `src/components/Header.tsx`,
`src/app/layout.tsx`, `src/components/ui/Toaster.tsx`.

- [ ] **Step 1: Scaffold** (non-interactive):
  ```bash
  cd "<repo>" && npx --yes create-next-app@latest frontend \
    --ts --tailwind --app --src-dir --import-alias "@/*" --no-eslint --use-npm --yes
  ```
- [ ] **Step 2: Design tokens** — copy mobileforyou's `src/app/globals.css` token block
  (`:root { --ink, --accent, --surface, --border, signal colors ... }`) and expose them to
  Tailwind v4 via `@theme inline` (map `--color-ink: var(--ink)`, `--color-accent`, etc.) so
  utilities like `bg-ink`, `text-accent`, `border-border-strong` work.
- [ ] **Step 3: `cn` util** — `src/lib/utils.ts`: `cn(...) = twMerge(clsx(...))`.
- [ ] **Step 4: UI primitives** — port mobileforyou's `Button` (CVA variants
  primary/accent/success/outline/ghost/danger, sizes sm/md/lg, `isLoading`), plus small
  `Card`, `Input`, `Badge`, `Spinner`. Drop mobileforyou-only bits (whatsapp variant, i18n).
- [ ] **Step 5: Header + layout** — sticky header (brand mark, nav links Home/Orders/Favorites/
  Chat, and an auth slot placeholder), `layout.tsx` wraps children + mounts a `<Toaster/>`.
- [ ] **Step 6: Verify** — `npm run dev`; the shell renders with correct fonts/colors.
      **Commit** `feat(web): scaffold Next.js app + mobileforyou design system + shell`.

---

### Task 2: API client + Auth (context, login, register)

**Files:** `src/lib/api.ts`, `src/lib/types.ts`, `src/context/AuthContext.tsx`,
`src/app/login/page.tsx`, `src/app/register/page.tsx`, update `Header.tsx`.

**Interfaces:**
- `api.get/post/del(path, body?)` → JSON; injects `Bearer` from `localStorage`; throws
  `ApiError{status,message}` on non-2xx.
- `AuthContext`: `{ user, token, login(username,pw), register(...), logout(), deleteAccount() }`.

- [ ] **Step 1: `lib/api.ts`** — a `fetch` wrapper: base URL from env, JSON headers, attach
  `Authorization` if a token is in `localStorage`, parse errors into `ApiError`.
- [ ] **Step 2: `types.ts`** — `Product, OrderPublic, OrderItem, ChatResponse, ChurnResponse,
  UserPublic` mirroring the backend schemas.
- [ ] **Step 3: `AuthContext`** — holds `token`/`user` (hydrated from `localStorage`);
  `login` → `POST /auth/login` → store token → `GET /auth/me`; `register` → `POST /auth/register`
  then login; `logout` clears storage; `deleteAccount` → `DELETE /auth/me` then logout.
- [ ] **Step 4: Pages** — `/login` + `/register` forms (Input + Button), toast on success/error,
  redirect home. Header auth slot shows Login/Register (logged out) or a user menu with Logout +
  Delete account (logged in).
- [ ] **Step 5: Verify** — register a user, land logged-in, refresh persists, logout works.
      **Commit** `feat(web): API client + JWT auth (login/register/logout/delete)`.

---

### Task 3: Main page — product grid + search

**Files:** `src/components/store/ProductCard.tsx`, `ProductGrid.tsx`, `SearchBar.tsx`,
`src/app/page.tsx`, `src/lib/format.ts` (USD).

**Interfaces:**
- `SearchBar` builds a query for `GET /products/search?q=&stock_op=&stock_value=&price_op=&price_value=`.

- [ ] **Step 1: `ProductCard`** — image (or placeholder), name, brand, `$price`, a stock badge
  (in stock / low / out), and action slots (favorite ♥, add-to-cart) filled in later tasks.
- [ ] **Step 2: `format.ts`** — `usd(n)` → `$1,234.00`.
- [ ] **Step 3: `SearchBar`** — a text box for multi-term name search, plus compact
  stock/price range controls (operator `<`/`>`/`=` + value). Submitting calls `/products/search`;
  empty result shows a friendly "no matches" notice; clearing restores the full grid.
- [ ] **Step 4: Home `page.tsx`** — a hero band (brand gradient), the `SearchBar`, and the
  `ProductGrid` (loads `GET /products`). Results replace the grid.
- [ ] **Step 5: Verify** — grid shows the 151 products; name/range search works; empty-state shows.
      **Commit** `feat(web): main page — product grid + search`.

---

### Task 4: Favorites

**Files:** `src/app/favorites/page.tsx`, favorite button in `ProductCard`, `src/hooks/useFavorites.ts`.

- [ ] **Step 1: `useFavorites`** — loads `GET /favorites`; `add(id)`→`POST`, `remove(id)`→`DELETE`;
  exposes a `Set` of favorited ids + toggles (login-gated → toast "log in to save").
- [ ] **Step 2: Heart button** on `ProductCard` reflects favorited state and toggles it.
- [ ] **Step 3: `/favorites` page** — grid of the user's favorites; empty-state; login-gated.
- [ ] **Step 4: Verify** — toggle a heart, see it on /favorites, persists across reload.
      **Commit** `feat(web): favorites page + heart toggle`.

---

### Task 5: Orders — cart, checkout, history

**Files:** `src/app/orders/page.tsx`, `src/hooks/useCart.ts`,
`src/components/store/{CartPanel,OrderCard,CheckoutForm}.tsx`, add-to-cart in `ProductCard`.

**Interfaces:**
- `useCart`: `add(product_id, qty)`→`POST /orders/items`, `remove(product_id)`→`DELETE`,
  `list()`→`GET /orders`, `purchase(order_id, address)`→`POST /orders/{id}/purchase`,
  `discard(order_id)`→`DELETE /orders/{id}`.

- [ ] **Step 1: `useCart`** — wraps the order endpoints; surfaces the current TEMP order + history;
  toasts on stock rejections (409 messages from the backend).
- [ ] **Step 2: Add-to-cart** button on `ProductCard` (disabled when out of stock).
- [ ] **Step 3: `/orders` page** — TEMP cart **pinned first & visually distinct**: line items,
  qty, live totals, remove, a `CheckoutForm` (shipping address + Purchase). CLOSE orders render
  as read-only history cards. Emptying the cart removes it.
- [ ] **Step 4: Verify** — add items, adjust, checkout → order moves to history, stock drops.
      **Commit** `feat(web): orders — cart, checkout, order history`.

---

### Task 6: Chat — the AI assistant

**Files:** `src/app/chat/page.tsx`, `src/components/store/ChatMessage.tsx`, `src/hooks/useChat.ts`.

- [ ] **Step 1: `useChat`** — persists a `session_id`; `send(message)`→`POST /chat`; tracks the
  message list, `remaining_prompts`, `available`, and `sources`.
- [ ] **Step 2: `/chat` page** — a conversation view (user + assistant bubbles), an input that
  disables at 0 remaining, a **remaining-prompts** indicator, and a graceful "assistant
  unavailable" state. Show `sources` (grounding products) under answers when present.
- [ ] **Step 3: Verify** — ask a question, get a grounded answer; the counter counts down; the
  6th prompt is blocked.
      **Commit** `feat(web): chat page — AI assistant with prompt counter`.

---

### Task 7: Backend CORS + polish + full run-through

**Files:** `backend/app/main.py` (CORS), responsive/loading polish across pages.

- [ ] **Step 1: CORS** — add `CORSMiddleware` to the FastAPI app allowing
  `http://localhost:3000` (origins from a settings value; methods/headers `*`).
- [ ] **Step 2: Polish** — loading spinners, empty states, disabled states, mobile responsive
  (grid collapses, header nav), consistent toasts.
- [ ] **Step 3: Verify** — `npm run build` passes (types/compile); full click-through of every
  page against the live backend.
      **Commit** `feat(web): backend CORS + storefront polish` and `feat(api): CORS for the web app`.

---

## Definition of Done (Phase 8)

- [ ] `npm run dev` serves a polished store at :3000 that looks like the mobileforyou family.
- [ ] Browse + multi-term/range search; empty-state notice.
- [ ] Register / login / logout / delete account (JWT persisted).
- [ ] Favorites (login-gated) add/remove, persisted.
- [ ] Cart → checkout → history; stock enforced; TEMP pinned & distinct.
- [ ] Chat with the AI assistant; remaining-prompts shown; blocks after 5.
- [ ] Toast on every outcome; responsive; `next build` passes.
- [ ] Backend allows CORS from the web origin.
- [ ] Pushed to `main` under Adir's name.

**Next phase:** Phase 9 — polish & submit (README screenshots, dockerize the frontend so
`docker compose up` serves everything, final run-through).
