Money
=====

The money package adds a plugin that provides a command for currency conversion between various currencies. 
The currency conversion data is updated hourly.

## Configuration

The money plugin features integration with [Open Exchange Rates](https://openexchangerates.org/) - You'll need to create
a free account there and get an API key before you can use this plugin.

Configuration is stored in `config/plugins/money.yml`.

* `API-key` - Your API key for the Open Exchange Rates site.
* `default-currs: [GBP, USD, EUR, JPY, AUD, CHF]` - List of currencies to convert to if a user doesn't specify any output currencies.
* `curr-separator: " | "` - What to use as a separator between output currencies.

## Usage

This package supplies the following command..
* `money <value> <'from' currency> [<currency> <currency> ...]` - Do a currency conversion
  * `<value>` represents the amount of currency you want to convert.
  * `<'from' currency>` represents the currency you want to convert from.
  * `[<currency> <currency> ...]` represents the currencies you want to convert to. This defaults to whatever's in the configuration if not supplied.
* The command will be output to the current channel - or in a private message, if used in one.
* The command requires the `money.main` permission to be used.

## Licensing

This package was created by [jimj316](https://github.com/jimj316), who has licensed his work under the Creative Commons
BY-NC-SA license. For more information, you can read the LICENSE file or check [this link](http://creativecommons.org/licenses/by-nc-sa/3.0/).
