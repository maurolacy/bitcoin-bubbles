# Scripts

## tidy.sh

A bash script used for extracting Bitcoin active addresses and market capitalization data from HTML pages (before the automated notebook implementation).

### Usage

```bash
./tidy.sh <file>.html
```

### What it does

Extracts date and active address data from HTML files downloaded from bitinfocharts.com, converting them to CSV format. This script was used in earlier versions of the notebooks that required manual data extraction.

**Note**: This script is no longer needed with the automated notebook (`bitcoinUsersCsvNoVAuto.nb`), which downloads and processes data automatically.

### Requirements

- `tidy` command-line HTML parser.
- Standard Unix tools (`sed`, `head`, `tee`, `basename`).