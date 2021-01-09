# Lending Bot <img src="www/images/icon192.png" width="50">
![Docker Cloud Build Status](https://img.shields.io/docker/cloud/build/volschin/lending-bot) ![Docker Pulls](https://img.shields.io/docker/pulls/volschin/lending-bot)
## Devs are Out of Office - Community Pull Requests will be considered

Lending Bot is written in Python and features automatic lending on exchanges Poloniex and Bitfinex.
It will automatically lend all cryptocurrencies found in your lending account.

It uses an advanced lending strategy which will spread offers across the lend book to take advantage of possible spikes in lending rates. Inspired by [MarginBot](https://github.com/HFenter/MarginBot) and [BitfinexLendingBot](https://github.com/eAndrius/BitfinexLendingBot).

Join the discussion at:

[![Join the chat at https://gitter.im/Mikadily/poloniexlendingbot](https://badges.gitter.im/Mikadily/poloniexlendingbot.svg)](https://gitter.im/Mikadily/poloniexlendingbot?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)

[<img src='https://img.shields.io/badge/Chat%20on-Telegram-brightgreen.svg' width='100'>](https://t.me/mikalendingbot)

[<img src='https://cdn.worldvectorlogo.com/logos/slack.svg' width='90'>](https://poloniexbot.slack.com/shared_invite/MTc5OTU4MDAzNTY4LTE0OTQzMTA2MzYtZDdkYTg1NjBkYg) **- Recommended for communicating with Devs**

[<img src='https://img.shields.io/reddit/subreddit-subscribers/poloniexlendingbot?style=social'>](https://www.reddit.com/r/poloniexlendingbot/) **- Recommended for focused discussion**

We also have a public [FAQ on the Github Wiki](https://github.com/BitBotFactory/MikaLendingBot/wiki/FAQ-(Troubleshooting)), feel free to add your questions or check there for support! 

## Documentation
[Click here to read the Documentation, hosted by readthedocs.io](http://poloniexlendingbot.readthedocs.io/en/latest/index.html)


### Features
- Automatically lend your coins on Poloniex and Bitfinex at the highest possible rates, 24 hours a day.
- Configure your own lending strategy! Be aggressive and hold out for a great rate or be conservative and lend often but at a lower rate, your choice!
- The ability to spread your offers out to take advantage of spikes in the lending rate.
- Withhold lending a percentage of your coins until the going rate reaches a certain threshold to maximize your profits.
- Lock in a high daily rate for a longer period of time period of up to sixty days, all configurable!
- Automatically transfer any funds you deposit (configurable on a coin-by-coin basis) to your lending account instantly after deposit.
- View a summary of your bot's activities, status, and reports via an easy-to-set-up webpage that you can access from anywhere!
- Choose any currency to see your profits in, even show how much you are making in USD!
- Select different lending strategies on a coin-by-coin basis.
- Run multiple instances of the bot for multiple accounts easily using multiple config files.
- Configure a date you would like your coins back, and watch the bot make sure all your coins are available to be traded or withdrawn at the beginning of that day.
- Docker support.
- And the best feature of all: It is absolutely free!
