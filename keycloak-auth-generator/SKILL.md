---
name: keycloak-auth-generator
description: "Auto-generates Keycloak SSO authentication code for any framework. Supports Next.js, Vue 3, Nuxt 3, FastAPI, Django, Flask, and Spring Boot+Thymeleaf. Generates login pages, logout, token refresh, middleware/guards, type definitions, and optional Docker-based local Keycloak setup. Trigger this skill when the user mentions 'Keycloak', 'SSO', 'keycloak login', 'auth code', 'keycloak auth', 'OIDC integration', 'login page', 'FastAPI auth', 'Django OIDC', 'Flask keycloak', or any request to add Keycloak authentication to a project. Uses official adapters instead of keycloakify."
---

# Keycloak Auth Generator

Auto-generates Keycloak SSO authentication code tailored to each framework's officially recommended approach:

**JavaScript/TypeScript:**
- Next.js → Auth.js v5 (NextAuth) + Keycloak Provider
- Vue 3 → `@josempgon/vue-keycloak` (Composition API wrapper) or direct `keycloak-js`
- Nuxt 3 → `sidebase/nuxt-auth` + Keycloak Provider

**Python:**
- FastAPI → `PyJWT` (JWT verification) or `fastapi-keycloak` library
- Django → `mozilla-django-oidc` or `django-allauth` (OIDC provider)
- Flask → `Authlib` (OAuth/OIDC client)

**Java:**
- Spring Boot + Thymeleaf → `spring-boot-starter-oauth2-client` + Spring Security

## Gathering User Information (Critical)

**NEVER generate code before collecting all required information.**
If the user has already provided some info, do not ask again. Only ask for missing items.

### Required Fields

1. **Framework** (required)
   - Next.js / Vue 3 / Nuxt 3 / FastAPI / Django / Flask / Thymeleaf
   - If the user uploads project files, attempt auto-detection (see below)
   - If detection fails, ask the user directly

2. **Keycloak Connection Info** (required)
   - **Keycloak URL**: Server address. e.g. `https://auth.company.com` or `http://localhost:8080`
   - **Realm name**: e.g. `my-realm`
   - **Client ID**: e.g. `my-app`
   - **Client Secret**: Only needed for server-side frameworks (Next.js, Nuxt, FastAPI, Django, Flask, Thymeleaf). Vue 3 uses a public client and does not need a secret.
     - If unknown, guide the user: "You can find it in Keycloak Admin Console → your Client → Credentials tab." Use placeholder (`your-client-secret-here`) in the generated code.

3. **Features** (optional — default: all included)
   - Login page
   - Logout (including Keycloak session termination)
   - Automatic token refresh (refresh token rotation)
   - Role-based access control (RBAC)
   - Include all unless the user explicitly asks to exclude some.

4. **UI Design System** (optional)
   Recommend popular design systems for the chosen framework and let the user pick.
   If the user doesn't mention one, ask:

   **Next.js:**
   - shadcn/ui (Tailwind-based, most popular) ← default recommendation
   - MUI (Material UI)
   - Ant Design
   - Tailwind only (no component library)

   **Vue 3:**
   - Vuetify (Material Design, most popular) ← default recommendation
   - PrimeVue (enterprise-grade, 80+ components)
   - Element Plus (clean design)
   - Naive UI (TypeScript-friendly)
   - Tailwind only

   **Nuxt 3:**
   - Nuxt UI (official Nuxt, Tailwind-based) ← default recommendation
   - Vuetify
   - PrimeVue
   - Tailwind only

   **FastAPI:**
   - No UI (API server) ← default
   - Swagger UI + OIDC integration (with fastapi-keycloak)
   - Jinja2 templates + Bootstrap (if admin pages needed)

   **Django:**
   - django-crispy-forms + Bootstrap 5 ← default recommendation
   - Tailwind (django-tailwind)
   - Plain Django templates (no styling)

   **Flask:**
   - Bootstrap 5 (CDN) ← default recommendation
   - Tailwind (CDN)
   - Plain HTML (no styling)

   **Thymeleaf:**
   - Bootstrap 5 ← default recommendation
   - Tailwind (CDN)
   - Plain HTML (no styling)

   Generate login/dashboard page UI using the selected design system's components (Button, Card, Input, etc.).

   **Custom design reference:**
   Every framework option list above should also include a final option:
   - 🎨 **Custom — provide a reference** (URL or image of desired design)

   If the user selects custom, ask:
   ```
   Want to share a design reference? You can provide:
   - A URL to a login page you like (e.g. https://example.com/login)
   - An uploaded image or screenshot
   - A text description of the style you want (e.g. "dark theme, minimal, centered card")
   ```

   When a reference is provided:
   - If URL: use `web_fetch` to analyze the page's layout, colors, spacing, and component patterns. Then replicate the style using the project's CSS framework (Tailwind, Bootstrap, etc.).
   - If image: analyze the visual design — layout structure, color palette, typography, spacing, button styles. Then generate CSS/components that match.
   - If text description: interpret the style keywords and generate appropriate UI.

   The generated login/dashboard pages should match the provided reference as closely as possible while using the project's framework-appropriate patterns (React components for Next.js, Vue SFCs for Vue, Thymeleaf templates, etc.).

