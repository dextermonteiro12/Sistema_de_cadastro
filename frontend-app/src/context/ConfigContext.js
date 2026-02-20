/**
 * React Context para compartilhar configuração entre componentes
 */

import React, { createContext, useState, useEffect, useCallback } from 'react';
import { apiService } from '../services/apiService';

export const ConfigContext = createContext();

export function ConfigProvider({ children }) {
  const [configKey, setConfigKey] = useState(null);
  const [config, setConfig] = useState(null);
  const [ambiente, setAmbiente] = useState(null);
  const [status, setStatus] = useState('desconectado');
  const [carregando, setCarregando] = useState(false);
  const [erro, setErro] = useState(null);

  // Carregar config da sessão ao montar
  useEffect(() => {
    if (apiService.carregarDaSessao()) {
      setConfigKey(apiService.configKey);
      setConfig(apiService.config);
      setAmbiente(apiService.ambiente || null);
      setStatus('conectado');
    }
  }, []);

  const validarConfig = useCallback(async (configData, options = {}) => {
    setCarregando(true);
    setErro(null);

    try {
      const resultado = await apiService.validarConfiguracao(configData, options);

      if (resultado.sucesso) {
        setConfigKey(resultado.config_key);
        setConfig(configData);
        setAmbiente(options?.ambiente || null);
        setStatus('conectado');
        return { sucesso: true, ...resultado };
      } else {
        setErro(resultado.erro);
        setStatus('erro');
        return { sucesso: false, erro: resultado.erro };
      }
    } catch (e) {
      const mensagem = e.message || 'Erro desconhecido';
      setErro(mensagem);
      setStatus('erro');
      return { sucesso: false, erro: mensagem };
    } finally {
      setCarregando(false);
    }
  }, []);

  const testarConexao = useCallback(async (configData) => {
    setCarregando(true);

    try {
      const resultado = await apiService.testarConexao(configData);
      return resultado;
    } finally {
      setCarregando(false);
    }
  }, []);

  const desconectar = useCallback(async () => {
    if (configKey) {
      await apiService.fecharConfiguracao(configKey);
    }
    apiService.limpar();
    setConfigKey(null);
    setConfig(null);
    setAmbiente(null);
    setStatus('desconectado');
    setErro(null);
  }, [configKey]);

  const value = {
    configKey,
    config,
    ambiente,
    status,
    carregando,
    erro,
    validarConfig,
    testarConexao,
    desconectar
  };

  return (
    <ConfigContext.Provider value={value}>
      {children}
    </ConfigContext.Provider>
  );
}

export function useConfig() {
  const context = React.useContext(ConfigContext);
  if (!context) {
    throw new Error('useConfig deve ser usado dentro de ConfigProvider');
  }
  return context;
}
