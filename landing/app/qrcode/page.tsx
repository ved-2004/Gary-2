import Image from "next/image";
import Link from "next/link";
import QRCode from "qrcode";

const TARGET_URL = "https://gary2.adityakotha.xyz/";
const MODULE_SIZE = 10;
const QUIET_ZONE = 28;
const FINDER_SIZE = 7;

function isWithinFinderPattern(x: number, y: number, size: number) {
  const topLeft = x < FINDER_SIZE && y < FINDER_SIZE;
  const topRight = x >= size - FINDER_SIZE && y < FINDER_SIZE;
  const bottomLeft = x < FINDER_SIZE && y >= size - FINDER_SIZE;
  return topLeft || topRight || bottomLeft;
}

function renderFinderPattern(x: number, y: number, totalSize: number) {
  return `
    <rect x="${x}" y="${y}" width="${totalSize}" height="${totalSize}" rx="${totalSize * 0.26}" fill="#111111" />
    <rect x="${x + MODULE_SIZE * 1.2}" y="${y + MODULE_SIZE * 1.2}" width="${totalSize - MODULE_SIZE * 2.4}" height="${totalSize - MODULE_SIZE * 2.4}" rx="${totalSize * 0.18}" fill="#fbf8f3" />
    <rect x="${x + MODULE_SIZE * 2.25}" y="${y + MODULE_SIZE * 2.25}" width="${totalSize - MODULE_SIZE * 4.5}" height="${totalSize - MODULE_SIZE * 4.5}" rx="${totalSize * 0.12}" fill="#7c5fd6" />
  `;
}

async function buildRoundedQrMarkup(url: string) {
  const qr = QRCode.create(url, {
    errorCorrectionLevel: "H",
    margin: 0,
  });
  const size = qr.modules.size;
  const totalModulesSize = size * MODULE_SIZE;
  const canvasSize = totalModulesSize + QUIET_ZONE * 2;
  const finderPixelSize = FINDER_SIZE * MODULE_SIZE;

  const darkModules: string[] = [];

  for (let y = 0; y < size; y += 1) {
    for (let x = 0; x < size; x += 1) {
      if (!qr.modules.get(x, y) || isWithinFinderPattern(x, y, size)) {
        continue;
      }

      darkModules.push(
        `<rect x="${QUIET_ZONE + x * MODULE_SIZE + 0.9}" y="${QUIET_ZONE + y * MODULE_SIZE + 0.9}" width="${MODULE_SIZE - 1.8}" height="${MODULE_SIZE - 1.8}" rx="${MODULE_SIZE * 0.32}" fill="#111111" />`,
      );
    }
  }

  return `
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${canvasSize} ${canvasSize}" role="img" aria-label="QR code for Gary.2">
      <rect width="${canvasSize}" height="${canvasSize}" rx="48" fill="#fbf8f3" />
      <rect x="10" y="10" width="${canvasSize - 20}" height="${canvasSize - 20}" rx="40" fill="none" stroke="rgba(124,95,214,0.12)" stroke-width="2" />
      ${renderFinderPattern(QUIET_ZONE, QUIET_ZONE, finderPixelSize)}
      ${renderFinderPattern(QUIET_ZONE + totalModulesSize - finderPixelSize, QUIET_ZONE, finderPixelSize)}
      ${renderFinderPattern(QUIET_ZONE, QUIET_ZONE + totalModulesSize - finderPixelSize, finderPixelSize)}
      ${darkModules.join("")}
    </svg>
  `;
}

