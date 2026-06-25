"""Table 5: ``historics`` — yearly peak-vs-average ILI summary."""

from __future__ import annotations

import pandas as pd


def build_historics(fluview: pd.DataFrame) -> pd.DataFrame:
    """Build the historical flu-season summary from FluView ILI data.

    For each calendar year, computes the peak weighted-ILI percentage, the
    epiweek of that peak, the yearly average, and the peak-vs-average gap.

    Returns:
        Columns: ``year``, ``decade_year``, ``peak_week_id``,
        ``peak_ili_percent``, ``average_wili_percent``, ``peak_vs_avg_diff``.
    """
    df = fluview[["epiweek", "wili"]].copy()
    df["year"] = df["epiweek"].astype(str).str[:4].astype(int)
    df["decade_year"] = (df["year"] // 10) * 10

    by_year = df.groupby("year")["wili"]
    df["peak_ili_percent"] = by_year.transform("max")
    df["average_wili_percent"] = by_year.transform("mean")

    # Epiweek at which each year's peak occurs.
    peak_idx = df.groupby("year")["wili"].idxmax()
    peak_week = df.loc[peak_idx, ["year", "epiweek"]].rename(
        columns={"epiweek": "peak_week_id"}
    )
    df = df.merge(peak_week, on="year", how="left")

    df["peak_vs_avg_diff"] = df["peak_ili_percent"] - df["average_wili_percent"]

    return (
        df[
            [
                "year",
                "decade_year",
                "peak_week_id",
                "peak_ili_percent",
                "average_wili_percent",
                "peak_vs_avg_diff",
            ]
        ]
        .drop_duplicates()
        .sort_values("year")
        .reset_index(drop=True)
    )
