import { MongoClient } from "mongodb";

declare global {
  // eslint-disable-next-line no-var -- required for HMR-safe singleton
  var _reanimateMongoClient: Promise<MongoClient> | undefined;
}

function getMongoUri(): string {
  const fromPrimary = process.env.MONGODB_URI?.trim();
  const fromAlias = process.env.MONGO_URI?.trim();
  return (fromPrimary || fromAlias || "").trim();
}

export function getMongoClient(): Promise<MongoClient> {
  const uri = getMongoUri();
  if (!uri) {
    throw new Error("MONGODB_URI is not configured");
  }
  if (!global._reanimateMongoClient) {
    global._reanimateMongoClient = new MongoClient(uri).connect();
  }
  return global._reanimateMongoClient;
}

export const GARY_DB_NAME = "gary";
export const WAITLIST_COLLECTION = "waitlist";
