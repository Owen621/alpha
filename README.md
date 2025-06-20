# alpha

20/06/25
![image](https://github.com/user-attachments/assets/e9470efb-db04-4ea6-a0a2-de072adf2954)

tested with 4 coins simultaneously with max 15 wallets for each so 60 wallets fetched in total

all data now correct in csv table

whole program took about 6 minutes to run however this wont increase much with additional coins up to a certain amount due to multi threading



17/06
Finds early transactions based on unix time on launch and token address both manually provided

Filters out failed transactions and minimum sol exchanged filter

Takes a while since it checks 100s of blocks for high volume tokens, however it uses minimal helius credits at the moment so its not a problem

Next steps:

automate fetching high volume recent tokens

at some point in order to reduce processing time, the transaction checking needs to be ran in parallel for all tokens potentially using ThreadPoolExecutor

calculate profit from these early buyers up to a "profit assessment point" at which point calculate unrealized profit and tag as a HODLER

store data on wallets in sqlite such as:
Tokens (metadata, launch time)
Wallets + activity logs (transactions, timestamps, PnL)
Wallet scores and tags (Hodler, Flipper, Whale, etc.)

classify wallets

introduce smart wallet history on stored wallets (check if lucky or degen sprayer)
pull its SPL transaction history and score eg:
For Wallet X:
- 12 tokens entered early
- 4 successful (>5x)
- 8 failed/rugged
- Hit Rate: 33%
- Avg ROI: 2.4x
tag these wallets now eg:
- Sniper: >40% hit rate, >3x avg ROI
- Sprayer: <20% hit rate, high volume
- Insider: Appears only in high-win tokens, but low frequency
- Luck: 1 big hit, otherwise losses
Only check history from a certain window of time, i need to know whos winning now not who won 2 years ago


19/06/2025
![image](https://github.com/user-attachments/assets/1517a9c7-d3f9-4050-8df7-7de5c4e4112e)

Still some errors as you can see with average price and a few other things but other than that lots of progress made

Can run multiple provided coins at a time and get pnl from early buyers from point in time x up to point in time y

exports this data to csv file

utilising multiple platforms to run concurrently in order to prevent 429 on free plans

edit: i think i may need to change stats that are calculated such as realised sol is not minusing original sol spent