5. **Existing project?** (optional)
   - New project or adding to existing?
   - If existing, suggest merge strategies for conflicting files (e.g. middleware.ts)

### How to Ask

When the user requests "Add Keycloak auth" without providing details, ask all required info at once.
Do NOT ask one question at a time — batch them together:

```
I need a few details to set up Keycloak SSO:

1. Framework: Which framework are you using? (Next.js, Vue 3, Nuxt 3, FastAPI, Django, Flask, Thymeleaf)
2. Keycloak URL: Your Keycloak server address (e.g. https://auth.company.com)
3. Realm: Realm name (e.g. my-realm)
4. Client ID: Client name (e.g. my-app)
5. Client Secret: Enter if known, or I'll use a placeholder you can fill in later.
```

After confirming the framework, recommend design systems:

```
Choose a UI design system:

Popular UI libraries for Next.js:
1. shadcn/ui — Tailwind-based, most popular (recommended)
2. MUI (Material UI) — Google Material Design
3. Ant Design — Enterprise style
4. Tailwind only — No component library
5. 🎨 Custom — provide a reference URL, image, or description

I'll build the login/dashboard pages using the selected design system's components.
If you choose custom, share a URL or image of a login page you like!
```

If the user only partially answers, follow up on the remaining items only.

### Framework Auto-Detection

If the user uploads files or shows project structure, auto-detect:
- `next.config.*` → Next.js
- `nuxt.config.*` → Nuxt 3
- `vite.config.*` + `vue` dependency → Vue 3
- `requirements.txt` or `pyproject.toml` + `fastapi` → FastAPI
- `manage.py` + `django` → Django
- `requirements.txt` + `flask` → Flask
- `pom.xml` or `build.gradle` + Thymeleaf dependency → Thymeleaf

When detected, confirm: "This looks like a Next.js project. Is that correct?"

## Generation Workflow

### Step 1: Verify All Required Info

Confirm all required fields (framework, Keycloak URL, realm, client ID) are collected.
If anything is missing, ask before generating code.

### Step 1.5: Analyze Existing Project Structure

If the user indicated this is an existing project (or if project files are accessible), actively analyze the project before generating code.

**1. Read dependency files:**

- `package.json` → installed packages, scripts, framework version
- `requirements.txt` / `pyproject.toml` → Python packages
- `pom.xml` / `build.gradle` → Java dependencies

**2. Scan directory structure:**

- Identify folder layout (e.g. `src/app/` vs `app/`, `pages/` vs App Router)
- Check for existing auth-related files (`middleware.ts`, `auth.ts`, `guards/`, `oidc/`, etc.)
- Check for existing login/logout pages
- Detect existing `.env` / `.env.local`

**3. Identify conflicts and ask before generating:**

If any of the following exist, ask the user explicitly before proceeding:

```text
Before generating, I found some existing files that may conflict:

- src/app/login/page.tsx — login page already exists
- middleware.ts — auth middleware already exists
- .env.local — environment file already exists

How would you like to handle these?
1. Overwrite — replace with newly generated files
2. Merge — I'll show a diff and you decide
3. Skip — keep existing files, only generate new ones
4. Ask me for each file individually
```

**4. Adapt generation to project conventions:**

