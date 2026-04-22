from __future__ import annotations

import contextlib
from dataclasses import dataclass
from functools import lru_cache
import io
from pathlib import Path
from typing import Any, TYPE_CHECKING, Sequence

import numpy as np

if TYPE_CHECKING:
    import pandas as pd
else:
    class _PandasNamespace(object):
        DataFrame = Any

    pd = _PandasNamespace()  # type: ignore[assignment]

from omni_skill_pipeline.models import (
    Asset,
    ContentType,
    EvidenceUnit,
    LoadedAsset,
    Modality,
    TabularDistillRequest,
)
from omni_skill_pipeline.extraction.modality.timeseries_parser import TimeSeriesSemanticParser
from omni_skill_pipeline.utils import unique_preserve_order


@lru_cache(maxsize=1)
def _pandas_runtime():
    # Some environments ship optional pandas deps built against old NumPy ABI,
    # which emit noisy diagnostics on stderr during import even when pandas works.
    with contextlib.redirect_stderr(io.StringIO()):
        import pandas as pd_runtime
        from pandas.api.types import is_datetime64_any_dtype as is_datetime64_any_dtype_runtime
        from pandas.api.types import is_numeric_dtype as is_numeric_dtype_runtime

    return pd_runtime, is_datetime64_any_dtype_runtime, is_numeric_dtype_runtime


def _is_datetime_dtype(series: Any) -> bool:
    _, is_datetime64_any_dtype_runtime, _ = _pandas_runtime()
    return bool(is_datetime64_any_dtype_runtime(series))


def _is_numeric(series: Any) -> bool:
    _, _, is_numeric_dtype_runtime = _pandas_runtime()
    return bool(is_numeric_dtype_runtime(series))


@dataclass(slots=True)
class TimeSeriesSignal:
    column: str
    trend_label: str
    pct_change: float | None
    largest_jump_timestamp: str | None
    largest_jump_value: float | None
    baseline_mean: float | None
    baseline_std: float | None
    baseline_min: float | None
    baseline_max: float | None
    recent_mean: float | None
    drift_score: float | None
    drift_label: str
    change_points: list[tuple[str, float]]
    anomaly_intervals: list[tuple[str, str]]
    anomaly_timestamps: list[str]


