---
name: dupe-check
description: "Find the item-moving flows in a server diff and prove none can duplicate or lose an item: the dev writes the dupe tests upstream's way, QA checks each flow's four paths (tests and a short in-game try). Use as server-dev before handing over any change that moves items, and as server-qa on every such change."
---
# Dupe check

Upstream AGENTS.md (section "Unit tests — where they earn their keep"; re-read it live on upstream `main`) requires a
test proving no item is duplicated or lost for every flow that moves items in or out of an inventory, bank, shop, trade,
equipment slot or ground stack. These are the only tests an upstream PR carries by default; every other test rule
(skill `server-track`) stays.

## The flows in a diff
A flow is one player action (an op, a button, a dialogue choice, a timer reward) whose code calls the item-moving API:
`inv*` from `api/invtx` and `ProtectedAccess` (`invAdd`, `invAddOrDrop`, `invDel`, `invReplace`, `invTransfer`,
`invMove*`, `invSwap`, `invTakeFee`, `invTransaction`, `invEquip`, `invDrop`), `wornUnequip`, `objRepo.add`/`del`
(ground stacks), the shop operations (`shopBuy`, `invSell`). `gates/server.py` names each file and its calls (the gate's
`for the reviewer: item flow in ...` lines) and fails a module whose main sources gain such a call with no test source of
that module added or changed; run it on your diff the same way: `git diff --unified=0 origin/main...HEAD` and read the
added lines that call those names.

## The dev: tests upstream's way
One test class per flow in the module's `src/test/kotlin`, built like upstream's own item tests (read two before
writing: `content/minigames/giants-foundry/.../FoundryRewardTransactionsTest.kt` for inventories, banks and overflow,
`content/bosses/brutus/.../BullBonesTest.kt` for a ground stack): a `Fixture` that builds a bare `Player()` with a silent
client, sets `player.inv[slot] = InvObj("obj.x", n)`, runs the script through `ProtectedAccess` with
`ProtectedAccessContextFactory.empty()` and real `ObjRepository`/`InvTransactionsScript` objects, and asserts counts with
`inv.count("obj.x")`. Cover the four paths:
1. **No space**: a full inventory (or bank, or the target slot taken) mid-action: the whole action rolls back, nothing
   taken and nothing given.
2. **Overflow**: a stack at `Int.MAX_VALUE - n + 1` and at exactly `Int.MAX_VALUE - n`: all or nothing at the boundary.
3. **Repeats and races**: the same action twice in one tick, and the source item gone between the check and the take
   (dropped, banked, consumed, the ground obj deleted, as `BullBonesTest` does with `objRepo.del`).
4. **Accounting**: each obj's total (every inventory, worn, bank, the ground) before and after differs by exactly what
   the action is meant to do.
A path that cannot occur in the flow (no stackable output: no overflow) is not tested; say why in one plain-text line of
the PR body's notes. Test names in backticks say the behaviour, as upstream's do. Nothing public for a test.

## QA: each flow's four paths
For each `item flow` the gate named: the four paths above have a test, or a reason in the PR text that holds against the
code; the tests assert totals, not only that no exception was thrown. Then a short in-game try on the branch's own server
(skill `server-track`, `osrs-devtools-desktop`): the action with a full inventory, a click repeated as fast as the client
allows, and the source dropped or banked mid-action, reading counts with `get_inventory` / `get_container_history`
before and after. A missing path, a test without totals or an in-game count off by one is a FAIL finding naming the flow.
