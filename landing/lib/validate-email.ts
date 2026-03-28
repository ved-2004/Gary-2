import dns from "node:dns/promises";

/** Lower-case list of common throwaway / disposable providers. */
const DISPOSABLE_DOMAINS = new Set(
  [
    "mailinator.com",
    "guerrillamail.com",
    "guerrillamailblock.com",
    "guerrillamail.net",
    "sharklasers.com",
    "yopmail.com",
    "yopmail.fr",
    "tempmail.com",
    "throwaway.email",
    "10minutemail.com",
    "10minutemail.net",
    "trashmail.com",
    "fakeinbox.com",
    "maildrop.cc",
    "getnada.com",
    "temp-mail.org",
    "dispostable.com",
    "mailnesia.com",
    "mailcatch.com",
    "spam4.me",
    "trashmail.de",
    "emailondeck.com",
    "moakt.com",
    "burnermail.io",
    "tempail.com",
    "inboxkitten.com",
    "mohmal.com",
    "emailfake.com",
    "mail.tm",
    "harakirimail.com",
    "tempinbox.com",
    "discard.email",
    "trashmail.ws",
    "mail-temporaire.fr",
    "tempr.email",
  ].map((d) => d.toLowerCase())
);

const DNS_TIMEOUT_MS = 6000;

function withTimeout<T>(promise: Promise<T>, ms: number): Promise<T> {
  return new Promise((resolve, reject) => {
    const t = setTimeout(() => reject(new Error("dns_timeout")), ms);
    promise.then(
      (v) => {
        clearTimeout(t);
        resolve(v);
      },
      (e: unknown) => {
        clearTimeout(t);
        reject(e);
      }
    );
  });
}

function isNotFoundError(err: unknown): boolean {
  const code =
    err && typeof err === "object" && "code" in err
      ? String((err as NodeJS.ErrnoException).code)
      : "";
  return code === "ENOTFOUND" || code === "ENODATA";
}

/**
 * Stricter than HTML5 — still allows most real addresses;
 * blocks obvious junk (length, structure, no dot in domain, etc.).
 */
export function isPlausibleEmailFormat(email: string): boolean {
  const e = email.trim().toLowerCase();
  if (e.length < 5 || e.length > 254) return false;
  const at = e.lastIndexOf("@");
  if (at < 1 || at !== e.indexOf("@")) return false;
  const local = e.slice(0, at);
  const domain = e.slice(at + 1);
  if (local.length > 64 || domain.length > 253) return false;
  if (domain.startsWith(".") || domain.endsWith(".") || domain.includes(".."))
    return false;
  if (!isValidDomainStructure(domain)) return false;
  if (!/^[a-z0-9](?:[a-z0-9._+-]*[a-z0-9])?$/i.test(local)) return false;
  if (local.includes("..")) return false;
  return true;
}

function isValidDomainStructure(domain: string): boolean {
  const labels = domain.toLowerCase().split(".");
  if (labels.length < 2) return false;
  for (const lab of labels) {
    if (lab.length < 1 || lab.length > 63) return false;
    if (!/^[a-z0-9](?:[a-z0-9-]*[a-z0-9])?$/.test(lab)) return false;
  }
  const tld = labels[labels.length - 1];
  if (tld.length < 2 || tld.length > 63 || /^[0-9]+$/.test(tld)) return false;
  return true;
}

export function isDisposableDomain(domain: string): boolean {
  const d = domain.toLowerCase();
  if (DISPOSABLE_DOMAINS.has(d)) return true;
  for (const blocked of DISPOSABLE_DOMAINS) {
    if (d.endsWith(`.${blocked}`)) return true;
  }
  return false;
}

async function domainCanReceiveMail(domain: string): Promise<boolean> {
  const d = domain.toLowerCase();
  try {
    const mx = await withTimeout(dns.resolveMx(d), DNS_TIMEOUT_MS);
    if (mx.length > 0) return true;
  } catch (err) {
    if (err instanceof Error && err.message === "dns_timeout") return false;
    if (isNotFoundError(err)) return false;
  }
  try {
    const a = await withTimeout(dns.resolve4(d), DNS_TIMEOUT_MS);
    if (a.length > 0) return true;
  } catch (err) {
    if (err instanceof Error && err.message === "dns_timeout") return false;
    if (isNotFoundError(err)) {
      /* fall through to AAAA */
    }
  }
  try {
    const aaaa = await withTimeout(dns.resolve6(d), DNS_TIMEOUT_MS);
    return aaaa.length > 0;
  } catch (err) {
    if (err instanceof Error && err.message === "dns_timeout") return false;
    return false;
  }
}

export async function validateSignupEmail(
  email: string
): Promise<{ ok: true } | { ok: false; error: string }> {
  const normalized = email.trim().toLowerCase();
  if (!isPlausibleEmailFormat(normalized)) {
    return { ok: false, error: "That doesn't look like a valid email address." };
  }
  const domain = normalized.slice(normalized.lastIndexOf("@") + 1);
  if (isDisposableDomain(domain)) {
    return {
      ok: false,
      error:
        "Please use a real work or personal inbox—temporary email addresses aren't accepted.",
    };
  }
  const reachable = await domainCanReceiveMail(domain);
  if (!reachable) {
    return {
      ok: false,
      error:
        "We couldn't verify that email domain. Check for typos or try another address.",
    };
  }
  return { ok: true };
}
