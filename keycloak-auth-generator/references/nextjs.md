# Next.js + Keycloak

## Overview

Next.js App Router + Keycloak SSO integration.
Server-side auth, so Client authentication must be ON (confidential client).

**Two auth library options:**

1. **Auth.js v5 (next-auth)** — Mature, well-documented Keycloak integration. Still works and widely used.
   - Install: `npm install next-auth@beta` (v5 is still under beta tag on npm)
   - Auth.js has been merged into the Better Auth project, but the `next-auth` package continues to work.

2. **Better Auth** (recommended for new projects) — The Auth.js team officially recommends Better Auth for new projects.
   - Install: `npm install better-auth`
   - Keycloak support via `genericOAuth` plugin with built-in `keycloak()` config.
   - ⚠️ **Caveat**: Keycloak + Next.js App Router integration with Better Auth is still relatively new. Full examples for token refresh, federated logout, and RBAC are limited as of early 2026.

**Default recommendation:**
- **Existing projects** already using next-auth → Stay with Auth.js v5 (Option 1)
- **New projects** → Ask the user which they prefer. If unsure, Auth.js v5 is the safer choice for Keycloak specifically due to mature documentation and community examples.

When the user selects Next.js, ask:

```
Which auth library would you like to use?

1. Auth.js (next-auth) — Mature Keycloak support, extensive docs (recommended if unsure)
2. Better Auth — Officially recommended for new projects, but Keycloak integration is newer

Both work with Keycloak. Auth.js has more battle-tested Keycloak examples.
```

---

## Option 1: Auth.js v5 (next-auth)

## Required Packages

```bash
npm install next-auth@beta
```

> Auth.js v5 is still published under the `beta` tag on npm as of early 2026. The API is stable and widely used in production. Install with `next-auth@beta` until the stable tag is released. If a stable version is already available when you read this, use `npm install next-auth` instead.

> **Next.js 16+ users:** The generated file is `proxy.ts` (not `middleware.ts`). If using Next.js 15 or earlier, rename it to `middleware.ts`.

## Environment Variables (.env.local)

```env
# Keycloak
KEYCLOAK_URL=https://auth.company.com
KEYCLOAK_REALM=my-realm
KEYCLOAK_CLIENT_ID=my-app
KEYCLOAK_CLIENT_SECRET=your-client-secret

# Auth.js
AUTH_SECRET=                    # generate with: npx auth secret
NEXTAUTH_URL=http://localhost:3000
AUTH_TRUST_HOST=true
```

Auth.js v5 auto-recognizes `AUTH_KEYCLOAK_ID`, `AUTH_KEYCLOAK_SECRET`, `AUTH_KEYCLOAK_ISSUER`, so you can omit values in provider code:

```env
AUTH_KEYCLOAK_ID=my-app
AUTH_KEYCLOAK_SECRET=your-client-secret
AUTH_KEYCLOAK_ISSUER=https://auth.company.com/realms/my-realm
```

## Generated Files

### 1. `src/auth.ts` — Auth.js Config (core)

```typescript
import NextAuth from "next-auth";
import Keycloak from "next-auth/providers/keycloak";
import type { JWT } from "next-auth/jwt";

async function refreshAccessToken(token: JWT): Promise<JWT> {
  try {
    const url = `${process.env.KEYCLOAK_URL}/realms/${process.env.KEYCLOAK_REALM}/protocol/openid-connect/token`;

    const response = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: new URLSearchParams({
        client_id: process.env.KEYCLOAK_CLIENT_ID!,
        client_secret: process.env.KEYCLOAK_CLIENT_SECRET!,
        grant_type: "refresh_token",
        refresh_token: token.refreshToken as string,
      }),
    });

    const refreshedTokens = await response.json();
    if (!response.ok) throw refreshedTokens;

    return {
      ...token,
      accessToken: refreshedTokens.access_token,
      accessTokenExpires: Date.now() + refreshedTokens.expires_in * 1000,
      refreshToken: refreshedTokens.refresh_token ?? token.refreshToken,
      idToken: refreshedTokens.id_token ?? token.idToken,
    };
  } catch (error) {
    console.error("Error refreshing access token:", error);
    return { ...token, error: "RefreshAccessTokenError" };
  }
}

export const { handlers, signIn, signOut, auth } = NextAuth({
  providers: [
    Keycloak({
      clientId: process.env.KEYCLOAK_CLIENT_ID!,
      clientSecret: process.env.KEYCLOAK_CLIENT_SECRET!,
      issuer: `${process.env.KEYCLOAK_URL}/realms/${process.env.KEYCLOAK_REALM}`,
    }),
  ],
  callbacks: {
    async jwt({ token, account }) {
      // Initial login: save token info from account
      if (account) {
        return {
          ...token,
          accessToken: account.access_token,
          accessTokenExpires: (account.expires_at ?? 0) * 1000,
          refreshToken: account.refresh_token,
          idToken: account.id_token,
        };
      }

      // Token still valid — return as-is
      if (Date.now() < (token.accessTokenExpires as number)) {
        return token;
      }

      // Expired — refresh
      return refreshAccessToken(token);
    },

    async session({ session, token }) {
      session.accessToken = token.accessToken as string;
      session.error = token.error as string | undefined;
      return session;
    },
  },
  events: {
    // Fully terminate Keycloak session (federated logout)
    async signOut(message) {
      if ("token" in message) {
        const idToken = message.token?.idToken;
        if (idToken) {
          const logoutUrl = `${process.env.KEYCLOAK_URL}/realms/${process.env.KEYCLOAK_REALM}/protocol/openid-connect/logout?id_token_hint=${idToken}`;
          await fetch(logoutUrl);
        }
      }
    },
  },
});
```

