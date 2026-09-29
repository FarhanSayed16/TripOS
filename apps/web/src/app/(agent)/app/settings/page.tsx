"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  useGetMyOrganizationQuery,
  useUpdateMyOrganizationMutation,
} from "@/lib/api/orgApi";
import { useGetMeQuery, useUpdateMeMutation } from "@/lib/api/authApi";
import { useI18n } from "@/lib/i18n";
import { Building2, Monitor, Tag, Bot, Globe, Bell, CheckCircle2, Circle, Upload, Plus, ExternalLink, Info } from "lucide-react";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";

const CURRENCIES = ["INR", "USD", "AED", "EUR", "GBP"];
const LOCALES = [
  { value: "en", labelKey: "common.english" },
  { value: "hi", labelKey: "common.hindi" },
];

export default function SettingsPage() {
  const { t, setLocale } = useI18n();
  const { data: org, isLoading: orgLoading } = useGetMyOrganizationQuery();
  const { data: me } = useGetMeQuery();
  const [updateOrg, { isLoading: savingOrg }] = useUpdateMyOrganizationMutation();
  const [updateMe, { isLoading: savingMe }] = useUpdateMeMutation();
  
  const [activeTab, setActiveTab] = useState("organization");
  
  const [orgCurrency, setOrgCurrency] = useState<string>("");
  const [userCurrency, setUserCurrency] = useState<string>("");
  const [orgLocale, setOrgLocale] = useState<string>("");
  const [userLocale, setUserLocale] = useState<string>("");
  const [message, setMessage] = useState<string | null>(null);

  const effectiveOrg = orgCurrency || org?.preferred_currency || "INR";
  const effectiveUser = userCurrency !== "" ? userCurrency : me?.preferred_currency ?? "";
  const effectiveOrgLocale = orgLocale || org?.default_locale || "en";
  const effectiveUserLocale = userLocale !== "" ? userLocale : me?.locale ?? "";

  const showMessage = (msg: string) => {
    setMessage(msg);
    setTimeout(() => setMessage(null), 3000);
  }

  const saveOrgCurrency = async () => {
    try {
      await updateOrg({ preferred_currency: effectiveOrg }).unwrap();
      showMessage(t("settings.savedAgencyCurrency"));
    } catch {
      showMessage(t("settings.saveFailed"));
    }
  };

  const saveUserCurrency = async () => {
    try {
      await updateMe({
        preferred_currency: effectiveUser === "" ? null : effectiveUser,
      }).unwrap();
      showMessage(effectiveUser ? t("settings.savedPersonalCurrency") : t("settings.clearedPersonalCurrency"));
    } catch {
      showMessage(t("settings.saveFailed"));
    }
  };

  const saveOrgLocale = async () => {
    try {
      await updateOrg({ default_locale: effectiveOrgLocale }).unwrap();
      if (!me?.locale) setLocale(effectiveOrgLocale as "en" | "hi");
      showMessage(t("settings.savedAgencyLocale"));
    } catch {
      showMessage(t("settings.saveFailed"));
    }
  };

  const saveUserLocale = async () => {
    try {
      await updateMe({
        locale: effectiveUserLocale === "" ? null : effectiveUserLocale,
      }).unwrap();
      const next = effectiveUserLocale === "" ? ((org?.default_locale as "en" | "hi") || "en") : (effectiveUserLocale as "en" | "hi");
      setLocale(next);
      showMessage(effectiveUserLocale ? t("settings.savedPersonalLocale") : t("settings.clearedPersonalLocale"));
    } catch {
      showMessage(t("settings.saveFailed"));
    }
  };

  if (orgLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-teal"></div>
      </div>
    );
  }

  const tabs = [
    { id: "organization", label: "Organization", icon: Building2 },
    { id: "display", label: "Display", icon: Monitor },
    { id: "deals", label: "Deal Codes", icon: Tag },
    { id: "ai", label: "AI Preferences", icon: Bot },
    { id: "domain", label: "Custom Domain", icon: Globe },
    { id: "notifications", label: "Notifications", icon: Bell },
  ];

  return (
    <div className="max-w-5xl mx-auto space-y-8 pb-16 animate-in fade-in duration-500">
      <div>
        <h1 className="page-title text-2xl tracking-tight">{t("settings.title")}</h1>
        <p className="page-subtitle mt-1">{t("settings.subtitle")}</p>
      </div>

      {message && (
        <div className="bg-emerald-50 border border-emerald-200 text-emerald-800 rounded-md px-4 py-3 flex items-center gap-2 shadow-sm transition-all">
          <CheckCircle2 className="w-4 h-4 text-emerald-500" />
          <span className="font-medium text-sm">{message}</span>
        </div>
      )}

      <div className="flex flex-col md:flex-row gap-8 items-start">
        {/* Tab Sidebar */}
        <div className="w-full md:w-64 flex flex-col gap-1 bg-paper/50 p-2 rounded-lg border border-line">
          {tabs.map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-3 px-4 py-2.5 rounded-md text-sm font-medium transition-all text-left ${
                activeTab === tab.id 
                  ? "bg-surface shadow-sm text-ink border border-line" 
                  : "text-muted-foreground hover:bg-surface/50 hover:text-ink border border-transparent"
              }`}
            >
              <tab.icon className={`w-4 h-4 ${activeTab === tab.id ? 'text-teal' : 'opacity-70'}`} />
              {tab.label}
            </button>
          ))}
        </div>

        {/* Content Area */}
        <div className="flex-1 w-full space-y-6">
          
          {/* ORGANIZATION TAB */}
          {activeTab === "organization" && (
            <div className="space-y-6 animate-in fade-in">
              <Card className="bg-paper border-line shadow-sm">
                <CardHeader className="border-b border-line pb-4 bg-surface/50">
                  <CardTitle className="text-lg">Agency Profile</CardTitle>
                  <CardDescription>Basic information about your organization.</CardDescription>
                </CardHeader>
                <CardContent className="space-y-6 pt-6">
                  <div className="flex items-center gap-6">
                    <div className="w-20 h-20 bg-teal/10 rounded-full flex items-center justify-center border-2 border-dashed border-teal/30 cursor-pointer hover:bg-teal/20 transition-colors">
                      <Upload className="w-6 h-6 text-teal" />
                    </div>
                    <div>
                      <h4 className="text-sm font-medium text-ink">Organization Logo</h4>
                      <p className="text-xs text-muted-foreground mt-1">Recommended: 256x256px, PNG or JPG.</p>
                      <Button variant="outline" size="sm" className="mt-3">Upload Logo</Button>
                    </div>
                  </div>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <label className="text-sm font-medium text-ink">Brand Name</label>
                      <Input defaultValue={org?.brand_name} className="bg-surface" />
                    </div>
                    <div className="space-y-2">
                      <label className="text-sm font-medium text-ink">Tagline</label>
                      <Input placeholder="Your trusted travel partner" className="bg-surface" />
                    </div>
                    <div className="space-y-2">
                      <label className="text-sm font-medium text-ink">Contact Email</label>
                      <Input type="email" placeholder="support@agency.com" className="bg-surface" />
                    </div>
                    <div className="space-y-2">
                      <label className="text-sm font-medium text-ink">Phone Number</label>
                      <Input placeholder="+91 98765 43210" className="bg-surface" />
                    </div>
                    <div className="space-y-2 md:col-span-2">
                      <label className="text-sm font-medium text-ink">Brand Color (Hex)</label>
                      <div className="flex gap-3">
                        <Input defaultValue="#0D9488" className="bg-surface font-mono max-w-[150px]" />
                        <div className="w-10 h-10 rounded border border-line bg-[#0D9488]"></div>
                      </div>
                    </div>
                  </div>
                  <div className="pt-4 border-t border-line">
                    <Button onClick={() => showMessage("Organization profile saved successfully.")} className="bg-teal hover:bg-teal-dark">Save Profile</Button>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}

          {/* DISPLAY TAB */}
          {activeTab === "display" && (
            <div className="space-y-6 animate-in fade-in">
              <Card className="bg-paper border-line shadow-sm">
                <CardHeader className="border-b border-line pb-4 bg-surface/50">
                  <CardTitle className="text-lg">Regional & Currency</CardTitle>
                  <CardDescription>Configure how prices and dates are shown.</CardDescription>
                </CardHeader>
                <CardContent className="space-y-6 pt-6">
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                    <div className="space-y-4">
                      <div>
                        <label className="text-sm font-medium text-ink flex items-center gap-2">
                          Agency Default Currency
                        </label>
                        <p className="text-xs text-muted-foreground mt-1 mb-2">
                          {t("settings.agencyCurrencyHelp", { brand: org?.brand_name || "your agency" })}
                        </p>
                        <select
                          className="w-full border border-line rounded-md h-10 px-3 bg-surface text-sm focus:ring-2 focus:ring-teal focus:outline-none"
                          value={effectiveOrg}
                          onChange={(e) => setOrgCurrency(e.target.value)}
                        >
                          {CURRENCIES.map((c) => (
                            <option key={c} value={c}>{c}</option>
                          ))}
                        </select>
                        <Button onClick={saveOrgCurrency} disabled={savingOrg} className="mt-3 bg-teal hover:bg-teal-dark w-full">
                          {savingOrg ? t("common.saving") : t("settings.saveAgencyCurrency")}
                        </Button>
                      </div>

                      <div className="pt-4 border-t border-line">
                        <label className="text-sm font-medium text-ink">Personal Currency Override</label>
                        <p className="text-xs text-muted-foreground mt-1 mb-2">Overrides the agency default for your account.</p>
                        <select
                          className="w-full border border-line rounded-md h-10 px-3 bg-surface text-sm focus:ring-2 focus:ring-teal focus:outline-none"
                          value={effectiveUser}
                          onChange={(e) => setUserCurrency(e.target.value)}
                        >
                          <option value="">{t("settings.useAgencyDefault")}</option>
                          {CURRENCIES.map((c) => (
                            <option key={c} value={c}>{c}</option>
                          ))}
                        </select>
                        <Button onClick={saveUserCurrency} disabled={savingMe} variant="outline" className="mt-3 w-full">
                          {savingMe ? t("common.saving") : t("settings.savePersonal")}
                        </Button>
                      </div>
                    </div>

                    <div className="space-y-4">
                      <div>
                        <label className="text-sm font-medium text-ink flex items-center gap-2">
                          Agency Default Locale
                        </label>
                        <p className="text-xs text-muted-foreground mt-1 mb-2">
                          {t("settings.agencyLocaleHelp")}
                        </p>
                        <select
                          className="w-full border border-line rounded-md h-10 px-3 bg-surface text-sm focus:ring-2 focus:ring-teal focus:outline-none"
                          value={effectiveOrgLocale}
                          onChange={(e) => setOrgLocale(e.target.value)}
                        >
                          {LOCALES.map((l) => (
                            <option key={l.value} value={l.value}>{t(l.labelKey)}</option>
                          ))}
                        </select>
                        <Button onClick={saveOrgLocale} disabled={savingOrg} className="mt-3 bg-teal hover:bg-teal-dark w-full">
                          {savingOrg ? t("common.saving") : t("settings.saveAgencyLocale")}
                        </Button>
                      </div>

                      <div className="pt-4 border-t border-line">
                        <label className="text-sm font-medium text-ink">Personal Locale Override</label>
                        <p className="text-xs text-muted-foreground mt-1 mb-2">Overrides the agency language for you.</p>
                        <select
                          className="w-full border border-line rounded-md h-10 px-3 bg-surface text-sm focus:ring-2 focus:ring-teal focus:outline-none"
                          value={effectiveUserLocale}
                          onChange={(e) => setUserLocale(e.target.value)}
                        >
                          <option value="">{t("settings.useAgencyDefault")}</option>
                          {LOCALES.map((l) => (
                            <option key={l.value} value={l.value}>{t(l.labelKey)}</option>
                          ))}
                        </select>
                        <Button onClick={saveUserLocale} disabled={savingMe} variant="outline" className="mt-3 w-full">
                          {savingMe ? t("common.saving") : t("settings.savePersonalLocale")}
                        </Button>
                      </div>
                    </div>
                  </div>

                  <div className="bg-sand/30 border border-line rounded-md p-4 flex items-start gap-3 mt-4">
                    <Info className="w-5 h-5 text-teal shrink-0 mt-0.5" />
                    <div>
                      <h4 className="text-sm font-medium text-ink">Charge Currency is fixed to INR</h4>
                      <p className="text-xs text-muted-foreground mt-1">
                        Platform billing and supplier payments are processed in INR. Your display currency determines how quotes are presented to customers, utilizing real-time FX rates.
                      </p>
                    </div>
                  </div>

                </CardContent>
              </Card>
            </div>
          )}

          {/* DEAL CODES TAB */}
          {activeTab === "deals" && (
            <div className="space-y-6 animate-in fade-in">
              <Card className="bg-paper border-line shadow-sm">
                <CardHeader className="border-b border-line pb-4 bg-surface/50 flex flex-row items-center justify-between">
                  <div>
                    <CardTitle className="text-lg">Deal Codes</CardTitle>
                    <CardDescription>Manage corporate or promotional deal codes for flights.</CardDescription>
                  </div>
                  <Button className="bg-teal hover:bg-teal-dark gap-2 shadow-sm">
                    <Plus className="w-4 h-4" /> Add Code
                  </Button>
                </CardHeader>
                <CardContent className="p-0">
                  <Table>
                    <TableHeader className="bg-sand/30">
                      <TableRow>
                        <TableHead>Code</TableHead>
                        <TableHead>Airline</TableHead>
                        <TableHead>Description</TableHead>
                        <TableHead>Status</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      <TableRow className="hover:bg-sand/10">
                        <TableCell className="font-mono font-medium text-ink">CORP-DEL</TableCell>
                        <TableCell>Air India (AI)</TableCell>
                        <TableCell className="text-muted-foreground">Delhi Corporate Rates 2026</TableCell>
                        <TableCell><Badge className="bg-emerald-100 text-emerald-800 border-emerald-200">Active</Badge></TableCell>
                      </TableRow>
                      <TableRow className="hover:bg-sand/10">
                        <TableCell className="font-mono font-medium text-ink">INDIGOFEST</TableCell>
                        <TableCell>IndiGo (6E)</TableCell>
                        <TableCell className="text-muted-foreground">Festival Season 10% Off</TableCell>
                        <TableCell><Badge className="bg-emerald-100 text-emerald-800 border-emerald-200">Active</Badge></TableCell>
                      </TableRow>
                      <TableRow className="hover:bg-sand/10">
                        <TableCell className="font-mono font-medium text-muted-foreground line-through">SUMMER25</TableCell>
                        <TableCell className="text-muted-foreground">Vistara (UK)</TableCell>
                        <TableCell className="text-muted-foreground">Expired Summer Promo</TableCell>
                        <TableCell><Badge variant="outline" className="text-muted-foreground border-line">Expired</Badge></TableCell>
                      </TableRow>
                    </TableBody>
                  </Table>
                </CardContent>
              </Card>
            </div>
          )}

          {/* AI PREFERENCES TAB */}
          {activeTab === "ai" && (
            <div className="space-y-6 animate-in fade-in">
              <Card className="bg-paper border-line shadow-sm">
                <CardHeader className="border-b border-line pb-4 bg-surface/50">
                  <CardTitle className="text-lg">AI Assistant Preferences</CardTitle>
                  <CardDescription>Tune how the AI agent builds quotes and searches for you.</CardDescription>
                </CardHeader>
                <CardContent className="space-y-6 pt-6">
                  <div className="flex items-center justify-between border-b border-line pb-6">
                    <div>
                      <h4 className="text-sm font-medium text-ink">Enable AI Assistant</h4>
                      <p className="text-xs text-muted-foreground mt-1">Allow the AI to parse emails and auto-draft quotes.</p>
                    </div>
                    <label className="relative inline-flex items-center cursor-pointer">
                      <input type="checkbox" value="" className="sr-only peer" defaultChecked />
                      <div className="w-11 h-6 bg-line peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-line after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-teal"></div>
                    </label>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="space-y-2">
                      <label className="text-sm font-medium text-ink">Preferred Airlines</label>
                      <Input placeholder="e.g. 6E, AI, UK" className="bg-surface font-mono" />
                      <p className="text-xs text-muted-foreground">AI will prioritize these carriers in search results.</p>
                    </div>
                    <div className="space-y-2">
                      <label className="text-sm font-medium text-ink">Maximum Stops</label>
                      <select className="w-full border border-line rounded-md h-10 px-3 bg-surface text-sm">
                        <option>Direct flights only</option>
                        <option>Up to 1 stop</option>
                        <option selected>Up to 2 stops</option>
                      </select>
                    </div>
                    <div className="space-y-2">
                      <label className="text-sm font-medium text-ink">Default Cabin Class</label>
                      <select className="w-full border border-line rounded-md h-10 px-3 bg-surface text-sm">
                        <option selected>Economy</option>
                        <option>Premium Economy</option>
                        <option>Business</option>
                      </select>
                    </div>
                  </div>
                  
                  <div className="pt-4 border-t border-line">
                    <Button onClick={() => showMessage("AI Preferences saved.")} className="bg-teal hover:bg-teal-dark">Save AI Preferences</Button>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}

          {/* CUSTOM DOMAIN TAB */}
          {activeTab === "domain" && (
            <div className="space-y-6 animate-in fade-in">
              <Card className="bg-paper border-line shadow-sm">
                <CardHeader className="border-b border-line pb-4 bg-surface/50">
                  <CardTitle className="text-lg flex justify-between items-center">
                    Custom Domain & White-label
                    <Badge className="bg-teal text-white">Pro Feature</Badge>
                  </CardTitle>
                  <CardDescription>Host public quotes and payment pages on your own domain.</CardDescription>
                </CardHeader>
                <CardContent className="space-y-6 pt-6">
                  
                  <div className="space-y-6 relative before:absolute before:inset-0 before:ml-5 before:-translate-x-px md:before:mx-auto md:before:translate-x-0 before:h-full before:w-0.5 before:bg-gradient-to-b before:from-transparent before:via-line before:to-transparent">
                    {/* Step 1 */}
                    <div className="relative flex items-center justify-between md:justify-normal md:odd:flex-row-reverse group is-active">
                      <div className="flex items-center justify-center w-10 h-10 rounded-full border border-white bg-mint text-white shadow shrink-0 md:order-1 md:group-odd:-translate-x-1/2 md:group-even:translate-x-1/2 z-10">
                        <CheckCircle2 className="w-5 h-5" />
                      </div>
                      <div className="w-[calc(100%-4rem)] md:w-[calc(50%-2.5rem)] bg-surface p-4 rounded-lg border border-line shadow-sm">
                        <h4 className="font-semibold text-ink text-sm">1. Brand Profile Complete</h4>
                        <p className="text-xs text-muted-foreground mt-1">Logo and agency name are configured in Organization settings.</p>
                      </div>
                    </div>
                    
                    {/* Step 2 */}
                    <div className="relative flex items-center justify-between md:justify-normal md:odd:flex-row-reverse group">
                      <div className="flex items-center justify-center w-10 h-10 rounded-full border-2 border-teal bg-paper text-teal shadow shrink-0 md:order-1 md:group-odd:-translate-x-1/2 md:group-even:translate-x-1/2 z-10">
                        <Circle className="w-4 h-4 fill-current" />
                      </div>
                      <div className="w-[calc(100%-4rem)] md:w-[calc(50%-2.5rem)] bg-surface p-4 rounded-lg border border-teal/30 shadow-sm ring-1 ring-teal/10">
                        <h4 className="font-semibold text-ink text-sm">2. Enter Custom Domain</h4>
                        <div className="flex gap-2 mt-3">
                          <Input placeholder="e.g. quotes.myagency.com" className="bg-paper h-9 text-sm" />
                          <Button size="sm" className="bg-teal hover:bg-teal-dark h-9">Verify</Button>
                        </div>
                      </div>
                    </div>

                    {/* Step 3 */}
                    <div className="relative flex items-center justify-between md:justify-normal md:odd:flex-row-reverse group">
                      <div className="flex items-center justify-center w-10 h-10 rounded-full border border-line bg-paper text-muted-foreground shadow shrink-0 md:order-1 md:group-odd:-translate-x-1/2 md:group-even:translate-x-1/2 z-10">
                        3
                      </div>
                      <div className="w-[calc(100%-4rem)] md:w-[calc(50%-2.5rem)] bg-sand/30 p-4 rounded-lg border border-line/60">
                        <h4 className="font-semibold text-muted-foreground text-sm">3. Update DNS Records</h4>
                        <p className="text-xs text-muted-foreground/70 mt-1">Pending domain verification.</p>
                      </div>
                    </div>
                  </div>

                  <div className="pt-6 border-t border-line text-center">
                    <a href="#" className="inline-flex items-center text-sm font-medium text-teal hover:underline">
                      Read the White-label Setup Guide <ExternalLink className="w-3.5 h-3.5 ml-1" />
                    </a>
                  </div>

                </CardContent>
              </Card>
            </div>
          )}

          {/* NOTIFICATIONS TAB */}
          {activeTab === "notifications" && (
            <div className="space-y-6 animate-in fade-in">
              <Card className="bg-paper border-line shadow-sm">
                <CardHeader className="border-b border-line pb-4 bg-surface/50">
                  <CardTitle className="text-lg">Notifications</CardTitle>
                  <CardDescription>Manage how you receive alerts and booking updates.</CardDescription>
                </CardHeader>
                <CardContent className="space-y-6 pt-6">
                  
                  <div className="space-y-4">
                    <div className="flex items-center justify-between p-4 border border-line rounded-lg bg-surface">
                      <div>
                        <h4 className="text-sm font-medium text-ink flex items-center gap-2">Email Notifications</h4>
                        <p className="text-xs text-muted-foreground mt-1">Receive booking confirmations and quote payment alerts via email.</p>
                      </div>
                      <label className="relative inline-flex items-center cursor-pointer">
                        <input type="checkbox" value="" className="sr-only peer" defaultChecked />
                        <div className="w-11 h-6 bg-line peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-line after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-teal"></div>
                      </label>
                    </div>

                    <div className="flex items-center justify-between p-4 border border-line rounded-lg bg-surface">
                      <div>
                        <h4 className="text-sm font-medium text-ink flex items-center gap-2">WhatsApp Alerts</h4>
                        <p className="text-xs text-muted-foreground mt-1">Get instant pings for failed bookings and urgent supplier issues.</p>
                      </div>
                      <label className="relative inline-flex items-center cursor-pointer">
                        <input type="checkbox" value="" className="sr-only peer" defaultChecked />
                        <div className="w-11 h-6 bg-line peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-line after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-teal"></div>
                      </label>
                    </div>
                  </div>

                </CardContent>
              </Card>
            </div>
          )}

        </div>
      </div>
    </div>
  );
}
