#!/usr/bin/env python3
"""
🚀 Script principal para executar o sistema completo.
"""

import os
import sys
import subprocess
import webbrowser
from threading import Timer

def main():
    print("=" * 60)
    print("🚀 SULAMÉRICA ODONTO - SISTEMA DE PROSPECÇÃO")
    print("=" * 60)
    
    # Verifica dependências
    try:
        import flask
        import sqlalchemy
        print("✅ Dependências Python OK")
    except ImportError as e:
        print(f"❌ Dependência faltando: {e}")
        print("Execute: pip install -r requirements.txt")
        sys.exit(1)
    
    # Cria diretórios
    os.makedirs('data', exist_ok=True)
    os.makedirs('prints_personalizados', exist_ok=True)
    print("✅ Diretórios criados")
    
    # Inicia o servidor
    print("\n" + "=" * 60)
    print("📊 Iniciando Painel de Prospecção...")
    print("🌐 Dashboard: http://localhost:5001")
    print("💡 Pressione Ctrl+C para parar")
    print("=" * 60 + "\n")
    
    # Abre o navegador UMA ÚNICA VEZ após 2 segundos
    Timer(2.0, lambda: webbrowser.open('http://localhost:5001', new=0)).start()
    
    # Inicia o Flask (sem debug para não abrir aba extra)
    from backend.app import app
    app.run(debug=False, port=5001, host='0.0.0.0')

if __name__ == '__main__':
    main()