<p align="center"><img src="assets/logo.png" width="200" alt="logo"></p>

# WoW Forever · Class Compendium

**[Open the live site →](https://standards-gg.github.io/class-compendium/)** Pick a class, get **10 slides**: build and talent order, rotation and panic buttons, a level plan with every trainer rank, stats and gear, dungeons, races, professions, macros and the 31–60 trainer list. Hover any icon for its in-game tooltip.

> The slides are an **editable starting point**: builds, rotations and picks are a matter of taste, not official knowledge. Edit `data/guides/<class>.json` and rebuild to make them yours.

## Classes

| Class | Spec |
|-------|------|
| [Warrior](https://standards-gg.github.io/class-compendium/warrior/) | Protection |
| [Paladin](https://standards-gg.github.io/class-compendium/paladin/) | Retribution |
| [Hunter](https://standards-gg.github.io/class-compendium/hunter/) | Beast Mastery |
| [Rogue](https://standards-gg.github.io/class-compendium/rogue/) | Combat |
| [Priest](https://standards-gg.github.io/class-compendium/priest/) | Shadow |
| [Shaman](https://standards-gg.github.io/class-compendium/shaman/) | Enhancement |
| [Mage](https://standards-gg.github.io/class-compendium/mage/) | Frost |
| [Warlock](https://standards-gg.github.io/class-compendium/warlock/) | Affliction |
| [Druid](https://standards-gg.github.io/class-compendium/druid/) | Feral |

## The 10 slides

1. **Cover**: class, spec, and a link to the recommended build in the [talent calculator](https://talents.standards.gg).
2. **The build**: the talent tree with the guide's ranks and the point-by-point order from level 10.
3. **Rotation & buttons**: core priorities, rotation per level range, panic buttons.
4. **Level plan**: every trainer ability and exact rank by level 1–30, with the talent points spent at those levels.
5. **Stats & gear**: stat priority, weapon and gear tips, things to remember.
6. **Dungeons & gear**: the 35 dungeons by level, gear picks and group tips.
7. **Races**: Alliance and Horde with ratings and every racial.
8. **Professions**: the guide's picks plus the Forever profession bonuses.
9. **Macros & trainers**.
10. **After 30**: trainer abilities 31–60.

## Hover tooltips

- **Abilities, poisons, professions, consumables**: Blizzard's WoW Forever client data (product `wow_classic_beta`, build 1.60.1.70338) via wago.tools, rendered with `scripts/spelltext.py`. Level plan icons show the exact rank taught at that level.
- **Talents and racials**: the [Standards.gg talent calculator](https://talents.standards.gg) data (shows the rank in the build, plus the next rank).
- Not covered: items (dungeon weapons, gear). Item stats come from the game server and are not in the client tables.

## Edit and rebuild

Slide content for each class lives in `data/guides/<class>.json` (build order, rotation, stats, races, professions, macros, tips). Everything else is generated from game data.

```bash
python build_decks.py           # slides/<class>/*.html (all classes except Rogue)
python render_decks.py          # thumbnails (needs Microsoft Edge; set EDGE if installed elsewhere)
python build_site.py            # landing page, viewer, data/decks.json
```

Regenerating the game data (needs the DB2 CSVs from wago.tools in `$DB2_CACHE`, a local WoW: Forever install for icons and the forevertalent repo for talent text):

```bash
python scripts/build_classes.py                       # data/classes.json + tooltips
tsx scripts/extract-icons.ts <ids.json> <outDir>      # icons from your own install
python scripts/make_icons.py                          # crisp 128 px icons
python scripts/build_tooltips.py                      # Combat Rogue deck tooltips
```

The hand-made Combat Rogue deck is `build.py` + `render.py` (PNGs and a PDF in `png/` and `Combat-Rogue-1-30.pdf`).

