import { useCallback, useEffect, useRef, useState } from "react";

export interface WebSocketMessage {
  type: string;
  [key: string]: any;
}

export const useWebSocket = (
  orgId: string,
  meetingId: string,
  token: string,
  onMessage: (message: WebSocketMessage) => void
) => {
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimerRef = useRef<number | null>(null);
  const heartbeatTimerRef = useRef<number | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const [status, setStatus] = useState<"idle" | "connecting" | "open" | "closed" | "error">("idle");

  const connect = useCallback(() => {
    if (typeof window === "undefined" || !token) {
      return;
    }

    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      return;
    }

    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const wsUrl = `${protocol}//localhost:8000/ws/meetings/${orgId}/${meetingId}?token=${token}`;

    if (wsRef.current) {
      wsRef.current.close();
    }

    setStatus("connecting");

    wsRef.current = new WebSocket(wsUrl);

    wsRef.current.onopen = () => {
      console.log("WebSocket connected");
      reconnectAttemptsRef.current = 0;
      setStatus("open");

      if (heartbeatTimerRef.current) {
        window.clearInterval(heartbeatTimerRef.current);
      }
      heartbeatTimerRef.current = window.setInterval(() => {
        if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
          wsRef.current.send(JSON.stringify({ type: "ping", timestamp: new Date().toISOString() }));
        }
      }, 25000);
    };

    wsRef.current.onmessage = (event) => {
      const message = JSON.parse(event.data);
      onMessage(message);
    };

    wsRef.current.onerror = (error) => {
      console.error("WebSocket error:", error);
      setStatus("error");
    };

    wsRef.current.onclose = () => {
      console.log("WebSocket disconnected");
      setStatus("closed");

      if (heartbeatTimerRef.current) {
        window.clearInterval(heartbeatTimerRef.current);
        heartbeatTimerRef.current = null;
      }

      const attempt = reconnectAttemptsRef.current + 1;
      reconnectAttemptsRef.current = attempt;
      const delay = Math.min(15000, 1000 * Math.pow(2, attempt));

      if (reconnectTimerRef.current) {
        window.clearTimeout(reconnectTimerRef.current);
      }

      reconnectTimerRef.current = window.setTimeout(() => {
        connect();
      }, delay);
    };
  }, [orgId, meetingId, token, onMessage]);

  const send = useCallback((message: WebSocketMessage) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
    }
  }, []);

  const disconnect = useCallback(() => {
    if (reconnectTimerRef.current) {
      window.clearTimeout(reconnectTimerRef.current);
      reconnectTimerRef.current = null;
    }
    if (heartbeatTimerRef.current) {
      window.clearInterval(heartbeatTimerRef.current);
      heartbeatTimerRef.current = null;
    }
    if (wsRef.current) {
      wsRef.current.close();
    }
  }, []);

  useEffect(() => {
    if (token) {
      connect();
    }

    return () => {
      disconnect();
    };
  }, [connect, disconnect, token]);

  return { connect, send, disconnect, ws: wsRef.current, status };
};
