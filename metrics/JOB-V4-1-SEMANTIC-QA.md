# JOB V4-1 SEMANTIC QA (manual, deterministic)

Type-safety pass: each canonical metric declares value_kind / allowed_unit / allowed_literal_shape.
Unrelated descendant literals are CONTEXT_ONLY or a different metric. MIXED / dates / deltas are not counts or index levels.

Dormant: RAY, GRASS = LEGACY_INACTIVE. Not active reports.
ORCA = hold-card-only, not onboarded.

Sample: `literal → asset → metric → source/as_of → class`

## BTC
| literal | asset | metric | source / as_of | class |
|---|---|---|---|---|
| $76,746 | BTC | btc.price.usd.current | UNKNOWN | hold_card CONFLICT vs hero |
| $79,337 | BTC | btc.price.usd.current | UNKNOWN | hero CONFLICT vs hold |
| $1.96B | BTC | btc.etf.flow.usd.7d | Farside | tooltip |
| $2.0B | BTC | btc.etf.flow.usd.7d | Farside | card compact (not chosen winner) |
| $2.67B | BTC | btc.etf.flow.usd.30d | Farside | tooltip (not 50D/200D) |

## PUMP
| literal | asset | metric | source / as_of | class |
|---|---|---|---|---|
| $6.8M/wk | PUMP | pump.buyback.usd.7d | defillama / 2026-08-25 | weekly total |
| $6.8M | PUMP | pump.buyback.usd.7d | same weekly fact | chart kpi |
| $1.0M | PUMP | pump.buyback.usd.1d | chart last bar | daily, not 7d |

## HYPE
| literal | asset | metric | source / as_of | class |
|---|---|---|---|---|
| $73.98 | HYPE | hype.price.usd.current | UNKNOWN | hold_card |
| $81.06 | HYPE | hype.price.usd.current | UNKNOWN | hero (CONFLICT vs hold) |

## SPX
| literal | asset | metric | source / as_of | class |
|---|---|---|---|---|
| ~25.9% | SPX | spx.holders.top20.pct | Solana RPC getTokenLargestAccounts · 2026-08-12 | STALE |

## ZEC
| literal | asset | metric | source / as_of | class |
|---|---|---|---|---|
| $629 | ZEC | zec.price.usd.current | UNKNOWN | hold_card |

## Global
| literal | asset | metric | source / as_of | class |
|---|---|---|---|---|
| ETF 7D/30D rows | BTC/ETH/SOL | *.etf.flow.usd.{7d,30d} | Farside + farside.co.uk links | market_layer |

## Hold-card-only
| literal | asset | metric | surface |
|---|---|---|---|
| $1.22 | ORCA | orca.price.usd.current | VISIBLE_HOLD_CARD_ONLY |
| $1.01 | ORCA | orca.threshold.out.usd | VISIBLE_HOLD_CARD_ONLY |

GRASS/RAY remnants inventory as LEGACY_INACTIVE. Not deleted. Not refreshed.
