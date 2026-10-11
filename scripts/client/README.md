# Vendored game-client readers

`casc/*`, `blp.ts` and `png.ts` read World of Warcraft's local CASC storage
by FileDataID, decode BLP2 textures and encode PNGs. They are used only by
`npm run extract:icons`.

They come from the WoW Forever Atlas project's `importers/wow-client`,
where they were written as original TypeScript implementations of the
binary formats documented in **wow.export**'s source
(https://github.com/Kruithne/wow.export, MIT, © Kruithne and Marlamin).
Because the algorithms and format layouts were learned from that code, its
MIT license applies and is reproduced in `WOW_EXPORT_LICENSE.txt`. Keep
this attribution if you redistribute these files.

Deliberately not supported: listfile/path lookups, Salsa20-encrypted
content, and CDN streaming (local installs only).
