import * as React from "react";
import { cn } from "@/lib/utils";

export const Textarea = React.forwardRef<HTMLTextAreaElement, React.TextareaHTMLAttributes<HTMLTextAreaElement>>(
  ({ className, ...props }, ref) => (
    <textarea
      ref={ref}
      className={cn(
        "w-full rounded-md border border-line bg-surface p-3 text-sm outline-none focus-visible:ring-2 focus-visible:ring-primary placeholder:text-muted",
        className,
      )}
      {...props}
    />
  ),
);
Textarea.displayName = "Textarea";