### 2. `src/app/api/auth/[...nextauth]/route.ts` — API Route

```typescript
import { handlers } from "@/auth";
export const { GET, POST } = handlers;
```

### 3. `src/proxy.ts` — Proxy (replaces middleware.ts since Next.js 16)

> **Note:** As of Next.js 16, `middleware.ts` has been renamed to `proxy.ts` and the exported function is `proxy` instead of `middleware`. If using Next.js 15 or earlier, rename the file back to `middleware.ts` and the function to `middleware`.

```typescript
import { auth } from "@/auth";
import { NextResponse } from "next/server";

export default auth((req) => {
  const isLoggedIn = !!req.auth;
  const isOnLoginPage = req.nextUrl.pathname === "/login";

  // Public paths — customize for your project
  const publicPaths = ["/", "/about", "/api/auth"];
  const isPublicPath = publicPaths.some((path) =>
    req.nextUrl.pathname.startsWith(path)
  );

  if (!isLoggedIn && !isPublicPath && !isOnLoginPage) {
    return NextResponse.redirect(new URL("/login", req.nextUrl.origin));
  }

  if (isLoggedIn && isOnLoginPage) {
    return NextResponse.redirect(new URL("/dashboard", req.nextUrl.origin));
  }

  return NextResponse.next();
});

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico).*)"],
};
```

### 4. `src/app/login/page.tsx` — Login Page

```tsx
import { signIn } from "@/auth";

export default function LoginPage() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="max-w-md w-full space-y-8 p-8 bg-white rounded-lg shadow">
        <div className="text-center">
          <h2 className="text-3xl font-bold text-gray-900">Login</h2>
          <p className="mt-2 text-sm text-gray-600">
            Sign in with your company SSO account
          </p>
        </div>
        <form
          action={async () => {
            "use server";
            await signIn("keycloak", { redirectTo: "/dashboard" });
          }}
        >
          <button
            type="submit"
            className="w-full flex justify-center py-3 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors"
          >
            Sign in with SSO
          </button>
        </form>
      </div>
    </div>
  );
}
```

### 5. `src/app/dashboard/page.tsx` — Dashboard (with logout)

```tsx
import { auth, signOut } from "@/auth";
import { redirect } from "next/navigation";

export default async function DashboardPage() {
  const session = await auth();

  if (!session) redirect("/login");
  if (session.error === "RefreshAccessTokenError") redirect("/login");

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-4xl mx-auto">
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex justify-between items-center mb-6">
            <h1 className="text-2xl font-bold">Dashboard</h1>
            <form
              action={async () => {
                "use server";
                await signOut({ redirectTo: "/login" });
              }}
            >
              <button
                type="submit"
                className="px-4 py-2 bg-red-500 text-white rounded-md hover:bg-red-600 transition-colors"
              >
                Sign out
              </button>
            </form>
          </div>
          <div className="space-y-3">
            <p>
              <span className="font-medium text-gray-700">Name:</span>{" "}
              {session.user?.name ?? "Unknown"}
            </p>
            <p>
              <span className="font-medium text-gray-700">Email:</span>{" "}
              {session.user?.email ?? "Unknown"}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
```

### 6. `src/types/next-auth.d.ts` — Type Extensions

```typescript
import "next-auth";

declare module "next-auth" {
  interface Session {
    accessToken?: string;
    error?: string;
  }
}

declare module "next-auth/jwt" {
  interface JWT {
    accessToken?: string;
    accessTokenExpires?: number;
    refreshToken?: string;
    idToken?: string;
    error?: string;
  }
}
```

## Adding RBAC (Role-Based Access Control)

When the user requests RBAC, add role extraction to the jwt callback in `auth.ts`:

```typescript
// Inside jwt callback
async jwt({ token, account, profile }) {
  if (account) {
    // Extract roles from Keycloak token
    const accessTokenParsed = JSON.parse(
      Buffer.from(account.access_token!.split(".")[1], "base64").toString()
    );
    token.roles = accessTokenParsed.realm_access?.roles ?? [];
  }
  // ... existing logic
},

async session({ session, token }) {
  session.roles = token.roles as string[];
  // ... existing logic
},
```

Add to types:

```typescript
declare module "next-auth" {
  interface Session {
    accessToken?: string;
    error?: string;
    roles?: string[];
  }
}
```

Check roles in proxy (or middleware for Next.js 15):

