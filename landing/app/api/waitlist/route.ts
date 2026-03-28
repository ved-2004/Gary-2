import { NextResponse } from "next/server";
import {
  getMongoClient,
  GARY_DB_NAME,
  WAITLIST_COLLECTION,
} from "@/lib/mongodb";
import { validateSignupEmail } from "@/lib/validate-email";

const MAX_MESSAGE = 4000;

export async function POST(request: Request) {
  let body: unknown;
  try {
    body = await request.json();
  } catch {
    return NextResponse.json({ error: "Invalid JSON" }, { status: 400 });
  }

  if (!body || typeof body !== "object") {
    return NextResponse.json({ error: "Invalid body" }, { status: 400 });
  }

  const { name, email, message } = body as Record<string, unknown>;

  const nameStr =
    typeof name === "string" ? name.trim() : "";
  const emailStr =
    typeof email === "string" ? email.trim().toLowerCase() : "";
  const messageStr =
    typeof message === "string" ? message.trim().slice(0, MAX_MESSAGE) : "";

  if (nameStr.length < 1) {
    return NextResponse.json({ error: "Name is required" }, { status: 400 });
  }
  if (nameStr.length > 200) {
    return NextResponse.json({ error: "Name is too long" }, { status: 400 });
  }
  const emailValidation = await validateSignupEmail(emailStr);
  if (!emailValidation.ok) {
    return NextResponse.json({ error: emailValidation.error }, { status: 400 });
  }

  try {
    const client = await getMongoClient();
    const db = client.db(GARY_DB_NAME);
    await db.collection(WAITLIST_COLLECTION).insertOne({
      name: nameStr,
      email: emailStr,
      message: messageStr || undefined,
      createdAt: new Date(),
      source: "reanimate-landing",
    });
  } catch (err) {
    console.error("[waitlist]", err);
    const msg =
      err instanceof Error && err.message === "MONGODB_URI is not configured"
        ? "Server is not configured for signups yet"
        : "Could not save your signup";
    return NextResponse.json({ error: msg }, { status: 500 });
  }

  return NextResponse.json({ ok: true });
}
