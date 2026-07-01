export function extractGridIdFromThumbnail(url: string): string | null {
  const m = url.match(/thumbnails\/([^/]+)\/\d+\.jpg$/);
  return m?.[1] ?? null;
}

export function buildThumbnailUrl(path: string): string {
  if (!path) return "";
  if (path.startsWith("http://") || path.startsWith("https://")) return path;
  const base = (import.meta.env.VITE_API_URL as string) || "";
  const baseNorm = base.replace(/\/+$/, "");
  const pathNorm = path.startsWith("/") ? path : `/${path}`;
  return `${baseNorm}${pathNorm}`;
}

export function openCellDetails(jobId: string, cellId: string): string {
  return `/classification/${jobId}/cell/${cellId}`;
}
