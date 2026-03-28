import { NextResponse } from "next/server";
import {
  getMongoClient,
  GARY_DB_NAME,
  WAITLIST_COLLECTION,
} from "@/lib/mongodb";

export async function GET() {
  try {
    const client = await getMongoClient();
    const db = client.db(GARY_DB_NAME);
    const count = await db.collection(WAITLIST_COLLECTION).countDocuments();
    return NextResponse.json({ count });
  } catch (err) {
    console.error("[waitlist/count]", err);
    const misconfigured =
      err instanceof Error && err.message === "MONGODB_URI is not configured";
    return NextResponse.json(
      {
        error: misconfigured ? "misconfigured" : "unavailable",
        count: 0,
      },
      { status: 503 }
    );
  }
}
