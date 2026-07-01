import { useEffect, useRef, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { areaStatusApi } from "@/api/endpoints";
import { wsBaseUrl } from "@/api/client";
import { isTerminal, type AreaStatusResponse, type JobStatus } from "@/api/types";

/**
 * Real-time job progress with WebSocket primary + HTTP polling fallback.
 * - Opens ws://.../api/v1/ws/progress/{job_id}
 * - Always polls /api/v1/area-status as a safety net (stops on terminal status).
 */
export function useJobProgress(jobId: string | null) {
  const [wsMsg, setWsMsg] = useState<Partial<AreaStatusResponse> | null>(null);
  const wsRef = useRef<WebSocket | null>(null);

  const poll = useQuery({
    queryKey: ["area-status", jobId],
    queryFn: () => areaStatusApi(jobId!),
    enabled: !!jobId,
    refetchInterval: (q) => (isTerminal(q.state.data?.status) ? false : 2000),
  });

  useEffect(() => {
    setWsMsg(null);
    if (!jobId) return;
    let closed = false;
    try {
      const ws = new WebSocket(`${wsBaseUrl()}/api/v1/ws/progress/${jobId}`);
      wsRef.current = ws;
      ws.onmessage = (e) => {
        try {
          const data = JSON.parse(e.data);
          setWsMsg(data);
        } catch {
          /* ignore non-JSON */
        }
      };
      ws.onerror = () => { /* polling is the fallback */ };
      ws.onclose = () => { if (!closed) wsRef.current = null; };
    } catch {
      // WebSocket unsupported / blocked — polling continues
    }
    return () => {
      closed = true;
      wsRef.current?.close();
      wsRef.current = null;
    };
  }, [jobId]);

  const status = (poll.data?.status ?? (wsMsg as AreaStatusResponse | null)?.status) as JobStatus | undefined;
  const step = wsMsg?.step ?? poll.data?.step;
  const progress = wsMsg?.progress ?? poll.data?.progress ?? 0;
  // Get grid_id from WebSocket message or fallback polling response
  const gridId = wsMsg?.grid_id ?? poll.data?.grid_id;

  return { status, step, progress, gridId, raw: poll.data, isLoading: poll.isLoading };
}