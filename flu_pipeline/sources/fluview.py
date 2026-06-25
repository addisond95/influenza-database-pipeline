"""CDC FluView (Delphi Epidata) source."""

from __future__ import annotations

import logging

import pandas as pd
import requests

from flu_pipeline.config import FLUVIEW_EPIWEEKS, FLUVIEW_REGION, FLUVIEW_URL

logger = logging.getLogger(__name__)

REQUEST_TIMEOUT = 60  # seconds


class FluViewError(RuntimeError):
    """Raised when the FluView API returns a non-success response."""


def fetch_fluview(
    url: str | None = None,
    region: str | None = None,
    epiweeks: str | None = None,
) -> pd.DataFrame:
    """Download CDC FluView ILI data for a region and epiweek range."""
    url = url or FLUVIEW_URL
    params = {
        "regions": region or FLUVIEW_REGION,
        "epiweeks": epiweeks or FLUVIEW_EPIWEEKS,
    }
    logger.info("Requesting FluView data: %s", params)

    response = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    payload = response.json()

    if payload.get("result") != 1:
        raise FluViewError(payload.get("message", "unknown FluView API error"))

    df = pd.DataFrame(payload["epidata"])
    logger.info(
        "FluView: %d weeks (%s..%s)",
        len(df),
        df["epiweek"].min(),
        df["epiweek"].max(),
    )
    return df
