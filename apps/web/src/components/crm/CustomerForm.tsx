'use client';

import { useState } from "react";
import { useCreateCustomerMutation } from "@/lib/api/crmApi";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { AlertCircle, CheckCircle2 } from "lucide-react";

interface CustomerFormProps {
  onSuccess?: () => void;
}

export function CustomerForm({ onSuccess }: CustomerFormProps) {
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [errorMsg, setErrorMsg] = useState("");
  
  const [createCustomer, { isLoading }] = useCreateCustomerMutation();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg("");
    try {
      await createCustomer({
        first_name: firstName,
        last_name: lastName,
        email: email || undefined,
        phone,
      }).unwrap();
      
      // Reset form
      setFirstName("");
      setLastName("");
      setEmail("");
      setPhone("");
      
      if (onSuccess) onSuccess();
    } catch (err: any) {
      setErrorMsg(err?.data?.detail || "Failed to create customer");
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {errorMsg && (
        <div className="flex items-center gap-2 p-3 text-sm text-red-600 bg-red-50 rounded-md">
          <AlertCircle className="w-4 h-4" />
          <span>{errorMsg}</span>
        </div>
      )}
      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label htmlFor="firstName">First Name</Label>
          <Input 
            id="firstName" 
            value={firstName}
            onChange={(e) => setFirstName(e.target.value)}
            required 
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="lastName">Last Name</Label>
          <Input 
            id="lastName" 
            value={lastName}
            onChange={(e) => setLastName(e.target.value)}
            required 
          />
        </div>
      </div>
      <div className="space-y-2">
        <Label htmlFor="phone">Phone Number</Label>
        <Input 
          id="phone" 
          type="tel"
          placeholder="e.g. 9876543210"
          value={phone}
          onChange={(e) => setPhone(e.target.value)}
          required 
        />
        <p className="text-xs text-muted-foreground">
          Will be normalized to E.164. Defaults to India (+91) if country code is omitted.
        </p>
      </div>
      <div className="space-y-2">
        <Label htmlFor="email">Email Address (Optional)</Label>
        <Input 
          id="email" 
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
        />
      </div>
      <Button type="submit" className="w-full" disabled={isLoading}>
        {isLoading ? "Saving..." : "Add Customer"}
      </Button>
    </form>
  );
}
