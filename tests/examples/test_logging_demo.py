#!/usr/bin/env python3
"""
Demo do sistema de logs estruturados em ação
Mostra como os logs funcionam durante o scraping
"""

import asyncio
import time
import sys
import os

# Adicionar diretório atual ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.structured_logger import structured_logger, Component, LogLevel


async def simulate_scraping_with_logs():
    """Simula processo de scraping com logs estruturados"""
    print("🧪 DEMO DO SISTEMA DE LOGS ESTRUTURADOS")
    print("=" * 50)
    
    # Configurar console para mostrar mais logs
    structured_logger.set_console_level(LogLevel.INFO)
    
    # 1. Log início da aplicação
    structured_logger.info(
        "Demo application started",
        component=Component.MAIN,
        context={'demo_mode': True, 'version': '3.0'}
    )
    
    # 2. Simular início de sessão de scraping
    with structured_logger.trace_operation("demo_scraping_session", Component.SCRAPER):
        config = {
            'max_pages': 2,
            'concurrent_jobs': 3,
            'url': 'catho.com.br/vagas/home-office'
        }
        
        session_trace_id = structured_logger.log_scraping_session_start(config)
        
        # 3. Simular navegação por páginas
        for page_num in range(1, 3):
            with structured_logger.track_performance(Component.SCRAPER, f"scrape_page_{page_num}") as tracker:
                structured_logger.scraper_log(
                    f"Starting page {page_num} extraction",
                    operation=f"scrape_page_{page_num}",
                    url=f"catho.com.br/vagas/home-office/?page={page_num}",
                    context={'page_number': page_num}
                )
                
                # Simular extração de jobs
                await asyncio.sleep(0.5)  # Simular tempo de carregamento
                
                jobs_found = 15 if page_num == 1 else 12
                structured_logger.scraper_log(
                    f"Page {page_num} extraction completed",
                    operation=f"scrape_page_{page_num}",
                    context={'jobs_found': jobs_found, 'page_number': page_num}
                )
        
        # 4. Simular sistema de retry
        print("\n🔄 Simulando operações com retry...")
        
        # Retry bem-sucedido
        with structured_logger.track_performance(Component.RETRY_SYSTEM, "scrape_job_details"):
            for attempt in range(1, 4):
                structured_logger.retry_log(
                    f"Attempting to scrape job details (attempt {attempt})",
                    operation="scrape_job_details",
                    attempt=attempt,
                    max_attempts=3,
                    url="catho.com.br/vagas/dev-python/123456"
                )
                
                await asyncio.sleep(0.2)
                
                if attempt == 3:  # Sucesso na 3ª tentativa
                    structured_logger.retry_log(
                        "Job details scraped successfully after retry",
                        LogLevel.INFO,
                        operation="scrape_job_details",
                        attempt=attempt,
                        success=True,
                        duration_ms=600,
                        context={'retry_reason': 'timeout_error'}
                    )
                    break
                else:
                    structured_logger.retry_log(
                        f"Attempt {attempt} failed, retrying...",
                        LogLevel.WARN,
                        operation="scrape_job_details",
                        attempt=attempt,
                        retry_reason="timeout_error",
                        success=False,
                        error="Connection timeout after 30s"
                    )
        
        # 5. Simular fallback de seletores
        print("\n🎯 Simulando fallback de seletores...")
        
        structured_logger.fallback_log(
            "Primary selector failed, trying fallback",
            LogLevel.WARN,
            operation="extract_job_title",
            context={
                'primary_selector': 'h2.job-title',
                'fallback_selector': '[data-testid="job-title"]',
                'element_type': 'job_title'
            }
        )
        
        await asyncio.sleep(0.1)
        
        structured_logger.fallback_log(
            "Fallback selector succeeded",
            operation="extract_job_title",
            success=True,
            context={'selector_used': '[data-testid="job-title"]', 'fallback_level': 2}
        )
        
        # 6. Simular validação de dados
        print("\n📋 Simulando validação de dados...")
        
        # Validação de lote
        jobs_to_validate = 27
        structured_logger.validation_log(
            f"Starting batch validation of {jobs_to_validate} jobs",
            operation="validate_batch",
            context={'job_count': jobs_to_validate}
        )
        
        await asyncio.sleep(0.3)
        
        # Resultados da validação
        validation_results = {
            'total_jobs': jobs_to_validate,
            'valid_jobs': 22,
            'invalid_jobs': 5,
            'quality_score': 0.815,
            'corrections_applied': 34,
            'anomalies_detected': 3
        }
        
        structured_logger.validation_log(
            "Batch validation completed",
            operation="validate_batch",
            validation_score=validation_results['quality_score'],
            success=True,
            context=validation_results
        )
        
        # Exemplo de anomalia detectada
        structured_logger.validation_log(
            "Anomaly detected in job data",
            LogLevel.WARN,
            operation="detect_anomalies",
            anomaly_type="suspicious_title",
            context={
                'job_title': 'URGENTE!!! GANHE R$ 50.000 !!!',
                'reason': 'excessive_special_chars',
                'severity': 'medium'
            }
        )
        
        # 7. Simular cache
        print("\n💾 Simulando operações de cache...")
        
        structured_logger.cache_log(
            "Cache hit for job details",
            operation="get_cached_job",
            context={
                'cache_key': 'job_123456',
                'hit_rate': 0.85,
                'ttl_remaining': 3600
            }
        )
        
        structured_logger.cache_log(
            "Cache miss, fetching from source",
            LogLevel.WARN,
            operation="get_cached_job",
            context={
                'cache_key': 'job_789012',
                'miss_reason': 'expired',
                'hit_rate': 0.85
            }
        )
        
        # 8. Finalizar sessão
        final_stats = {
            'total_jobs_found': jobs_to_validate,
            'valid_jobs': validation_results['valid_jobs'],
            'quality_score': validation_results['quality_score'],
            'total_pages_processed': 2,
            'cache_hit_rate': 0.85,
            'retry_operations': 1,
            'fallback_operations': 1,
            'total_duration_seconds': 2.1
        }
        
        structured_logger.log_scraping_session_end(final_stats)
    
    # 9. Mostrar estatísticas dos logs
    print(f"\n📊 ESTATÍSTICAS DOS LOGS GERADOS:")
    log_stats = structured_logger.get_log_stats()
    
    for log_type, stats in log_stats.items():
        if 'size_mb' in stats:
            print(f"   📄 {log_type}: {stats['lines']} linhas, {stats['size_mb']}MB")
    
    # 10. Mostrar exemplos de logs
    print(f"\n📁 ARQUIVOS DE LOG CRIADOS:")
    log_files = structured_logger.get_log_files()
    
    for log_type, file_path in log_files.items():
        if file_path.exists():
            print(f"   📄 {log_type}: {file_path}")
        
    print(f"\n💡 COMO VISUALIZAR OS LOGS:")
    print(f"   📖 Logs principais: tail -f logs/scraper.log")
    print(f"   🔍 Logs de debug: tail -f logs/scraper_debug.log") 
    print(f"   ❌ Apenas erros: tail -f logs/scraper_errors.log")
    
    print(f"\n🔍 EXEMPLO DE LOG JSON:")
    main_log_file = log_files['main']
    if main_log_file.exists():
        with open(main_log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            if lines:
                import json
                try:
                    last_log = json.loads(lines[-1].strip())
                    print(f"   {json.dumps(last_log, indent=2, ensure_ascii=False)}")
                except:
                    print(f"   {lines[-1].strip()}")


async def main():
    """Função principal do demo"""
    try:
        await simulate_scraping_with_logs()
        
        print("\n" + "=" * 50)
        print("🎉 DEMO CONCLUÍDO COM SUCESSO!")
        print("=" * 50)
        
        print("\n💡 BENEFÍCIOS DO SISTEMA DE LOGS:")
        print("   ✅ Logs estruturados em JSON para análise")
        print("   ✅ Trace IDs para correlacionar operações")
        print("   ✅ Performance tracking automático")
        print("   ✅ Logs específicos por componente")
        print("   ✅ Múltiplos arquivos por severidade")
        print("   ✅ Rotação automática para produção")
        print("   ✅ Context rico para debugging")
        
        print("\n🚀 O SISTEMA ESTÁ PRONTO!")
        print("   Execute 'python main.py' para usar com logs completos")
        
    except Exception as e:
        print(f"\n❌ Erro durante demo: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())