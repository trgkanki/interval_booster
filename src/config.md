# Induction booster

- **targetRetentionRate**: Your target retention rate for first review. Default 0.85
- **sampleDays**: How many days to look back for interval calculation. Default 60
- **whitelistDecks**: List of deck names to apply to. *Default: \[\] (apply to all decks)*

- **targetRetentionRateOverrides**: List of retention rate overrides. You can specify [search query](https://docs.ankiweb.net/#/searching) to specify cards to override `targetRetentionRate`. Example:
  ```
  "targetRetentionRateOverrides": [
    { "query": "flag:3", "override": 0.95 },
    { "query": "prop:ivl<=30", "override": 0.8 }
  ]
  ```
  Later entries will have more precedence over former ones.
  > Note that this won't affect newly learnt cards.

## autoEaseConfig

Imported code from [Auto Ease Factor](https://ankiweb.net/shared/info/1672712021) addons.

- Leash: controls how much the ease can change per review, so a small leash of 10 or 50 will not let the algorithm adjust things until it has much more data.
- minEase: minimum bound of card ease. *Default: 5000 (500%)*
- maxEase: maximum bound of card ease. *Default: 1500 (150%)*
- movingAverageWeight: indicates how much to focus on more recent results when determining success rate. Higher numbers will focus more on recent performance. *(This is very sensitive, values between 0.07 and 0.3 are reasonable)*