export default async function QrCodePage() {
  const qrMarkup = await buildRoundedQrMarkup(TARGET_URL);

  return (
    <main className="min-h-screen overflow-hidden bg-[#f5f3f0] text-[#111111]">
      <div
        aria-hidden="true"
        className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_top,rgba(177,158,239,0.35),transparent_35%),radial-gradient(circle_at_80%_20%,rgba(124,95,214,0.16),transparent_24%),linear-gradient(180deg,#f8f5f1_0%,#f1eeea_100%)]"
      />

      <div
        aria-hidden="true"
        className="pointer-events-none absolute inset-0 opacity-35"
        style={{
          backgroundImage:
            "linear-gradient(rgba(17,17,17,0.05) 1px, transparent 1px), linear-gradient(90deg, rgba(17,17,17,0.05) 1px, transparent 1px)",
          backgroundSize: "28px 28px",
          maskImage:
            "radial-gradient(circle at center, rgba(0,0,0,0.95) 0%, rgba(0,0,0,0.82) 38%, rgba(0,0,0,0.12) 76%, transparent 100%)",
          WebkitMaskImage:
            "radial-gradient(circle at center, rgba(0,0,0,0.95) 0%, rgba(0,0,0,0.82) 38%, rgba(0,0,0,0.12) 76%, transparent 100%)",
        }}
      />

      <section className="relative flex min-h-screen items-center justify-center px-5 py-12 sm:px-8">
        <div className="w-full max-w-[38rem]">
          <div className="rounded-[36px] border border-black/8 bg-[rgba(255,255,255,0.78)] p-4 shadow-[0_24px_80px_rgba(17,17,17,0.12)] backdrop-blur-2xl sm:p-6">
            <div className="rounded-[30px] border border-[rgba(124,95,214,0.14)] bg-[linear-gradient(180deg,rgba(255,255,255,0.92),rgba(250,247,243,0.94))] p-5 shadow-[inset_0_1px_0_rgba(255,255,255,0.75)] sm:p-7">
              <div className="flex flex-col items-center text-center">
                <div className="rounded-full border border-[rgba(124,95,214,0.16)] bg-[rgba(124,95,214,0.08)] px-4 py-2 font-[family-name:var(--font-geist-pixel-square)] text-[10px] uppercase tracking-[0.18em] text-[#7c5fd6]">
                  Gary.2
                </div>
                <h1 className="mt-5 font-[family-name:var(--font-geist-pixel-square)] text-[clamp(26px,5vw,42px)] leading-[1.08] text-[#111111]">
                  Scan to open the live site.
                </h1>
                <p className="mt-3 max-w-md text-[14px] leading-7 text-black/58">
                  Clean link. One scan. Straight into Gary.2.
                </p>
              </div>

              <div className="mx-auto mt-8 w-full max-w-[28rem]">
                <div className="relative rounded-[32px] border border-black/8 bg-white p-5 shadow-[0_20px_50px_rgba(17,17,17,0.1)] sm:p-6">
                  <div
                    className="overflow-hidden rounded-[28px] bg-[#fbf8f3]"
                    dangerouslySetInnerHTML={{ __html: qrMarkup }}
                  />

                  <div className="pointer-events-none absolute inset-0 flex items-center justify-center">
                    <div className="rounded-[26px] border border-[rgba(124,95,214,0.16)] bg-white/96 p-3 shadow-[0_14px_30px_rgba(17,17,17,0.16)] backdrop-blur-sm">
                      <div className="overflow-hidden rounded-[18px] bg-[#111111] p-2">
                        <Image
                          src="/FinalLogo.png"
                          alt="Gary.2 logo"
                          width={72}
                          height={72}
                          className="h-[3.6rem] w-[3.6rem] rounded-[14px] object-contain"
                          priority
                        />
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <div className="mt-8 flex flex-col items-center gap-3 text-center">
                <div className="rounded-full border border-black/8 bg-[#f7f3ee] px-4 py-2 font-[family-name:var(--font-geist-pixel-square)] text-[11px] text-black/62">
                  {TARGET_URL}
                </div>
                <Link
                  href={TARGET_URL}
                  className="rounded-full bg-[#111111] px-5 py-3 font-[family-name:var(--font-geist-pixel-square)] text-[11px] text-white transition hover:-translate-y-0.5 hover:bg-[#7c5fd6] hover:shadow-[0_10px_26px_rgba(124,95,214,0.28)]"
                >
                  Open in browser
                </Link>
              </div>
            </div>
          </div>
        </div>
      </section>
    </main>
  );
}
