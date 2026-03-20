# Nuxt 3 + Keycloak

## Overview

Nuxt 3 + `sidebase/nuxt-auth` (Auth.js-based) or direct `keycloak-js` usage.
Nuxt uses SSR, so both server and client sides must be considered.

> **⚠️ Note on Auth.js → Better Auth migration:** Auth.js has joined the Better Auth project. There is an open issue on sidebase/nuxt-auth to migrate to Better Auth (#1058). As of early 2026, sidebase/nuxt-auth still works and is maintained, but the long-term direction is uncertain. If starting a brand new Nuxt project and comfortable with early-stage integration, consider using Better Auth directly with Nuxt (via `better-auth` npm package). Otherwise, sidebase/nuxt-auth remains the most battle-tested option for Keycloak + Nuxt.

**Two approaches:**
1. `@sidebase/nuxt-auth` — Integrates Auth.js into Nuxt. Server-side session management. (recommended)
2. `keycloak-js` direct usage — Client-side only. Suitable for SPA mode.

Default to Option 1. If the user wants client-side only, use Option 2.

## Option 1: sidebase/nuxt-auth (recommended)

### Required Packages

```bash
npm install @sidebase/nuxt-auth next-auth@4.21.1
```

> sidebase/nuxt-auth is based on NextAuth v4, NOT Auth.js v5.

### Environment Variables (.env)

```env
KEYCLOAK_URL=https://auth.company.com
KEYCLOAK_REALM=my-realm
KEYCLOAK_CLIENT_ID=my-app
KEYCLOAK_CLIENT_SECRET=your-client-secret

NUXT_AUTH_SECRET=your-random-secret
NEXTAUTH_URL=http://localhost:3000
```

### nuxt.config.ts

```typescript
export default defineNuxtConfig({
  modules: ["@sidebase/nuxt-auth"],
  auth: {
    baseURL: process.env.NEXTAUTH_URL,
    provider: {
      type: "authjs",
    },
  },
});
```

### server/api/auth/[...].ts — Auth Handler

```typescript
import { NuxtAuthHandler } from "#auth";
import KeycloakProvider from "next-auth/providers/keycloak";

export default NuxtAuthHandler({
  secret: process.env.NUXT_AUTH_SECRET,
  providers: [
    // @ts-expect-error — nextauth v4 type compat
    KeycloakProvider.default({
      clientId: process.env.KEYCLOAK_CLIENT_ID!,
      clientSecret: process.env.KEYCLOAK_CLIENT_SECRET!,
      issuer: `${process.env.KEYCLOAK_URL}/realms/${process.env.KEYCLOAK_REALM}`,
    }),
  ],
  callbacks: {
    async jwt({ token, account }) {
      if (account) {
        token.accessToken = account.access_token;
        token.refreshToken = account.refresh_token;
        token.accessTokenExpires = (account.expires_at ?? 0) * 1000;
        token.idToken = account.id_token;
      }

      // Token still valid — return as-is
      if (Date.now() < (token.accessTokenExpires as number)) {
        return token;
      }

      // Expired — refresh
      return await refreshAccessToken(token);
    },
    async session({ session, token }) {
      session.accessToken = token.accessToken as string;
      session.error = token.error as string | undefined;
      return session;
    },
  },
});

async function refreshAccessToken(token: any) {
  try {
    const url = `${process.env.KEYCLOAK_URL}/realms/${process.env.KEYCLOAK_REALM}/protocol/openid-connect/token`;

    const response = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: new URLSearchParams({
        client_id: process.env.KEYCLOAK_CLIENT_ID!,
        client_secret: process.env.KEYCLOAK_CLIENT_SECRET!,
        grant_type: "refresh_token",
        refresh_token: token.refreshToken,
      }),
    });

    const refreshed = await response.json();
    if (!response.ok) throw refreshed;

    return {
      ...token,
      accessToken: refreshed.access_token,
      accessTokenExpires: Date.now() + refreshed.expires_in * 1000,
      refreshToken: refreshed.refresh_token ?? token.refreshToken,
    };
  } catch (error) {
    return { ...token, error: "RefreshAccessTokenError" };
  }
}
```

### pages/login.vue — Login Page

```vue
<script setup lang="ts">
const { signIn, status } = useAuth();

// Already authenticated → redirect to dashboard
if (status.value === "authenticated") {
  navigateTo("/dashboard");
}
</script>

<template>
  <div class="min-h-screen flex items-center justify-center bg-gray-50">
    <div class="max-w-md w-full space-y-8 p-8 bg-white rounded-lg shadow">
      <div class="text-center">
        <h2 class="text-3xl font-bold text-gray-900">Login</h2>
        <p class="mt-2 text-sm text-gray-600">
          Sign in with your company SSO account
        </p>
      </div>
      <button
        @click="signIn('keycloak', { callbackUrl: '/dashboard' })"
        class="w-full py-3 px-4 rounded-md text-white bg-blue-600 hover:bg-blue-700 transition-colors"
      >
        Sign in with SSO
      </button>
    </div>
  </div>
</template>
```

### pages/dashboard.vue — Dashboard

```vue
<script setup lang="ts">
definePageMeta({ middleware: "auth" });

const { data, signOut } = useAuth();
</script>

<template>
  <div class="min-h-screen bg-gray-50 p-8">
    <div class="max-w-4xl mx-auto">
      <div class="bg-white rounded-lg shadow p-6">
        <div class="flex justify-between items-center mb-6">
          <h1 class="text-2xl font-bold">Dashboard</h1>
          <button
            @click="signOut({ callbackUrl: '/login' })"
            class="px-4 py-2 bg-red-500 text-white rounded-md hover:bg-red-600 transition-colors"
          >
            Sign out
          </button>
        </div>
        <div v-if="data" class="space-y-3">
          <p>
            <span class="font-medium">Name:</span>
            {{ data.user?.name }}
          </p>
          <p>
            <span class="font-medium">Email:</span>
            {{ data.user?.email }}
          </p>
        </div>
      </div>
    </div>
  </div>
</template>
```

### middleware/auth.ts — Auth Middleware

```typescript
export default defineNuxtRouteMiddleware((to, from) => {
  const { status } = useAuth();

  if (status.value === "unauthenticated") {
    return navigateTo("/login");
  }
});
```

## Option 2: keycloak-js Direct Usage (SPA mode)

Only suitable when using Nuxt with `ssr: false`.

### Required Packages

```bash
npm install keycloak-js
```

### plugins/keycloak.client.ts

`.client.ts` suffix ensures this runs client-side only:

```typescript
import Keycloak from "keycloak-js";

export default defineNuxtPlugin(async () => {
  const keycloak = new Keycloak({
    url: useRuntimeConfig().public.keycloakUrl,
    realm: useRuntimeConfig().public.keycloakRealm,
    clientId: useRuntimeConfig().public.keycloakClientId,
  });

  await keycloak.init({
    onLoad: "check-sso",
    checkLoginIframe: false,
  });

  // Auto token refresh
  setInterval(() => {
    keycloak.updateToken(30).catch(() => keycloak.logout());
  }, 10000);

  return {
    provide: { keycloak },
  };
});
```

### nuxt.config.ts (Option 2)

```typescript
export default defineNuxtConfig({
  ssr: false,
  runtimeConfig: {
    public: {
      keycloakUrl: process.env.NUXT_PUBLIC_KEYCLOAK_URL,
      keycloakRealm: process.env.NUXT_PUBLIC_KEYCLOAK_REALM,
      keycloakClientId: process.env.NUXT_PUBLIC_KEYCLOAK_CLIENT_ID,
    },
  },
});
```

## Keycloak Client Configuration

**Option 1 (sidebase/nuxt-auth):**

| Setting | Value |
|---------|-------|
| Client authentication | ON (confidential) |
| Valid redirect URIs | `http://localhost:3000/api/auth/callback/keycloak` |
| Web origins | `http://localhost:3000` |

**Option 2 (keycloak-js):**

| Setting | Value |
|---------|-------|
| Client authentication | OFF (public) |
| Valid redirect URIs | `http://localhost:3000/*` |
| Web origins | `http://localhost:3000` |

## Troubleshooting

**`KeycloakProvider.default is not a function`**
→ In Nuxt 3, you may need to append `.default` when using NextAuth providers

**Hydration mismatch error**
→ For conditional rendering based on auth state, use `<ClientOnly>` wrapper

**`useAuth()` undefined**
→ Verify `@sidebase/nuxt-auth` module is registered in `nuxt.config.ts`
