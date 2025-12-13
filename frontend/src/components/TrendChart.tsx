import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';

interface DataPoint {
  year: number;
  [key: string]: number | string | null;
}

interface TrendChartProps {
  data: DataPoint[];
  metrics: string[];
  companies?: string[];
  chartType?: 'line' | 'bar';
  title?: string;
  height?: number;
}

// Color palette for multiple lines/bars
const COLORS = [
  '#3b82f6', // blue
  '#10b981', // emerald
  '#f59e0b', // amber
  '#ef4444', // red
  '#8b5cf6', // violet
  '#ec4899', // pink
  '#06b6d4', // cyan
  '#84cc16', // lime
];

const formatValue = (value: number | null, metric?: string): string => {
  if (value === null || value === undefined) return 'N/A';

  // Check if it's a percentage/margin metric
  if (metric?.includes('margin')) {
    return `${value.toFixed(1)}%`;
  }

  // Format large numbers
  if (Math.abs(value) >= 1_000_000_000) {
    return `$${(value / 1_000_000_000).toFixed(1)}B`;
  }
  if (Math.abs(value) >= 1_000_000) {
    return `$${(value / 1_000_000).toFixed(1)}M`;
  }
  if (Math.abs(value) >= 1_000) {
    return `$${(value / 1_000).toFixed(1)}K`;
  }

  return `$${value.toFixed(2)}`;
};

// Custom tooltip for better display
const CustomTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload || payload.length === 0) return null;

  return (
    <div className="bg-gray-800 border border-gray-700 rounded-lg px-4 py-3 shadow-xl">
      <p className="text-gray-300 font-medium mb-2">{label}</p>
      {payload.map((entry: any, index: number) => (
        <div key={index} className="flex items-center gap-2 text-sm">
          <div
            className="w-3 h-3 rounded-full"
            style={{ backgroundColor: entry.color }}
          />
          <span className="text-gray-400">{entry.name}:</span>
          <span className="text-white font-medium">
            {formatValue(entry.value, entry.dataKey)}
          </span>
        </div>
      ))}
    </div>
  );
};

export function TrendChart({
  data,
  metrics,
  companies,
  chartType = 'line',
  title,
  height = 300,
}: TrendChartProps) {
  // Sort data by year ascending for proper chart display
  const sortedData = [...data].sort((a, b) => a.year - b.year);

  // Determine which keys to render
  // If companies provided, use those; otherwise use metrics
  const dataKeys = companies || metrics;

  if (sortedData.length === 0) {
    return (
      <div className="flex items-center justify-center h-48 text-gray-500">
        No data available for chart
      </div>
    );
  }

  return (
    <div className="w-full">
      {title && (
        <h4 className="text-sm font-medium text-gray-300 mb-3">{title}</h4>
      )}
      <ResponsiveContainer width="100%" height={height}>
        {chartType === 'line' ? (
          <LineChart data={sortedData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
            <XAxis
              dataKey="year"
              stroke="#9ca3af"
              tick={{ fill: '#9ca3af', fontSize: 12 }}
            />
            <YAxis
              stroke="#9ca3af"
              tick={{ fill: '#9ca3af', fontSize: 12 }}
              tickFormatter={(val) => formatValue(val)}
            />
            <Tooltip content={<CustomTooltip />} />
            <Legend
              wrapperStyle={{ paddingTop: '10px' }}
              formatter={(value) => <span className="text-gray-300">{value}</span>}
            />
            {dataKeys.map((key, idx) => (
              <Line
                key={key}
                type="monotone"
                dataKey={key}
                name={key}
                stroke={COLORS[idx % COLORS.length]}
                strokeWidth={2}
                dot={{ fill: COLORS[idx % COLORS.length], strokeWidth: 2, r: 4 }}
                activeDot={{ r: 6 }}
                connectNulls
              />
            ))}
          </LineChart>
        ) : (
          <BarChart data={sortedData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
            <XAxis
              dataKey="year"
              stroke="#9ca3af"
              tick={{ fill: '#9ca3af', fontSize: 12 }}
            />
            <YAxis
              stroke="#9ca3af"
              tick={{ fill: '#9ca3af', fontSize: 12 }}
              tickFormatter={(val) => formatValue(val)}
            />
            <Tooltip content={<CustomTooltip />} />
            <Legend
              wrapperStyle={{ paddingTop: '10px' }}
              formatter={(value) => <span className="text-gray-300">{value}</span>}
            />
            {dataKeys.map((key, idx) => (
              <Bar
                key={key}
                dataKey={key}
                name={key}
                fill={COLORS[idx % COLORS.length]}
                radius={[4, 4, 0, 0]}
              />
            ))}
          </BarChart>
        )}
      </ResponsiveContainer>
    </div>
  );
}

// Specialized chart for comparing companies on a single metric
interface CompanyComparisonChartProps {
  companies: Array<{
    ticker: string;
    data: Array<{ year: number; value: number | null }>;
  }>;
  metric: string;
  chartType?: 'line' | 'bar';
  height?: number;
}

export function CompanyComparisonChart({
  companies,
  metric,
  chartType = 'bar',
  height = 300,
}: CompanyComparisonChartProps) {
  // Transform data for Recharts - pivot to year-based structure
  const yearMap = new Map<number, DataPoint>();

  companies.forEach((company) => {
    company.data.forEach((point) => {
      if (!yearMap.has(point.year)) {
        yearMap.set(point.year, { year: point.year });
      }
      const yearData = yearMap.get(point.year)!;
      yearData[company.ticker] = point.value;
    });
  });

  const chartData: DataPoint[] = Array.from(yearMap.values()).sort((a, b) => a.year - b.year);
  const tickers = companies.map((c) => c.ticker);

  const metricLabels: Record<string, string> = {
    revenue: 'Revenue',
    net_income: 'Net Income',
    eps: 'EPS',
    gross_margin: 'Gross Margin',
    operating_margin: 'Operating Margin',
    total_assets: 'Total Assets',
    total_debt: 'Total Debt',
    cash: 'Cash',
  };

  return (
    <TrendChart
      data={chartData}
      metrics={[metric]}
      companies={tickers}
      chartType={chartType}
      title={metricLabels[metric] || metric}
      height={height}
    />
  );
}
