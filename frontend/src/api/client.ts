import axios, { AxiosError } from "axios";
import { toast } from "@/hooks/use-toast";

const baseURL = import.meta.env.VITE_API_URL as string | undefined;

if (!baseURL && import.meta.env.DEV) {
  // eslint-disable-next-line no-console
  console.warn("[api] VITE_API_URL is not set — API calls will fail. Add it to .env");
}

export const api = axios.create({
  baseURL: baseURL ?? "/",
  timeout: 60_000,
});

export const wsBaseUrl = (): string => {
  const explicit = import.meta.env.VITE_WS_URL as string | undefined;
  if (explicit) return explicit.replace(/\/+$/, "");
  const base = baseURL ?? window.location.origin;
  return base.replace(/^http/i, (m) => (m.toLowerCase() === "https" ? "wss" : "ws")).replace(/\/+$/, "");
};

/** Centralized error → toast mapping. Returns the original error so callers can still react. */
api.interceptors.response.use(
  (r) => r,
  (err: AxiosError<{ detail?: string; message?: string }>) => {
    const status = err.response?.status;
    const detail = err.response?.data?.detail || err.response?.data?.message;
    let title = "Request failed";
    let description = detail || err.message;
    switch (status) {
      case 404: title = "Resource not found"; break;
      case 413: title = "File too large"; description = detail || "Upload exceeds server limit"; break;
      case 415: title = "Unsupported file type"; description = detail || "Server rejected the file type"; break;
      case 500: title = "Server error"; description = detail || "Try again in a moment"; break;
      case 501: title = "Coming soon"; description = detail || "This feature is not implemented yet"; break;
      default:
        if (!status) { title = "Network error"; description = "Could not reach backend"; }
    }
    toast({ title, description, variant: status === 501 ? "default" : "destructive" });
    return Promise.reject(err);
  }
);