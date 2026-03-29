import { MongoClient } from "mongodb";

declare global {
  var _gary2MongoClient: Promise<MongoClient> | undefined;
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
  if (!global._gary2MongoClient) {
    global._gary2MongoClient = new MongoClient(uri).connect();
  }
  return global._gary2MongoClient;
}

export const GARY_DB_NAME = "gary";
export const WAITLIST_COLLECTION = "waitlist";
