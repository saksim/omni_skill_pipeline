from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Sequence

import numpy as np


@dataclass(slots=True)
class ParsedChangePoint:
    index: int
    timestamp: str
    previous_value: float
    current_value: float
    delta: float
    delta_zscore: float


@dataclass(slots=True)
class ParsedAnomalyInterval:
    start_timestamp: str
    end_timestamp: str
    length: int
    max_zscore: float


@dataclass(slots=True)
class ParsedTimeSeriesSignal:
    baseline_mean: float
    baseline_std: float
    baseline_min: float
    baseline_max: float
    recent_mean: float
    drift_score: float
    drift_label: str
    change_points: list[ParsedChangePoint] = field(default_factory=list)
    anomaly_intervals: list[ParsedAnomalyInterval] = field(default_factory=list)
    anomaly_timestamps: list[str] = field(default_factory=list)


class TimeSeriesSemanticParser(object):
    def __init__(
        self,
        *,
        baseline_ratio: float = 0.35,
        min_baseline_points: int = 4,
        change_sigma: float = 2.0,
        anomaly_z_threshold: float = 2.2,
        drift_z_threshold: float = 1.8,
        eps: float = 1e-9,
    ) -> None:
        self.baseline_ratio = baseline_ratio
        self.min_baseline_points = min_baseline_points
        self.change_sigma = change_sigma
        self.anomaly_z_threshold = anomaly_z_threshold
        self.drift_z_threshold = drift_z_threshold
        self.eps = eps

    def parse(self, *, timestamps: Sequence[object], values: Sequence[float]) -> ParsedTimeSeriesSignal:
        if not values:
            return ParsedTimeSeriesSignal(
                baseline_mean=0.0,
                baseline_std=0.0,
                baseline_min=0.0,
                baseline_max=0.0,
                recent_mean=0.0,
                drift_score=0.0,
                drift_label='stable',
            )

        normalized_timestamps = [str(item) for item in timestamps]
        series = np.asarray(values, dtype=float)
        n = int(series.shape[0])
        baseline_count = self._baseline_count(n)
        baseline = series[:baseline_count]
        recent = series[-baseline_count:]

        baseline_mean = float(np.mean(baseline))
        baseline_std = float(np.std(baseline))
        baseline_min = float(np.min(baseline))
        baseline_max = float(np.max(baseline))
        recent_mean = float(np.mean(recent))

        drift_delta = recent_mean - baseline_mean
        drift_score = abs(drift_delta) / (baseline_std + self.eps)
        if drift_score >= self.drift_z_threshold and drift_delta > 0:
            drift_label = 'upward_drift'
        elif drift_score >= self.drift_z_threshold and drift_delta < 0:
            drift_label = 'downward_drift'
        else:
            drift_label = 'stable'

        change_points = self._detect_change_points(series, normalized_timestamps, baseline_std)
        anomaly_intervals, anomaly_timestamps = self._detect_anomaly_intervals(
            series=series,
            timestamps=normalized_timestamps,
            baseline_mean=baseline_mean,
            baseline_std=baseline_std,
        )

        return ParsedTimeSeriesSignal(
            baseline_mean=baseline_mean,
            baseline_std=baseline_std,
            baseline_min=baseline_min,
            baseline_max=baseline_max,
            recent_mean=recent_mean,
            drift_score=float(drift_score),
            drift_label=drift_label,
            change_points=change_points,
            anomaly_intervals=anomaly_intervals,
            anomaly_timestamps=anomaly_timestamps,
        )

    def _baseline_count(self, n: int) -> int:
        ratio_count = int(math.ceil(float(n) * self.baseline_ratio))
        return max(1, min(n, max(self.min_baseline_points, ratio_count)))

    def _detect_change_points(
        self,
        series: np.ndarray,
        timestamps: list[str],
        baseline_std: float,
    ) -> list[ParsedChangePoint]:
        if series.shape[0] < 2:
            return []
        diffs = np.diff(series)
        abs_diffs = np.abs(diffs)
        diff_std = float(np.std(abs_diffs))
        threshold = max((baseline_std + self.eps) * self.change_sigma, (diff_std + self.eps) * self.change_sigma)
        points: list[ParsedChangePoint] = []
        for idx, delta in enumerate(diffs, start=1):
            abs_delta = abs(float(delta))
            if abs_delta < threshold:
                continue
            z_score = abs_delta / (diff_std + self.eps)
            points.append(
                ParsedChangePoint(
                    index=idx,
                    timestamp=timestamps[idx],
                    previous_value=float(series[idx - 1]),
                    current_value=float(series[idx]),
                    delta=float(delta),
                    delta_zscore=float(z_score),
                )
            )
        return points

    def _detect_anomaly_intervals(
        self,
        *,
        series: np.ndarray,
        timestamps: list[str],
        baseline_mean: float,
        baseline_std: float,
    ) -> tuple[list[ParsedAnomalyInterval], list[str]]:
        if series.size == 0:
            return [], []
        z_scores = np.abs((series - baseline_mean) / (baseline_std + self.eps))
        mask = z_scores >= self.anomaly_z_threshold
        intervals: list[ParsedAnomalyInterval] = []
        anomaly_timestamps: list[str] = []
        start_idx: int | None = None
        max_z = 0.0
        for idx, flagged in enumerate(mask):
            if flagged:
                anomaly_timestamps.append(timestamps[idx])
                max_z = max(max_z, float(z_scores[idx]))
                if start_idx is None:
                    start_idx = idx
                continue
            if start_idx is None:
                continue
            end_idx = idx - 1
            intervals.append(
                ParsedAnomalyInterval(
                    start_timestamp=timestamps[start_idx],
                    end_timestamp=timestamps[end_idx],
                    length=end_idx - start_idx + 1,
                    max_zscore=max_z,
                )
            )
            start_idx = None
            max_z = 0.0

        if start_idx is not None:
            end_idx = len(mask) - 1
            intervals.append(
                ParsedAnomalyInterval(
                    start_timestamp=timestamps[start_idx],
                    end_timestamp=timestamps[end_idx],
                    length=end_idx - start_idx + 1,
                    max_zscore=max_z,
                )
            )
        return intervals, anomaly_timestamps
