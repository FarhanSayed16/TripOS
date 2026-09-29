'use client';

import { Suspense, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import { useVerifyMutation } from "@/lib/api/authApi";
import { Card, CardHeader, CardTitle, CardDescription, CardFooter } from "@/components/ui/card";
import { Loader2, CheckCircle2, XCircle } from "lucide-react";

function VerifyContent() {
  const searchParams = useSearchParams();
  const token = searchParams.get('token');
  
  const [verifyApi] = useVerifyMutation();
  const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading');

  useEffect(() => {
    if (!token) {
      setStatus('error');
      return;
    }
    
    verifyApi({ token }).unwrap()
      .then(() => setStatus('success'))
      .catch(() => setStatus('error'));
  }, [token, verifyApi]);

  return (
    <Card className="w-full max-w-md shadow-lg border-line animate-in fade-in zoom-in-95">
      <CardHeader className="text-center space-y-2">
        {status === 'loading' && (
          <>
            <div className="mx-auto w-12 h-12 flex items-center justify-center mb-4">
              <Loader2 className="w-8 h-8 text-focus animate-spin" />
            </div>
            <CardTitle className="text-xl font-bold text-ink">Verifying your email...</CardTitle>
            <CardDescription>Please wait while we confirm your email address.</CardDescription>
          </>
        )}
        
        {status === 'success' && (
          <>
            <div className="mx-auto w-12 h-12 bg-mint/10 rounded-full flex items-center justify-center mb-4">
              <CheckCircle2 className="w-6 h-6 text-mint" />
            </div>
            <CardTitle className="text-xl font-bold text-ink">Email Verified!</CardTitle>
            <CardDescription>Your account has been successfully verified. You can now sign in.</CardDescription>
            <CardFooter className="flex justify-center pt-4">
              <Link href="/login" className="text-sm font-medium text-focus hover:underline">Continue to Login</Link>
            </CardFooter>
          </>
        )}
        
        {status === 'error' && (
          <>
            <div className="mx-auto w-12 h-12 bg-coral/10 rounded-full flex items-center justify-center mb-4">
              <XCircle className="w-6 h-6 text-coral" />
            </div>
            <CardTitle className="text-xl font-bold text-ink">Verification Failed</CardTitle>
            <CardDescription>The verification link is invalid or has expired. Please try signing up again.</CardDescription>
            <CardFooter className="flex justify-center pt-4">
              <Link href="/signup" className="text-sm font-medium text-focus hover:underline">Back to Sign Up</Link>
            </CardFooter>
          </>
        )}
      </CardHeader>
    </Card>
  );
}

export default function VerifyPage() {
  return (
    <Suspense fallback={
      <Card className="w-full max-w-md shadow-lg border-line animate-in fade-in zoom-in-95 p-8 text-center">
        <Loader2 className="w-8 h-8 text-focus animate-spin mx-auto" />
      </Card>
    }>
      <VerifyContent />
    </Suspense>
  );
}
