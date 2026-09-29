import { redirect } from "next/navigation";

export default async function CrmDetailRedirect({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  redirect(`/app/customers/${id}`);
}
