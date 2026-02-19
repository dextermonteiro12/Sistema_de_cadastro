/**
 * Hook customizado para requisições com config_key automático
 */

import { useState, useCallback } from 'react';
import { useConfig } from '../context/ConfigContext';

export function useApi() {
  const { configKey } = useConfig();
  const [carregando, setCarregando] = useState(false);
  const [erro, setErro] = useState(null);

  const fazer_requisicao = useCallback(async (endpoint, options = {}) => {
    if (!configKey) {
      setErro('Nenhuma configuração ativa');
      return null;
    }

    setCarregando(true);
    setErro(null);

    try {
      const headers = {
        'Content-Type': 'application/json',
        'X-Config-Key': configKey,
        ...options.headers
      };

      const response = await fetch(endpoint, {
        ...options,
        headers
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || data.message || 'Erro na requisição');
      }

      return await response.json();
    } catch (e) {
      setErro(e.message);
      console.error('Erro API:', e);
      return null;
    } finally {
      setCarregando(false);
    }
  }, [configKey]);

  return { fazer_requisicao, carregando, erro };
}
