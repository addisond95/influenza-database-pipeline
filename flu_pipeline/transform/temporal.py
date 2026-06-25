"""Table 2: ``temporal`` — epiweek calendar reference."""

from __future__ import annotations

import pandas as pd


def add_epiweek_id(rhino: pd.DataFrame) -> pd.DataFrame:
    """Return a copy of ``rhino`` with an integer ``epiweek_id`` column.

    The id combines the four-digit year from ``Week End`` with the zero-padded
    week number, e.g. week 40 ending in 2023 -> ``202340``.
    """
    out = rhino.copy()
    out["epiweek_id"] = (
        out["Week End"].str[:4] + out["Week"].astype(str).str.zfill(2)
    )
    return out


def build_temporal(rhino: pd.DataFrame) -> pd.DataFrame:
    """Build the distinct epiweek calendar table.

    Args:
        rhino: County-exploded RHINO frame containing ``Week``, ``Week Start``,
            ``Week End`` and ``Season`` columns.

    Returns:
        Columns: ``epiweek_id`` (int), ``week_start`` (date), ``week_end``
        (date), ``season`` (str), sorted ascending by ``epiweek_id``.
    """
    with_id = add_epiweek_id(rhino)
    temporal = (
        with_id[["epiweek_id", "Week Start", "Week End", "Season"]]
        .drop_duplicates()
        .sort_values("epiweek_id")
        .reset_index(drop=True)
    )
    temporal["epiweek_id"] = temporal["epiweek_id"].astype(int)
    temporal["Week Start"] = pd.to_datetime(temporal["Week Start"])
    temporal["Week End"] = pd.to_datetime(temporal["Week End"])
    return temporal.rename(
        columns={
            "Week Start": "week_start",
            "Week End": "week_end",
            "Season": "season",
        }
    )
