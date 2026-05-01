import os
import sys
import json
import threading
from datetime import datetime
from flask import Flask, jsonify, request, render_template
from flask_cors import CORS

# Adiciona o diretório pai ao path para importar os módulos
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.models import (
    init_db, get_session, Lead, ScrapingJob, ScrapingProgress
)
from backend.processors.lead_processor import LeadProcessor

# Tentativa de importar o scraper (se existir)
try:
    from backend.scrapers.maps_scraper import GoogleMapsScraper
    SCRAPER_DISPONIVEL = True
except ImportError:
    print("⚠️ Scraper não encontrado. Funcionalidade de scraping desabilitada.")
    SCRAPER_DISPONIVEL = False

try:
    from backend.scrapers.print_automator import PrintAutomator
    PRINT_AUTOMATOR_DISPONIVEL = True
except ImportError:
    print("⚠️ Print automator não encontrado.")
    PRINT_AUTOMATOR_DISPONIVEL = False

app = Flask(__name__, template_folder='../frontend', static_folder='../frontend')
CORS(app)

# Inicializa o banco de dados
init_db()

# Instancia o processador de leads (singleton)
lead_processor = LeadProcessor()

# Estado global dos jobs (para MVP, depois pode ir para Redis)
active_jobs = {}

@app.route('/')
def index():
    """Serve o DASHBOARD"""
    return render_template('index.html')

@app.route('/landing.html')
def landing():
    """Serve a LANDING PAGE de vendas personalizada"""
    return render_template('landing.html')

@app.route('/preview_print.html')
def preview_print():
    """Serve a página de preview para prints"""
    return render_template('preview_print.html')

# ==================== API ENDPOINTS ====================

@app.route('/api/health')
def health_check():
    """Endpoint de saúde da API"""
    return jsonify({
        'status': 'online',
        'timestamp': datetime.now().isoformat(),
        'scraper_disponivel': SCRAPER_DISPONIVEL,
        'print_automator_disponivel': PRINT_AUTOMATOR_DISPONIVEL
    })

