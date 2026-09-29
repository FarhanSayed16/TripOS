import { mergeProps } from "@base-ui/react/merge-props"
import { useRender } from "@base-ui/react/use-render"
import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "cn"

const badgeVariants = cva(
  "group/badge inline-flex h-5 w-fit shrink-0 items-center justify-center gap-1 overflow-hidden rounded-4xl border border-transparent px-2 py-0.5 text-xs font-medium whitespace-nowrap transition-all focus-visible:border-ring focus-visible:ring-[3px] focus-visible:ring-ring/50 has-data-[icon=inline-end]:pr-1.5 has-data-[icon=inline-start]:pl-1.5 aria-invalid:border-destructive aria-invalid:ring-destructive/20 dark:aria-invalid:ring-destructive/40 [&>svg]:pointer-events-none [&>svg]:size-3!",
  {
    variants: {
      variant: {
        default: "bg-primary text-primary-foreground [a]:hover:bg-primary/80",
        secondary:
          "bg-secondary text-secondary-foreground [a]:hover:bg-secondary/80",
        destructive:
          "bg-destructive/10 text-destructive focus-visible:ring-destructive/20 dark:bg-destructive/20 dark:focus-visible:ring-destructive/40 [a]:hover:bg-destructive/20",
        outline:
          "border-border text-foreground [a]:hover:bg-muted [a]:hover:text-muted-foreground",
        ghost:
          "hover:bg-muted hover:text-muted-foreground dark:hover:bg-muted/50",
        link: "text-primary underline-offset-4 hover:underline",
        /* ── Semantic status variants ── */
        confirmed:
          "bg-emerald-50 text-emerald-700 border-emerald-200 status-dot",
        active:
          "bg-emerald-50 text-emerald-700 border-emerald-200 status-dot",
        pending:
          "bg-amber-50 text-amber-700 border-amber-200 status-dot",
        draft:
          "bg-slate-50 text-slate-600 border-slate-200 status-dot",
        failed:
          "bg-red-50 text-red-700 border-red-200 status-dot",
        expired:
          "bg-red-50 text-red-600 border-red-200 status-dot",
        sent:
          "bg-blue-50 text-blue-700 border-blue-200 status-dot",
        ready:
          "bg-blue-50 text-blue-700 border-blue-200 status-dot",
        paid:
          "bg-teal/5 text-teal border-teal/20 status-dot",
        captured:
          "bg-teal/5 text-teal border-teal/20 status-dot",
        cancelled:
          "bg-surface text-muted-foreground border-line status-dot",
        refunded:
          "bg-violet-50 text-violet-700 border-violet-200 status-dot",
        live:
          "bg-teal/10 text-teal-dark border-teal/20 status-dot",
        simulated:
          "bg-blue-50 text-blue-700 border-blue-200 status-dot",
        mock:
          "bg-amber-50 text-amber-700 border-amber-200 status-dot",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
)

function Badge({
  className,
  variant = "default",
  render,
  ...props
}: useRender.ComponentProps<"span"> & VariantProps<typeof badgeVariants>) {
  return useRender({
    defaultTagName: "span",
    props: mergeProps<"span">(
      {
        className: cn(badgeVariants({ variant }), className),
      },
      props
    ),
    render,
    state: {
      slot: "badge",
      variant,
    },
  })
}

export { Badge, badgeVariants }
