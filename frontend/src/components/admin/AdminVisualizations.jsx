import React, { useMemo, useState } from "react";


const riskColors = {
  low: "risk-low",
  moderate: "risk-moderate",
  high: "risk-high",
  critical: "risk-critical",
};

const paletteClasses = [
  "palette-primary",
  "palette-success",
  "palette-warning",
  "palette-danger",
  "palette-accent",
  "palette-muted",
];


export function formatNumber(value) {
  return new Intl.NumberFormat().format(Number(value) || 0);
}

function normalizeClass(value) {
  return String(value || "")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-|-$/g, "");
}

function labelForDate(value) {
  const parsed = new Date(`${value}T00:00:00`);
  if (Number.isNaN(parsed.getTime())) return value || "";
  return parsed.toLocaleDateString(undefined, { month: "short", day: "numeric" });
}

function barClassFor(row, index) {
  const label = normalizeClass(row.category || row.label || row.sport);
  if (riskColors[label]) return riskColors[label];
  if (label.includes("approved") || label.includes("active") || label.includes("completed")) return "palette-success";
  if (label.includes("pending") || label.includes("processing") || label.includes("queued")) return "palette-warning";
  if (label.includes("rejected") || label.includes("failed") || label.includes("critical")) return "palette-danger";
  return paletteClasses[index % paletteClasses.length];
}

export function AdminBarDistribution({
  rows = [],
  labelKey = "label",
  valueKey = "count",
  emptyText,
}) {
  const values = rows.map((row) => Number(row[valueKey]) || 0);
  const maxValue = Math.max(...values, 0);

  if (!rows.length || maxValue === 0) {
    return <div className="admin-empty-state">{emptyText}</div>;
  }

  return (
    <div className="admin-bar-list" role="list">
      {rows.map((row, index) => {
        const value = Number(row[valueKey]) || 0;
        const width = maxValue > 0 ? (value / maxValue) * 100 : 0;
        const label = row[labelKey] || "Unlabeled";

        return (
          <div className="admin-bar-row" key={`${label}-${index}`} role="listitem">
            <div className="admin-bar-label">
              <span title={label}>{label}</span>
              <strong>{formatNumber(value)}</strong>
            </div>
            <div
              className="admin-bar-track"
              aria-label={`${label}: ${formatNumber(value)}`}
              title={`${label}: ${formatNumber(value)}`}
            >
              <div
                className={`admin-bar-fill ${barClassFor(row, index)}`}
                style={{ width: `${Math.max(width, value > 0 ? 3 : 0)}%` }}
              />
            </div>
          </div>
        );
      })}
    </div>
  );
}

