'use client';

import { useState } from "react";
import Link from "next/link";
import { useLoginMutation } from "@/lib/api/authApi";
import { useAuth } from "@/contexts/AuthContext";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { AlertCircle, Mail, Lock, Loader2 } from "lucide-react";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [errorMsg, setErrorMsg] = useState("");
  
  const [loginApi, { isLoading }] = useLoginMutation();
  const { login } = useAuth();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg("");
    try {
      const response = await loginApi({ email, password }).unwrap();
      await login(response.access_token);
    } catch (err: any) {
      setErrorMsg(err?.data?.detail || "Invalid email or password");
    }
  };

  return (
    <div className="w-full relative z-10 bg-white/70 backdrop-blur-xl p-8 sm:p-10 rounded-[2rem] shadow-[0_8px_30px_rgb(0,0,0,0.04)] border border-white/50">
      {/* Header */}
      <div className="space-y-2 mb-8 text-center">
        <h1 className="text-3xl font-display font-medium tracking-tight text-ink">Welcome back</h1>
        <p className="text-[15px] text-muted-foreground">
          Sign in to your TripOS account to continue
        </p>
      </div>

      {/* Form */}
      <form onSubmit={handleSubmit} className="space-y-5">
        {errorMsg && (
          <div className="flex items-center gap-2.5 p-3.5 text-sm text-red-700 bg-red-50 border border-red-100 rounded-xl animate-scale-in">
            <AlertCircle className="w-4 h-4 flex-shrink-0" />
            <span>{errorMsg}</span>
          </div>
        )}

        <div className="space-y-2">
          <Label htmlFor="email" className="text-sm font-medium text-ink">Email address</Label>
          <div className="relative group">
            <Mail className="absolute left-4 top-1/2 -translate-y-1/2 h-[18px] w-[18px] text-muted-foreground/40 group-focus-within:text-teal transition-colors" />
            <Input
              id="email"
              type="email"
              placeholder="you@agency.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              className="pl-11 h-12 bg-white/50 border-line/60 rounded-xl focus:bg-white focus:border-teal/50 focus:ring-4 focus:ring-teal/10 transition-all text-[15px]"
            />
          </div>
        </div>

        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <Label htmlFor="password" className="text-sm font-medium text-ink">Password</Label>
            <Link href="/forgot-password" className="text-sm font-medium text-teal hover:text-teal-dark transition-colors hover:underline">
              Forgot password?
            </Link>
          </div>
          <div className="relative group">
            <Lock className="absolute left-4 top-1/2 -translate-y-1/2 h-[18px] w-[18px] text-muted-foreground/40 group-focus-within:text-teal transition-colors" />
            <Input
              id="password"
              type="password"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              className="pl-11 h-12 bg-white/50 border-line/60 rounded-xl focus:bg-white focus:border-teal/50 focus:ring-4 focus:ring-teal/10 transition-all text-[15px] tracking-widest placeholder:tracking-normal"
            />
          </div>
        </div>

        <div className="pt-2">
          <Button
            type="submit"
            className="w-full h-12 rounded-xl bg-gradient-to-r from-teal to-teal-dark hover:from-teal-dark hover:to-teal text-white font-medium text-[15px] shadow-[0_4px_14px_0_rgba(20,184,166,0.39)] hover:shadow-[0_6px_20px_rgba(20,184,166,0.23)] hover:-translate-y-0.5 transition-all duration-200"
            disabled={isLoading}
          >
            {isLoading ? (
              <>
                <Loader2 className="h-5 w-5 animate-spin mr-2" />
                Signing in...
              </>
            ) : (
              "Sign In"
            )}
          </Button>
        </div>
      </form>

      {/* Footer */}
      <div className="mt-8 text-center text-[15px] text-muted-foreground">
        Don&apos;t have an account?{" "}
        <Link href="/signup" className="font-medium text-teal hover:text-teal-dark transition-colors hover:underline">
          Request access
        </Link>
      </div>
    </div>
  );
}
