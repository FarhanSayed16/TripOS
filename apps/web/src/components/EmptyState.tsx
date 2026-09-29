import Link from "next/link";
import { ReactNode } from "react";
import { cn } from "@/lib/utils";

type EmptyStateProps = {
  title: string;
  description?: string;
  icon?: ReactNode;
  actionLabel?: string;
  actionHref?: string;
  onAction?: () => void;
  className?: string;
};

export function EmptyState({
  title,
  description,
  icon,
  actionLabel,
  actionHref,
  onAction,
  className,
}: EmptyStateProps) {
  return (
    <div
      className={cn(
        "empty-state-container animate-scale-in",
        className
      )}
    >
      {icon ? (
        <div className="text-teal/30 mb-3">
          {icon}
        </div>
      ) : null}
      <h3 className="font-display text-xl text-ink tracking-tight">{title}</h3>
      {description ? (
        <p className="text-sm text-muted-foreground max-w-sm mt-1 leading-relaxed">{description}</p>
      ) : null}
      {actionLabel && actionHref ? (
        <Link
          href={actionHref}
          className="mt-4 inline-flex items-center gap-2 btn-gradient rounded-lg px-5 py-2.5 text-sm font-medium text-white no-underline"
        >
          {actionLabel}
        </Link>
      ) : null}
      {actionLabel && onAction && !actionHref ? (
        <button
          type="button"
          onClick={onAction}
          className="mt-4 inline-flex items-center gap-2 btn-gradient rounded-lg px-5 py-2.5 text-sm font-medium text-white"
        >
          {actionLabel}
        </button>
      ) : null}
    </div>
  );
}
