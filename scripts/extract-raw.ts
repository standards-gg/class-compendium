/**
 * Extract textures by FileDataID from a local WoW: Forever install into PNG files at full size (no downsampling).
 *
 *   tsx scripts/extract-raw.ts <outDir> <id> [<id> ...]
 *
 * WOW_INSTALL_DIR overrides the default install path. Same vendored CASC reader + BLP decoder as extract-icons.ts.
 */
import { mkdirSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { decodeBlp } from "./client/blp.js";
import { LocalCasc } from "./client/casc/local-casc.js";
import { encodePng } from "./client/png.js";

const INSTALL_DIR = process.env.WOW_INSTALL_DIR ?? "C:/Program Files (x86)/World of Warcraft";
const PRODUCT = process.env.WOW_PRODUCT ?? "wow_classic_beta";

async function main() {
  const [outDir, ...idArgs] = process.argv.slice(2);
  const ids = idArgs.map((s) => Number(s));
  mkdirSync(outDir, { recursive: true });
  const casc = await LocalCasc.open(INSTALL_DIR, PRODUCT);
  for (const id of ids) {
    try {
      const img = decodeBlp(casc.getFileByFileDataId(id));
      writeFileSync(join(outDir, `${id}.png`), encodePng(img.width, img.height, img.rgba));
      console.error(`${id}: ${img.width}x${img.height}`);
    } catch (err) {
      console.error(`${id}: ${(err as Error).message}`);
    }
  }
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
