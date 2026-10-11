/**
 * Extract icons by FileDataID from a local WoW: Forever install into PNG files (64px).
 * Uses the vendored CASC reader + BLP decoder in ./client (from wow.export, MIT, see client/WOW_EXPORT_LICENSE.txt).
 *
 *   tsx scripts/extract-icons.ts <ids.json> <outDir>
 *
 * WOW_INSTALL_DIR overrides the default install path.
 */
import { existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { decodeBlp, type DecodedImage } from "./client/blp.js";
import { LocalCasc } from "./client/casc/local-casc.js";
import { encodePng } from "./client/png.js";

const INSTALL_DIR = process.env.WOW_INSTALL_DIR ?? "C:/Program Files (x86)/World of Warcraft";
const PRODUCT = "wow_classic_beta";
const SIZE = 64;

function toSize(img: DecodedImage): DecodedImage {
  if (img.width <= SIZE && img.height <= SIZE) return img;
  const fx = Math.round(img.width / SIZE);
  const fy = Math.round(img.height / SIZE);
  const out = Buffer.alloc(SIZE * SIZE * 4);
  for (let y = 0; y < SIZE; y++) {
    for (let x = 0; x < SIZE; x++) {
      const acc = [0, 0, 0, 0];
      for (let dy = 0; dy < fy; dy++) {
        for (let dx = 0; dx < fx; dx++) {
          const i = ((y * fy + dy) * img.width + (x * fx + dx)) * 4;
          for (let c = 0; c < 4; c++) acc[c] += img.rgba[i + c];
        }
      }
      for (let c = 0; c < 4; c++) out[(y * SIZE + x) * 4 + c] = Math.round(acc[c] / (fx * fy));
    }
  }
  return { width: SIZE, height: SIZE, rgba: out };
}

async function main() {
  const [idsPath, outDir] = process.argv.slice(2);
  const ids = JSON.parse(readFileSync(idsPath, "utf-8")) as number[];
  mkdirSync(outDir, { recursive: true });
  const todo = ids.filter((id) => !existsSync(join(outDir, `${id}.png`)));
  console.error(`${ids.length} requested, ${todo.length} to extract from ${INSTALL_DIR}`);
  if (!todo.length) return;
  const casc = await LocalCasc.open(INSTALL_DIR, PRODUCT);
  let ok = 0;
  const failed: number[] = [];
  for (const id of todo) {
    try {
      const img = toSize(decodeBlp(casc.getFileByFileDataId(id)));
      writeFileSync(join(outDir, `${id}.png`), encodePng(img.width, img.height, img.rgba));
      ok++;
    } catch (err) {
      failed.push(id);
      if (failed.length <= 8) console.error(`  ${id}: ${(err as Error).message}`);
    }
  }
  console.error(`extracted ${ok}, failed ${failed.length}`);
  writeFileSync(join(outDir, "_failed.json"), JSON.stringify(failed));
}
main().catch((e) => { console.error(e); process.exitCode = 1; });
