"use client";

import { use, useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { ArrowLeft, MessageCircle, Copy, Check, ExternalLink, Loader2, Send } from "lucide-react";

import { useGetWhatsappPreviewQuery, useSendQuoteMutation } from "@/lib/api/quotesApi";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";

export default function SendQuotePage({ params }: { params: Promise<{ id: string }> }) {
  const resolvedParams = use(params);
  const router = useRouter();
  
  const { data: preview, isLoading, error } = useGetWhatsappPreviewQuery(resolvedParams.id);
  const [sendQuote, { isLoading: isSending }] = useSendQuoteMutation();

  const [message, setMessage] = useState("");
  const [phone, setPhone] = useState("");
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    if (preview) {
      setMessage(preview.message_template);
      setPhone(preview.phone_e164);
    }
  }, [preview]);

  if (isLoading) {
    return <div className="p-8 text-center text-gray-500">Loading preview...</div>;
  }

  if (error || !preview) {
    return (
      <div className="p-8 text-center">
        <div className="bg-red-50 text-red-700 p-4 rounded-md max-w-md mx-auto border border-red-200">
          <p className="font-bold mb-1">Failed to generate preview</p>
          <p className="text-sm">{(error as any)?.data?.detail || "Ensure the quote is marked 'Ready' and the customer has a valid E.164 phone number."}</p>
        </div>
        <Button variant="outline" className="mt-4" onClick={() => router.back()}>Go Back</Button>
      </div>
    );
  }

  // Prefer backend-built wa.me URL (MessagingProvider); fall back locally
  const waMeLink =
    preview.wa_me_url ||
    `https://wa.me/${phone.replace("+", "")}?text=${encodeURIComponent(message)}`;

  const handleCopy = () => {
    navigator.clipboard.writeText(message);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleMarkSent = async () => {
    try {
      await sendQuote({ id: resolvedParams.id, content: message }).unwrap();
      router.push(`/app/quotes/${resolvedParams.id}`);
    } catch (err) {
      console.error(err);
      alert("Failed to mark as sent.");
    }
  };

  return (
    <div className="max-w-3xl mx-auto space-y-8 pb-20">
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon" onClick={() => router.back()}>
          <ArrowLeft className="w-5 h-5" />
        </Button>
        <div>
          <h1 className="page-title">Send Quote</h1>
          <p className="text-gray-500">Review and send via WhatsApp.</p>
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <MessageCircle className="w-5 h-5 text-green-500" />
            WhatsApp Preview
          </CardTitle>
          <CardDescription>
            Sending to <strong className="text-ink">{phone}</strong>. You can safely edit the message below before sending.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <Textarea 
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            className="min-h-[250px] font-mono text-sm leading-relaxed"
          />

          <div className="bg-sand/30 p-4 rounded-lg border border-line space-y-4">
            <p className="text-sm font-medium">1. Send the message</p>
            <div className="flex gap-2">
              <a href={waMeLink} target="_blank" rel="noopener noreferrer" className="flex-1">
                <Button className="w-full bg-[#25D366] hover:bg-[#128C7E] text-white gap-2">
                  <ExternalLink className="w-4 h-4" />
                  Open WhatsApp
                </Button>
              </a>
              <Button variant="outline" onClick={handleCopy} className="gap-2 shrink-0">
                {copied ? <Check className="w-4 h-4 text-green-500" /> : <Copy className="w-4 h-4" />}
                {copied ? "Copied" : "Copy Text"}
              </Button>
            </div>

            <p className="text-sm font-medium pt-4 border-t border-line">2. Confirm delivery</p>
            <Button 
              onClick={handleMarkSent} 
              disabled={isSending}
              className="w-full bg-focus hover:bg-focus/90 gap-2"
            >
              {isSending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
              Mark Quote as Sent
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
