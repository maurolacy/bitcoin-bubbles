# Bitcoin Bubble Prediction Models

## Introduction

An implementation of the models described in "Are Bitcoin Bubbles Predictable? Combining a Generalized Metcalfe's Law and the LPPLS Model" (arXiv:1803.05663) in Mathematica.

This repository contains implementations of:

- **LPPLS Model**: Log-Periodic Power Law Singularity model for predicting bubble breakouts/crashes.
- **Metcalfe's Law Model**: Using active Bitcoin addresses as a proxy for network users to assess overvaluation.

**⚠️ Important Disclaimer**: This is research / educational software. Not investment advice. Use at your own risk. See the [Disclaimer](#disclaimer) section below.

## Dependencies

- **Mathematica**: Version 12.0 or later (tested with versions 12.0 and 13.2).
- **R**: Required for some auxiliary scripts and data processing (`loess` dof estimation).

## Getting Started

### Quick Start

1. **Install Dependencies**:
   - Mathematica 12.0 or later.
   - R (for auxiliary scripts).

2. **Run the Overvaluation Model**:
   - Open `bitcoinUsersCsvNoVAuto.nb` in Mathematica.
   - The notebook automatically downloads data from online sources.
   - Execute all cells (Cell → Evaluate Notebook).
   - Results are exported to the `pdf/` folder.

3. **Run LPPLS Model**:
   - Open the appropriate LPPLS notebook (e.g., `LPPLS25.nb` for 2025 predictions).
   - Execute all cells.
   - The model will fit price data and attempt to identify bubble regimes.

### Data Sources

The notebooks automatically fetch data from:

- Bitcoin price data: cryptodatadownload.com
- Active addresses: bitinfocharts.com
- Market capitalization: bitinfocharts.com

**Note**: Ensure you have internet connectivity for automatic data download.

### Output Files

- **PDF files**: Generated plots and analysis saved to `pdf/` folder.
- **CSV files**: Processed data saved to `csv/` folder (if generated).

## Methodology

### LPPLS Model

The Log-Periodic Power Law Singularity model attempts to identify bubble regimes by detecting log-periodic oscillations in price data that precede crashes. The model fits price data to detect critical points where bubbles may burst.

### Metcalfe's Law Model

Uses active Bitcoin addresses as a proxy for network users. Fits Bitcoin market capitalization to a generalized Metcalfe's law model (value ∝ n², where n is the number of users). Compares actual market cap to the model's prediction to assess overvaluation.

## Notebooks

### LPPLS Models

- **LPPLS18.nb** - Breakout prediction for the 2018 bubble.
- **LPPLS21.nb** - Breakout prediction for the 2021 bubble.
- **LPPLS23.nb** - Breakout prediction for the 2023 bubble.
- **LPPLS24.nb** - Breakout prediction for the 2024 bubble.
- **LPPLS25.nb** - Breakout prediction for the 2025 bubble (most recent).

### Overvaluation Models

- **bitcoinUsersCsvNoVAuto.nb** - Overvaluation model with automatic data download and processing (recommended).

**Note**: Older versions (`bitcoinUsersCsv.nb`, `bitcoinUsersCsvNoV.nb`) have been moved to the `deprecated/` folder. These earlier implementations required manual data verification or lacked automatic processing features.

## Limitations and Caveats

### 1. False Positive Problem

The LPPLS model has a significant limitation: **it produces many false positives**. The model frequently signals potential bubble breakouts that do not materialize into actual crashes. This creates several problems:

- **Signal fatigue**: Too many warnings make it difficult to distinguish real signals from noise.
- **Low precision**: Many false alarms relative to actual crashes.
- **Limited practical utility**: Without a reliable way to filter false positives, the model's predictive value is severely diminished.

**Historical Performance**: The model successfully predicted the 2021 Bitcoin crash, but has not performed well for subsequent bubble periods. This inconsistency further limits its reliability.

### 2. Data Quality Issues

#### Active Addresses Proxy Breakdown

The Metcalfe's law model uses active Bitcoin addresses as a proxy for network users. This approach has become increasingly problematic:

- **Lightning Network Impact**: The introduction of Lightning Network (LN) around 2020 means a growing portion of Bitcoin transactions occur off-chain.
- **Missing Activity**: LN transactions do not appear in on-chain active address data, creating a systematic undercount of actual network usage.
- **Proxy Validity**: The active addresses metric becomes less valid as a proxy for total network activity over time.

**Attempted Mitigation**: An attempt was made to cap user data to ~2020 (the peak in active addresses) and extrapolate using an exponential trend. However, this approach replaces hard data with assumptions, which undermines the model's empirical foundation and is not a satisfactory solution.

**Data Gap**: Reliable historical time series data for Lightning Network usage/transactions is not readily available, making it difficult to properly account for off-chain activity.

### 3. Model Assumptions

- **Metcalfe's Law**: Assumes network value scales as n², which may not hold for Bitcoin.
- **Single Metric**: Relies primarily on active addresses, ignoring other factors (speculation, institutional adoption, regulation, etc.).
- **Market Complexity**: Real markets are influenced by many factors beyond network size.

### 4. Temporal Limitations

- **Data Freshness**: Results become stale quickly as new data arrives.
- **Model Drift**: The relationship between active addresses and market cap may change over time.
- **Regime Changes**: Market dynamics may shift in ways the model doesn't capture.

## Disclaimer

**This software is provided for educational and research purposes only.**

- **Not Investment Advice**: This software does not constitute financial, investment, or trading advice.
- **No Warranty**: The models may be inaccurate, incomplete, or produce incorrect results.
- **Use at Your Own Risk**: Any use of this software for investment decisions is at your own risk.
- **Past Performance**: Past model performance (e.g., 2021 prediction) does not guarantee future accuracy.
- **Research Tool**: This is a research implementation, not a production trading system.

The authors and contributors are not responsible for any financial losses or damages resulting from the use of this software.

## References

- [Are Bitcoin Bubbles Predictable? Combining a Generalized Metcalfe's Law and the LPPLS Model](https://arxiv.org/pdf/1803.05663.pdf) - arXiv:1803.05663.
- [Transaction Dynamics of Blockchain and Predictable Bitcoin Bubbles](https://polybox.ethz.ch/index.php/s/LzLmTZXzqF8rCAs).
- [Metcalfe's Law](https://en.wikipedia.org/wiki/Metcalfe%27s_law).

## External Data Sources

- Bitcoin active addresses: [bitinfocharts.com](https://bitinfocharts.com).
- Bitcoin market capitalization: [bitinfocharts.com](https://bitinfocharts.com).
- Bitcoin price data: [cryptodatadownload.com](https://www.cryptodatadownload.com/data/bitstamp/).
- Bitcoin circulating supply: [blockchain.com](https://www.blockchain.com/charts/total-bitcoins).

## License

This project is provided for educational and research purposes. See the [LICENSE](LICENSE) file for details.

## Attribution

If you use this code in your research, publications, or projects, please provide appropriate attribution:

### Citation Format

When citing this implementation, please include:

- **This repository**: [Bitcoin-bubbles](https://github.com/maurolacy/bitcoin-bubbles).
- **Original academic paper**: "Are Bitcoin Bubbles Predictable? Combining a Generalized Metcalfe's Law and the LPPLS Model" (arXiv:1803.05663).
- **Author**: [Mauro Lacy Bopp](https://github.com/maurolacy).

### Example Citation

```
[Mauro Lacy Bopp]. (2025). Bitcoin Bubble Prediction Models - Mathematica Implementation.
GitHub Repository: [Bitcoin-bubbles](https://github.com/maurolacy/bitcoin-bubbles).
Based on: Sornette et al. (2018). "Are Bitcoin Bubbles Predictable? Combining a Generalized
Metcalfe's Law and the LPPLS Model." arXiv:1803.05663
```

### Commercial Use

For commercial use or incorporation into commercial products, please contact the author for permission.
