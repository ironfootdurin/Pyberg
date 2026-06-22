from sec_edgar_downloader import Downloader
from pathlib import Path
import shutil

def get_quarterly(ticker):
    form = '10-Q'
    folder = Path(__file__).parent / 'temp' / 'filings'
    folder.mkdir(parents=True, exist_ok=True)
    dl = Downloader(
        company_name=ticker,
        email_address='pyberg@duck.com',
        download_folder=folder
        )
    result = dl.get(form, ticker, limit=1)
    if result == 0:
        return False
    else:

        filings_dir = folder / 'sec-edgar-filings' / ticker / form

        latest_folder = sorted(filings_dir.iterdir())[-1]

        filing_file = latest_folder / 'full-submission.txt'
        html_file = latest_folder / f'{ticker}.html'
        shutil.copy(filing_file, html_file)
        return html_file.relative_to(folder).as_posix()


if __name__ == '__main__':
    ticker = input('Ticker: ')
    filing_file = get_quarterly(ticker)
    print(filing_file)