export function AdminTimeSeriesChart({
  rows = [],
  valueKey,
  emptyText,
  ariaLabel,
  compact = false,
}) {
  const chart = useMemo(() => {
    const points = rows.map((row, index) => ({
      x: index,
      date: row.date,
      value: Number(row[valueKey]) || 0,
    }));
    const maxValue = Math.max(...points.map((point) => point.value), 0);
    const width = Math.max(points.length * 58, 360);
    const height = compact ? 190 : 230;
    const plotTop = 18;
    const plotRight = 20;
    const plotBottom = 42;
    const plotLeft = 42;
    const plotWidth = width - plotLeft - plotRight;
    const plotHeight = height - plotTop - plotBottom;
    const xStep = points.length > 1 ? plotWidth / (points.length - 1) : 0;
    const yMax = Math.max(maxValue, 1);
    const scaled = points.map((point, index) => ({
      ...point,
      px: points.length > 1 ? plotLeft + index * xStep : plotLeft + plotWidth / 2,
      py: plotTop + plotHeight - (point.value / yMax) * plotHeight,
    }));
    const linePath = scaled
      .map((point, index) => `${index === 0 ? "M" : "L"} ${point.px} ${point.py}`)
      .join(" ");
    const areaPath = scaled.length
      ? `${linePath} L ${scaled[scaled.length - 1].px} ${plotTop + plotHeight} L ${scaled[0].px} ${plotTop + plotHeight} Z`
      : "";

    return {
      points: scaled,
      maxValue,
      width,
      height,
      plotTop,
      plotLeft,
      plotBottom,
      plotHeight,
      plotWidth,
      linePath,
      areaPath,
      ticks: [0, 0.5, 1].map((ratio) => ({
        ratio,
        y: plotTop + plotHeight - ratio * plotHeight,
        value: Math.round(yMax * ratio),
      })),
    };
  }, [compact, rows, valueKey]);

  if (!rows.length || chart.maxValue === 0) {
    return <div className="admin-empty-state">{emptyText}</div>;
  }

  return (
    <div className={`admin-timeseries-frame ${compact ? "compact" : ""}`} role="img" aria-label={ariaLabel}>
      <svg className="admin-timeseries-svg" viewBox={`0 0 ${chart.width} ${chart.height}`} preserveAspectRatio="none">
        <defs>
          <linearGradient id={`adminChartFill-${valueKey}-${compact ? "compact" : "normal"}`} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="currentColor" stopOpacity="0.22" />
            <stop offset="100%" stopColor="currentColor" stopOpacity="0.03" />
          </linearGradient>
        </defs>
        {chart.ticks.map((tick) => (
          <g key={tick.ratio}>
            <line className="admin-chart-grid-line" x1={chart.plotLeft} x2={chart.plotLeft + chart.plotWidth} y1={tick.y} y2={tick.y} />
            <text className="admin-chart-y-label" x={chart.plotLeft - 10} y={tick.y + 4}>{tick.value}</text>
          </g>
        ))}
        <line className="admin-chart-axis" x1={chart.plotLeft} x2={chart.plotLeft + chart.plotWidth} y1={chart.height - chart.plotBottom} y2={chart.height - chart.plotBottom} />
        <line className="admin-chart-axis" x1={chart.plotLeft} x2={chart.plotLeft} y1={chart.plotTop} y2={chart.height - chart.plotBottom} />
        <path className="admin-chart-area" d={chart.areaPath} fill={`url(#adminChartFill-${valueKey}-${compact ? "compact" : "normal"})`} />
        <path className="admin-chart-line" d={chart.linePath} />
        {chart.points.map((point, index) => (
          <g className="admin-chart-point-group" key={`${point.date}-${index}`} tabIndex="0">
            <circle className="admin-chart-point" cx={point.px} cy={point.py} r="4.5" />
            <title>{`${labelForDate(point.date)}: ${formatNumber(point.value)}`}</title>
          </g>
        ))}
        {chart.points.map((point, index) => {
          const shouldShow = chart.points.length <= 8 || index === 0 || index === chart.points.length - 1 || index % Math.ceil(chart.points.length / 6) === 0;
          return shouldShow ? (
            <text className="admin-chart-x-label" key={`label-${point.date}-${index}`} x={point.px} y={chart.height - 14}>{labelForDate(point.date)}</text>
          ) : null;
        })}
      </svg>
      <div className="admin-chart-tooltip-note">Hover or focus data points for exact values.</div>
    </div>
  );
}

export function AdminRecentList({
  items = [],
  limit = 5,
  emptyText,
  renderItem,
}) {
  const [expanded, setExpanded] = useState(false);
  const visibleItems = expanded ? items : items.slice(0, limit);
  const hasMore = items.length > limit;

  if (!items.length) {
    return <div className="admin-empty-state">{emptyText}</div>;
  }

  return (
    <>
      <div className="admin-activity-list">
        {visibleItems.map(renderItem)}
      </div>
      {hasMore && (
        <button className="admin-show-more-button" type="button" onClick={() => setExpanded((current) => !current)}>
          {expanded ? "Show Less" : `Show More (${items.length - limit})`}
        </button>
      )}
    </>
  );
}
