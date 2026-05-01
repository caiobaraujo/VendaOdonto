#!/usr/bin/env python3
"""
🚀 Script principal para executar o sistema completo.
Inicia o servidor Flask com o dashboard e todas as funcionalidades.
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
    
    # Verifica se as dependências estão instaladas
    try:
        import flask
        import sqlalchemy
        print("✅ Dependências Python OK")
    except ImportError as e:
        print(f"❌ Dependência faltando: {e}")
        print("Execute: pip install -r requirements.txt")
        sys.exit(1)
    
    # Cria diretórios necessários
    os.makedirs('data', exist_ok=True)
    os.makedirs('prints_personalizados', exist_ok=True)
    print("✅ Diretórios criados")
    
    # Inicia o servidor
    print("\n" + "=" * 60)
    print("📊 Iniciando Painel de Prospecção...")
    print("🌐 Dashboard: http://localhost:5001")
    print("💡 Pressione Ctrl+C para parar")
    print("=" * 60 + "\n")
    
    # Abre o navegador automaticamente após 1.5 segundos
    Timer(1.5, lambda: webbrowser.open('http://localhost:5001')).start()
    
    # Inicia o Flask
    from backend.app import app
    app.run(debug=True, port=5001, host='0.0.0.0')

if __name__ == '__main__':
    main()