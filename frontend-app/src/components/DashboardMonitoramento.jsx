// frontend-app/src/components/Dashboard/DashboardMonitoramento.jsx
import React, { useState, useEffect } from 'react';
import {
  BarChart, Bar, LineChart, Line, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { useMonitoringData } from '../../hooks/useMonitoringData';
import { useConfig } from '../../context/ConfigContext';

const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6'];

export function DashboardMonitoramento() {
  const { config } = useConfig();
  const monitoring = useMonitoringData(config?.config_key, 5000); // 5s para time-real

  const { statusGeral, cards, performance_ms, lastUpdate } = monitoring;

  // Dados para gráfico de workers
  const workersData = performance_ms?.length > 0 
    ? performance_ms 
    : [
        { Fila: 'Principal', Media: 0 },
        { Fila: 'Secundária', Media: 0 }
      ];

  // Status indicator color
  const statusBg = statusGeral === 'ESTÁVEL' 
    ? 'bg-green-500' 
    : 'bg-red-500';

  const statusLight = statusGeral === 'ESTÁVEL' 
    ? 'bg-green-100' 
    : 'bg-red-100';

  return (
    <div className="space-y-6 p-6">
      {/* Header com Timer */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-800">Monitoramento em Tempo Real</h1>
          <p className="text-sm text-gray-500 mt-2">
            🔄 Atualizado em: {lastUpdate.toLocaleTimeString()}
          </p>
        </div>
        <div className={`flex items-center gap-2 px-4 py-2 rounded-full ${statusLight}`}>
          <div className={`w-3 h-3 rounded-full ${statusBg} animate-pulse`}></div>
          <span className="font-semibold text-gray-800">{statusGeral}</span>
        </div>
      </div>

      {/* KPI Cards - Real-time Indicators */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Indicador 1: Workers Ativos */}
        <Card className="bg-gradient-to-br from-green-50 to-green-100 border-green-300 shadow-lg">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-700">
              👷 Workers Ativos
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-4xl font-bold text-green-900">4</p>
                <p className="text-xs text-green-700 mt-1">de 5 disponíveis</p>
              </div>
              <div className="text-5xl opacity-30">👷</div>
            </div>
            <div className="mt-4 bg-green-200 rounded-full h-2">
              <div className="bg-green-600 h-2 rounded-full" style={{ width: '80%' }}></div>
            </div>
          </CardContent>
        </Card>

        {/* Indicador 2: Fila Pendente */}
        <Card className={`bg-gradient-to-br ${
          cards?.fila_pendente > 100 
            ? 'from-red-50 to-red-100 border-red-300' 
            : 'from-yellow-50 to-yellow-100 border-yellow-300'
        } shadow-lg`}>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-700">
              ⏳ Fila Pendente
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-4xl font-bold text-yellow-900">
                  {cards?.fila_pendente || 0}
                </p>
                <p className="text-xs text-yellow-700 mt-1">registros</p>
              </div>
              <div className="text-5xl opacity-30">⏳</div>
            </div>
            <div className="mt-4">
              <p className="text-xs text-gray-600 mb-1">Capacidade: 500</p>
              <div className="bg-gray-200 rounded-full h-2">
                <div 
                  className={`h-2 rounded-full transition-all ${
                    cards?.fila_pendente > 400 ? 'bg-red-600' : 'bg-yellow-600'
                  }`}
                  style={{ width: `${Math.min((cards?.fila_pendente || 0) / 500 * 100, 100)}%` }}
                ></div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Indicador 3: Taxa de Erro */}
        <Card className={`bg-gradient-to-br ${
          cards?.erros_servicos > 5 
            ? 'from-red-50 to-red-100 border-red-300' 
            : 'from-green-50 to-green-100 border-green-300'
        } shadow-lg`}>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-700">
              ⚠️ Erros Hoje
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-between">
              <div>
                <p className={`text-4xl font-bold ${
                  cards?.erros_servicos > 5 ? 'text-red-900' : 'text-green-900'
                }`}>
                  {cards?.erros_servicos || 0}
                </p>
                <p className={`text-xs mt-1 ${
                  cards?.erros_servicos > 5 ? 'text-red-700' : 'text-green-700'
                }`}>
                  falhas registradas
                </p>
              </div>
              <div className="text-5xl opacity-30">⚠️</div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Gráficos */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Performance dos Workers */}
        <Card className="shadow-lg">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <span>⚡</span>
              Performance dos Workers (Tempo)
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={workersData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis 
                  dataKey="Fila" 
                  stroke="#9ca3af"
                  style={{ fontSize: '12px' }}
                />
                <YAxis 
                  stroke="#9ca3af"
                  label={{ value: 'Tempo (ms)', angle: -90, position: 'insideLeft' }}
                />
                <Tooltip 
                  contentStyle={{
                    backgroundColor: '#fff',
                    border: '1px solid #e5e7eb',
                    borderRadius: '8px'
                  }}
                  formatter={(value) => `${value.toFixed(2)}ms`}
                />
                <Bar dataKey="Media" fill="#3b82f6" name="Tempo Médio">
                  {workersData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Status dos Serviços */}
        <Card className="shadow-lg">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <span>🔍</span>
              Status dos Serviços
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {/* Serviço 1 */}
              <div className="flex items-center justify-between p-3 bg-green-50 rounded-lg">
                <div className="flex items-center gap-3">
                  <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                  <span className="font-medium text-gray-700">API Gateway</span>
                </div>
                <span className="text-xs font-semibold text-green-700">ONLINE</span>
              </div>

              {/* Serviço 2 */}
              <div className="flex items-center justify-between p-3 bg-green-50 rounded-lg">
                <div className="flex items-center gap-3">
                  <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                  <span className="font-medium text-gray-700">Worker gRPC</span>
                </div>
                <span className="text-xs font-semibold text-green-700">ONLINE</span>
              </div>

              {/* Serviço 3 */}
              <div className="flex items-center justify-between p-3 bg-green-50 rounded-lg">
                <div className="flex items-center gap-3">
                  <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                  <span className="font-medium text-gray-700">Banco de Dados</span>
                </div>
                <span className="text-xs font-semibold text-green-700">CONECTADO</span>
              </div>

              {/* Serviço 4 - Offline */}
              <div className="flex items-center justify-between p-3 bg-red-50 rounded-lg">
                <div className="flex items-center gap-3">
                  <div className="w-3 h-3 bg-red-500 rounded-full animate-pulse"></div>
                  <span className="font-medium text-gray-700">Cache Redis</span>
                </div>
                <span className="text-xs font-semibold text-red-700">OFFLINE</span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Alertas / Notificações */}
      <Card className="bg-gradient-to-r from-yellow-50 to-orange-50 border-orange-300 shadow-lg">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-orange-900">
            <span>🔔</span>
            Alertas Recentes
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            <div className="p-2 text-sm text-orange-800 flex items-start gap-2">
              <span className="mt-1">⚠️</span>
              <span>Fila pendente em 35% da capacidade máxima</span>
            </div>
            <div className="p-2 text-sm text-orange-800 flex items-start gap-2">
              <span className="mt-1">📊</span>
              <span>Performance de worker Principal: 125ms (normal: 50ms)</span>
            </div>
            <div className="p-2 text-sm text-orange-800 flex items-start gap-2">
              <span className="mt-1">🔌</span>
              <span>Redis offline há 2 horas - cache desabilitado</span>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}