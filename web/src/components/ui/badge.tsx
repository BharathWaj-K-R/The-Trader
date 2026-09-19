import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "@/lib/utils"

const badgeVariants = cva(
  "inline-flex items-center rounded-md border px-2 py-0.5 text-[11px] font-medium tracking-wide transition-colors",
  {
    variants: {
      variant: {
        default: "border-zinc-700 bg-zinc-100 text-zinc-900 dark:border-zinc-600 dark:bg-zinc-200 dark:text-zinc-900",
        secondary: "border-zinc-800 bg-zinc-900 text-zinc-300",
        outline: "border-zinc-700 bg-transparent text-zinc-400",
        success: "border-zinc-600 bg-zinc-800 text-zinc-100",
        danger: "border-zinc-600 bg-zinc-100 text-zinc-900",
        warning: "border-zinc-600 bg-zinc-700 text-zinc-100",
      },
    },
    defaultVariants: { variant: "default" },
  },
)

export interface BadgeProps extends React.HTMLAttributes<HTMLDivElement>, VariantProps<typeof badgeVariants> {}

export function Badge({ className, variant, ...props }: BadgeProps) {
  return <div className={cn(badgeVariants({ variant }), className)} {...props} />
}
