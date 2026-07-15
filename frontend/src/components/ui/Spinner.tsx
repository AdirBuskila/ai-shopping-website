import { cn } from "@/lib/utils";

const sizes = { xs: "h-3 w-3", sm: "h-4 w-4", md: "h-5 w-5", lg: "h-6 w-6" };

export function Spinner({ size = "sm", className }: { size?: keyof typeof sizes; className?: string }) {
  return (
    <span
      role="status"
      aria-label="Loading"
      className={cn(
        "inline-block animate-spin rounded-full border-2 border-current border-t-transparent",
        sizes[size],
        className,
      )}
    />
  );
}
