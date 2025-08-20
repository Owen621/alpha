# alpha

This program finds early buyers on provided solana tokens. The goal is to try to find wallets with an edge on the market (eg inside info or highly skilled). These wallets change frequently so this program should be run on many coins weekly idealy. Consistent early buyers should then be looked further into manually (usually a very small pool of wallets). These wallets can be tracked or copied. You want to avoid KOL wallets, these can be found online. Often, the wallets found by this program are unknown by most people which is perfect, you dont want copy traders ruining the charts. I built this for personal use over a few weeks at the start of summer. So far, it has been very useful for me and has lead to many profitable trades.


20/08
Not updated this in a while since I've been away but program fully works now no issues fetching any reasonably recent token (old ones wont be relevant anyway), finding early buyers above x sol, calculating pnl on multiple transactions, and storing results in csv.


03/07
When there is a 10 or so minute gap between launch and migration where nothing has happened, especially since at the moment migration is such a low mc theres no much activity beforehand, the program may take a while to go through this period. This is important though to find the pre dex buyers with alpha. For the real thing, I suggest the window is extended massively and blocks are extensively searched, utilising the number of wallets per token limit rather than window cut off. The program will take a while to execute however this is not too important for now since accuracy of the data is vital

01/07
![image](https://github.com/user-attachments/assets/c2b5829b-a9cd-41d7-96a6-f2de1441090e)
Now you just need the token address, no migration time or anything else. I ran 4 at once with 0.06 window and it didnt take long
Also tested some edge cases where migration and launch were within the same minute and where a token was on a dex that tx didnt come up as swaps
I had to remove the selection statements for that case and will fix at a later date since its causing some errors in the output as you can see -100% roi partially holding is because there were txs with the wallet and token in which fees were paid: 3PTxoyKhj4gLjWLd9GetfSHr3ZU6DyaUhpJmg9JGkPatmopsPXD9jctLpa8agV4S41EdhuyTHZbxrdjXq7TJvcJj. One was createIdempotent and another something else not too sure what these are but ill look into filtering in a different way.
Next I need to automate fetching high volume/mc tokens on dex need to find an api



24/06
![image](https://github.com/user-attachments/assets/2af45433-0d4c-4ee4-989b-15f1ea9db637)
Estimated launch time is no longer provided. Automatically finds launch time from given migration time
(launch time cannot be fetched easily on solana)
apis which fetch coins can easily get migration time


23/06
![image](https://github.com/user-attachments/assets/4b7523fe-2a61-46e4-8775-53bdf51c2252)

optimisation. 4x20


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

