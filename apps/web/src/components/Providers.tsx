'use client';

import { Provider } from 'react-redux';
import { store } from '@/lib/store';
import { ReactNode } from 'react';
import { Toaster } from '@/components/ui/toast';
import { AuthProvider } from '@/contexts/AuthContext';
import { LocaleBootstrap } from '@/components/LocaleBootstrap';

export function Providers({ children }: { children: ReactNode }) {
  return (
    <Provider store={store}>
      <AuthProvider>
        <LocaleBootstrap>
          <Toaster>{children}</Toaster>
        </LocaleBootstrap>
      </AuthProvider>
    </Provider>
  );
}
