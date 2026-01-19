from flask import Blueprint, request, jsonify
import pyodbc

home_bp = Blueprint('home', __name__)

class HomeEngine:
    def __init__(self, config):
        self.conn_str = (
            f"DRIVER={{SQL Server}};"
            f"SERVER={config['servidor']};"
            f"DATABASE={config['banco']};"
            f"UID={config['usuario']};"
            f"PWD={config['senha']};"
        )

    def get_saude_dados(self):
        try:
            conn = pyodbc.connect(self.conn_str, timeout=3)
            cursor = conn.cursor()

            # Query 1: Fila ADSVC
            cursor.execute("SELECT COUNT(1) FROM ADSVC_EXECUTAR WITH(NOLOCK)")
            fila_pendente = cursor.fetchone()[0]

            # Query 2: Erros 24h
            cursor.execute("""
                SELECT COUNT(1) FROM TB_SERVICO_EXEC 
                WHERE DS_ERRO <> '' 
                AND DT_HR_EXECUTADO >= DATEADD(hh, -24, GETDATE())
            """)
            erros_hoje = cursor.fetchone()[0]

            # Query 3: Performance (Cálculo dinâmico do QT_TEMPO_EXEC)
            # Substitua 'DT_GERACAO' pelo nome da sua coluna de data (ex: DT_INICIO ou DT_ENTRADA)
            # Query 3: Performance/Carga Atual
            # Mudamos para COUNT para garantir que o dashboard receba dados 
            # sem depender de colunas de data específicas
            cursor.execute("""
                SELECT 
                    'Fila Principal' as Fila, 
                    COUNT(1) as QT_TEMPO_EXEC
                FROM ADSVC_EXECUTANDO WITH(NOLOCK)
                
                UNION ALL
                
                SELECT 
                    'Fila Secundária' as Fila, 
                    COUNT(1) as QT_TEMPO_EXEC
                FROM ADSVC_EXECUTANDO_MF1 WITH(NOLOCK)
            """)
            
            perf_rows = cursor.fetchall()
            # O dashboard receberá a quantidade de registros em execução como "Media"
            performance = [{"Fila": row[0], "Media": float(row[1])} for row in perf_rows]

            conn.close()

            status_geral = "ESTÁVEL"
            if fila_pendente > 1000 or erros_hoje > 50:
                status_geral = "CRÍTICO"

            return {
                "status_geral": status_geral,
                "cards": {
                    "fila_pendente": fila_pendente,
                    "erros_servicos": erros_hoje
                },
                "performance_ms": performance
            }

        except Exception as e:
            print(f"Erro detalhado no SQL: {e}")
            return None

@home_bp.route('/api/saude-servidor', methods=['POST'])
def rota_saude():
    data = request.json
    config = data.get('config')
    
    if not config:
        return jsonify({"erro": "Configuração SQL não encontrada"}), 400
    
    engine = HomeEngine(config)
    resultado = engine.get_saude_dados()
    
    if resultado:
        return jsonify(resultado), 200
    else:
        return jsonify({
            "status_geral": "OFFLINE",
            "cards": {"fila_pendente": 0, "erros_servicos": 0},
            "performance_ms": []
        }), 500