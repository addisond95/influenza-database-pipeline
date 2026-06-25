"""Data source extractors.

Each module exposes a ``fetch_*`` function that returns a tidy pandas DataFrame.
Network access is isolated here so the transform layer stays pure and testable.
"""
