import { useEffect, useRef } from 'react';

// Plotly is loaded via CDN script tag in index.html
// eslint-disable-next-line @typescript-eslint/no-explicit-any
declare const Plotly: any;

interface Props {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  figure: Record<string, any>;
  height?: number;
}

export default function PlotlyChart({ figure, height = 500 }: Props) {
  const divRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!divRef.current || !figure?.data || typeof Plotly === 'undefined') return;
    Plotly.react(
      divRef.current,
      figure.data,
      { ...figure.layout, height, autosize: true },
      { responsive: true, displayModeBar: true },
    );
  }, [figure, height]);

  return <div ref={divRef} style={{ width: '100%', minHeight: height }} />;
}
