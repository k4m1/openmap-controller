# Performance: what a zoom out costs, and what was done

`tools/offline-test/perf.py` counts what a zoom out makes the client do. It can't give frames per
second: fill and layout are the game's, so `/openmap bench` (in game) is the measure of a change.
The test's world is built from the repo's own zone and overlay data (about 40 zones, 480 base tiles,
800 overlays: a player's is 49 / 516 / 937), with made-up positions and file IDs.

## Where the work is, in the order it was cheapest to take away

| # | Cause | Seen as | Done |
|---|-------|---------|------|
| 0 | The first opening of the map makes every zone's tiles (and the colour-matched and interior copies of them) in one frame | 4594 regions made in `S.Build`, 3563 of them zone tiles | `S.Build` plans the zones (frame, level, pieces: no regions) and `S.BuildZones` makes their tiles about 4 ms a frame, in the same order: 1032 regions in the opening frame |
| 1 | Fading tiles set their opacity on every frame (Stitch.lua, the file loader), 700 and more at once while a zoom out brings the continents' tiles in | up to 3000 calls in a step | 8 steps a fade: a third to a half fewer calls |
| 2 | All names' lettering made in one frame at the first zoom out (a name is hundreds of font strings) | 351 regions made in one step | one name a call: 144 at most |
| 3 | The live zone art (Unexplored areas: hide, Classic, a client that isn't English) instead of the baked tiles | up to 667 textures drawn at once (231 baked) and 3.7k calls a step | not done: needs baked art for that setting |
| 4 | Culled continent tiles stay anchored while their layer is hidden | about 200 placed, not drawn | not done: unverified that the client lays out regions under a hidden frame; measure in game first |
| 5 | The blur copies stay anchored while hidden | about 230 placed, not drawn | not done: as 4 |
| 6 | `S.Cull` re-ran `ShowZone` over every tile of every zone in view each time the view left its keep region | the worst frame of a wheel zoom: 2740 (x100 Lua instructions) | `ShowZone` keeps what it last ran with (`S.zsig`) and returns early when the grade, view, live art, explored state and (for a zone not wholly inside the keep region) the cull are unchanged: 1530 |
| 7 | `UpdateUnderground` (Close.lua) filtered every cave by continent on every `S.SetView` | 31% of a pan's addon Lua | the caves that can surface are listed once per set of continents in view: a pan costs a fifth less |

| 8 | Per-frame Lua: the loader set each fading tile's opacity every frame, and three scripts ran on every frame to wait for 0.05 to 0.15 s | the loader stayed shown for the 0.3 s of the last fades | a tile fades with an Alpha animation of its own (made once: `S.FadeIn`, counted as `anims` in perf.py); one timer releases the baked tiles when the last fade is over; the map's check, the gamepad look and the names' watch are `C_Timer` tickers while their frame is shown |

A view that hasn't changed makes no calls (tested), so the cost is in the steps of a zoom, not at rest.

## Lua's own work

Rows 6 and 7 are CPU, not regions. perf.py counts the instructions the addon's files run in a frame
(`debug.sethook` with a count, skipping the stub's, which stand for the client's), in a pan, a
mouse-wheel zoom and a notched zoom, and an idle frame must run none. `CPU_BUDGETS` is the mean and
worst frame, 15% over what the code costs now. Instruction counts say where Lua's time goes; they
aren't milliseconds, and `/openmap bench` is the measure. What's left in a pan: the caves' `Surface`
test per frame, `ShowZone`, the loader's fade.

## The zones' tiles come after the opening

`S.Build` counts a zone's tiles (`S.CountOverlays`, which also makes the zones' pieces: cities and
`Shade.Under` need them all) to say whether it's a zone or a city, gives it its frame and level, and
queues it. A city's art is made at once. `S.BuildZones(ms)` makes the queued zones in their order (the
order they draw over each other in), and each is graded, greyed and shown as it comes, as the blur's
copies are (`BuildBlur`). perf.py checks that the textures, masks, zones, tiles and overlays, and a
zoom out's counts, come out the same as when they were all made at once.

## Budgets

`BUDGETS` in perf.py is what the code does now, 10% over. A change that makes a step of a zoom out
draw, anchor, touch or make more regions than that fails; when a change takes work away, lower them.
