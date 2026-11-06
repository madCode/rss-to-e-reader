title: Retries Are a Load Test You Didn't Schedule
author: Mei Chen
date: 2026-05-30
extractor: trafilatura
---
Engineering
## Retries Are a Load Test You Didn't Schedule
Last winter one of our services fell over for forty minutes. The root cause was a slow database query, but the reason it took the whole service down was something we had added on purpose: retries. Every client that timed out tried again, and then again, and the database that was struggling with one copy of the load was suddenly handling four.
Retries are one of those things that are obviously good in isolation. A single request that fails because of a brief network blip should be tried again. The trouble is that failures are rarely isolated. When something goes wrong, it tends to go wrong for everyone at once.
## The arithmetic
Suppose each layer of a call chain retries three times. A request that passes through three layers can turn into
```
3 × 3 × 3 = 27
```
attempts at the bottom layer. That multiplier only shows up when the bottom layer is already in trouble, which is the worst possible moment for it.
| Layers | Retries per layer | Worst-case attempts |
| 1 | 3 | 3 |
| 2 | 3 | 9 |
| 3 | 3 | 27 |
### What we changed
We now retry in exactly one place, at the edge of the system, and every retry waits a little longer than the last with some randomness mixed in so that clients don't all come back at the same moment:
```
def backoff(attempt, base=0.2, cap=10.0):
    delay = min(cap, base * 2 ** attempt)
    return random.uniform(0, delay)
```
We also added a retry budget: if more than a tenth of recent requests are retries, the client stops retrying altogether and fails fast. That sounds alarming, but a quick, honest error is much easier to recover from than a slow pile-up.
![Request rate during the incident](https://field-notes.example/content/images/2026/05/retry-graph.png)
### The lesson
The general lesson is that any mechanism that adds work in response to failure needs a limit. Retries, reconnects, cache refills and autoscaling all share this shape. Each is sensible on its own, and each can turn a small problem into a large one when everything triggers it at once.
