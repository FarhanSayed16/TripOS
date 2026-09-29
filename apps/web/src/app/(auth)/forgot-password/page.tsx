'use client';

import { useState } from "react";
import Link from "next/link";
import { useForgotPasswordMutation } from "@/lib/api/authApi";
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { AlertCircle, CheckCircle2 } from "lucide-react";

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [errorMsg, setErrorMsg] = useState("");
  const [isSuccess, setIsSuccess] = useState(false);
  
  const [forgotApi, { isLoading }] = useForgotPasswordMutation();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg("");
    try {
      await forgotApi({ email }).unwrap();
      setIsSuccess(true);
    } catch (err: any) {
      setErrorMsg(err?.data?.detail || "Failed to process request");
    }
  };

  if (isSuccess) {
    return (
      <Card className="w-full max-w-md shadow-lg border-line animate-in fade-in zoom-in-95">
        <CardHeader className="text-center space-y-2">
          <div className="mx-auto w-12 h-12 bg-mint/10 rounded-full flex items-center justify-center mb-4">
            <CheckCircle2 className="w-6 h-6 text-mint" />
          </div>
          <CardTitle className="text-2xl font-bold text-ink">Check your email</CardTitle>
          <CardDescription>
            If an account exists with <span className="font-medium text-ink">{email}</span>, we have sent a password reset link.
          </CardDescription>
        </CardHeader>
        <CardFooter className="flex justify-center">
          <Link href="/login" className="text-sm font-medium text-focus hover:underline">Return to login</Link>
        </CardFooter>
      </Card>
    );
  }

  return (
    <Card className="w-full max-w-md shadow-lg border-line animate-in fade-in zoom-in-95">
      <form onSubmit={handleSubmit}>
        <CardHeader className="space-y-1">
          <CardTitle className="text-2xl font-bold tracking-tight text-ink">Reset Password</CardTitle>
          <CardDescription>
            Enter your email address and we'll send you a link to reset your password.
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
            <Label htmlFor="email">Email address</Label>
            <Input 
              id="email" 
              type="email" 
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required 
            />
          </div>
        </CardContent>
        <CardFooter className="flex flex-col space-y-4">
          <Button type="submit" className="w-full" disabled={isLoading}>
            {isLoading ? "Sending link..." : "Send Reset Link"}
          </Button>
          <div className="text-center text-sm text-muted-foreground">
            Remember your password? <Link href="/login" className="text-focus hover:underline">Sign in</Link>
          </div>
        </CardFooter>
      </form>
    </Card>
  );
}
