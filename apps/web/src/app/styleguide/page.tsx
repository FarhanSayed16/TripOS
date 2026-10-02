'use client';

import { PageTransition } from "@/components/PageTransition";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Table, TableHeader, TableRow, TableHead, TableBody, TableCell } from "@/components/ui/table";
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from "@/components/ui/select";
import { Dialog, DialogTrigger, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog";
import { Alert, AlertTitle, AlertDescription } from "@/components/ui/alert";
import { AlertCircle, CheckCircle2 } from "lucide-react";

export default function StyleguidePage() {
  return (
    <PageTransition>
      <div className="p-8 max-w-5xl mx-auto space-y-12">
        <div>
          <h1 className="text-3xl font-bold text-ink mb-2">Design System Styleguide</h1>
          <p className="text-muted-foreground">A demonstration of all loaded primitives and custom tokens.</p>
        </div>

        <section className="space-y-4">
          <h2 className="text-xl font-semibold border-b pb-2">Custom Brand Tokens</h2>
          <div className="flex gap-4 flex-wrap">
            <div className="h-16 w-16 rounded-md bg-ink text-paper flex items-center justify-center text-xs">Ink</div>
            <div className="h-16 w-16 rounded-md bg-paper border flex items-center justify-center text-xs">Paper</div>
            <div className="h-16 w-16 rounded-md bg-teal text-white flex items-center justify-center text-xs">Teal</div>
            <div className="h-16 w-16 rounded-md bg-coral text-white flex items-center justify-center text-xs">Coral</div>
            <div className="h-16 w-16 rounded-md bg-amber text-white flex items-center justify-center text-xs">Amber</div>
            <div className="h-16 w-16 rounded-md bg-mint text-white flex items-center justify-center text-xs">Mint</div>
            <div className="h-16 w-16 rounded-md bg-focus text-white flex items-center justify-center text-xs">Focus</div>
            <div className="h-16 w-16 rounded-md bg-line flex items-center justify-center text-xs text-ink">Line</div>
          </div>
        </section>

        <section className="space-y-4">
          <h2 className="text-xl font-semibold border-b pb-2">Buttons</h2>
          <div className="flex gap-4 items-center flex-wrap">
            <Button>Primary</Button>
            <Button variant="secondary">Secondary</Button>
            <Button variant="destructive">Destructive</Button>
            <Button variant="outline">Outline</Button>
            <Button variant="ghost">Ghost</Button>
            <Button variant="link">Link</Button>
            <Button disabled>Disabled</Button>
          </div>
        </section>

        <section className="space-y-4">
          <h2 className="text-xl font-semibold border-b pb-2">Inputs & Controls</h2>
          <div className="grid md:grid-cols-2 gap-8">
            <div className="space-y-4">
              <Input placeholder="Standard text input..." />
              <Input placeholder="Disabled input..." disabled />
              <Textarea placeholder="Textarea input..." />
            </div>
            <div className="space-y-4">
              <Select>
                <SelectTrigger>
                  <SelectValue placeholder="Select an option" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="1">Option 1</SelectItem>
                  <SelectItem value="2">Option 2</SelectItem>
                  <SelectItem value="3">Option 3</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </section>

        <section className="space-y-4">
          <h2 className="text-xl font-semibold border-b pb-2">Badges & Indicators</h2>
          <div className="flex gap-4 items-center flex-wrap">
            <Badge>Default</Badge>
            <Badge variant="secondary">Secondary</Badge>
            <Badge variant="outline">Outline</Badge>
            <Badge variant="destructive">Destructive</Badge>
            <Badge variant="confirmed">Confirmed</Badge>
            <Badge variant="pending">Pending</Badge>
            <Badge variant="failed">Failed</Badge>
            <Badge variant="live">Live</Badge>
            <Badge variant="simulated">Simulated</Badge>
            <Badge variant="mock">Mock</Badge>
          </div>
        </section>

        <section className="space-y-4">
          <h2 className="text-xl font-semibold border-b pb-2">Alerts</h2>
          <div className="flex flex-col gap-4">
            <Alert>
              <CheckCircle2 className="h-4 w-4" />
              <AlertTitle>Success</AlertTitle>
              <AlertDescription>Your changes have been saved successfully.</AlertDescription>
            </Alert>
            <Alert variant="warning">
              <AlertCircle className="h-4 w-4" />
              <AlertTitle>Warning</AlertTitle>
              <AlertDescription>This is a warning alert using the amber token.</AlertDescription>
            </Alert>
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertTitle>Error</AlertTitle>
              <AlertDescription>Something went wrong! Please try again.</AlertDescription>
            </Alert>
          </div>
        </section>

        <section className="space-y-4">
          <h2 className="text-xl font-semibold border-b pb-2">Overlays (Modals & Toasts)</h2>
          <div className="flex gap-4 items-center">
            <Dialog>
              <DialogTrigger render={<Button variant="outline" />}>
                Open Modal
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>Are you absolutely sure?</DialogTitle>
                  <DialogDescription>
                    This action cannot be undone. This will permanently delete your account and remove your data from our servers.
                  </DialogDescription>
                </DialogHeader>
              </DialogContent>
            </Dialog>
            <Button variant="outline" onClick={() => alert("Toast integration requires Toaster in layout, omitted here for brevity")}>Trigger Toast</Button>
          </div>
        </section>

        <section className="space-y-4">
          <h2 className="text-xl font-semibold border-b pb-2">Tables & Empty States</h2>
          <Card>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Invoice</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Method</TableHead>
                  <TableHead className="text-right">Amount</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                <TableRow>
                  <TableCell className="font-medium">INV001</TableCell>
                  <TableCell><Badge className="bg-mint text-white hover:bg-mint/80">Paid</Badge></TableCell>
                  <TableCell>Credit Card</TableCell>
                  <TableCell className="text-right">₹2,500.00</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell className="font-medium">INV002</TableCell>
                  <TableCell><Badge variant="outline">Pending</Badge></TableCell>
                  <TableCell>Bank Transfer</TableCell>
                  <TableCell className="text-right">₹15,000.00</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell colSpan={4} className="h-24 text-center text-muted-foreground">
                    No more results found.
                  </TableCell>
                </TableRow>
              </TableBody>
            </Table>
          </Card>
        </section>

        <section className="space-y-4">
          <h2 className="text-xl font-semibold border-b pb-2">Skeletons & Loading</h2>
          <div className="flex items-center space-x-4">
            <Skeleton className="h-12 w-12 rounded-full" />
            <div className="space-y-2">
              <Skeleton className="h-4 w-[250px]" />
              <Skeleton className="h-4 w-[200px]" />
            </div>
          </div>
        </section>

      </div>
    </PageTransition>
  );
}
