'use client';

import { ReactNode, Children, cloneElement, isValidElement } from 'react';

export function PageTransition({ children }: { children: ReactNode }) {
  return (
    <div className="motion-safe:animate-in motion-safe:fade-in motion-safe:slide-in-from-bottom-3 motion-safe:duration-500 motion-safe:ease-out fill-mode-both motion-reduce:animate-none">
      {children}
    </div>
  );
}

export function StaggerContainer({
  children,
  className = "",
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <div className={className}>
      {Children.map(children, (child, index) => {
        if (isValidElement(child)) {
          return cloneElement(child as React.ReactElement<any>, {
            className: `${(child.props as any).className || ""} stagger-item`.trim(),
            style: {
              ...((child.props as any).style || {}),
              "--stagger-index": index,
            } as React.CSSProperties,
          });
        }
        return child;
      })}
    </div>
  );
}
