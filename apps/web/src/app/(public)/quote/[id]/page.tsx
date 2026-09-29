import { redirect } from "next/navigation";

/** Legacy path — plan uses `/q/[token]`. */
export default async function LegacyQuoteRedirect({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  redirect(`/q/${id}`);
}
