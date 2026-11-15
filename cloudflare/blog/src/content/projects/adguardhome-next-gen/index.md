---
title: "AdGuard Home Next-Gen"
description: "Experimental AdGuard Home fork: domain-hash blocklists that fit million-entry feeds on ~512 MiB routers and OpenSticks."
date: "2026-11-14"
repoURL: "https://github.com/LaurensBosscher/AdGuardHome-Next-Gen"
demoURL: "https://blog.bosscher.ch/posts/adguard_home_next_gen/"
---

Fork of [AdGuard Home](https://github.com/AdguardTeam/AdGuardHome) that diverts simple DNS block rules into a sorted on-disk hash index (mmap + binary search), keeping complex/allowlist rules on urlfilter.

Write-up: [AdGuard Home: Next-Gen](/posts/adguard_home_next_gen/).
