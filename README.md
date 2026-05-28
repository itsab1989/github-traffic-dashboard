See full Reference and Usage Guide at:
https://soul-traveller.github.io/github-traffic-dashboard/

> This is a modified version of the original [github-traffic-dashboard](https://github.com/soul-traveller/github-traffic-dashboard), extended with platform-specific download statistics (Windows / macOS / Linux).

# 📊 GitHub Traffic & Downloads Dashboard

This dashboard tracks historical traffic data (clones, views, and release downloads) for GitHub repositories.

**Last Updated:** 2026-05-28T07:59:58.288080Z

## 📋 How Metrics Are Calculated

This dashboard uses GitHub Traffic API data to calculate the following metrics:

### 📊 Core Metrics

**Views:**
- Counted when someone visits the repository page
- Includes page views from web browsers
- Does not include visits via command-line tools or APIs

**Clones:**
- Counted when someone clones the repository
- Includes clones via `git clone`, GitHub Desktop, download ZIP, and API
- Can occur without a corresponding view event

**Release Downloads:**
- Counted when someone downloads a pre-compiled release asset (binary/installer)
- Split by platform from the asset file name (Windows, macOS, Linux); **All** is the combined total
- This is a **separate metric** from Clones - cloning the source is not a release download
- **Lifetime** totals reflect all-time downloads (GitHub's cumulative `download_count`) and are accurate immediately
- **Per-day** figures are derived by diffing daily snapshots, so they only accrue from the first tracked day onward

**Important:** Views and Clones are **independent metrics**. Users can:
- View without cloning
- Clone without viewing (e.g., via `git clone` command)
- Both view and clone

### 🔢 Calculation Formulas

**For any time period (short-term, medium-term, lifetime):**

**Total Metrics:**
- Total Views = Sum of daily views for the period
- Total Clones = Sum of daily clones for the period

**Unique Metrics:**
- Unique Views = Sum of daily unique views for the period
- Unique Clones = Sum of daily unique clones for the period
  - Note: This sums daily unique counts, which may count the same user on multiple days

**Repeat Metrics:**
- Repeat Views = Total Views - Unique Views
- Repeat Clones = Total Clones - Unique Clones
- Repeat Percentage = (Repeat / Total) × 100

**Example:**
```
If a repository has:
- Total Views: 100
- Unique Views: 20
Then:
- Repeat Views = 100 - 20 = 80
- Repeat Percentage = (80 / 100) × 100 = 80%
```

### 📈 Graph Data Aggregation

**Daily Graphs:**
- Shows raw daily data points
- Each point represents one day's activity

**Weekly Graphs:**
- Aggregates daily data into 7-day periods
- Each point represents the sum of 7 consecutive days

**Bi-Weekly Graphs:**
- Aggregates daily data into 14-day periods
- Each point represents the sum of 14 consecutive days

**Cumulative Graphs:**
- Shows running totals over time
- Each point represents the sum of all previous days plus current day

## 📋 Table of Contents

Quick navigation to repository statistics:

- [ChromIQ](#chromiq)

# ChromIQ

### 🗅️ Clones

*Repository clone statistics showing total and unique clones over different time periods.*

| Period | Total | Unique |
|--------|-------|--------|
| Last 30 Days | 6212 | 1356 |
| Last 90 Days | 6212 | 1356 |
| Lifetime | 6212 | 1356 |

### 📄 Repeat vs New Clones

*Analysis of repository adoption showing repeat clones vs new unique clones.*

*Note: GitHub API does not provide geographical location data for cloners.*

| Period | Total Clones | Unique Clones | Repeat Clones | Repeat % |
|--------|--------------|----------------|----------------|----------|
| Last 30 Days | 6212 | 1356 | 4856 | 78.2% |
| Last 90 Days | 6212 | 1356 | 4856 | 78.2% |
| Lifetime | 6212 | 1356 | 4856 | 78.2% |

### 👀 Views

*Repository view statistics showing total and unique views over different time periods.*

| Period | Total | Unique |
|--------|-------|--------|
| Last 30 Days | 871 | 250 |
| Last 90 Days | 871 | 250 |
| Lifetime | 871 | 250 |

### 📞 Referrers

*Top referrer sources driving traffic to this repository.*

**Total Unique Referrers:** 10

| Referrer | Total Views | Unique Visitors |
|----------|-------------|----------------|
| github.com | 87 | 14 |
| reddit.com | 36 | 14 |
| dpreview.com | 28 | 11 |
| printerknowledge.com | 13 | 7 |
| Google | 11 | 7 |
| hub.displaycal.net | 11 | 2 |
| forum.luminous-landscape.com | 7 | 4 |
| freelists.org | 4 | 1 |
| com.reddit.frontpage | 2 | 2 |
| www-printerknowledge-com.translate.goog | 2 | 1 |

### 👥 Repeat vs New Visitors

*Analysis of visitor engagement showing repeat visitors vs new unique visitors.*

*Note: GitHub API does not provide geographical location data for visitors.*

| Period | Total Views | Unique Visitors | Repeat Visitors | Repeat % |
|--------|-------------|-----------------|-----------------|----------|
| Last 30 Days | 871 | 250 | 621 | 71.3% |
| Last 90 Days | 871 | 250 | 621 | 71.3% |
| Lifetime | 871 | 250 | 621 | 71.3% |

### 📥 Release Downloads

*Pre-compiled release-asset downloads, split by platform. This is separate from clones.*

*Lifetime totals reflect all-time downloads (GitHub's cumulative counter). Per-day figures (Last 30/90 Days) are derived from daily snapshots and only accrue from the first tracked day onward.*

| Platform | Last 30 Days | Last 90 Days | Lifetime |
|----------|-----------|-----------|----------|
| 🪟 Windows | 28 | 28 | 118 |
| 🍎 macOS | 49 | 49 | 528 |
| 🐧 Linux | 1 | 1 | 32 |
| **All** | **78** | **78** | **678** |

🆕 **Latest Release:** `v3.8.0-beta.18` - **0** downloads (published 2026-05-28)

<details>
<summary><strong>📦 Per-version downloads</strong> (179 releases - click to expand)</summary>

| Release | 🪟 Windows | 🍎 macOS | 🐧 Linux | Total |
|---------|-----------|----------|----------|-------|
| v3.8.0-beta.18 | 0 | 0 | 0 | **0** |
| v3.8.0-beta.17 | 0 | 1 | 1 | **2** |
| v3.8.0-beta.16 | 2 | 1 | 0 | **3** |
| v3.8.0-beta.15 | 2 | 1 | 0 | **3** |
| v3.8.0-beta.14 | 6 | 1 | 0 | **7** |
| v3.8.0-beta.13 | 0 | 0 | 0 | **0** |
| v3.8.0-beta.12 | 0 | 0 | 0 | **0** |
| v3.8.0-beta.11 | 1 | 0 | 0 | **1** |
| v3.8.0-beta.10 | 1 | 0 | 0 | **1** |
| v3.8.0-beta.9 | 1 | 1 | 0 | **2** |
| v3.7.42 | 8 | 2 | 0 | **10** |
| v3.8.0-beta.8 | 0 | 0 | 0 | **0** |
| v3.8.0-beta.6 | 2 | 1 | 0 | **3** |
| v3.7.41 | 1 | 1 | 0 | **2** |
| v3.8.0-beta.5 | 0 | 0 | 0 | **0** |
| v3.8.0-beta.4 | 0 | 0 | 0 | **0** |
| v3.7.40 | 2 | 1 | 0 | **3** |
| v3.7.39 | 1 | 2 | 0 | **3** |
| v3.8.0-beta.3 | 0 | 0 | 0 | **0** |
| v3.8.0-beta.2 | 0 | 1 | 0 | **1** |
| v3.8.0-beta.1 | 0 | 1 | 0 | **1** |
| v3.7.38 | 1 | 2 | 0 | **3** |
| v3.7.37 | 1 | 0 | 0 | **1** |
| v3.7.36 | 1 | 0 | 0 | **1** |
| v3.7.35 | 0 | 0 | 0 | **0** |
| v3.7.34 | 0 | 0 | 0 | **0** |
| v3.7.33 | 1 | 1 | 0 | **2** |
| v3.7.32 | 1 | 1 | 0 | **2** |
| v3.7.31 | 1 | 0 | 0 | **1** |
| v3.7.30 | 0 | 0 | 0 | **0** |
| v3.7.29 | 0 | 0 | 0 | **0** |
| v3.7.28 | 0 | 1 | 0 | **1** |
| v3.7.27 | 1 | 1 | 0 | **2** |
| v3.7.26 | 0 | 0 | 0 | **0** |
| v3.7.25 | 2 | 0 | 0 | **2** |
| v3.7.24 | 2 | 0 | 0 | **2** |
| v3.7.23 | 0 | 1 | 0 | **1** |
| v3.7.22 | 2 | 4 | 2 | **8** |
| v3.7.21 | 1 | 2 | 0 | **3** |
| v3.7.20 | 0 | 1 | 0 | **1** |
| v3.7.19 | 4 | 2 | 0 | **6** |
| v3.7.18 | 0 | 1 | 0 | **1** |
| v3.7.17 | 1 | 1 | 0 | **2** |
| v3.7.16 | 0 | 0 | 0 | **0** |
| v3.7.15 | 1 | 3 | 0 | **4** |
| v3.7.14 | 3 | 2 | 0 | **5** |
| v3.7.13 | 0 | 2 | 0 | **2** |
| v3.7.12 | 0 | 1 | 0 | **1** |
| v3.7.11 | 1 | 1 | 0 | **2** |
| v3.7.10 | 2 | 6 | 0 | **8** |
| v3.7.9 | 0 | 10 | 0 | **10** |
| v3.7.8 | 0 | 9 | 0 | **9** |
| v3.7.7 | 0 | 4 | 0 | **4** |
| v3.7.6 | 0 | 6 | 0 | **6** |
| v3.7.5 | 5 | 7 | 1 | **13** |
| v3.7.4 | 1 | 8 | 0 | **9** |
| v3.7.3 | 0 | 8 | 0 | **8** |
| v3.7.2 | 1 | 1 | 0 | **2** |
| v3.7.1 | 0 | 38 | 2 | **40** |
| v3.7.0 | 3 | 35 | 3 | **41** |
| v3.6.7 | 3 | 40 | 3 | **46** |
| v3.6.6 | 4 | 32 | 2 | **38** |
| v3.6.5 | 3 | 42 | 3 | **48** |
| v3.6.4 | 3 | 48 | 3 | **54** |
| v3.6.3 | 0 | 1 | 0 | **1** |
| v3.6.2 | 0 | 0 | 0 | **0** |
| v3.6.1 | 0 | 1 | 0 | **1** |
| v3.6.0 | 3 | 6 | 4 | **13** |
| v3.5.13 | 1 | 1 | 3 | **5** |
| v3.5.12 | 0 | 1 | 0 | **1** |
| v3.5.11 | 0 | 0 | 0 | **0** |
| v3.5.10 | 1 | 0 | 0 | **1** |
| v3.5.9 | 2 | 0 | 0 | **2** |
| v3.5.8 | 1 | 2 | 0 | **3** |
| v3.5.7 | 1 | 0 | 0 | **1** |
| v3.5.6 | 0 | 0 | 0 | **0** |
| v3.5.5 | 0 | 3 | 0 | **3** |
| v3.5.4 | 0 | 0 | 0 | **0** |
| v3.5.3 | 0 | 1 | 0 | **1** |
| v3.5.2 | 1 | 1 | 0 | **2** |
| v3.5.1 | 0 | 1 | 0 | **1** |
| v3.5.0 | 1 | 3 | 1 | **5** |
| v3.5.0-beta.6 | 0 | 1 | 1 | **2** |
| v3.5.0-beta.5 | 0 | 0 | 2 | **2** |
| v3.2.9 | 3 | 1 | 0 | **4** |
| v3.5.0-beta.4 | 0 | 2 | 1 | **3** |
| v3.5.0-beta.3 | 0 | 0 | 0 | **0** |
| v3.5.0-beta.2 | 0 | 2 | 0 | **2** |
| v3.5.0-beta.1 | 0 | 0 | 0 | **0** |
| v3.2.8 | 1 | 2 | 0 | **3** |
| v3.2.7 | 0 | 3 | 0 | **3** |
| v3.2.6 | 0 | 0 | 0 | **0** |
| v3.2.5 | 0 | 1 | 0 | **1** |
| v3.2.4 | 0 | 1 | 0 | **1** |
| v3.2.3 | 0 | 0 | 0 | **0** |
| v3.2.2 | 0 | 1 | 0 | **1** |
| v3.2.1 | 0 | 0 | 0 | **0** |
| v3.2.0 | 0 | 1 | 0 | **1** |
| v3.2.0-beta.3 | 1 | 2 | 0 | **3** |
| v3.2.0-beta.2 | 0 | 2 | 0 | **2** |
| v3.2.0-beta.1 | 0 | 1 | 0 | **1** |
| v3.1.4 | 0 | 1 | 0 | **1** |
| v3.1.3 | 0 | 2 | 0 | **2** |
| v3.1.2 | 0 | 1 | 0 | **1** |
| v3.1.1 | 1 | 3 | 0 | **4** |
| v3.1.0 | 1 | 1 | 0 | **2** |
| v3.0.2 | 0 | 1 | 0 | **1** |
| v3.0.1 | 0 | 0 | 0 | **0** |
| v3.0.0 | 2 | 3 | 0 | **5** |
| v3.0.0-beta.10 | 3 | 15 | 0 | **18** |
| v3.0.0-beta.9 | 0 | 1 | 0 | **1** |
| v3.0.0-beta.8 | 2 | 1 | 0 | **3** |
| v3.0.0-beta.7 | 1 | 0 | 0 | **1** |
| v3.0.0-beta.6 | 1 | 0 | 0 | **1** |
| v3.0.0-beta.5 | 0 | 0 | 0 | **0** |
| v3.0.0-beta.4 | 1 | 1 | 0 | **2** |
| v3.0.0-beta.3 | 1 | 0 | 0 | **1** |
| v3.0.0-beta.2 | 5 | 0 | 0 | **5** |
| v3.0.0-beta.1 | 8 | 0 | 0 | **8** |
| v2.11.0 | 0 | 2 | 0 | **2** |
| v2.10.3 | 0 | 2 | 0 | **2** |
| v2.10.2 | 0 | 5 | 0 | **5** |
| v2.10.1 | 0 | 4 | 0 | **4** |
| v2.10.0 | 0 | 1 | 0 | **1** |
| v2.9.4 | 0 | 2 | 0 | **2** |
| v2.9.3 | 0 | 1 | 0 | **1** |
| v2.9.2 | 0 | 1 | 0 | **1** |
| v2.9.1 | 0 | 0 | 0 | **0** |
| v2.9.0 | 0 | 2 | 0 | **2** |
| v2.8.1 | 0 | 3 | 0 | **3** |
| v2.8.0 | 0 | 1 | 0 | **1** |
| v2.7.0 | 0 | 2 | 0 | **2** |
| v2.6.0 | 0 | 2 | 0 | **2** |
| v2.5.0 | 0 | 2 | 0 | **2** |
| v2.4.1 | 0 | 7 | 0 | **7** |
| v2.4.0 | 0 | 0 | 0 | **0** |
| v2.3.3 | 0 | 2 | 0 | **2** |
| v2.3.2 | 0 | 1 | 0 | **1** |
| v2.3.1 | 0 | 1 | 0 | **1** |
| v2.3.0 | 0 | 0 | 0 | **0** |
| v2.2.3 | 0 | 10 | 0 | **10** |
| v2.2.2 | 0 | 5 | 0 | **5** |
| v2.2.1 | 0 | 1 | 0 | **1** |
| v2.2.0 | 0 | 4 | 0 | **4** |
| v2.1.4 | 0 | 0 | 0 | **0** |
| v2.1.2 | 0 | 8 | 0 | **8** |
| v2.1.1 | 0 | 5 | 0 | **5** |
| v2.1.0 | 0 | 1 | 0 | **1** |
| v2.0.9 | 0 | 6 | 0 | **6** |
| v2.0.8 | 0 | 0 | 0 | **0** |
| v2.0.7 | 0 | 1 | 0 | **1** |
| v2.0.6 | 0 | 1 | 0 | **1** |
| v2.0.5 | 0 | 3 | 0 | **3** |
| v2.0.4 | 0 | 1 | 0 | **1** |
| v2.0.3 | 0 | 2 | 0 | **2** |
| v2.0.2 | 0 | 0 | 0 | **0** |
| v2.0.1 | 0 | 0 | 0 | **0** |
| v2.0.0 | 0 | 2 | 0 | **2** |
| v1.7.1 | 0 | 4 | 0 | **4** |
| v1.7.0 | 0 | 1 | 0 | **1** |
| v1.6.1 | 0 | 1 | 0 | **1** |
| v1.6.0 | 0 | 1 | 0 | **1** |
| v1.5.2 | 0 | 1 | 0 | **1** |
| v1.5.1 | 0 | 3 | 0 | **3** |
| v1.5.0 | 0 | 1 | 0 | **1** |
| v1.4.0 | 0 | 1 | 0 | **1** |
| v1.3.1 | 0 | 3 | 0 | **3** |
| v1.3.0 | 0 | 1 | 0 | **1** |
| v1.2.0 | 0 | 1 | 0 | **1** |
| v1.1.6 | 0 | 2 | 0 | **2** |
| v1.1.5 | 0 | 0 | 0 | **0** |
| v1.1.3 | 0 | 3 | 0 | **3** |
| v1.1.2 | 0 | 1 | 0 | **1** |
| v1.1.1 | 0 | 1 | 0 | **1** |
| v1.1.0 | 0 | 1 | 0 | **1** |
| v1.0.3 | 0 | 1 | 0 | **1** |
| v1.0.2 | 0 | 2 | 0 | **2** |
| v1.0.1 | 0 | 1 | 0 | **1** |
| v1.0.0 | 0 | 1 | 0 | **1** |

</details>

**By Architecture (lifetime):**

*Lifetime downloads split by CPU architecture - useful for deciding which builds are still worth shipping.*

| Platform | arm64 | x86_64 | universal | Total |
|----------|-------|-------|-------|-------|
| 🪟 Windows | 22 | 96 | 0 | **118** |
| 🍎 macOS | 325 | 138 | 65 | **528** |
| 🐧 Linux | 8 | 24 | 0 | **32** |

**Top 10 Releases by Downloads (lifetime):**

| Release | Downloads | Published |
|---------|-----------|-----------|
| v3.6.4 | 54 | 2026-05-17 |
| v3.6.5 | 48 | 2026-05-18 |
| v3.6.7 | 46 | 2026-05-18 |
| v3.7.0 | 41 | 2026-05-18 |
| v3.7.1 | 40 | 2026-05-18 |
| v3.6.6 | 38 | 2026-05-18 |
| v3.0.0-beta.10 | 18 | 2026-05-08 |
| v3.7.5 | 13 | 2026-05-19 |
| v3.6.0 | 13 | 2026-05-17 |
| v3.7.42 | 10 | 2026-05-26 |

#### Daily Release Downloads (30 Days)

*Per-day downloads for the last 30 days, by platform. Useful for spotting download spikes after new releases.*

![Daily Downloads 30 Days](graphs/itsab1989_ChromIQ_downloads_daily_30d.png)

#### Cumulative Release Downloads (Lifetime)

*All-time running download totals by platform. Useful for seeing overall adoption per platform.*

![Cumulative Downloads](graphs/itsab1989_ChromIQ_downloads_cumulative.png)

### 📈 Traffic Graphs

*Visual representations of traffic trends over different time periods.*

#### Daily Traffic (30 Days)

*Shows daily clones and views trends for the last 30 days. Useful for identifying short-term patterns and recent activity spikes.*

![Daily 30 Days](graphs/itsab1989_ChromIQ_daily_30d.png)

#### Weekly Traffic (12 Weeks)

*Shows weekly aggregated clones and views for the last 12 weeks (~3 months). Useful for identifying medium-term trends and seasonal patterns.*

![Weekly 12 Weeks](graphs/itsab1989_ChromIQ_weekly_12m.png)

#### Bi-Weekly Traffic (26 Periods)

*Shows bi-weekly aggregated clones and views for the last 26 periods (~1 year). Useful for identifying long-term trends and yearly patterns.*

![Bi-Weekly 26 Periods](graphs/itsab1989_ChromIQ_biweekly_26y.png)

#### Cumulative Traffic (Lifetime)

*Shows running totals of both clones and views over the entire lifetime of tracking. Useful for seeing overall growth and total adoption.*

![Cumulative](graphs/itsab1989_ChromIQ_cumulative.png)

#### Separate Cumulative Graphs

*Individual cumulative graphs for clones and views, allowing for easier comparison between the two metrics.*

**Cumulative Clones:**

![Cumulative Clones](graphs/itsab1989_ChromIQ_cumulative_clones.png)

**Cumulative Views:**

![Cumulative Views](graphs/itsab1989_ChromIQ_cumulative_views.png)

---

*This dashboard is automatically updated daily using GitHub Actions.*
