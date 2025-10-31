// PageContainer.tsx
import { ReactNode } from "react";

interface PageContainerProps {
  children: ReactNode;
  className?: string;
}

export function PageContainer({ children, className = "" }: PageContainerProps) {
  return (
    <div className={`py-6 pr-6 ${className}`}>
      <div className="w-full">
        {children}
      </div>
    </div>
  );
}