/**
 * API Service com gerenciamento de configuração
 * Centraliza todas as requisições HTTP
 */

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

class ApiService {
  constructor() {
    this.configKey = null;
    this.config = null;
    this.sessionId = null;
    this.ambiente = null;
    this.ensureSessionId();
  }

  ensureSessionId() {
    const fromSession = sessionStorage.getItem('pld_session_id');
    if (fromSession) {
      this.sessionId = fromSession;
      return this.sessionId;
    }

    const generated = `sess_${Date.now()}_${Math.random().toString(36).slice(2, 10)}`;
    this.sessionId = generated;
    sessionStorage.setItem('pld_session_id', generated);
    return generated;
  }

  /**
   * Valida e ativa configuração SQL Server
   * @param {Object} config - { servidor, banco, usuario, senha }
   * @returns {Promise}
   */
  async validarConfiguracao(config, options = {}) {
    try {
      const sessionId = this.ensureSessionId();
      const ambiente = options?.ambiente || null;

      const response = await fetch(`${API_BASE_URL}/config/validar`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          config,
          session_id: sessionId,
          ambiente
        })
      });

      const data = await response.json();

      if (response.ok) {
        // Salvar na sessão
        this.configKey = data.config_key;
        this.config = config;
        this.ambiente = ambiente;
        sessionStorage.setItem('config_key', data.config_key);
        sessionStorage.setItem('pld_config', JSON.stringify(data.detalhes));
        sessionStorage.setItem('pld_ambiente', ambiente || '');

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
    * Lista nomes de bases candidatas a partir do Advice.xml
    * Aceita pasta raiz (com config/Advice.xml) ou caminho completo do XML
    * @param {string} folderPath
   */
  async listarBasesDaPasta(folderPath) {
    try {
      const response = await fetch(`${API_BASE_URL}/config/listar-bases-pasta`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ folder_path: folderPath })
      });

      const data = await response.json();
      
      console.log('🔵 [API] Resposta bruta do backend:', data);
      console.log('🔵 [API] data.bases:', data.bases);
      console.log('🔵 [API] Tipo de data.bases:', Array.isArray(data.bases) ? 'Array' : typeof data.bases);
      if (Array.isArray(data.bases)) {
        console.log('🔵 [API] Total de bases no array:', data.bases.length);
        data.bases.forEach((base, idx) => {
          console.log(`🔵 [API] Base ${idx}:`, base);
        });
      }

      if (!response.ok) {
        return {
          status: 'erro',
          mensagem: data?.detail || 'Erro ao ler Advice.xml',
          bases: []
        };
      }

      return data;
    } catch (error) {
      return {
        status: 'erro',
        mensagem: error.message,
        bases: []
      };
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
    this.ensureSessionId();
    const configKey = sessionStorage.getItem('config_key');
    const config = sessionStorage.getItem('pld_config');
    const ambiente = sessionStorage.getItem('pld_ambiente');

    if (configKey) {
      this.configKey = configKey;
      this.config = config ? JSON.parse(config) : null;
      this.ambiente = ambiente || null;
      console.log(`✓ Config carregada da sessão: ${configKey}`);
      return true;
    }
    return false;
  }

  /**
   * Salva configuração do usuário (com credenciais criptografadas)
   * @param {Object} config - { xml_path, sql_server, sql_username, sql_password, bases }
   * @returns {Promise}
   */
  async salvarConfiguracao(config) {
    try {
      const token = localStorage.getItem('auth_token');
      
      if (!token) {
        console.error('❌ Token não encontrado');
        return { status: 'erro', mensagem: 'Token de autenticação ausente' };
      }

      const response = await fetch(`${API_BASE_URL}/user-config/save`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(config)
      });

      const data = await response.json();

      if (response.ok) {
        console.log('✅ Configuração salva com sucesso:', data);
        localStorage.setItem('user_config_id', data.config_id);
        return { status: 'ok', ...data };
      } else {
        console.error('❌ Erro ao salvar config:', data);
        return { status: 'erro', mensagem: data.detail || 'Erro ao salvar' };
      }
    } catch (error) {
      console.error('❌ Erro ao salvar configuração:', error);
      return { status: 'erro', mensagem: error.message };
    }
  }

  /**
   * Carrega configuração do usuário
   * @returns {Promise}
   */
  async carregarConfiguracao() {
    try {
      const token = localStorage.getItem('auth_token');
      
      if (!token) {
        return { status: 'erro', mensagem: 'Token de autenticação ausente' };
      }

      const response = await fetch(`${API_BASE_URL}/user-config/get`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      const data = await response.json();

      if (response.ok) {
        console.log('✅ Configuração carregada:', data);
        return { status: 'ok', ...data };
      } else {
        console.warn('⚠️ Configuração não encontrada:', data);
        return { status: 'nao_encontrada' };
      }
    } catch (error) {
      console.error('❌ Erro ao carregar configuração:', error);
      return { status: 'erro', mensagem: error.message };
    }
  }

  /**
   * Carrega bases disponíveis do usuário
   * @returns {Promise}
   */
  async carregarBases() {
    try {
      const token = localStorage.getItem('auth_token');
      
      if (!token) {
        return { total: 0, bases: [] };
      }

      const response = await fetch(`${API_BASE_URL}/user-config/bases`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      const data = await response.json();

      if (response.ok) {
        console.log(`✅ ${data.total} base(s) carregada(s)`);
        return data;
      } else {
        return { total: 0, bases: [] };
      }
    } catch (error) {
      console.error('❌ Erro ao carregar bases:', error);
      return { total: 0, bases: [] };
    }
  }

  /**
   * Carrega informações da configuração (sem senhas)
   * @returns {Promise}
   */
  async carregarInfoConfiguracao() {
    try {
      const token = localStorage.getItem('auth_token');
      
      if (!token) {
        return { status: 'nao_autenticado' };
      }

      const response = await fetch(`${API_BASE_URL}/user-config/info`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      const data = await response.json();
      return data;
    } catch (error) {
      console.error('❌ Erro ao carregar info:', error);
      return { status: 'erro' };
    }
  }

  /**
   * Salva base ativa selecionada na sessão
   * @param {Object|null} base
   */
  salvarBaseAtiva(base) {
    if (!base) {
      sessionStorage.removeItem('pld_base_ativa');
      if (typeof window !== 'undefined') {
        window.dispatchEvent(new Event('pld-base-ativa-updated'));
      }
      return;
    }
    sessionStorage.setItem('pld_base_ativa', JSON.stringify(base));
    if (typeof window !== 'undefined') {
      window.dispatchEvent(new Event('pld-base-ativa-updated'));
    }
  }

  /**
   * Recupera base ativa da sessão
   * @returns {Object|null}
   */
  carregarBaseAtiva() {
    const raw = sessionStorage.getItem('pld_base_ativa');
    if (!raw) return null;
    try {
      return JSON.parse(raw);
    } catch {
      return null;
    }
  }

  /**
   * Salva configuração SQL ativa para módulos legados
   * @param {Object|null} config
   */
  salvarSqlConfig(config) {
    if (!config) {
      sessionStorage.removeItem('pld_sql_config');
      return;
    }
    sessionStorage.setItem('pld_sql_config', JSON.stringify(config));
  }

  /**
   * Recupera configuração SQL ativa
   * @returns {Object|null}
   */
  carregarSqlConfig() {
    const raw = sessionStorage.getItem('pld_sql_config');
    if (!raw) return null;
    try {
      return JSON.parse(raw);
    } catch {
      return null;
    }
  }

  /**
   * Limpa configuração
   */
  limpar() {
    this.configKey = null;
    this.config = null;
    this.ambiente = null;
    sessionStorage.removeItem('config_key');
    sessionStorage.removeItem('pld_config');
    sessionStorage.removeItem('pld_ambiente');
    sessionStorage.removeItem('pld_base_ativa');
    sessionStorage.removeItem('pld_sql_config');
  }
}

// Singleton global
export const apiService = new ApiService();

// Carregar config da sessão automaticamente
apiService.carregarDaSessao();
