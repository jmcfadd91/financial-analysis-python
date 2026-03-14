import React from 'react';
// @ts-expect-error — react-plotly.js has no bundled types
import Plot from 'react-plotly.js';

interface Props {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  figure: Record<string, any>;
  height?: number;
}

export default function PlotlyChart({ figure, height = 500 }: Props) {
  return (
    <Plot
      data={figure.data ?? []}
      layout={{ ...figure.layout, autosize: true, height }}
      config={{ responsive: true, displayModeBar: true }}
      style={{ width: '100%' }}
      useResizeHandler
    />
  );
}