@app.route('/api/leads', methods=['GET'])
def listar_leads():
    """
    Lista todos os leads com paginação e filtros.
    Query params:
        - page: número da página (default 1)
        - per_page: itens por página (default 50)
        - status: filtrar por status (Novo, Contatado, etc)
        - bairro: filtrar por bairro
        - pronto_para_enviar: SIM ou REVISAR
    """
    session = get_session()
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 50))
        status_filter = request.args.get('status')
        bairro_filter = request.args.get('bairro')
        pronto_filter = request.args.get('pronto_para_enviar')
        
        query = session.query(Lead)
        
        if status_filter:
            query = query.filter(Lead.status == status_filter)
        if bairro_filter:
            query = query.filter(Lead.bairro == bairro_filter)
        if pronto_filter:
            query = query.filter(Lead.pronto_para_enviar == pronto_filter)
        
        total = query.count()
        leads = query.order_by(
            Lead.pronto_para_enviar.desc(),
            Lead.prioridade.desc(),
            Lead.empresa_contato.asc()
        ).offset((page - 1) * per_page).limit(per_page).all()
        
        return jsonify({
            'leads': [lead.to_dict() for lead in leads],
            'total': total,
            'page': page,
            'per_page': per_page,
            'total_pages': (total + per_page - 1) // per_page
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()

@app.route('/api/leads/<int:lead_id>', methods=['GET'])
def obter_lead(lead_id):
    """Obtém um lead específico pelo ID"""
    session = get_session()
    try:
        lead = session.query(Lead).get(lead_id)
        if not lead:
            return jsonify({'error': 'Lead não encontrado'}), 404
        return jsonify(lead.to_dict())
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()

@app.route('/api/leads/<int:lead_id>/status', methods=['PUT'])
def atualizar_status_lead(lead_id):
    """Atualiza o status de um lead"""
    session = get_session()
    try:
        data = request.get_json()
        novo_status = data.get('status')
        observacao = data.get('observacao', '')
        
        lead = session.query(Lead).get(lead_id)
        if not lead:
            return jsonify({'error': 'Lead não encontrado'}), 404
        
        lead.status = novo_status
        lead.ultimo_contato = datetime.now()
        if observacao:
            lead.observacao = observacao
        
        session.commit()
        return jsonify({'message': 'Status atualizado com sucesso', 'lead': lead.to_dict()})
    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()

@app.route('/api/leads/<int:lead_id>/gerar-print', methods=['POST'])
def gerar_print_lead(lead_id):
    """Gera print personalizado para um lead específico"""
    if not PRINT_AUTOMATOR_DISPONIVEL:
        return jsonify({'error': 'Gerador de prints não disponível'}), 503
    
    session = get_session()
    try:
        lead = session.query(Lead).get(lead_id)
        if not lead:
            return jsonify({'error': 'Lead não encontrado'}), 404
        
        if not lead.link_preview:
            return jsonify({'error': 'Lead não possui link de preview'}), 400
        
        print(f"\n🖨️ GERANDO PRINT INDIVIDUAL")
        print(f"📍 Empresa: {lead.empresa_contato}")
        
        automator = PrintAutomator()
        caminho_print = automator.gerar_print(
            url_preview=lead.link_preview,
            nome_empresa=lead.empresa_contato
        )
        automator.fechar()
        
        lead.caminho_print = caminho_print
        session.commit()
        
        # Cria URL relativa para o frontend
        nome_arquivo = os.path.basename(caminho_print)
        url_print = f"/static/prints/{nome_arquivo}"
        
        print(f"✅ Print gerado: {url_print}")
        
        return jsonify({
            'message': 'Print gerado com sucesso!',
            'caminho_print': caminho_print,
            'url_print': url_print,
            'lead': lead.to_dict()
        })
    except Exception as e:
        session.rollback()
        print(f"❌ Erro: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()

@app.route('/api/leads/gerar-prints-lote', methods=['POST'])
def gerar_prints_lote():
    """Gera prints para múltiplos leads de uma vez"""
    if not PRINT_AUTOMATOR_DISPONIVEL:
        return jsonify({'error': 'Gerador de prints não disponível'}), 503
    
    session = get_session()
    try:
        data = request.get_json()
        lead_ids = data.get('lead_ids', [])
        
        if not lead_ids:
            return jsonify({'error': 'Lista de IDs vazia'}), 400
        
        leads = session.query(Lead).filter(Lead.id.in_(lead_ids)).all()
        
        leads_data = [
            {
                'empresa_contato': lead.empresa_contato,
                'link_preview': lead.link_preview,
                'id': lead.id
            }
            for lead in leads if lead.link_preview
        ]
        
        automator = PrintAutomator()
        resultados = automator.gerar_prints_em_lote(leads_data)
        automator.fechar()
        
                # Atualiza os caminhos no banco
        for resultado in resultados:
            if resultado['sucesso']:
                lead = session.query(Lead).filter(
                    Lead.empresa_contato == resultado['empresa']
                ).first()
                if lead:
                    lead.caminho_print = resultado['caminho_print']
        
        session.commit()
        
        # Cria URLs para o frontend
        for r in resultados:
            if r['sucesso']:
                nome_arquivo = os.path.basename(r['caminho_print'])
                r['url_print'] = f"/static/prints/{nome_arquivo}"
        
        return jsonify({
            'message': f'{len([r for r in resultados if r["sucesso"]])} prints gerados com sucesso',
            'resultados': resultados
        })
    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()

@app.route('/api/scraping/iniciar', methods=['POST'])
def iniciar_scraping():
    """Inicia um job de scraping"""
    if not SCRAPER_DISPONIVEL:
        return jsonify({'error': 'Scraper não disponível'}), 503
    
    data = request.get_json()
    bairro = data.get('bairro', 'Santo Agostinho Belo Horizonte')
    nicho = data.get('nicho', 'Clínica de Estética')
    
    job_id = datetime.now().strftime('%Y%m%d%H%M%S')
    
    # Cria registro do job
    session = get_session()
    try:
        job = ScrapingJob(
            consulta=f"{nicho} em {bairro}",
            bairro=bairro,
            nicho=nicho
        )
        session.add(job)
        session.commit()
        job_id = job.id
        
        # Inicia scraping em thread separada
        thread = threading.Thread(
            target=_executar_scraping,
            args=(job_id, bairro, nicho)
        )
        thread.start()
        
        return jsonify({
            'message': 'Scraping iniciado com sucesso',
            'job_id': job_id,
            'consulta': f"{nicho} em {bairro}"
        }), 202
    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()

@app.route('/api/scraping/status/<int:job_id>')
def status_scraping(job_id):
    """Verifica o status de um job de scraping"""
    session = get_session()
    try:
        job = session.query(ScrapingJob).get(job_id)
        if not job:
            return jsonify({'error': 'Job não encontrado'}), 404
        
        return jsonify({
            'job_id': job.id,
            'status': job.status,
            'consulta': job.consulta,
            'leads_encontrados': job.leads_encontrados,
            'leads_novos': job.leads_novos,
            'log': job.log,
            'data_inicio': job.data_inicio.isoformat() if job.data_inicio else None,
            'data_fim': job.data_fim.isoformat() if job.data_fim else None
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()

@app.route('/api/scraping/historico')
def historico_scraping():
    """Lista o histórico de jobs de scraping"""
    session = get_session()
    try:
        jobs = session.query(ScrapingJob).order_by(
            ScrapingJob.data_inicio.desc()
        ).limit(20).all()
        
        return jsonify({
            'jobs': [
                {
                    'id': job.id,
                    'consulta': job.consulta,
                    'status': job.status,
                    'leads_encontrados': job.leads_encontrados,
                    'leads_novos': job.leads_novos,
                    'data_inicio': job.data_inicio.isoformat() if job.data_inicio else None,
                    'data_fim': job.data_fim.isoformat() if job.data_fim else None
                }
                for job in jobs
            ]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()

@app.route('/api/estatisticas')
def estatisticas():
    """Retorna estatísticas gerais do CRM"""
    session = get_session()
    try:
        total_leads = session.query(Lead).count()
        leads_por_status = {}
        statuses = session.query(Lead.status).distinct().all()
        for (status,) in statuses:
            count = session.query(Lead).filter(Lead.status == status).count()
            leads_por_status[status] = count
        
        leads_por_bairro = {}
        bairros = session.query(Lead.bairro).distinct().all()
        for (bairro,) in bairros:
            count = session.query(Lead).filter(Lead.bairro == bairro).count()
            leads_por_bairro[bairro] = count
        
        prontos_envio = session.query(Lead).filter(
            Lead.pronto_para_enviar == 'SIM'
        ).count()
        
        return jsonify({
            'total_leads': total_leads,
            'leads_por_status': leads_por_status,
            'leads_por_bairro': leads_por_bairro,
            'prontos_para_envio': prontos_envio
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()

# ==================== FUNÇÕES AUXILIARES ====================

def _executar_scraping(job_id: int, bairro: str, nicho: str):
    """
    Executa o scraping EM PRIMEIRO PLANO para o usuário ver.
    Mostra progresso real no banco de dados.
    """
    session = get_session()
    try:
        job = session.query(ScrapingJob).get(job_id)
        if not job:
            return
        
        # Atualiza status do job
        job.status = 'executando'
        session.commit()
        
        # Importa e executa o scraper
        from backend.scrapers.maps_scraper import GoogleMapsScraper
        
        scraper = GoogleMapsScraper(max_leads=6)  # Limite de 6
        resultado = scraper.buscar_leads(bairro=bairro, nicho=nicho)
        
        leads_brutos = resultado['leads']
        progresso = resultado['progresso']
        
        # Salva progresso no banco
        for msg in progresso:
            progress_entry = ScrapingProgress(
                job_id=job_id,
                mensagem=msg
            )
            session.add(progress_entry)
        session.commit()
        
        # Processa e salva leads (evitando duplicados)
        leads_processados = 0
        leads_novos = 0
        leads_existentes = 0
        
        for lead_bruto in leads_brutos:
            lead_processado = lead_processor.processar_lead_bruto(lead_bruto)
            telefone = lead_processado['telefone']
            
            if not telefone:
                continue
            
            # Verifica duplicata pelo telefone
            existente = session.query(Lead).filter(
                Lead.telefone == telefone
            ).first()
            
            if existente:
                # Atualiza informações
                existente.empresa_original = lead_processado['empresa_original']
                existente.bairro = lead_processado['bairro']
                existente.link_landing = lead_processado['link_landing']
                existente.link_preview = lead_processado['link_preview']
                existente.data_processamento = datetime.now()
                leads_existentes += 1
            else:
                novo_lead = Lead(
                    empresa_original=lead_processado['empresa_original'],
                    empresa_contato=lead_processado['empresa_contato'],
                    telefone=telefone,
                    bairro=lead_processado['bairro'],
                    site=lead_processado.get('site', ''),
                    segmento=lead_processado['segmento'],
                    link_landing=lead_processado['link_landing'],
                    link_preview=lead_processado['link_preview'],
                    prioridade=lead_processado['prioridade'],
                    pronto_para_enviar=lead_processado['pronto_para_enviar'],
                    mensagem_whatsapp=lead_processado['mensagem_whatsapp'],
                    data_captura=datetime.now(),
                    data_processamento=datetime.now()
                )
                session.add(novo_lead)
                leads_novos += 1
            
            leads_processados += 1
        
        # Atualiza o job
        job.status = 'concluido'
        job.leads_encontrados = leads_processados
        job.leads_novos = leads_novos
        job.data_fim = datetime.now()
        job.log = f"OK: {leads_novos} novos, {leads_existentes} atualizados, {len(progresso)} passos"
        
        session.commit()
        
    except Exception as e:
        session.rollback()
        try:
            job = session.query(ScrapingJob).get(job_id)
            if job:
                job.status = 'erro'
                job.log = str(e)[:500]
                job.data_fim = datetime.now()
                session.commit()
        except Exception:
            pass
    finally:
        session.close()

@app.route('/api/scraping/progresso/<int:job_id>')
def progresso_scraping(job_id):
    """Retorna o progresso detalhado de um job de scraping"""
    session = get_session()
    try:
        progress_list = session.query(ScrapingProgress).filter(
            ScrapingProgress.job_id == job_id
        ).order_by(ScrapingProgress.timestamp.asc()).all()
        
        return jsonify({
            'job_id': job_id,
            'progresso': [p.to_dict() for p in progress_list],
            'total_passos': len(progress_list)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        session.close() 


@app.route('/static/prints/<nome_arquivo>')
def servir_print(nome_arquivo):
    """Serve os arquivos de print gerados"""
    import flask
    pasta_prints = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'prints_personalizados')
    return flask.send_from_directory(pasta_prints, nome_arquivo)


if __name__ == '__main__':
    print("🚀 Iniciando servidor do Painel de Prospecção...")
    print("📊 Dashboard: http://localhost:5001")
    print("❤️ Health Check: http://localhost:5001/api/health")
    app.run(debug=True, port=5001, host='0.0.0.0')