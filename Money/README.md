Money
=====

CONFIGURATION
You'll need to setup the following in money.yml:
- You need an API key for the exchange rate service, [openexchangerates.org](https://openexchangerates.org/), which are free for 1000 uses/month. Enter it in API-key.

Other than that, the program should work fine wit the default settings. You can adjust the following if you wish:
- You can change the default out currencies by changing default-currs. This is used if a user doesn't enter what currency(ies) to convert to.
- You can change the output currency separator with curr-separator. By default, it is " | "

HOW TO USE
The command syntax is .money <value> <start currency> [<end currency 1> <end currency 2>...]
(replace . with whatever command character you're using)
- <value> is the amount of money to convert from;
- <start currency> is the currency that <value> is in.
- <end currency X> (optional) is the currency to convert to. You can enter as many values as you like.
If no end currency is entered, the command will default to a selection of common currencies, defined in money.yml
Output will be sent to wherever the command was issued. If you use the command in a channel, the output will go to that channel etc.

CREDITS
This was made by jimj316, with extensive help from gDude2002
pls don't steal