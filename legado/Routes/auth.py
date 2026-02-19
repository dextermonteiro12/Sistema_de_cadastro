from flask import Blueprint, request, jsonify

# Definindo o Blueprint
auth_bp = Blueprint('auth', __name__)

@auth_bp.route("/login", methods=["POST"])
def login():
    d = request.json
    
    # Usando a lógica exata do seu backup:
    # username: admin / password: 1234
    if d.get('username') == 'admin' and d.get('password') == '1234':
        return jsonify({
            "status": "ok", 
            "user": "admin", 
            "tipo": "ADMIN"
        }), 200
        
    return jsonify({"message": "Erro"}), 401