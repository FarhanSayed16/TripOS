'use client';

import { useEffect } from 'react';

/** Unregister stale service workers that break Next/Turbopack fetches in local dev. */
export function ServiceWorkerCleanup() {
  useEffect(() => {
    if (typeof window === 'undefined' || !('serviceWorker' in navigator)) return;
    navigator.serviceWorker
      .getRegistrations()
      .then((regs) => Promise.all(regs.map((r) => r.unregister())))
      .catch(() => undefined);
  }, []);
  return null;
}
