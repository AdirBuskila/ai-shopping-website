"use client";

import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";
import { Spinner } from "./Spinner";

const buttonVariants = cva(
  [
    "relative inline-flex items-center justify-center gap-2",
    "font-semibold tracking-tight",
    "transition-all duration-200",
    "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-ink",
    "disabled:opacity-50 disabled:pointer-events-none",
    "active:scale-[0.98] select-none",
  ],
  {
    variants: {
      variant: {
        primary: "bg-ink text-white hover:bg-ink-soft shadow-sm hover:shadow-md",
        accent: "bg-accent text-accent-ink hover:bg-accent-hover shadow-md hover:shadow-glow",
        success: "bg-success text-white hover:bg-success-hover shadow-md hover:shadow-lg",
        outline: "bg-transparent text-ink border border-border-strong hover:bg-surface-muted hover:border-ink",
        ghost: "bg-transparent text-ink-muted hover:bg-surface-muted hover:text-ink",
        danger: "bg-danger text-white hover:bg-danger-hover shadow-sm hover:shadow-md",
      },
      size: {
        sm: "h-9 px-4 text-xs rounded-md",
        md: "h-11 px-5 text-sm rounded-lg",
        lg: "h-13 px-6 text-base rounded-xl",
      },
      fullWidth: { true: "w-full" },
    },
    defaultVariants: { variant: "primary", size: "md" },
  },
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  isLoading?: boolean;
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, fullWidth, type = "button", isLoading = false, disabled, children, ...props }, ref) => (
    <button
      ref={ref}
      type={type}
      disabled={disabled || isLoading}
      aria-busy={isLoading || undefined}
      className={cn(buttonVariants({ variant, size, fullWidth }), className)}
      {...props}
    >
      <span className={cn("inline-flex items-center gap-2 transition-opacity", isLoading ? "opacity-0" : "opacity-100")}>
        {children}
      </span>
      {isLoading && (
        <span className="absolute inset-0 flex items-center justify-center">
          <Spinner size="sm" />
        </span>
      )}
    </button>
  ),
);
Button.displayName = "Button";
