import * as React from "react";

/**
 * Base UI warns when `nativeButton` is true but `render` is not a real <button>.
 * Custom components (Next Link, our Button) must use nativeButton={false}.
 */
export function resolveNativeButton(
  render: React.ReactElement | undefined | null,
  explicit?: boolean
): boolean {
  if (explicit !== undefined) return explicit;
  if (render == null) return true;
  if (React.isValidElement(render)) {
    return typeof render.type === "string" && render.type === "button";
  }
  return false;
}
