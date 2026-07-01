import React from "react";
import { Bot, User, Copy, RefreshCw } from "lucide-react";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import MarkdownRenderer from "./MarkdownRenderer";
import type { ChatMessage } from "@/api/types";

interface Props {
  message: ChatMessage;
  onCopy: (content: string, id: string) => void;
  onRetry: (request: ChatMessage["request"]) => void;
  copiedId: string | null;
}

function AnimatedDots() {
  return (
    <span className="inline-flex gap-0.5">
      <span className="w-1.5 h-1.5 rounded-full bg-muted-foreground animate-bounce" style={{ animationDelay: "0ms" }} />
      <span className="w-1.5 h-1.5 rounded-full bg-muted-foreground animate-bounce" style={{ animationDelay: "150ms" }} />
      <span className="w-1.5 h-1.5 rounded-full bg-muted-foreground animate-bounce" style={{ animationDelay: "300ms" }} />
    </span>
  );
}

const MessageBubble = React.memo(function MessageBubble({ message, onCopy, onRetry, copiedId }: Props) {
  const isUser = message.role === "user";

  return (
    <div className={`flex gap-2 ${isUser ? "flex-row-reverse" : ""}`}>
      <Avatar className="h-7 w-7 shrink-0 mt-0.5">
        <AvatarFallback className={isUser ? "bg-muted" : "bg-primary/20 text-primary"}>
          {isUser ? <User className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
        </AvatarFallback>
      </Avatar>

      <div
        className={`max-w-[85%] rounded-lg px-3 py-2 text-sm ${
          isUser
            ? "bg-primary/20 text-foreground rounded-tr-sm"
            : message.status === "failed"
              ? "bg-destructive/10 text-foreground rounded-tl-sm"
              : "bg-secondary/60 text-foreground rounded-tl-sm"
        }`}
      >
        {message.status === "pending" ? (
          <div className="flex items-center gap-2 py-1">
            <AnimatedDots />
          </div>
        ) : message.status === "failed" ? (
          <div className="space-y-1">
            <p className="text-xs text-destructive">Request failed. Please try again.</p>
            {message.request && (
              <button
                onClick={() => onRetry(message.request)}
                className="text-xs text-destructive hover:text-destructive/80 flex items-center gap-1"
              >
                <RefreshCw className="h-3 w-3" /> Retry
              </button>
            )}
          </div>
        ) : isUser ? (
          <p className="whitespace-pre-wrap">{message.content}</p>
        ) : (
          <div>
            <MarkdownRenderer content={message.content} />
            <button
              onClick={() => onCopy(message.content, message.id)}
              className="mt-1 text-[10px] text-muted-foreground hover:text-foreground flex items-center gap-1"
            >
              {copiedId === message.id ? (
                <span className="text-primary">✓ Copied</span>
              ) : (
                <><Copy className="h-3 w-3" /> Copy</>
              )}
            </button>
          </div>
        )}
      </div>
    </div>
  );
});

export default MessageBubble;
