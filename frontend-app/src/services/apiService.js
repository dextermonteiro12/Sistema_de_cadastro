/**
 * API Service com gerenciamento de configuração
 * Centraliza todas as requisições HTTP
 */

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

class ApiService {
  constructor() {
    this.configKey = null;
    this.config = null;
  }

  /**
   * Valida e ativa configuração SQL Server
   * @param {Object} config - { servidor, banco, usuario, senha }
   * @returns {Promise}
   */
  async validarConfiguracao(config) {
    try {
      const response = await fetch(`${API_BASE_URL}/config/validar`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ config })
      });

      const data = await response.json();

      if (response.ok) {
        // Salvar na sessão
        this.configKey = data.config_key;
        this.config = config;
        sessionStorage.setItem('config_key', data.config_key);
        sessionStorage.setItem('pld_config', JSON.stringify(data.detalhes));

        console.log(`✓ Config ativada: ${this.configKey}`);
        return { sucesso: true, ...data };
      } else {
        console.error('✗ Erro na validação:', data);
        return { sucesso: false, erro: data.mensagem };
      }
    } catch (error) {
      console.error('✗ Erro ao validar:', error);
      return { sucesso: false, erro: error.message };
    }
  }

  /**
   * Apenas testa a conexão sem ativar
   * @param {Object} config
   */
  async testarConexao(config) {
    try {
      const response = await fetch(`${API_BASE_URL}/config/teste`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ config })
      });

      const data = await response.json();
      return data;
    } catch (error) {
      return { status: 'erro', mensagem: error.message };
    }
  }

  /**
   * Obtém status da configuração ativa
   */
  async obterStatusConfig() {
    if (!this.configKey) {
      return { erro: 'Nenhuma configuração ativa' };
    }

    try {
      const response = await fetch(`${API_BASE_URL}/config/status/${this.configKey}`);
      const data = await response.json();
      return data;
    } catch (error) {
      return { erro: error.message };
    }
  }

  /**
   * Lista todas as configurações ativas
   */
  async listarConfiguracoes() {
    try {
      const response = await fetch(`${API_BASE_URL}/config/listar`);
      const data = await response.json();
      return data;
    } catch (error) {
      return { erro: error.message };
    }
  }

  /**
   * Fecha uma configuração
   */
  async fecharConfiguracao(configKey) {
    try {
      const response = await fetch(`${API_BASE_URL}/config/fechar/${configKey}`, {
        method: 'POST'
      });
      const data = await response.json();
      return data;
    } catch (error) {
      return { erro: error.message };
    }
  }

  /**
   * Requisição genérica GET com headers de autenticação
   */
  async get(endpoint) {
    const headers = this.obterHeaders();
    const response = await fetch(`${API_BASE_URL}${endpoint}`, { headers });
    return response.json();
  }

  /**
   * Requisição genérica POST com headers de autenticação
   */
  async post(endpoint, data) {
    const headers = this.obterHeaders();
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: 'POST',
      headers,
      body: JSON.stringify(data)
    });
    return response.json();
  }

  /**
   * Monta headers com config_key
   */
  obterHeaders() {
    const headers = { 'Content-Type': 'application/json' };
    if (this.configKey) {
      headers['X-Config-Key'] = this.configKey;
    }
    return headers;
  }

  /**
   * Carrega config da sessão se existir
   */
  carregarDaSessao() {
    const configKey = sessionStorage.getItem('config_key');
    const config = sessionStorage.getItem('pld_config');

    if (configKey) {
      this.configKey = configKey;
      this.config = config ? JSON.parse(config) : null;
      console.log(`✓ Config carregada da sessão: ${configKey}`);
      return true;
    }
    return false;
  }

  /**
   * Limpa configuração
   */
  limpar() {
    this.configKey = null;
    this.config = null;
    sessionStorage.removeItem('config_key');
    sessionStorage.removeItem('pld_config');
  }
}

// Singleton global
export const apiService = new ApiService();

// Carregar config da sessão automaticamente
apiService.carregarDaSessao();
