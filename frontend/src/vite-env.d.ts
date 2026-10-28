/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** Optional override for the API base URL. Defaults to "/api" (proxied in dev). */
  readonly VITE_API_BASE?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