class TabularAdapter(object):
    SUPPORTED_SUFFIXES = {'.csv', '.tsv', '.txt', '.json', '.xlsx', '.xls'}

    def __init__(self, timeseries_parser: TimeSeriesSemanticParser | None = None) -> None:
        self.timeseries_parser = timeseries_parser or TimeSeriesSemanticParser()

    def load(self, request: TabularDistillRequest) -> LoadedAsset:
        request.validate()
        path = Path(request.file_path)
        if not path.exists():
            raise FileNotFoundError(str(path))

        frame = self._read_frame(path)
        if frame.empty:
            raise ValueError('Tabular input is empty.')

        asset = Asset(
            modality=Modality.TABULAR,
            source_uri=str(path.resolve()),
            metadata={
                'filename': path.name,
                'row_count': int(len(frame)),
                'column_count': int(len(frame.columns)),
            },
        )
        title_hint = request.title or path.stem.replace('_', ' ')
        evidence_units: list[EvidenceUnit] = []

        evidence_units.append(self._schema_evidence(asset.asset_id, frame))
        evidence_units.append(self._missingness_evidence(asset.asset_id, frame))

        entity_columns = self._resolve_entity_columns(frame, request.entity_columns)
        if entity_columns:
            evidence_units.append(self._entity_evidence(asset.asset_id, frame, entity_columns))

        numeric_columns = [column for column in frame.columns if _is_numeric(frame[column])]
        if numeric_columns:
            evidence_units.extend(self._numeric_profile_evidence(asset.asset_id, frame, numeric_columns))

        time_column = self._resolve_time_column(frame, request.time_column)
        if time_column:
            prepared = self._prepare_time_frame(frame, time_column)
            value_columns = self._resolve_value_columns(prepared, request.value_columns, request.max_series)
            if value_columns:
                evidence_units.extend(
                    self._timeseries_evidence(asset.asset_id, prepared, time_column, value_columns, request.max_series)
                )
        else:
            evidence_units.append(self._generic_table_guidance(asset.asset_id, frame, numeric_columns))

        return LoadedAsset(
            asset=asset,
            evidence_units=evidence_units,
            title_hint=title_hint,
            adapter_metadata={
                'time_column': time_column,
                'entity_columns': entity_columns,
                'numeric_columns': numeric_columns[:12],
            },
        )

    def _read_frame(self, path: Path) -> pd.DataFrame:
        pd_runtime, _, _ = _pandas_runtime()
        suffix = path.suffix.lower()
        if suffix not in self.SUPPORTED_SUFFIXES:
            raise ValueError('Unsupported tabular format: %s' % suffix)
        if suffix == '.csv':
            return pd_runtime.read_csv(path)
        if suffix in {'.tsv', '.txt'}:
            return pd_runtime.read_csv(path, sep='\t')
        if suffix == '.json':
            try:
                return pd_runtime.read_json(path)
            except ValueError:
                return pd_runtime.read_json(path, lines=True)
        if suffix in {'.xlsx', '.xls'}:
            return pd_runtime.read_excel(path)
        raise ValueError('Unsupported tabular format: %s' % suffix)

    def _schema_evidence(self, asset_id: str, frame: pd.DataFrame) -> EvidenceUnit:
        lines = ['Table schema summary']
        lines.append('Rows: %s' % len(frame))
        lines.append('Columns: %s' % len(frame.columns))
        lines.append('1. Confirm row count and dtype assumptions before interpreting the table.')
        lines.append('2. Normalize time zones, units, and duplicated keys before aggregation.')
        lines.append('If a column mixes numeric and string forms, clean it before trend analysis.')
        lines.append('Verify the business grain of one row before building any skill from this table.')
        for column in frame.columns[:20]:
            lines.append('- %s :: %s' % (column, frame[column].dtype))
        return EvidenceUnit(
            asset_id=asset_id,
            span_ref='table:schema:0001',
            content_type=ContentType.TABLE,
            content='\n'.join(lines),
            confidence=0.9,
            tags=['schema'],
        )

    def _missingness_evidence(self, asset_id: str, frame: pd.DataFrame) -> EvidenceUnit:
        missing = (frame.isna().mean().sort_values(ascending=False) * 100.0).round(2)
        lines = ['Table missingness profile']
        lines.append('1. Inspect the highest-missing columns before trusting downstream trends.')
        lines.append('If missingness jumps after a date boundary, inspect upstream ingestion or schema drift.')
        lines.append('Verify whether null means unavailable, zero, or not applicable in the source system.')
        for column, percent in missing.head(10).items():
            lines.append('- %s missing_pct=%s' % (column, percent))
        return EvidenceUnit(
            asset_id=asset_id,
            span_ref='table:missingness:0001',
            content_type=ContentType.TABLE,
            content='\n'.join(lines),
            confidence=0.88,
            tags=['missingness'],
        )

    def _entity_evidence(self, asset_id: str, frame: pd.DataFrame, entity_columns: Sequence[str]) -> EvidenceUnit:
        lines = ['Entity/group summary']
        lines.append('1. Compare per-entity counts before aggregating the whole table.')
        lines.append('If one entity dominates the sample, review entity bias before reading the global average.')
        for column in entity_columns:
            sample = frame[column].astype(str).fillna('NA').value_counts().head(5)
            lines.append('Top values for %s:' % column)
            for value, count in sample.items():
                lines.append('- %s -> %s rows' % (value, count))
        return EvidenceUnit(
            asset_id=asset_id,
            span_ref='table:entities:0001',
            content_type=ContentType.TABLE,
            content='\n'.join(lines),
            confidence=0.82,
            tags=['entity'],
        )

    def _numeric_profile_evidence(
        self,
        asset_id: str,
        frame: pd.DataFrame,
        numeric_columns: Sequence[str],
    ) -> list[EvidenceUnit]:
        pd_runtime, _, _ = _pandas_runtime()
        evidence: list[EvidenceUnit] = []
        for index, column in enumerate(numeric_columns[:8], start=1):
            series = pd_runtime.to_numeric(frame[column], errors='coerce').dropna()
            if series.empty:
                continue
            quantiles = series.quantile([0.1, 0.5, 0.9]).to_dict()
            lines = [
                'Numeric profile for %s' % column,
                'count=%s mean=%.4f std=%.4f min=%.4f max=%.4f' % (
                    len(series),
                    float(series.mean()),
                    float(series.std(ddof=0)) if len(series) > 1 else 0.0,
                    float(series.min()),
                    float(series.max()),
                ),
                'p10=%.4f median=%.4f p90=%.4f' % (
                    float(quantiles.get(0.1, 0.0)),
                    float(quantiles.get(0.5, 0.0)),
                    float(quantiles.get(0.9, 0.0)),
                ),
                '1. Review distribution shape before setting thresholds on %s.' % column,
                'If %s shows a long tail, inspect outliers before computing a baseline.' % column,
                'Verify extreme rows against source records and unit assumptions.',
            ]
            evidence.append(
                EvidenceUnit(
                    asset_id=asset_id,
                    span_ref='table:numeric:%04d' % index,
                    content_type=ContentType.METRIC,
                    content='\n'.join(lines),
                    confidence=0.8,
                    tags=['numeric', column],
                )
            )
        return evidence

    def _timeseries_evidence(
        self,
        asset_id: str,
        frame: pd.DataFrame,
        time_column: str,
        value_columns: Sequence[str],
        max_series: int,
    ) -> list[EvidenceUnit]:
        evidence: list[EvidenceUnit] = []
        range_start = frame[time_column].min()
        range_end = frame[time_column].max()
        overview_lines = [
            'Time series overview',
            'time_column=%s range=%s -> %s' % (time_column, range_start, range_end),
            '1. Sort by %s before comparing neighboring measurements.' % time_column,
            '2. Investigate abrupt deltas before averaging the full observation window.',
            'If anomalies cluster near a timestamp boundary, inspect deploys, ingest gaps, or backfills first.',
            'Verify each anomaly against raw rows immediately before and after the flagged timestamp.',
        ]
        evidence.append(
            EvidenceUnit(
                asset_id=asset_id,
                span_ref='timeseries:overview:0001',
                content_type=ContentType.METRIC,
                content='\n'.join(overview_lines),
                confidence=0.9,
                tags=['timeseries', time_column],
            )
        )

        for index, column in enumerate(value_columns[:max_series], start=1):
            signal = self._summarize_signal(frame, time_column, column)
            lines = [
                'Time series diagnostic for %s' % column,
                'trend=%s pct_change=%s' % (
                    signal.trend_label,
                    self._format_optional(signal.pct_change, suffix='%'),
                ),
                'largest_jump_timestamp=%s largest_jump_value=%s'
                % (
                    signal.largest_jump_timestamp or 'none',
                    self._format_optional(signal.largest_jump_value),
                ),
                'baseline_mean=%s baseline_std=%s baseline_range=%s..%s'
                % (
                    self._format_optional(signal.baseline_mean),
                    self._format_optional(signal.baseline_std),
                    self._format_optional(signal.baseline_min),
                    self._format_optional(signal.baseline_max),
                ),
                'recent_mean=%s drift_label=%s drift_score=%s'
                % (
                    self._format_optional(signal.recent_mean),
                    signal.drift_label,
                    self._format_optional(signal.drift_score),
                ),
                'change_points=%s'
                % (
                    ', '.join('%s(delta=%s)' % (item[0], self._format_optional(item[1])) for item in signal.change_points[:6])
                    if signal.change_points
                    else 'none'
                ),
                'anomaly_timestamps=%s'
                % (', '.join(signal.anomaly_timestamps[:5]) if signal.anomaly_timestamps else 'none'),
                '1. Sort %s by %s before comparing local deltas.' % (column, time_column),
                '2. Review the largest jump around %s before trusting a global trend.'
                % (signal.largest_jump_timestamp or 'the highest-delta window'),
                'If %s deviates more than the rolling baseline, inspect deploys, schema changes, or data loss first.'
                % column,
                'Verify each flagged point against neighboring rows and source records.',
            ]
            evidence.append(
                EvidenceUnit(
                    asset_id=asset_id,
                    span_ref='timeseries:metric:%04d' % index,
                    content_type=ContentType.METRIC,
                    content='\n'.join(lines),
                    confidence=0.86,
                    tags=['timeseries', column],
                )
            )
            should_emit_event = bool(signal.anomaly_timestamps or signal.change_points or signal.anomaly_intervals)
            if should_emit_event:
                event_lines = [
                    'Detected anomaly windows for %s' % column,
                    'When anomalies cluster, inspect the shared upstream dependency before per-row debugging.',
                ]
                if signal.change_points:
                    event_lines.append('change_point_candidates:')
                    for timestamp, delta in signal.change_points[:8]:
                        event_lines.append('- change_point=%s delta=%s' % (timestamp, self._format_optional(delta)))
                if signal.anomaly_intervals:
                    event_lines.append('anomaly_intervals:')
                    for start, end in signal.anomaly_intervals[:6]:
                        event_lines.append('- anomaly_interval=%s -> %s' % (start, end))
                for timestamp in signal.anomaly_timestamps[:8]:
                    event_lines.append('- anomaly_at=%s' % timestamp)
                evidence.append(
                    EvidenceUnit(
                        asset_id=asset_id,
                        span_ref='timeseries:event:%04d' % index,
                        content_type=ContentType.EVENT,
                        content='\n'.join(event_lines),
                        confidence=0.78,
                        tags=unique_preserve_order(
                            ['anomaly', column, 'timeseries:baseline', 'timeseries:change_point', 'timeseries:drift']
                        ),
                    )
                )
        return evidence

    def _generic_table_guidance(
        self,
        asset_id: str,
        frame: pd.DataFrame,
        numeric_columns: Sequence[str],
    ) -> EvidenceUnit:
        lines = [
            'Structured table guidance',
            '1. Validate primary keys and duplicate rows before summarizing the table.',
            '2. Review high-cardinality dimensions separately from measure columns.',
            'If a metric changes sharply across one slice but not others, inspect grouping bias before global conclusions.',
            'Verify representative rows from each major slice before publishing a skill.',
        ]
        if numeric_columns:
            lines.append('numeric_columns=%s' % ', '.join(numeric_columns[:10]))
        lines.append('sample_rows=%s' % min(5, len(frame)))
        return EvidenceUnit(
            asset_id=asset_id,
            span_ref='table:guidance:0001',
            content_type=ContentType.TABLE,
            content='\n'.join(lines),
            confidence=0.78,
            tags=['table'],
        )

    def _resolve_time_column(self, frame: pd.DataFrame, explicit: str | None) -> str | None:
        if explicit and explicit in frame.columns:
            return explicit
        for column in frame.columns:
            if _is_datetime_dtype(frame[column]):
                return column
        candidates = []
        for column in frame.columns:
            lowered = column.lower()
            if any(token in lowered for token in ('time', 'date', 'timestamp', 'ts')):
                candidates.append(column)
        pd_runtime, _, _ = _pandas_runtime()
        for column in candidates:
            parsed = pd_runtime.to_datetime(frame[column], errors='coerce', utc=False)
            if parsed.notna().mean() >= 0.7:
                frame[column] = parsed
                return column
        return None

    def _prepare_time_frame(self, frame: pd.DataFrame, time_column: str) -> pd.DataFrame:
        prepared = frame.copy()
        if not _is_datetime_dtype(prepared[time_column]):
            pd_runtime, _, _ = _pandas_runtime()
            prepared[time_column] = pd_runtime.to_datetime(prepared[time_column], errors='coerce', utc=False)
        prepared = prepared.dropna(subset=[time_column]).sort_values(time_column).reset_index(drop=True)
        return prepared

    def _resolve_value_columns(
        self,
        frame: pd.DataFrame,
        explicit_columns: Sequence[str],
        max_series: int,
    ) -> list[str]:
        if explicit_columns:
            return [column for column in explicit_columns if column in frame.columns][:max_series]
        numeric_columns = [column for column in frame.columns if _is_numeric(frame[column])]
        return numeric_columns[:max_series]

    def _resolve_entity_columns(self, frame: pd.DataFrame, explicit_columns: Sequence[str]) -> list[str]:
        if explicit_columns:
            return [column for column in explicit_columns if column in frame.columns]
        candidates = []
        for column in frame.columns:
            series = frame[column]
            if _is_numeric(series):
                continue
            cardinality = series.astype(str).nunique(dropna=True)
            if 1 < cardinality <= 12:
                candidates.append(column)
        return candidates[:3]

    def _summarize_signal(self, frame: pd.DataFrame, time_column: str, value_column: str) -> TimeSeriesSignal:
        pd_runtime, _, _ = _pandas_runtime()
        series = pd_runtime.to_numeric(frame[value_column], errors='coerce')
        valid = frame.loc[series.notna(), [time_column]].copy()
        valid[value_column] = series.dropna().values
        if valid.empty:
            return TimeSeriesSignal(
                value_column,
                'flat',
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                'stable',
                [],
                [],
                [],
            )

        values = valid[value_column].astype(float)
        pct_change = None
        if len(values) >= 2 and float(values.iloc[0]) != 0:
            pct_change = float((values.iloc[-1] - values.iloc[0]) / abs(values.iloc[0]) * 100.0)
        delta = float(values.iloc[-1] - values.iloc[0]) if len(values) >= 2 else 0.0
        if delta > 0:
            trend_label = 'upward'
        elif delta < 0:
            trend_label = 'downward'
        else:
            trend_label = 'flat'

        diffs = values.diff().abs()
        jump_index = diffs.idxmax() if len(diffs.dropna()) else None
        largest_jump_timestamp = None
        largest_jump_value = None
        pd_runtime, _, _ = _pandas_runtime()
        if jump_index is not None and not pd_runtime.isna(jump_index):
            timestamp = valid.loc[jump_index, time_column]
            largest_jump_timestamp = str(timestamp)
            largest_jump_value = float(diffs.loc[jump_index])

        anomaly_timestamps: list[str] = []
        mean = float(values.mean())
        std = float(values.std(ddof=0)) if len(values) > 1 else 0.0
        if std > 0:
            z_scores = ((values - mean) / std).abs()
            anomaly_rows = valid.loc[z_scores > 2.5, time_column]
            anomaly_timestamps = [str(item) for item in anomaly_rows.head(8).tolist()]

        semantic = self.timeseries_parser.parse(
            timestamps=valid[time_column].tolist(),
            values=[float(item) for item in values.tolist()],
        )

        return TimeSeriesSignal(
            column=value_column,
            trend_label=trend_label,
            pct_change=pct_change,
            largest_jump_timestamp=largest_jump_timestamp,
            largest_jump_value=largest_jump_value,
            baseline_mean=semantic.baseline_mean,
            baseline_std=semantic.baseline_std,
            baseline_min=semantic.baseline_min,
            baseline_max=semantic.baseline_max,
            recent_mean=semantic.recent_mean,
            drift_score=semantic.drift_score,
            drift_label=semantic.drift_label,
            change_points=[(item.timestamp, item.delta) for item in semantic.change_points],
            anomaly_intervals=[(item.start_timestamp, item.end_timestamp) for item in semantic.anomaly_intervals],
            anomaly_timestamps=unique_preserve_order(semantic.anomaly_timestamps + anomaly_timestamps),
        )

    def _format_optional(self, value: float | None, suffix: str = '') -> str:
        if value is None or (isinstance(value, float) and np.isnan(value)):
            return 'none'
        return '%.4f%s' % (float(value), suffix)
