# Chernarus Town Centers

In-game center coordinates for all 78 named towns and cities of Chernarus, for use when
placing events, spawn points, zones, or other position-based server config.

Source data: town names + keypad grid references from
<https://www.mydayz.eu/docs/chernarus/towns-and-cities/>.
Centers were computed locally — see **Method** below. Machine-readable copies:
[`town-centers.csv`](town-centers.csv) and [`town-centers.json`](town-centers.json).

## Coordinates

DayZ world coordinates: `x` = east/west, `z` = north/south (origin 0,0 at the south-west
corner; map is 15360 x 15360 m). Terrain height (`y`) is not included — query it in-game or
let the engine surface-snap. `building_count` = number of building objects within 250 m of the
center (a rough size/confidence signal).

| Town | Category | Sector | Grid X | Grid Y | center x | center z | buildings |
|------|----------|--------|-------:|-------:|---------:|---------:|----------:|
| Balota | Village | South-West | 045 | 129 | 4471 | 2452 | 77 |
| Belaya Polana | Hamlet | North-East | 140 | 002 | 14086 | 15013 | 43 |
| Berezhki | Hamlet | East | 151 | 015 | 15186 | 13829 | 27 |
| Berezino | Large City | East | 129 | 053 | 12908 | 10096 | 198 |
| Bogatyrka | Hamlet | West | 014 | 064 | 1542 | 9035 | 28 |
| Bor | Village | South-West | 033 | 114 | 3283 | 3935 | 57 |
| Chernaya Polana | Town | North-East | 121 | 016 | 12087 | 13796 | 113 |
| Chernogorsk | Large City | South | 067 | 127 | 6602 | 2534 | 311 |
| Dobroe | Hamlet | North-East | 129 | 003 | 12927 | 15038 | 33 |
| Dolina | Village | South-East | 112 | 087 | 11301 | 6587 | 81 |
| Drozhino | Hamlet | South-West | 033 | 104 | 3355 | 4928 | 22 |
| Dubky | Village | South | 066 | 117 | 6659 | 3599 | 68 |
| Dubrovka | Village | East | 104 | 055 | 10482 | 9790 | 47 |
| Elektrozavodsk | Large City | South-East | 103 | 132 | 10475 | 2252 | 231 |
| Gorka | Village | Center | 095 | 065 | 9524 | 8835 | 123 |
| Grishino | Town | North | 059 | 050 | 5991 | 10304 | 76 |
| Guglovo | Hamlet | Center | 084 | 086 | 8416 | 6646 | 39 |
| Gvozdno | Village | North | 085 | 034 | 8566 | 11953 | 35 |
| Kabanino | Village | Center | 053 | 067 | 5355 | 8587 | 43 |
| Kamenka | Village | South-West | 019 | 131 | 1842 | 2215 | 68 |
| Kamensk | Village | North | 066 | 008 | 6646 | 14430 | 77 |
| Kamyshovo | Village | South-East | 121 | 118 | 12069 | 3541 | 85 |
| Karmanovka | Village | North-East | 125 | 007 | 12646 | 14717 | 45 |
| Khelm | Village | North-East | 122 | 044 | 12296 | 10896 | 69 |
| Komarovo | Village | South-West | 036 | 128 | 3622 | 2491 | 55 |
| Kozlovka | Village | South-West | 044 | 107 | 4396 | 4641 | 45 |
| Krasnoe | Hamlet | North | 064 | 003 | 6444 | 14936 | 12 |
| Krasnostav | Town | North-East | 111 | 030 | 11163 | 12264 | 106 |
| Lopatino | Village | West | 027 | 053 | 2750 | 9948 | 74 |
| Mamino | Hamlet | North | 079 | 023 | 7980 | 13045 | 23 |
| Mogilevka | Village | South | 075 | 102 | 7572 | 5144 | 65 |
| Msta | Village | East | 112 | 098 | 11306 | 5467 | 47 |
| Myshkino | Village | West | 020 | 080 | 1994 | 7314 | 49 |
| Nadezhdino | Village | South | 058 | 106 | 5859 | 4756 | 48 |
| Nagornoe | Hamlet | North-East | 092 | 007 | 9342 | 14602 | 89 |
| Nizhnoye | Village | East | 129 | 074 | 12913 | 8101 | 78 |
| Novaya Petrovka | Small City | North-West | 036 | 022 | 3380 | 13049 | 179 |
| Novodmitrovsk | Large City | North-East | 116 | 009 | 11627 | 14472 | 178 |
| Novoselky | Village | South | 061 | 121 | 6179 | 3186 | 141 |
| Novy Sobor | Village | Center | 070 | 076 | 7100 | 7700 | 65 |
| Olsha | Village | North-East | 133 | 024 | 13295 | 12976 | 65 |
| Orlovets | Village | East | 121 | 080 | 12137 | 7264 | 64 |
| Pavlovo | Village | South-West | 016 | 115 | 1694 | 3830 | 60 |
| Pogorevka | Village | West | 044 | 089 | 4475 | 6418 | 43 |
| Polana | Town | East | 106 | 073 | 10689 | 8057 | 77 |
| Polesovo | Village | North | 057 | 018 | 5846 | 13559 | 42 |
| Prigorodki | Village | South | 079 | 121 | 7841 | 3042 | 115 |
| Pulkovo | Hamlet | West | 049 | 097 | 4923 | 5662 | 42 |
| Pusta | Village | South | 091 | 115 | 9149 | 3905 | 36 |
| Pustoshka | Village | West | 030 | 074 | 3063 | 7897 | 112 |
| Ratnoe | Village | North | 061 | 026 | 6278 | 12693 | 46 |
| Rogovo | Village | West | 047 | 085 | 4738 | 6786 | 42 |
| Samorodok | Hamlet | North | 057 | 008 | 5920 | 14369 | 14 |
| Severograd | Large City | Center | 079 | 027 | 7954 | 12658 | 178 |
| Shakhovka | Hamlet | Center | 096 | 087 | 9646 | 6602 | 48 |
| Sinistok | Village | North-West | 014 | 034 | 1497 | 12017 | 59 |
| Smirnovo | Hamlet | North | 114 | 002 | 11466 | 14879 | 44 |
| Solnichniy | Village | South-East | 134 | 092 | 13392 | 6264 | 75 |
| Sosnovka | Village | West | 025 | 090 | 2489 | 6370 | 24 |
| Staroye | Village | East | 101 | 099 | 10160 | 5500 | 68 |
| Stary Sobor | Town | Center | 061 | 076 | 6111 | 7776 | 101 |
| Stary Yar | Village | Northwest | 049 | 002 | 4993 | 15066 | 105 |
| Svergino | Village | North-East | 095 | 015 | 9572 | 13785 | 78 |
| Svetlojarsk | Small City | North-East | 139 | 021 | 13909 | 13268 | 169 |
| Tisy | Village | North-West | 034 | 005 | 3335 | 14975 | 34 |
| Topolniki | Village | North-West | 027 | 030 | 2777 | 12345 | 83 |
| Troitskoe | Hamlet | North | 076 | 019 | 7570 | 13406 | 48 |
| Tulga | Village | South-East | 128 | 109 | 12792 | 4430 | 24 |
| Turovo | Village | North-East | 135 | 012 | 13547 | 14088 | 49 |
| Vavilovo | Town | North-West | 022 | 043 | 2291 | 11059 | 66 |
| Vybor | Town | West | 038 | 064 | 3826 | 8926 | 118 |
| Vyshnaya Dubrovka | Hamlet | East | 099 | 049 | 9979 | 10380 | 23 |
| Vyshnoye | Village | Center | 065 | 093 | 6537 | 6094 | 24 |
| Vysotovo | Village | South | 056 | 128 | 5690 | 2539 | 101 |
| Zabolotye | Hamlet | West | 011 | 053 | 1206 | 10008 | 26 |
| Zaprudnoe | Village | North-West | 045 | 021 | 4456 | 13198 | 22 |
| Zelenogorsk | Large City | West | 027 | 099 | 2650 | 5230 | 253 |
| Zvir | Village | South-West | 004 | 101 | 465 | 5252 | 45 |

## Method

1. **Town list + grid refs** scraped from the MyDayZ towns-and-cities table (keypad `X`/`Y`).
2. **Grid -> world seed:** `x = X * 100`, `z = 15360 - Y * 100` (the table's `Y` is measured
   from the north edge). Calibrated against known in-game anchors (Berezino, Chernogorsk,
   Vybor) from this server's own config files — all matched.
3. **Refinement:** mean-shift over the 11,680 building objects in `../mapgrouppos.xml`
   (250 m radius, iterated to convergence) to snap each seed onto the real building-cluster
   centroid. So these are *building-density* centers, not bare grid-cell midpoints.
4. **Manual fix:** two north-edge hamlets (Mamino, Smirnovo) initially merged into the adjacent
   large cities (Severograd, Novodmitrovsk); re-run with a tighter radius to isolate them.

Accuracy ~ +/-50-100 m. Large cities span 400-600 m, so the "center" is the densest point, not a
boundary. Regenerate by re-scraping the source table and re-running the mean-shift against
`mapgrouppos.xml`.

> Note: `docs/` and all `*.md` files are excluded from the FTP deploy (see `CLAUDE.md`), so this
> is a local reference only and never ships to the live server.
