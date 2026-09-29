'use client';

import { Suspense, useState } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import Link from "next/link";
import { useResetPasswordMutation } from "@/lib/api/authApi";
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { AlertCircle, CheckCircle2, Loader2 } from "lucide-react";

function ResetPasswordContent() {
  const searchParams = useSearchParams();
  const token = searchParams.get('token');
  const router = useRouter();

  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [errorMsg, setErrorMsg] = useState("");
  const [isSuccess, setIsSuccess] = useState(false);
  
  const [resetApi, { isLoading }] = useResetPasswordMutation();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg("");
    
    if (!token) {
      setErrorMsg("Invalid reset link. Please request a new one.");
      return;
    }
    
    if (password !== confirmPassword) {
      setErrorMsg("Passwords do not match");
      return;
    }

    try {
      await resetApi({ token, new_password: password }).unwrap();
      setIsSuccess(true);
    } catch (err: any) {
      setErrorMsg(err?.data?.detail || "Failed to reset password. The link may have expired.");
    }
  };

  if (!token) {
    return (
      <Card className="w-full max-w-md shadow-lg border-line p-6 text-center">
        <h2 className="text-lg font-bold text-coral mb-2">Invalid Link</h2>
        <p className="text-sm text-muted-foreground mb-4">This password reset link is missing or malformed.</p>
        <Link href="/forgot-password" className="text-sm font-medium text-focus hover:underline">Request a new link</Link>
      </Card>
    );
  }

  if (isSuccess) {
    return (
      <Card className="w-full max-w-md shadow-lg border-line animate-in fade-in zoom-in-95">
        <CardHeader className="text-center space-y-2">
          <div className="mx-auto w-12 h-12 bg-mint/10 rounded-full flex items-center justify-center mb-4">
            <CheckCircle2 className="w-6 h-6 text-mint" />
          </div>
          <CardTitle className="text-2xl font-bold text-ink">Password Reset!</CardTitle>
          <CardDescription>
            Your password has been successfully updated. You can now sign in with your new credentials.
          </CardDescription>
        </CardHeader>
        <CardFooter className="flex justify-center">
          <Link href="/login" className="text-sm font-medium text-focus hover:underline">Continue to login</Link>
        </CardFooter>
      </Card>
    );
  }

  return (
    <Card className="w-full max-w-md shadow-lg border-line animate-in fade-in zoom-in-95">
      <form onSubmit={handleSubmit}>
        <CardHeader className="space-y-1">
          <CardTitle className="text-2xl font-bold tracking-tight text-ink">Set New Password</CardTitle>
          <CardDescription>
            Please enter your new password below.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {errorMsg && (
            <div className="flex items-center gap-2 p-3 text-sm text-red-600 bg-red-50 rounded-md">
              <AlertCircle className="w-4 h-4" />
              <span>{errorMsg}</span>
            </div>
          )}
          <div className="space-y-2">
            <Label htmlFor="password">New Password</Label>
            <Input 
              id="password" 
              type="password" 
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required 
              minLength={8}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="confirmPassword">Confirm Password</Label>
            <Input 
              id="confirmPassword" 
              type="password" 
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              required 
              minLength={8}
            />
          </div>
        </CardContent>
        <CardFooter className="flex flex-col space-y-4">
          <Button type="submit" className="w-full" disabled={isLoading}>
            {isLoading ? "Resetting..." : "Reset Password"}
          </Button>
        </CardFooter>
      </form>
    </Card>
  );
}

export default function ResetPasswordPage() {
  return (
    <Suspense fallback={
      <Card className="w-full max-w-md shadow-lg border-line p-8 text-center">
        <Loader2 className="w-8 h-8 text-focus animate-spin mx-auto" />
      </Card>
    }>
      <ResetPasswordContent />
    </Suspense>
  );
}
