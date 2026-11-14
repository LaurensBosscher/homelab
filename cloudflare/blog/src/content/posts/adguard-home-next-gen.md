---
title: How I run 2 million DNS block rules on a $10 modem
author: Laurens Bosscher
pubDatetime: 2026-11-14T18:00:00+01:00
featured: true
draft: false
tags:
  - AdGuard Home
  - Ad blocking
  - DNS
  - OpenStick
  - Memory
  - Go
description: AdGuard Home Next-Gen stores simple DNS blocks as mmap'd FNV hashes so million-entry threat lists fit on ~100–512 MiB routers.
---

## Table of contents

In my [OpenStick post](/posts/openstick/) I mentioned that I'm running a fork of AdGuard Home that can handle large blocklists without eating all the RAM. This is that story.

The device has roughly **465 MiB** of usable RAM and a Podman cgroup cap around **250 MiB** for AdGuard Home. Stock AdGuard Home is excellent software — but feed it HaGeZi-class Threat Intelligence Feeds (on the order of **two million** domains) and a filter rebuild will happily try to allocate **hundreds of megabytes**. On a modem stick, that is not a "slow GC day". That is an OOM kill, and then nothing on the network can resolve DNS until something restarts the container.

So I forked it.

> [!NOTE]
> The fork is **experimental** and aimed at homelabs / routers / SBCs. Do not point a hospital at it. Source, design notes, and benchmarks live in [AdGuardHome-Next-Gen](https://github.com/LaurensBosscher/AdGuardHome-Next-Gen). Base tag: upstream `v1.0.0-b.1`.

## What actually goes wrong upstream

AdGuard Home's filtering path builds a full [`urlfilter`](https://github.com/AdguardTeam/urlfilter) `DNSEngine` for every list. A simple `||ads.example^` rule becomes a rich `NetworkRule` object — about **296 bytes** each after urlfilter v0.23.4 — plus shortcut-index overhead.

That creates **two** separate failure modes:

1. **Steady state.** Every blocked domain lives as a heap object. A million synthetic `||domain^` rules measure around **~150 MiB** RSS for the rule engine alone on a desktop. Fine on a NAS. Fatal on a 100–512 MiB router budget once you stack real lists.
2. **Rebuild peak.** During a filter update the old engine must keep answering DNS while the new one is built, so the live heap roughly **doubles**. With Go's default `GOGC=100`, the heap is only collected once it has grown to about twice the live set — so the transient peak is roughly **three times** one engine. A 2.1M-rule HaGeZi TI rebuild has been reported north of **800 MiB**.

Upstream PR [#8498](https://github.com/AdguardTeam/AdGuardHome/pull/8498) (still open at the time of writing) is a very good mitigation for the *peak*: skip unchanged rebuilds, serialize rebuilds, tighten `GOGC` during the build, collect before and after. I ported that work into the fork. It does **not** change the deeper issue: **steady-state still stores every rule as a rich object**. If the live engine alone does not fit, no amount of clever GC timing will save you.

## The idea: dual-path filtering

I stole the core idea from [esp32-c3-adblock](https://github.com/M-Abozaid/esp32-c3-adblock): on a $2 MCU with no PSRAM, hundreds of thousands of domains are stored as **sorted truncated FNV-1a hashes** and binary-searched. Flash-backed, tiny, fast enough for DNS.

AdGuard Home cannot throw away full Adblock syntax, though. People need `@@` allow exceptions, `$client` rules, regex, and the occasional weird modifier. So Next-Gen splits the world in two:

```
filter update
  ├─ simple hosts / ||domain^  → hash → sort/merge → blocklist.bin (mmap)
  └─ complex / allowlist rules → compact urlfilter DNSEngine

DNS query
  ├─ allowlist urlfilter first (exceptions must win)
  ├─ complex block engine (when leftovers exist)
  └─ domainhash index (mmap + binary search, including parent suffixes)
```

On the OpenStick, after loading HaGeZi Normal / Pro / Ultimate / Threat Intelligence Feeds on top of the baseline lists, that diversion was almost total: **2,184,149** unique hashes, **2.7M** domains diverted, and only **seven** small leftover files still going through urlfilter.

## Optimisation 1 — change the representation

This is the whole point of the fork.

| | Stock urlfilter | Next-Gen domainhash |
|---|---|---|
| Per domain | `NetworkRule` (~296 B) + index | truncated hash (default **5 bytes**) |
| 1M domains, steady | **~149 MiB** live heap | **~4.8 MiB** on disk / page cache |
| 1M domains, warm hit | ~2384 ns | **~141 ns** |
| 1M domains, build | ~922 ms | **~242 ms** |

Numbers above are synthetic `||domain^` lists on a desktop (AMD Ryzen AI MAX+ 395, linux/amd64, go1.27.3, `GOMAXPROCS=4`, **2026-11-12**), measured with the harness in the repo. Urlfilter RSS is live heap and is not reclaimable without dropping the engine. Domainhash steady-state for lookups is the mmap file size — reclaimable under pressure.

## Optimisation 2 — truncated FNV-1a (40-bit by default)

Each domain is hashed with FNV-1a-64; the low `hash_bytes` are kept (default **5** = 40-bit; max **8** = full 64-bit). Entries are stored little-endian and sorted so lookups are a plain binary search.

Birthday collisions at 40-bit are expected around the half-million-domain mark. That means a rare **over-block** (false positive), not an under-block. For ads and trackers that trade-off is fine. For stricter threat-intel policy, set `domain_hash_bytes: 8` (~8 MiB per million domains). On the full OpenStick load I saw **three** 40-bit collisions.

## Optimisation 3 — normalise before hashing

Domains are canonicalised once:

- trim, lowercase ASCII
- strip a trailing dot
- strip a leading `www.` only when at least two labels remain (so `www.com` is never turned into "block all of `com`")
- basic label validation

That collapses `WWW.Example.com.` and `example.com` into one hash, which matches how hosts lists are usually written.

## Optimisation 4 — parent-suffix matching

If `example.com` is blocked, `ads.tracker.example.com` must be blocked too. The index walks parent suffixes with at least two labels (`ads.tracker.example.com` → `tracker.example.com` → `example.com`) and never matches a bare TLD. Same hosts-file semantics, without storing every subdomain.

## Optimisation 5 — mmap + page cache (not a disk read per query)

The finished `blocklist.bin` is opened with `mmap(PROT_READ, MAP_SHARED)` on Unix.

Linux does **not** copy the whole file into RAM up front. Pages fault into the **page cache** on first touch. After that, a warm lookup is a RAM-speed binary search over roughly `log₂(N)` cache lines — no `read()` syscall per DNS query. Under memory pressure the kernel can reclaim clean mmap pages and fault them back later. A million × 5-byte index is **~4.8 MiB**, small enough to stay resident on OpenStick-class devices when RAM allows.

That reclaimability matters. Heap objects from urlfilter are sticky until you drop the engine. An mmap blob can shrink under pressure without throwing away the blocklist.

## Optimisation 6 — stream, hash-only batches, external merge-sort

Building the index must not temporarily allocate "all domains as strings". The builder:

1. Parses each line, normalises once, and keeps only a **full 64-bit hash** in an in-memory batch (`[]uint64`, 8 bytes each).
2. When the batch hits the memory budget, sorts by truncated hash and flushes a **run file** under the data directory (not `/tmp` — on many routers `/tmp` is tmpfs and counts against RAM).
3. Merges runs with a min-heap into `blocklist.bin.tmp-*`, `fsync`s, then **atomically renames** over the previous blob.
4. Deletes intermediate runs. The old mmap stays valid until the new index is swapped in and the old one is closed.

Collision detection compares distinct full 64-bit hashes that share a truncated prefix; domain strings are not retained after hashing. After a 2026-11-12 pass that made batches hash-only, desktop builds got about **3.7–6×** faster than the earlier Next-Gen baseline at the same file sizes. Raw FNV is cheap; end-to-end time is sort, merge, and I/O.

Hard caps: in-memory batch ceiling **16 MiB**, floor budget **8 MiB**.

## Optimisation 7 — size the rebuild from MemAvailable (and GOMEMLIMIT)

Batch size is not a magic constant. `ResolveMemBudget` does:

1. Linux `MemAvailable − domain_hash_mem_margin_bytes`
2. optional absolute `domain_hash_mem_budget_bytes`
3. if `GOMEMLIMIT` / a soft memory limit is set: also cap to `GOMEMLIMIT − 32 MiB` reserve
4. floor at 8 MiB

That is how rebuild peaks stayed under roughly **140 MiB** on the OpenStick while loading millions of diverted domains inside a 250 MiB cgroup.

## Optimisation 8 — parallel divert, shared builder

Filter files are split with up to `min(max(GOMAXPROCS − 1, 1), 8)` workers into one shared builder (mutex on append/flush). Worker count follows CPU; the batch budget follows memory. Parallel run-merge and hand-written NEON FNV kernels are still optional later — builds are not FNV-bound today.

## Optimisation 9 — query path order (correctness first)

Exceptions must win:

1. Allowlist urlfilter first.
2. If every simple block was diverted and no complex leftovers remain (`domainHashOnlyBlocks`), check the hash index before the (empty) block engine.
3. Otherwise run the complex urlfilter block engine, then the hash index.

Hit metadata uses a static rule text `"domainhash"` so the hot path does not allocate `"domainhash:"+host` per query.

## Optimisation 10 — port of PR #8498 for whatever still uses urlfilter

Allowlists and complex leftovers still rebuild urlfilter. The fork therefore ports the rebuild mitigations:

- **Fingerprint skip** — process-seeded `maphash` over list IDs, paths, and file bytes; unchanged sync/API noise does not rebuild engines.
- **Serialized rebuilds** — periodic update and a UI tweak cannot double an already-doubled peak.
- **`GOGC=20` only during rebuild** — nested-safe; never loosens a stricter user `GOGC`.
- **`FreeOSMemory` before and after** — clear dead heap before the peak, return pages after.
- Failed rebuilds close storages and do not install a bad fingerprint.

#8498 shrinks the peak for rich engines. Domainhash removes most rules from those engines. You want both.

## Optimisation 11 — DNS cache persistence

On a stick, process and container restarts are normal. A cold DNS cache means every client waits on upstream RTT again.

`dns.cache_persist_enabled` periodically dumps dnsproxy's general and ECS caches to `data/dns_cache.bin` (magic `AGHDNSC1`) and reloads on start, skipping expired entries. Writes go through a temp file and atomic rename.

dnsproxy does not expose a public dump/load API yet, so this (and the cache-stats work) peeks at unexported fields with `reflect` / `unsafe`. That is brittle across dnsproxy upgrades and covered by layout tests — acceptable for an experimental fork, called out honestly.

Related quality-of-life ports that are not memory wins but help on small boxes:

- DNS cache statistics on the dashboard ([#8642](https://github.com/AdguardTeam/AdGuardHome/pull/8642))
- Hide zero-valued Safe Browsing / Parental / Safe Search stats when those features are disabled ([#8538](https://github.com/AdguardTeam/AdGuardHome/pull/8538))

## OpenStick field results

Device: OpenStick aarch64, ~465 MiB RAM, `adguardhome.service` with `MemoryMax=250M`, Next-Gen binary, `domain_hash_enabled`, **2026-11-01**.

| Stage | Unique hashes | `blocklist.bin` | Steady RSS | Rebuild peak |
|---|---:|---:|---:|---:|
| Baseline lists | 186k | 0.89 MiB | ~38 MiB | ~61 MiB |
| + full HaGeZi TIF stack | **2.18M** | **11 MiB** | **~47 MiB** | **~122 MiB** |

Hashes grew about **12×**. Steady RSS moved about **+9 MiB**. Rebuild peaks stayed under ~140 MiB. DNS blocking still worked (`doubleclick.net` → `0.0.0.0`). The same TIF-class load is what tends to OOM stock urlfilter on this class of device.

One related footnote: on *small* lists, Podman RSS for AGH on the stick still sawtooths roughly **8–40 MiB** on a 1–2 hour cadence. That is normal Go heap breathing under `GOGC=100` plus DNS caches filling — **not** the million-rule OOM mode. Cheap knobs without a fork: `GOMEMLIMIT`, a lower `GOGC`, and a smaller `dns.cache_size`.

## How to turn it on

```yaml
filtering:
  domain_hash_enabled: true
  domain_hash_bytes: 5  # 40-bit; use 8 for stricter TI collision policy
  # domain_hash_mem_budget_bytes: 16777216
  # domain_hash_mem_margin_bytes: 33554432

dns:
  cache_enabled: true
  cache_persist_enabled: true
  # cache_persist_interval: 5m
```

```bash
GOMEMLIMIT=96MiB GOGC=50 ./AdGuardHome
```

Images and design docs:

- [AdGuardHome-Next-Gen](https://github.com/LaurensBosscher/AdGuardHome-Next-Gen)
- [docs/NEXTGEN.md](https://github.com/LaurensBosscher/AdGuardHome-Next-Gen/blob/master/docs/NEXTGEN.md)
- [docs/BENCHMARKS.md](https://github.com/LaurensBosscher/AdGuardHome-Next-Gen/blob/master/docs/BENCHMARKS.md)
- GHCR package: [`adguardhome-next-gen`](https://github.com/LaurensBosscher/AdGuardHome-Next-Gen/pkgs/container/adguardhome-next-gen)

## What this is not

- Full Adblock syntax inside the hash index (`$client`, regex, paths, cosmetics stay in urlfilter).
- A replacement for SafeBrowsing's `hashprefix` protocol.
- A promise that 40-bit hashing never over-blocks — use 64-bit when that matters.
- Production-certified DNS for anything life-critical.

## Takeaway

The interesting part is not "I recompiled AdGuard Home with `-O3`". Stock AGH already does a lot right. The interesting part is treating the common DNS-block case as a **sorted hash set in the page cache**, keeping urlfilter for the exceptions a hash table cannot express, and wrapping both with memory-aware rebuilds and a cache that survives restarts.

On a desktop that is a nice speed and RAM win. On a $10 modem it is the difference between "2 million threat domains" and "OOM, try again with a toy list".
