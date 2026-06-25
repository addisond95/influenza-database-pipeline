"""WA Census population-density source."""

from __future__ import annotations

import logging

import pandas as pd

from flu_pipeline.config import CENSUS_URL

logger = logging.getLogger(__name__)


def fetch_census(url: str | None = None) -> pd.DataFrame:
    """Download WA county population-density data."""
    url = url or CENSUS_URL
    logger.info("Downloading Census data from %s", url)
    df = pd.read_csv(url)
    logger.info("Census: %d county rows", len(df))
    return df
