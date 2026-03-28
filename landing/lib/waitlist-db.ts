import type { Collection, Db } from "mongodb";
import { MongoServerError } from "mongodb";
import { WAITLIST_COLLECTION } from "@/lib/mongodb";

/** Shown when this email is already in the waitlist. */
export const WAITLIST_DUPLICATE_MESSAGE =
  "You're already on the list with this email. We'll reach out when there's news—no need to sign up again.";

let emailIndexEnsured = false;

/**
 * Ensures a unique index on `email` so concurrent signups can't create duplicates.
 * If the collection already has duplicate emails, indexing may fail; we log and continue.
 */
export async function ensureWaitlistEmailIndex(db: Db): Promise<void> {
  if (emailIndexEnsured) return;
  const col = db.collection(WAITLIST_COLLECTION);
  try {
    await col.createIndex(
      { email: 1 },
      {
        unique: true,
        name: "waitlist_email_unique",
        background: true,
      }
    );
  } catch (err) {
    console.warn(
      "[waitlist] could not ensure unique email index (existing duplicates or conflict):",
      err
    );
  }
  emailIndexEnsured = true;
}

export async function waitlistEmailExists(
  col: Collection,
  email: string
): Promise<boolean> {
  const found = await col.findOne({ email }, { projection: { _id: 1 } });
  return found !== null;
}

export function isMongoDuplicateKeyError(err: unknown): boolean {
  return err instanceof MongoServerError && err.code === 11000;
}
