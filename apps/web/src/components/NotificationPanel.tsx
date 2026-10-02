"use client";

import { useState, useRef, useEffect } from "react";
import { Bell, CheckCheck, AlertTriangle, CheckCircle2, CreditCard, Clock, Info, Plane, X } from "lucide-react";
import { useGetNotificationsQuery, useGetUnreadCountQuery, useMarkReadMutation, useMarkAllReadMutation, Notification } from "@/lib/api/notificationsApi";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";

function timeAgo(dateStr: string): string {
  const now = Date.now();
  const then = new Date(dateStr).getTime();
  const diffMs = now - then;
  const minutes = Math.floor(diffMs / 60000);
  if (minutes < 1) return "Just now";
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  return `${days}d ago`;
}

const iconMap: Record<string, React.ReactNode> = {
  "alert-triangle": <AlertTriangle className="w-4 h-4" />,
  "check-circle": <CheckCircle2 className="w-4 h-4" />,
  "credit-card": <CreditCard className="w-4 h-4" />,
  "clock": <Clock className="w-4 h-4" />,
  "plane": <Plane className="w-4 h-4" />,
  "info": <Info className="w-4 h-4" />,
  "bell": <Bell className="w-4 h-4" />,
};

const severityStyles: Record<string, { bg: string; text: string; dot: string }> = {
  error:   { bg: "bg-coral/10",  text: "text-coral",  dot: "bg-coral" },
  warning: { bg: "bg-amber-50",  text: "text-amber-600", dot: "bg-amber-400" },
  success: { bg: "bg-mint/10",   text: "text-mint",   dot: "bg-mint" },
  info:    { bg: "bg-teal/10",   text: "text-teal",   dot: "bg-teal" },
};

function NotificationItem({ notification, onRead }: { notification: Notification; onRead: (n: Notification) => void }) {
  const style = severityStyles[notification.severity] || severityStyles.info;

  return (
    <button
      type="button"
      onClick={() => onRead(notification)}
      className={`w-full text-left px-4 py-3 flex gap-3 items-start hover:bg-sand/50 transition-colors ${
        notification.is_read ? "opacity-60" : ""
      }`}
    >
      <div className={`w-8 h-8 rounded-lg ${style.bg} ${style.text} flex items-center justify-center flex-shrink-0 mt-0.5`}>
        {iconMap[notification.icon] || iconMap.bell}
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-start justify-between gap-2">
          <p className={`text-sm font-medium text-ink leading-tight ${notification.is_read ? "" : "font-semibold"}`}>
            {notification.title}
          </p>
          {!notification.is_read && (
            <div className={`w-2 h-2 rounded-full ${style.dot} flex-shrink-0 mt-1.5`} />
          )}
        </div>
        {notification.body && (
          <p className="text-xs text-muted-foreground mt-0.5 line-clamp-2">{notification.body}</p>
        )}
        <span className="text-[10px] text-muted-foreground/70 mt-1 block">
          {timeAgo(notification.created_at)}
        </span>
      </div>
    </button>
  );
}

export function NotificationPanel() {
  const [open, setOpen] = useState(false);
  const panelRef = useRef<HTMLDivElement>(null);
  const router = useRouter();

  const { data: notifications = [], isLoading } = useGetNotificationsQuery(
    { limit: 20 },
    { pollingInterval: 30000 }
  );
  const { data: unreadData } = useGetUnreadCountQuery(undefined, {
    pollingInterval: 15000,
  });
  const [markRead] = useMarkReadMutation();
  const [markAllRead] = useMarkAllReadMutation();

  const unreadCount = unreadData?.count ?? 0;

  // Close on outside click
  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (panelRef.current && !panelRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    if (open) {
      document.addEventListener("mousedown", handleClickOutside);
      return () => document.removeEventListener("mousedown", handleClickOutside);
    }
  }, [open]);

  const handleRead = async (notification: Notification) => {
    if (!notification.is_read) {
      await markRead(notification.id);
    }
    if (notification.link) {
      router.push(notification.link);
      setOpen(false);
    }
  };

  return (
    <div className="relative" ref={panelRef}>
      {/* Bell Trigger */}
      <button
        type="button"
        onClick={() => setOpen(!open)}
        className="relative p-2 rounded-full hover:bg-muted/50 transition-colors"
        aria-label={unreadCount > 0 ? `${unreadCount} unread notifications` : "Notifications"}
      >
        <Bell className="h-4 w-4 text-ink" />
        {unreadCount > 0 && (
          <span className="absolute -top-0.5 -right-0.5 min-w-[18px] h-[18px] flex items-center justify-center rounded-full bg-coral text-white text-[10px] font-bold px-1 border-2 border-surface">
            {unreadCount > 99 ? "99+" : unreadCount}
          </span>
        )}
      </button>

      {/* Dropdown Panel */}
      {open && (
        <div className="absolute right-0 top-full mt-2 w-[380px] max-h-[480px] bg-paper border border-line rounded-xl shadow-xl z-50 overflow-hidden animate-in fade-in slide-in-from-top-2 duration-200">
          {/* Header */}
          <div className="flex items-center justify-between px-4 py-3 border-b border-line bg-surface/50">
            <h3 className="text-sm font-semibold text-ink">Notifications</h3>
            <div className="flex items-center gap-2">
              {unreadCount > 0 && (
                <Button
                  variant="ghost"
                  size="sm"
                  className="text-xs h-7 gap-1 text-teal hover:text-teal-dark"
                  onClick={async () => {
                    await markAllRead();
                  }}
                >
                  <CheckCheck className="w-3.5 h-3.5" />
                  Mark all read
                </Button>
              )}
              <button
                type="button"
                onClick={() => setOpen(false)}
                className="p-1 rounded hover:bg-muted/50 transition-colors"
              >
                <X className="w-4 h-4 text-muted-foreground" />
              </button>
            </div>
          </div>

          {/* List */}
          <div className="overflow-y-auto max-h-[400px] divide-y divide-line/50">
            {isLoading ? (
              <div className="p-8 text-center text-sm text-muted-foreground">
                Loading...
              </div>
            ) : notifications.length === 0 ? (
              <div className="p-8 text-center">
                <Bell className="w-8 h-8 mx-auto mb-3 text-muted-foreground/20" />
                <p className="text-sm font-medium text-muted-foreground">You're all caught up!</p>
                <p className="text-xs text-muted-foreground/60 mt-1">No notifications yet.</p>
              </div>
            ) : (
              notifications.map((n) => (
                <NotificationItem key={n.id} notification={n} onRead={handleRead} />
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
}
