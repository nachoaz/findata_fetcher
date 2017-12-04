# findata_fetcher

## Main Idea
Downloads all available fundamentals and price data for tickers specified in
company list text files; these should be prefixed by market and postfixed by
`clist_pofix` (which provides details on how this set of stocks were screened).

## Usage
Standing inside the `scripts` directory, first create the `clist` files (which
will reside inside `data/company_lists`) corresponding to the list of companies
you want to consider, then download the data using `download_tkr_data.py`, then
write the corresponding `cp_data` ('close price' data) files using
`write_cp_datafiles.py`. Finally, write the `.dat` file corresponding to your
specified `clist`, `feat_map`, and `lag_months`.


## Example
`python write_clist_files.py clist_pofix`
where clist_pofix specifies what you want your clist_files to be named.
*Note*: this is yet to be written.

`python download_tkr_data.py consg_tech_more_than_10_years_head YOUR_API_KEY`
here `consg_tech_more_than_10_years_head` is a clist_pofix specifying where to
find the list of companies to use.

`python write_datafiles.py consg_tech_more_than_10_years_head`

`python prepare_data.py consg_tech_more_than_10_years_head jda_map.txt 3`
Here, jda_map.txt is a `feat_map` file. A `feat_map` file should reside in
`scripts/feature_mappings`, should be postfixed as `.txt`, and should abide by
the following format:
 * the delimiter is the bar character `|`
 * the first line should be: `srfile|srfile_feat|mdfile_feat|version`
 * the first column should be one of (`income`, `balance`, `cashflow`, `growth`,
   `metrics`), and answers the question of "which srow_data .xlsx file does this
   reside in?"
 * the second column answers the question "by what name is the piece of data that
   you want indexed on the .xlsx file that you specified in column 1?"
 * the third column answers the question "what name would you like this piece of
   data to have on the .dat file that will be produced?"
 * the fourth column shoudl be one of (`ttm`, `mrq`, `ttm_implicit`, or
   `mrq_implicit`). It specifies whether you want this piece of data to be in
   the form of 'trailing twelve months' or in 'most recent quarter' form. The
   `_implicit` versions are the same as the first two, except that while the
   first two versions rename the corresponding .dat column as specified by
   `mdfile_feat` _and_ append a `_ttm` or `_mrq` postfix to that .dat column
   name, the `_implicit` versions do not.


*Note*: You'll need an API key from Quandl. Read [here](goo.gl/gbtxsi).
