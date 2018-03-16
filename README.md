# Findata Fetcher

## Main Idea
Downloads all available fundamentals and price data for tickers specified in a 
ticker list ("ticlist") .dat file, puts this data in a .dat file compatible with
[Deep Quant](https://github.com/euclidjda/deep-quant).


## Setup
Clone the repo:

```shell
git clone https://github.com/nachoaz/findata_fetcher.git
cd findata_fetcher
```

We suggest that you create a virtual environment to house the necessary versions
of the software you'll need to use Findata Fetcher. Once you've created and
activated that environment (or not), you can setup your environment and install
the required versions onto that environment by doing:

```shell
export FINDATA_FETCHER_ROOT=`pwd`
pip3 install -r requirements.txt
```

## Quickstart Guide
To create `open-dataset.dat` from `open-ticlist.dat`, simply run:

```shell
python fetch_data_write_datfile.py open-ticlist.dat jda-map YOURQUANDLAPIKEY
```

*Note*: You'll need an API key from Quandl. Read [here](https://goo.gl/4VccrT).

Also note that you might have to run this several times to get the *full*
dataset; because some of the downloading work is parallelized, different
processes make requests to the server from which data is downloaded; because of
this, it can occur that too many requests are made and --in turn-- some are
rejected by the server (and this results in some data that _is_ hosted by the
server not being downloaded at times, which is why you have to try again).


## Usage Details
Findata Fetcher pulls from a number of sources to build a .dat file that can
then be used for modeling with deep-quant. To know what to pull, Findata Fetcher
relies on a ticker list ('ticlist') .dat file; these 'ticlist' files are the
interface between Findata Fetcher and the user. They live in
`data/ticker-lists`.

Every 'ticlist' file should abide by the following format: it should be a
three-column space-delimtied file with the header "Ticker Market Sector" at the
very top.  See, for example, the first few lines of `open-ticlist.dat`, from
which `open-dataset.dat` is built:

```text 
Ticker Market Sector
AAL NASDAQ Services
AAON NASDAQ Industrial_Goods
AAPL NASDAQ Consumer_Goods
AAWW NASDAQ Services
```

Note that the ticker and market names are all caps, that the first letter of
every word in the sector name is capitalized, and that any spaces in a sector
name are replaced by an underscore.

Although a 'ticlist' file can be written manually by the user, there's a script
(`create_ticlist_file_from_screener_result.py`) that translates a .csv file
(typically the output of a stock screener) into a 'ticlist' .dat file, and puts
it where it in the `ticker-lists` directory. (All that's required for this to
work is that the .csv file's name must begin with the market in which the
tickers listed in that file are sold --in lowercase, and the file must contain
(at least) the columns 'Ticker' and 'Sector'.) Note that you can specify more
than one screener result .csv file (it'll simply concatenate the results). This
is how `open-ticlist.dat` is built, for example:

```shell
python create_ticlist_file_from_screener_result.py open-ticlist.dat
nasdaq_geq_100m_USA_more_than_10_years.csv
nyse_geq_100m_USA_more_than_10_years.csv
```

The other important interface between Findata Fetcher and the user are
'feat_map'.txt files (which reside in `data/feature-mappings`). These files
allow the user to specify not only _which_ pieces of data to use, but also the
format and desired name for the feature associated with each of those pieces of
data. Every 'feat_map' file must be written manually by the user, and must also
abide by a particular format. See the contents of `jda-map.txt`, for example:

```text
srfile|srfile_feat|mdfile_feat|version
income|Revenues|saleq|ttm
income|Cost of Revenue|cogsq|ttm
income|Selling, General and Administrative Expense|xsgaq|ttm
income|Operating Income|oiadpq|ttm
income|Net Income|niq|ttm
balance|Cash and Equivalents|cheq|mrq
balance|Trade and Non-Trade Receivables|rectq|mrq
balance|Inventory|invtq|mrq
balance|Investments Current|acoq|mrq
```
A few notes on the format of 'feat_map' files:

>  * the delimiter is the bar character `|`
>  * the first line should be: `srfile|srfile_feat|mdfile_feat|version`
>  * the first column should be one of (`income`, `balance`, `cashflow`,
>    `growth`, `metrics`), and answers the question of "which srow_data .xlsx
>    file does this reside in?"
>  * the second column answers the question "by what name is the piece of data
>    that you want indexed on the .xlsx file that you specified in column 1?"
>  * the third column answers the question "what name would you like this piece
>    of data to have on the .dat file that will be produced?"
>  * the fourth column should be one of (`ttm`, `mrq`, `ttm_implicit`, or
>    `mrq_implicit`). It specifies whether you want this piece of data to be in
>    the form of 'trailing twelve months' or in 'most recent quarter' form. The
>    `_implicit` versions are the same as the first two, except that while the
>    first two versions rename the corresponding .dat column as specified by
>    `mdfile_feat` _and_ append a `_ttm` or `_mrq` postfix to that .dat column
>    name, the `_implicit` versions do not.


Once you have a 'ticlist' file and a 'feat_map' file in place, you can build a
deep-quant-compatible dataset.dat file either in one shot using
`fetch_data_write_datfile.py` or in steps, using `download_ticker_data.py`,
`write_cp_datafiles.py`, `write_processed_datafiles.py`, and `write_datfile.py`
(in that order).
