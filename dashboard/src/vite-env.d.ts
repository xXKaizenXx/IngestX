/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_URL: string;
  readonly VITE_WS_URL: string;
  readonly VITE_STREAM_TOKEN: string;
  readonly VITE_MERCHANT_ID: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
