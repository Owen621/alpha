# Alpha – Solana Wallet Discovery Engine

## Overview

**Alpha** is a data-driven tool designed to identify *early buyers* of newly launched Solana tokens. Its goal is to surface wallets that consistently enter positions early—potentially indicating informational or executional edge.

The tool automates the process of analysing on-chain activity to uncover high-signal wallets that can be further investigated, tracked, or used for strategy development.

Built over several weeks for personal use, Alpha has already proven useful in identifying profitable trading opportunities over summer.

---

## Key Features

- **Early Buyer Detection**  
  Identifies wallets interacting with a token shortly after launch using on-chain transaction data.

- **PnL & ROI Calculation**  
  Tracks wallet performance across multiple transactions within a defined time window.

- **Multi-token Processing**  
  Supports concurrent analysis of multiple tokens using multi-threading.

- **Data Export**  
  Outputs structured results into CSV for further analysis.

- **Efficient API Usage**  
  Optimised to minimise API credit usage while scanning high volumes of blocks.

---

## Technical Highlights

- Parallel transaction processing (multi-threading)
- Block-level scanning for precise early-entry detection
- Filtering of failed transactions and low-signal activity
- Designed for extensibility (wallet tracking, scoring, and classification)

---

## Limitations / Scope

- Wallet scoring/classification system was **designed but not implemented**
- Focus is currently on **early buyer discovery**, not automated trading

---

## Planned Improvements

- Persist wallet and token data using SQLite  
- Implement wallet classification system (e.g. Sniper, Insider, Whale)  
- Introduce historical performance scoring (hit rate, ROI over time)  

---

## Development Log

### 20/08
Fully functional pipeline:
- Fetches recent tokens reliably  
- Identifies early buyers above threshold SOL  
- Calculates PnL across multiple transactions  
- Stores results in CSV  

---

### 03/07
- Handles inactivity gaps between launch and migration  
- Important for detecting pre-DEX buyers  
- Accuracy prioritised over execution speed  
- Suggestion: extend search window and rely on wallet limits rather than time cutoffs  

---

### 01/07
![image](https://github.com/user-attachments/assets/c2b5829b-a9cd-41d7-96a6-f2de1441090e)

- Simplified input: only token address required  
- Tested multiple concurrent runs successfully  
- Handled edge cases:
  - Launch and migration occurring within the same minute  
  - Tokens where transactions were not classified as swaps  

**Known Issue:**  
- Some transactions (e.g. `createIdempotent`, fee-related interactions) distort ROI calculations (e.g. -100% ROI when partially holding)  
- Requires improved filtering logic  

**Next Step:**  
- Automate fetching high-volume / high-MC tokens via API  

---

### 24/06
![image](https://github.com/user-attachments/assets/2af45433-0d4c-4ee4-989b-15f1ea9db637)

- Launch time no longer manually required  
- Automatically derived from migration time  
- (Direct launch time retrieval is difficult on Solana)  

---

### 23/06
![image](https://github.com/user-attachments/assets/4b7523fe-2a61-46e4-8775-53bdf51c2252)

- Initial optimisation work  
- Parallel runs: 4 × 20 configuration  

---

### 20/06/25
![image](https://github.com/user-attachments/assets/e9470efb-db04-4ea6-a0a2-de072adf2954)

- Tested with 4 tokens simultaneously  
- Up to 15 wallets per token (60 wallets total)  
- Data validated in CSV output  

**Performance:**
- ~6 minutes runtime  
- Scales efficiently with additional tokens due to multi-threading  

---

### 19/06/2025
![image](https://github.com/user-attachments/assets/1517a9c7-d3f9-4050-8df7-7de5c4e4112e)

- Multi-token support implemented  
- PnL calculated between configurable time windows  
- CSV export working  

**Notes:**
- Some inaccuracies in average price and metrics  
- Realised SOL calculation may need adjustment (cost basis not fully accounted for)  

---

### 17/06
Initial implementation:

- Early transaction detection using:
  - Token address  
  - Launch time (manual input)  
- Filtering:
  - Failed transactions  
  - Minimum SOL threshold  

**Performance Notes:**
- Scans hundreds of blocks for high-volume tokens  
- Low API credit usage (Helius), so acceptable trade-off  

---

## Original Next Steps (Design Notes)

- Automate fetching high-volume recent tokens  

- Improve performance:
  - Parallelise transaction processing across tokens  
  - Potential use of `ThreadPoolExecutor`  

- Profit analysis:
  - Calculate profit up to a defined "assessment point"  
  - Include unrealised profit and identify long-term holders  

- Data storage (SQLite):
  - Tokens (metadata, launch time)  
  - Wallets (activity logs, transactions, timestamps, PnL)  
  - Wallet scores and tags  

---

## Wallet Classification Concept (Planned)

Example metrics for a wallet:

- 12 tokens entered early  
- 4 successful (>5x)  
- 8 failed/rugged  
- Hit Rate: 33%  
- Avg ROI: 2.4x  

Proposed classifications:

- **Sniper** → >40% hit rate, >3x avg ROI  
- **Sprayer** → <20% hit rate, high volume  
- **Insider** → Appears only in high-performing tokens  
- **Luck** → One major win, otherwise losses  

Time-window filtering is important (focus on recent performance, not historical outliers).

---

## Summary

Alpha demonstrates practical experience in:

- Blockchain data processing (Solana)
- Building data pipelines for noisy, real-world datasets
- Performance analytics (PnL, ROI)
- Concurrency and optimisation
- Iterative system design and debugging

The project reflects a strong focus on extracting actionable insights from on-chain data and solving real-world problems in a fast-moving environment.