- Match existing folder structure (don't impose new layout)
- Use already-installed package versions (don't downgrade)
- Apply version-specific logic (e.g. Next.js 15 vs 16 middleware naming)

**5. Report before generating:**

```text
Project Analysis:
- Framework: Next.js 15 (App Router, src/ layout)
- next-auth@4 already installed → will upgrade to v5
- Conflicts: login page, middleware.ts, .env.local (handling: merge)
- No existing Keycloak config found
```

### Step 2: Generate Framework-Specific Code

Read the appropriate reference file and generate code:

- Next.js → `references/nextjs.md`
- Vue 3 → `references/vue3.md`
- Nuxt 3 → `references/nuxt3.md`
- FastAPI → `references/fastapi.md`
- Django → `references/django.md`
- Flask → `references/flask.md`
- Thymeleaf → `references/thymeleaf.md`

### Step 3: Output Files

Write generated files to the appropriate project paths.
If existing files would be overwritten, suggest merge strategies instead.

### Step 4: Auto-Install Packages

Automatically install required packages after code generation.
If bash tool is available, execute directly. Otherwise, provide commands.

**Next.js + shadcn/ui:**

```bash
npm install next-auth@beta
npx shadcn@latest init
npx shadcn@latest add card button badge avatar
npx auth secret
```

**Next.js + MUI:**

```bash
npm install next-auth@beta @mui/material @emotion/react @emotion/styled
npx auth secret
```

**Next.js + Ant Design:**

```bash
npm install next-auth@beta antd @ant-design/icons
npx auth secret
```

**Next.js + Tailwind only:**

```bash
npm install next-auth@beta
npx auth secret
```

**Vue 3:**

```bash
npm install keycloak-js @josempgon/vue-keycloak
# + selected UI: npm install vuetify / primevue / element-plus / naive-ui
```

**Nuxt 3:**

```bash
npm install @sidebase/nuxt-auth next-auth@4.21.1
# + selected UI: npx nuxi module add @nuxt/ui / npm install vuetify
```

**FastAPI:**

```bash
pip install fastapi uvicorn "pyjwt[crypto]" httpx
```

**Django:**

```bash
pip install mozilla-django-oidc
# + selected UI: pip install django-crispy-forms crispy-bootstrap5
```

**Flask:**

```bash
pip install flask authlib requests
```

**Thymeleaf:**
Provide Gradle/Maven dependency snippets (cannot auto-install).

Show results after installation. Provide troubleshooting if errors occur.

### Step 5: Keycloak Environment Selection

After package installation, ask the user:

```text
Choose your Keycloak server setup:

1. 🐳 Local Docker Keycloak (recommended — test immediately, no server needed)
2. 🏢 Existing Keycloak server (your team/company already has one)
3. 📄 Code only (connect to Keycloak later)
```

#### Option 1: Local Docker Keycloak (recommended)

For users without a Keycloak server, in early development, or wanting local testing.
Only requires Docker.

**Generate these files:**

1. `docker-compose.yml`:

```yaml
version: "3.8"
services:
  keycloak:
    image: quay.io/keycloak/keycloak:latest
    environment:
      KEYCLOAK_ADMIN: admin
      KEYCLOAK_ADMIN_PASSWORD: admin
    command: start-dev --import-realm
    volumes:
      - ./keycloak/realm-export.json:/opt/keycloak/data/import/realm-export.json
    ports:
      - "8080:8080"
```

2. `keycloak/realm-export.json`:

Auto-generate from user's realm, client ID, and framework-specific redirect URIs.
Include a test user (testuser / 1234).

```json
{
  "realm": "{user input realm}",
  "enabled": true,
  "clients": [
    {
      "clientId": "{user input client ID}",
      "enabled": true,
      "publicClient": false,
      "secret": "{auto-generated or user input}",
      "redirectUris": ["{framework callback URL}/*"],
      "webOrigins": ["{framework default origin}"],
      "standardFlowEnabled": true,
      "directAccessGrantsEnabled": true
    }
  ],
  "users": [
    {
      "username": "testuser",
      "email": "test@test.com",
      "firstName": "Test",
      "lastName": "User",
      "enabled": true,
      "credentials": [{ "type": "password", "value": "1234", "temporary": false }]
    }
  ]
}
```

Framework-specific redirect URIs:

- Next.js: `http://localhost:3000/api/auth/callback/keycloak`
- Vue 3: `http://localhost:5173/*`
- Nuxt 3: `http://localhost:3000/api/auth/callback/keycloak`
- FastAPI: `http://localhost:8000/*`
- Django: `http://localhost:8000/oidc/callback/`
- Flask: `http://localhost:5000/auth/callback`
- Thymeleaf: `http://localhost:8180/login/oauth2/code/keycloak` (use port 8180 for Keycloak)

**Execution** (auto-run if bash tool available):

```bash
docker compose up -d
echo "⏳ Waiting for Keycloak..."
for i in $(seq 1 30); do
  if curl -sf http://localhost:8080/health/ready > /dev/null 2>&1; then
    echo "✅ Keycloak is ready!"
    break
  fi
  sleep 2
done
```

**Auto-update .env after startup:**

- `KEYCLOAK_URL=http://localhost:8080`
- `KEYCLOAK_REALM={input}`
- `KEYCLOAK_CLIENT_ID={input}`
- `KEYCLOAK_CLIENT_SECRET={secret from realm-export.json}`

**Final message:**

```text
✅ Setup complete!

Run: npm run dev (or framework-specific command)
Test account: testuser / 1234
Keycloak Admin: http://localhost:8080 (admin / admin)
```

#### Option 2: Existing Keycloak Server

Do NOT generate Docker files. Populate .env with user-provided values.

Provide detailed Keycloak Admin Console instructions:

1. Create/verify Client
1. Valid Redirect URIs (framework-specific callback URL)
1. Web Origins
1. Client Secret location (Credentials tab)
1. Test user creation (if needed)

#### Option 3: Code Only

Use placeholder values in .env. Advise to update later.
Note that clicking "SSO Login" will fail without a running Keycloak server.

### Step 6: Final Summary

```text
📋 Generation Complete

Framework: Next.js (App Router)
UI: shadcn/ui
Keycloak: Local Docker (http://localhost:8080)

Generated files:
  ✔ src/auth.ts
  ✔ src/middleware.ts
  ✔ src/app/login/page.tsx
  ✔ src/app/dashboard/page.tsx
  ✔ src/app/unauthorized/page.tsx
  ✔ src/app/api/auth/[...nextauth]/route.ts
  ✔ src/types/next-auth.d.ts
  ✔ .env.local
  ✔ docker-compose.yml
  ✔ keycloak/realm-export.json

Installed packages:
  ✔ next-auth@beta
  ✔ shadcn/ui (card, button, badge, avatar)

Run: npm run dev
Test account: testuser / 1234
```

## Common Environment Variable Rules

| Variable | Description | Example |
|----------|-------------|---------|
| `KEYCLOAK_URL` (or `VITE_KEYCLOAK_URL`) | Keycloak server address | `https://auth.company.com` |
| `KEYCLOAK_REALM` (or `VITE_KEYCLOAK_REALM`) | Realm name | `my-realm` |
| `KEYCLOAK_CLIENT_ID` (or `VITE_KEYCLOAK_CLIENT_ID`) | Client ID | `my-app` |
| `KEYCLOAK_CLIENT_SECRET` | Client Secret (server-side only) | `abc123...` |

Use `VITE_` or `NUXT_PUBLIC_` prefix for client-side frameworks (Vue/Nuxt).
No prefix for server-side frameworks (Next.js, Django, Flask, FastAPI, Thymeleaf).

## Keycloak Admin Console Setup Guide

Provide this for Option 2 users:

1. **Create/verify Client**
   - Client type: OpenID Connect
   - Client authentication: ON (confidential) — Next.js, Nuxt, FastAPI, Django, Flask, Thymeleaf
   - Client authentication: OFF (public) — Vue 3 (direct keycloak-js)
2. **Redirect URI**
   - Dev: `http://localhost:{port}/*` (port varies by framework)
   - Prod: `https://your-domain.com/*`
3. **Web Origins**
   - Dev: `http://localhost:{port}`
   - Or `+` for automatic matching

## Important Notes

- **Next.js 16+**: `middleware.ts` is renamed to `proxy.ts`. The generated file should be `proxy.ts` with `export function proxy()`. For Next.js 15 or earlier, use `middleware.ts` with `export function middleware()`. Always check which Next.js version the user is on.
- **next-auth / Auth.js status**: Auth.js has officially joined the Better Auth project. The `next-auth` package still works and is widely used. For Next.js + Keycloak, ask the user whether they prefer Auth.js v5 (mature Keycloak support) or Better Auth (officially recommended for new projects, but Keycloak integration is newer). Default to Auth.js v5 if the user is unsure.
- **FastAPI**: Do NOT use `python-jose` — it is abandoned (last release 2021) and broken on Python 3.10+. Use `PyJWT` (`pyjwt[crypto]`) instead. FastAPI official docs have also switched to PyJWT.
- **Nuxt 3 + sidebase/nuxt-auth**: Still works and maintained, but Auth.js joining Better Auth creates uncertainty. There is an open migration issue (#1058). For new Nuxt projects, mention this caveat and let the user decide.
- `keycloak-js` has an independent release cycle since Keycloak 26.1+. Always use the latest version.
- `keycloak-connect` (Node.js adapter) is **deprecated**. Do not use.
- This skill targets **Auth.js v5**, not NextAuth v4.
- For Vue 3, `@josempgon/vue-keycloak` is actively maintained. `@baloise/vue-keycloak` is no longer updated.
- `flask-oidc` is unmaintained. Use `Authlib` instead.
- `django-allauth` 0.56.0+ removed the dedicated Keycloak provider. Use the OpenID Connect provider.
- `fastapi-keycloak` includes admin features (user CRUD). For API auth only, plain JWT verification is lighter.
