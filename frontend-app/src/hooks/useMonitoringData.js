// frontend-app/src/hooks/useMonitoringData.js
import { useState, useEffect } from 'react';
import { apiService } from '../services/apiService';

export function useMonitoringData(configKey, interval = 10000) {
  const [data, setData] = useState({
    statusGeral: 'ESTÁVEL',
    cards: { fila_pendente: 0, erros_servicos: 0 },
    performance_ms: [],
    lastUpdate: new Date(),
    loading: true,
    error: null
  });

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await apiService.post('/api/saude-servidor', {
          config_key: configKey
        });
        setData(prev => ({
          ...prev,
          statusGeral: response.data.status_geral,
          cards: response.data.cards,
          performance_ms: response.data.performance_ms,
          lastUpdate: new Date(),
          loading: false,
          error: null
        }));
      } catch (err) {
        setData(prev => ({
          ...prev,
          error: err.message,
          loading: false
        }));
      }
    };

    fetchData();
    const intervalId = setInterval(fetchData, interval);

    return () => clearInterval(intervalId);
  }, [configKey, interval]);

  return data;
}