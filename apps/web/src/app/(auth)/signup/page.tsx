'use client';

import { useState } from "react";
import Link from "next/link";
import { useSignupMutation } from "@/lib/api/authApi";
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { AlertCircle, CheckCircle2 } from "lucide-react";

export default function SignupPage() {
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [errorMsg, setErrorMsg] = useState("");
  const [isSuccess, setIsSuccess] = useState(false);
  
  const [signupApi, { isLoading }] = useSignupMutation();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg("");
    try {
      await signupApi({ first_name: firstName, last_name: lastName, email, password }).unwrap();
      setIsSuccess(true);
    } catch (err: any) {
      setErrorMsg(err?.data?.detail || "Registration failed");
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
            We've sent a verification link to <span className="font-medium text-ink">{email}</span>. Please click the link to activate your account.
          </CardDescription>
        </CardHeader>
        <CardFooter className="flex justify-center">
          <Link href="/login" className="text-sm text-focus hover:underline">Return to login</Link>
        </CardFooter>
      </Card>
    );
  }

  return (
    <Card className="w-full max-w-md shadow-lg border-line animate-in fade-in zoom-in-95">
      <form onSubmit={handleSubmit}>
        <CardHeader className="space-y-1">
          <CardTitle className="text-2xl font-bold tracking-tight text-ink">Create an Account</CardTitle>
          <CardDescription>
            Enter your details below to create your agency account
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {errorMsg && (
            <div className="flex items-center gap-2 p-3 text-sm text-red-600 bg-red-50 rounded-md">
              <AlertCircle className="w-4 h-4" />
              <span>{errorMsg}</span>
            </div>
          )}
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="firstName">First Name</Label>
              <Input id="firstName" value={firstName} onChange={(e) => setFirstName(e.target.value)} required />
            </div>
            <div className="space-y-2">
              <Label htmlFor="lastName">Last Name</Label>
              <Input id="lastName" value={lastName} onChange={(e) => setLastName(e.target.value)} required />
            </div>
          </div>
          <div className="space-y-2">
            <Label htmlFor="email">Email</Label>
            <Input id="email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
          </div>
          <div className="space-y-2">
            <Label htmlFor="password">Password</Label>
            <Input id="password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} required minLength={8} />
          </div>
        </CardContent>
        <CardFooter className="flex flex-col space-y-4">
          <Button type="submit" className="w-full" disabled={isLoading}>
            {isLoading ? "Creating account..." : "Sign Up"}
          </Button>
          <div className="text-center text-sm text-muted-foreground">
            Already have an account? <Link href="/login" className="text-focus hover:underline">Sign in</Link>
          </div>
        </CardFooter>
      </form>
    </Card>
  );
}
