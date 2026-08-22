"use client";

import React, { useEffect, useState } from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  AreaChart,
  Area,
} from 'recharts';

interface HistoryItem {
  audit_kind: string;
  fact_key: string;
  action: string;
  confidence: number;
  detail: string;
  created_at: number;
}

interface ChartData {
  time: string;
  timestamp: number;
  confidence: number;
}

export const MemoryHistoryChart: React.FC = () => {
  const [data, setData] = useState<ChartData[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchHistory = async () => {
      try {
        const res = await fetch('/api/brain/history?limit=50');
        if (!res.ok) throw new Error('Failed to fetch history');
        const history: HistoryItem[] = await res.json();
        
        // Transform to time-series (sorted by time)
        const chartData = history
          .map(item => ({
            time: new Date(item.created_at * 1000).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
            timestamp: item.created_at,
            confidence: item.confidence,
          }))
          .sort((a, b) => a.timestamp - b.timestamp);
        
        setData(chartData);
      } catch (err) {
        console.error('History fetch error:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchHistory();
    const interval = setInterval(fetchHistory, 30000); // Refresh every 30s
    return () => clearInterval(interval);
  }, []);

  if (loading && data.length === 0) {
    return (
      <div className="h-48 flex items-center justify-center bg-slate-900/50 rounded-lg border border-slate-800">
        <span className="text-slate-500 text-sm animate-pulse">Loading history...</span>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
        Cognitive Confidence Trend
      </h4>
      <div className="h-48 w-full bg-slate-900/50 p-2 rounded-lg border border-slate-800">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data}>
            <defs>
              <linearGradient id="colorConf" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#6366f1" stopOpacity={0.3}/>
                <stop offset="95%" stopColor="#6366f1" stopOpacity={0}/>
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
            <XAxis 
              dataKey="time" 
              stroke="#64748b" 
              fontSize={10} 
              tickLine={false}
              axisLine={false}
              minTickGap={30}
            />
            <YAxis 
              stroke="#64748b" 
              fontSize={10} 
              tickLine={false}
              axisLine={false}
              domain={[0, 1]}
              ticks={[0, 0.5, 1]}
            />
            <Tooltip 
              contentStyle={{ backgroundColor: '#0f172a', border: '1px solid #1e293b', borderRadius: '8px', fontSize: '12px' }}
              itemStyle={{ color: '#818cf8' }}
            />
            <Area 
              type="monotone" 
              dataKey="confidence" 
              stroke="#6366f1" 
              fillOpacity={1} 
              fill="url(#colorConf)" 
              strokeWidth={2}
              animationDuration={1000}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};
