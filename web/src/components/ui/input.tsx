import * as React from "react";
import { cn } from "@/lib/utils";

export const Input = React.forwardRef<HTMLInputElement, React.InputHTMLAttributes<HTMLInputElement>>(
  ({ className, ...props }, ref) => (
    <input
      ref={ref}
      className={cn(
        "h-9 w-full rounded-md border border-line bg-surface px-3 text-sm outline-none focus-visible:ring-2 focus-visible:ring-primary placeholder:text-muted",
        className,
      )}
      {...props}
    />
  ),
);
Input.displayName = "Input";
