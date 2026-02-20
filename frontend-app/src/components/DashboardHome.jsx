// frontend-app/src/components/Dashboard/DashboardHome.jsx
import React, { useState, useEffect } from 'react';
import {
  LineChart, Line, AreaChart, Area, BarChart, Bar, ComposedChart,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  Cell
} from 'recharts';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { useMonitoringData } from '../../hooks/useMonitoringData';
import { useConfig } from '../../context/ConfigContext';

// Mock data - será substituído por dados reais depois
const generateMockData = () => {
  const hours = [];
  for (let i = 0; i < 24; i++) {
    hours.push({
      hora: `${String(i).padStart(2, '0')}:00`,
      clientes: Math.floor(Math.random() * 300) + 100,
      erros: Math.floor(Math.random() * 10),
      fila: Math.floor(Math.random() * 200) + 20
    });
  }
  return hours;
};

export function DashboardHome() {
  const { config } = useConfig();
  const monitoring = useMonitoringData(config?.config_key, 10000);
  const [historicalData, setHistoricalData] = useState(generateMockData());

  const { statusGeral, cards, lastUpdate } = monitoring;

  const statusColor = statusGeral === 'ESTÁVEL' 
    ? 'from-green-50 to-green-100 border-green-300' 
    : 'from-red-50 to-red-100 border-red-300';

  const statusTextColor = statusGeral === 'ESTÁVEL' 
    ? 'text-green-900' 
    : 'text-red-900';

  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-800">Dashboard Home</h1>
          <p className="text-sm text-gray-500 mt-2">
            Last updated: {lastUpdate.toLocaleTimeString()}
          </p>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Card 1: Total Clientes */}
        <Card className="bg-gradient-to-br from-blue-50 to-blue-100 border-blue-300 shadow-lg hover:shadow-xl transition">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-700 flex items-center gap-2">
              <span className="text-2xl">👥</span>
              Total de Clientes
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-4xl font-bold text-blue-900">
              {cards?.fila_pendente || 0}
            </div>
            <p className="text-xs text-blue-700 mt-2">Processados hoje</p>
          </CardContent>
        </Card>

        {/* Card 2: Fila Pendente */}
        <Card className="bg-gradient-to-br from-yellow-50 to-yellow-100 border-yellow-300 shadow-lg hover:shadow-xl transition">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-700 flex items-center gap-2">
              <span className="text-2xl">⏳</span>
              Fila Pendente
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-4xl font-bold text-yellow-900">
              {cards?.fila_pendente || 0}
            </div>
            <p className="text-xs text-yellow-700 mt-2">Aguardando processamento</p>
          </CardContent>
        </Card>

        {/* Card 3: Erros Hoje */}
        <Card className="bg-gradient-to-br from-red-50 to-red-100 border-red-300 shadow-lg hover:shadow-xl transition">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-700 flex items-center gap-2">
              <span className="text-2xl">⚠️</span>
              Erros Hoje
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-4xl font-bold text-red-900">
              {cards?.erros_servicos || 0}
            </div>
            <p className="text-xs text-red-700 mt-2">Falhas registradas</p>
          </CardContent>
        </Card>

        {/* Card 4: Status Geral */}
        <Card className={`bg-gradient-to-br ${statusColor} shadow-lg hover:shadow-xl transition`}>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-700 flex items-center gap-2">
              <span className="text-2xl">{statusGeral === 'ESTÁVEL' ? '✅' : '🔴'}</span>
              Status Geral
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className={`text-4xl font-bold ${statusTextColor}`}>
              {statusGeral}
            </div>
            <p className={`text-xs mt-2 ${statusGeral === 'ESTÁVEL' ? 'text-green-700' : 'text-red-700'}`}>
              Sistema {statusGeral.toLowerCase()}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Evolução de Clientes */}
        <Card className="shadow-lg">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <span>📈</span>
              Evolução de Clientes (24h)
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <AreaChart data={historicalData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                <defs>
                  <linearGradient id="colorClientes" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.8}/>
                    <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis 
                  dataKey="hora" 
                  stroke="#9ca3af"
                  style={{ fontSize: '12px' }}
                />
                <YAxis stroke="#9ca3af" style={{ fontSize: '12px' }} />
                <Tooltip 
                  contentStyle={{
                    backgroundColor: '#fff',
                    border: '1px solid #e5e7eb',
                    borderRadius: '8px'
                  }}
                  formatter={(value) => `${value} clientes`}
                />
                <Area 
                  type="monotone" 
                  dataKey="clientes" 
                  stroke="#3b82f6" 
                  fillOpacity={1} 
                  fill="url(#colorClientes)"
                  name="Clientes"
                />
              </AreaChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Fila e Erros */}
        <Card className="shadow-lg">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <span>📊</span>
              Fila Pendente e Erros (24h)
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={historicalData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis 
                  dataKey="hora" 
                  stroke="#9ca3af"
                  style={{ fontSize: '12px' }}
                />
                <YAxis stroke="#9ca3af" style={{ fontSize: '12px' }} />
                <Tooltip 
                  contentStyle={{
                    backgroundColor: '#fff',
                    border: '1px solid #e5e7eb',
                    borderRadius: '8px'
                  }}
                />
                <Legend />
                <Line 
                  type="monotone" 
                  dataKey="fila" 
                  stroke="#f59e0b" 
                  strokeWidth={2}
                  name="Fila"
                  dot={false}
                />
                <Line 
                  type="monotone" 
                  dataKey="erros" 
                  stroke="#ef4444" 
                  strokeWidth={2}
                  name="Erros"
                  dot={false}
                />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Dashboard Combinado */}
        <Card className="col-span-1 lg:col-span-2 shadow-lg">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <span>🎯</span>
              Dashboard Combinado: Clientes + Fila + Erros
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={350}>
              <ComposedChart data={historicalData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis 
                  dataKey="hora" 
                  stroke="#9ca3af"
                  style={{ fontSize: '12px' }}
                />
                <YAxis 
                  yAxisId="left" 
                  stroke="#9ca3af"
                  label={{ value: 'Clientes', angle: -90, position: 'insideLeft' }}
                />
                <YAxis 
                  yAxisId="right" 
                  orientation="right" 
                  stroke="#9ca3af"
                  label={{ value: 'Fila / Erros', angle: 90, position: 'insideRight' }}
                />
                <Tooltip 
                  contentStyle={{
                    backgroundColor: '#fff',
                    border: '1px solid #e5e7eb',
                    borderRadius: '8px'
                  }}
                />
                <Legend />
                <Area 
                  yAxisId="left"
                  type="monotone" 
                  dataKey="clientes" 
                  fill="#3b82f6" 
                  stroke="#3b82f6" 
                  opacity={0.6}
                  name="Clientes"
                />
                <Bar 
                  yAxisId="right"
                  dataKey="fila" 
                  fill="#f59e0b"
                  name="Fila"
                  opacity={0.8}
                />
                <Line 
                  yAxisId="right"
                  type="monotone" 
                  dataKey="erros" 
                  stroke="#ef4444" 
                  strokeWidth={3}
                  name="Erros"
                />
              </ComposedChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}