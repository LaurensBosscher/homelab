---
title: "AdGuard Home: Next-Gen — Blocking 2 million addresses without crashing a $10 OpenStick"
author: Laurens Bosscher
pubDatetime: 2026-11-14T19:00:00+01:00
featured: true
draft: false
tags:
  - AdGuard Home
  - Ad blocking
  - DNS
  - OpenStick
  - Memory
  - Go
description: How a dual-path hash index lets AdGuard Home run million-entry blocklists on a ~465 MiB OpenStick without OOM.
---

AdGuard Home is a fantastic piece of software. It has a large community, is battle-tested, easy to run, and easy to configure — so I did just that! I installed it on my mighty [OpenStick](/posts/openstick/) and since the internet is a big, bad place I figured I would enable the [HaGeZi Threat Intelligence](https://github.com/hagezi/dns-blocklists) feeds (on the order of **1–2 million** domains depending on which lists you stack) and… it crashed!

At this point we have a few options:

1. Use a different solution, perhaps something like dnsmasq ad blocking or [esp32-c3-adblock](https://github.com/M-Abozaid/esp32-c3-adblock)
2. Use more powerful hardware (we do have an almost empty Kubernetes cluster after all)
3. Spend an evening looking into AdGuard Home, learn some Go, and see if we can find a good solution

Needless to say that 3. is the most _fun_ and _interesting_ solution, so we went with that :D

## NetworkRule

The first thing to understand is that AdGuard Home is more sophisticated than alternatives such as esp32-c3-adblock. Instead of simply blocking domains, it allows you to create NetworkRules containing all kinds of fancy filters:

[Basic rules — AdGuard Knowledge Base](https://adguard.com/kb/general/ad-filtering/create-own-filters/#basic-rules)

This is modelled as a struct and uses about ~296 bytes (+ overhead). That's actually pretty good, and it allows AdGuard Home to support functionality such as regex, DNS rewriting, exceptions, etc. I do not see any obvious optimisations without sacrificing functionality.

```go
type NetworkRule struct {
	// DNSRewrite is the DNS rewrite rule, if any.
	DNSRewrite *DNSRewrite

	// Shortcut is the longest substring of the rule pattern with no special
	// characters.
	Shortcut string

	// Whitelist is true if this is an exception rule.
	//
	// TODO(a.garipov):  Consider unexporting.
	Whitelist bool
	// contains filtered or unexported fields
}
```

There's a second challenge with the AdGuard Home implementation in that a rebuild of the filter list keeps the input files (from the internet), the new filter list, and the old filter list in memory. This has the advantage that you can still do DNS requests while the server is updating; it has the disadvantage that we need roughly 3× "idle" memory when doing the updates.

The worst-case scenario is thus not 296 bytes alone. As a rough order of magnitude — ~296 B per `NetworkRule`, plus shortcut-index overhead, then ~2–3× during a rebuild while the old engine stays alive and Go's GC catches up — you can think in terms of **~1 KB of peak pressure per filter line**. That makes for easy napkin math: ~1 million entries → on the order of **~1 GB** peak. That's about twice as much RAM as we have on the stick, and that's what caused our OpenStick to crash when we started enabling the blocklists.

## So how do we solve this?

Given that a rebuild triggers ~3× the "idle" memory usage, any NetworkRule memory that we can reduce would pay off three times. What is the most efficient implementation that we can think of? esp32-c3-adblock leads the way, and 40 bits seem like a very nice target to aim for — however that only works for _simple_ rules.

So what percentage of the filters could we represent using simple hashes? On the OpenStick's currently enabled lists:

| Path | Rules | Share |
|---|---:|---:|
| Hash / domainhash (simple hosts / `\|\|domain^`) | 2,146,449 | **93.2%** |
| Complex urlfilter NetworkRules (modifiers, `@@`, regex/path, etc.) | 156,553 | 6.8% |
| Total rule-ish lines | 2,303,002 | 100% |

Replacing the existing NetworkRule implementation with the simple hash implementation would allow us to cover 93.2% of the cases and potentially save roughly 800–900 MB of memory when we do a rebuild. That's not bad!

However, _replacing_ the existing implementation comes at the cost of losing 6.8% of the rules and, more importantly, losing compatibility with the existing blocklists. Most of the complex rules come from Phishing Army, and since even [Troy Hunt got phished](https://www.troyhunt.com/a-sneaky-phish-just-grabbed-my-mailchimp-mailing-list/), that does not seem like a good place to compromise:

![Breakdown of complex leftover rules by source list](../../assets/images/adguard_home_next_gen/complex_rules_break_down.svg)

## Best- and worst-case DNS blocking paths

There's an additional advantage to the hash-based approach: lookups become about ~17× faster as well. If we sort the hashes, we can do a binary search in O(log N). This is _faster_, however in practice this just means that your bad domains get blocked faster. For everything that is not in the blocklist (including legitimate DNS requests), we still need to check the more complex NetworkRules.

The existing AdGuard Home implementation (via `urlfilter`) uses a rather smart index. Every NetworkRule has a `setShortcut()` method which _can_ generate a shortcut — the longest literal substring of the pattern without special characters (e.g. `||ads.example.com^` → `"ads.example.com"`).

That shortcut is **not** stored as overlapping slices pointing at the rule. Instead the engine:

1. Slides a fixed **5-character** window over the shortcut
2. Picks **one** of those 5-grams — whichever currently has the **fewest** rules already indexed under it (the rarest bucket)
3. Appends a storage ID for that rule under that single key

So the index looks more like:

```text
{
    "ads.e" -> [id42]          // this rule's chosen (rarest) 5-gram
    "track" -> [id7, id19]     // two rules that both landed here
    ...
}
```

On a DNS query, urlfilter builds `http://` + hostname, slides the same 5-character window over that string, unions every storage ID found, then runs the full `Match()` on each candidate. False positives are expected; `Match()` is the source of truth.

![Shortcut index lookup overview](../../assets/images/adguard_home_next_gen/index_lookup.svg)

Pretty smart and efficient for lookups! The best-case scenario is:

1. No index hit
2. Allow the request

The bad case is a legitimate hostname whose 5-grams collide with many indexed keys:

1. On the order of ~100–200 candidate hits (worst case we measured on our leftovers: ~150 unique rules on a max-length DNS name)
2. Run `Match()` for all of them
3. None block, so allow the lookup

By moving most simple domain blocks out of this index, we shrink the candidate sets and make legitimate requests cheaper as well.

A rare double win (at the cost of more complexity)!

## The dual-path implementation

The solution that I eventually ended up with is as follows:

![Dual-path filter update and DNS query architecture](../../assets/images/adguard_home_next_gen/architecture.svg)

Simple hosts / `||domain^` rules are hashed into a sorted on-disk blob (`blocklist.bin`) and mmap'd for lookup. Everything a hash table cannot express — `@@` exceptions, `$`-modifiers, regex, path rules, and awkward list formats — stays in a compact urlfilter engine.

As you can see, none of these optimisations come for free. While we greatly reduce the memory usage and lookup time (in most scenarios), we do so at the cost of effectively implementing a whole secondary (although simple) blocking engine.

This means twice the surface for bugs, crashes, and security issues. That's less of an issue for a homelab, more of an issue for an open-source project.

Despite this approach clearly having many benefits and being more efficient, I have thus decided to keep the fork separate from the upstream project for now.

## Results

Synthetic desktop benchmarks (same-shape `||domain^` lists, `GOMAXPROCS=4`, 2026-11-12):

| N | urlfilter RSS | domainhash file | domainhash build | warm hit |
|---:|---:|---:|---:|---:|
| 100k | 22.7 MiB | 488 KiB | 25 ms | 125 ns |
| 500k | 84.2 MiB | 2.4 MiB | 108 ms | 131 ns |
| 1M | 149.3 MiB | 4.8 MiB | 242 ms | 141 ns |

![Comparison of urlfilter and domainhash memory and lookup cost](../../assets/images/adguard_home_next_gen/implementations_compared.svg)

Live OpenStick (465 MiB RAM, `MemoryMax=250M`, 2026-11-01), stacking HaGeZi lists including the full Threat Intelligence feed:

| Stage | Hashes | `blocklist.bin` | Steady RSS | Rebuild peak |
|---|---:|---:|---:|---:|
| Baseline | 186k | 0.89 MiB | ~38 MiB | ~61 MiB |
| + full HaGeZi TIF stack | **2.18M** | **11 MiB** | **~47 MiB** | **~122 MiB** |

![Live OpenStick scale-up results for domainhash](../../assets/images/adguard_home_next_gen/live_results.svg)

Hashes grew about 12×; steady RSS barely moved. The same TIF-class load is what tended to OOM stock urlfilter on this class of device.

## Additional optimisations

I've implemented a number of other optimisations that provide improvements in memory/CPU-constrained scenarios or make rebuilding more efficient, but compared to the hash approach above these have a minor effect.

### Domain normalisation before hashing

Since we merge multiple filter lists it makes sense to reduce duplicates. For every domain we do the following before hashing:

- Trim, lowercase ASCII only
- Strip a trailing `.`
- Strip leading `www.` (only if ≥2 labels remain, so that we don't end up blocking `www.com`)

This costs us more CPU time when rebuilding the blocklist but collapses duplicates across lists. Since we rebuild usually once per day, this seems like the right trade-off.

### Parent matching

At lookup time, `ContainsDomain("ads.tracker.example.com")` checks:

- `ads.tracker.example.com`
- `tracker.example.com`
- `example.com`
- not the TLD alone (`com`)

So blocking `example.com` also blocks subdomains without storing every subdomain in the hash blob. That is a **lookup** cost (a few extra hashes + binary searches), not extra rebuild work.

### Storing the blocklist on disk

The hashed blocklist is kept as a file on disk. This has the following advantages:

1. It survives reboots
2. Linux can map parts of the file (`mmap`), so we can allow extremely large blocklists on extremely low-memory devices (although we still need to be able to run Linux + AdGuard, so 64 MB is probably the lower limit)
3. Linux may decide to evict clean pages of the file from memory if there's memory pressure. This seems preferable to the system crashing

### Streaming merge-sort builder for the hash blocklists

Instead of keeping all domains in memory when rebuilding, we batch them; the in-memory batch is capped at ~16 MB before flushing a sorted run file to disk, then we merge-sort the runs into `blocklist.bin`.

Filter files are split across up to 8 worker goroutines, but they **share one builder** and one memory budget — so peak rebuild scratch is still on the order of that ~16 MB batch (plus the small leftover urlfilter engine), not `16 MB × 8`. Good to be aware of either way if you are on a tiny router.

### Query-path ordering

Since parts of our engine have a very different cost, it makes sense to optimise the way that we execute them. The live order is:

1. **Allowlist urlfilter first** — exceptions must win (user-configured; typically on the order of 0…100 entries)
2. **Complex block urlfilter** — rewrites, `$`-rules, and leftover complex blocks (skipped entirely when every simple block was diverted and nothing complex remains)
3. **Hash blocklist lookup** — the cheap check for diverted simple domains

When there are no complex leftovers left, we can take a fast path and go allowlist → hash only.

Technically we could race some of these on multi-core machines, but the expected speed-up would be small: the expensive lists are already much smaller, and parallelisation has _overhead_ that swamps microsecond-scale lookups.

### Cache persistence

Since we experiment a lot and deploy new builds to test, process restarts are common. A cold DNS cache means every client waits on upstream RTT again. Next-Gen can periodically dump the live dnsproxy cache to disk (`data/dns_cache.bin`) and reload it on start, skipping expired entries — so the stick comes back warm after a redeploy.

## Try it

- Fork: [AdGuardHome-Next-Gen](https://github.com/LaurensBosscher/AdGuardHome-Next-Gen)
- Design notes: [docs/NEXTGEN.md](https://github.com/LaurensBosscher/AdGuardHome-Next-Gen/blob/master/docs/NEXTGEN.md)
- Benchmarks: [docs/BENCHMARKS.md](https://github.com/LaurensBosscher/AdGuardHome-Next-Gen/blob/master/docs/BENCHMARKS.md)

Experimental, homelab-grade — not for anything life-critical. Here be dragons.