```typescript
// In proxy.ts (or middleware.ts for Next.js 15)
// Specific path requires role
if (req.nextUrl.pathname.startsWith("/admin")) {
  const session = req.auth;
  const roles = (session as any)?.roles ?? [];
  if (!roles.includes("admin")) {
    return NextResponse.redirect(new URL("/unauthorized", req.nextUrl.origin));
  }
}
```

## Keycloak Client Configuration

| Setting | Value |
|---------|-------|
| Client type | OpenID Connect |
| Client authentication | ON |
| Valid redirect URIs | `http://localhost:3000/api/auth/callback/keycloak` (dev) |
| Web origins | `http://localhost:3000` |
| Post logout redirect URIs | `http://localhost:3000` |

## Troubleshooting

**"Invalid redirect_uri" error**
→ Add `http://localhost:3000/*` to Valid Redirect URIs in Keycloak Admin Console

**"CORS error"**
→ Add `http://localhost:3000` to Web origins, or enter `+`

**Token refresh failed**
→ Verify Client Secret. Check Realm Settings → Tokens for Refresh Token lifespan

**AUTH_SECRET not set**
→ Run `npx auth secret`, then add to `.env.local`

---

## Option 2: Better Auth

### Required Packages

```bash
npm install better-auth
```

### Environment Variables (.env.local)

```env
KEYCLOAK_URL=https://auth.company.com
KEYCLOAK_REALM=my-realm
KEYCLOAK_CLIENT_ID=my-app
KEYCLOAK_CLIENT_SECRET=your-client-secret

BETTER_AUTH_SECRET=your-secret-here
BETTER_AUTH_URL=http://localhost:3000
```

### Generated Files

#### 1. `src/lib/auth.ts` — Better Auth Config

```typescript
import { betterAuth } from "better-auth";
import { genericOAuth, keycloak } from "better-auth/plugins";

export const auth = betterAuth({
  secret: process.env.BETTER_AUTH_SECRET,
  baseURL: process.env.BETTER_AUTH_URL,
  plugins: [
    genericOAuth({
      config: [
        keycloak({
          clientId: process.env.KEYCLOAK_CLIENT_ID!,
          clientSecret: process.env.KEYCLOAK_CLIENT_SECRET!,
          issuer: `${process.env.KEYCLOAK_URL}/realms/${process.env.KEYCLOAK_REALM}`,
        }),
      ],
    }),
  ],
});
```

#### 2. `src/lib/auth-client.ts` — Client-side Auth

```typescript
import { createAuthClient } from "better-auth/react";
import { genericOAuthClient } from "better-auth/client/plugins";

export const { signIn, signOut, useSession, getSession } = createAuthClient({
  baseURL: process.env.NEXT_PUBLIC_BETTER_AUTH_URL,
  plugins: [genericOAuthClient()],
});
```

#### 3. `src/app/api/auth/[...all]/route.ts` — API Route

```typescript
import { toNextJsHandler } from "better-auth/next-js";
import { auth } from "@/lib/auth";

export const { GET, POST } = toNextJsHandler(auth);
```

#### 4. `src/proxy.ts` — Proxy (Next.js 16+)

```typescript
import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";
import { auth } from "@/lib/auth";
import { headers } from "next/headers";

export async function proxy(request: NextRequest) {
  const session = await auth.api.getSession({
    headers: await headers(),
  });

  const isOnLoginPage = request.nextUrl.pathname === "/login";
  const publicPaths = ["/", "/about", "/api/auth"];
  const isPublicPath = publicPaths.some((path) =>
    request.nextUrl.pathname.startsWith(path)
  );

  if (!session && !isPublicPath && !isOnLoginPage) {
    return NextResponse.redirect(new URL("/login", request.url));
  }

  if (session && isOnLoginPage) {
    return NextResponse.redirect(new URL("/dashboard", request.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico).*)"],
};
```

#### 5. Login/Dashboard Pages

Login and dashboard pages follow the same UI pattern as Option 1, but use Better Auth's `signIn` and `signOut` from `@/lib/auth-client` instead of `@/auth`.

```tsx
// src/app/login/page.tsx
"use client";
import { signIn } from "@/lib/auth-client";

export default function LoginPage() {
  return (
    <button onClick={() => signIn.social({ provider: "keycloak" })}>
      Sign in with SSO
    </button>
  );
}
```

```tsx
// src/app/dashboard/page.tsx
"use client";
import { useSession, signOut } from "@/lib/auth-client";

export default function DashboardPage() {
  const { data: session } = useSession();
  // ... render user info and sign out button
}
```

### Important Notes for Better Auth + Keycloak

- Better Auth's Keycloak integration uses the `genericOAuth` plugin with a built-in `keycloak()` helper.
- Token refresh, federated logout, and RBAC patterns are still evolving. Check Better Auth docs for the latest.
- If you need advanced Keycloak features (federated logout, token introspection, role mapping), Auth.js v5 currently has more documented patterns.
- Better Auth requires a database by default. For stateless JWT sessions (no database), Auth.js v5 may be a better fit.
