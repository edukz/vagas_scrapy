import asyncio
import sys
import os

# Adicionar pasta src ao path para imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.scraper import scrape_catho_jobs
from src.filters import JobFilter, get_filter_configuration
from src.utils import save_results
from src.structured_logger import structured_logger, Component


async def main():
    """
    Função principal - versão modularizada e organizada
    """
    # Inicializar sistema de logs
    structured_logger.log_system_info()
    structured_logger.info(
        "Application started",
        component=Component.MAIN,
        context={'version': '3.0', 'features': ['retry', 'fallback', 'validation', 'logging', 'circuit_breaker', 'metrics', 'alerts']}
    )
    
    print("=== WEB SCRAPER CATHO (VERSÃO MODULARIZADA) ===\n")
    print("✨ Projeto reorganizado com arquitetura modular:")
    print("   📦 cache.py - Sistema de cache inteligente")
    print("   📦 scraper.py - Lógica de scraping e extração")
    print("   📦 filters.py - Sistema de filtros avançados")
    print("   📦 navigation.py - Navegação multi-página")
    print("   🛡️ retry_system.py - Sistema de retry automático")
    print("   🎯 selector_fallback.py - Fallback de seletores")
    print("   📋 data_validator.py - Validação robusta de dados")
    print("   📝 structured_logger.py - Logs estruturados")
    print("   🔧 circuit_breaker.py - Proteção contra sobrecarga")
    print("   📊 metrics_tracker.py - Monitoramento em tempo real")
    print("   🚨 alert_system.py - Alertas automáticos")
    print("   📦 utils.py - Utilitários e performance")
    print("   📦 main.py - Interface principal (este arquivo)")
    
    print("\n🔍 Recursos disponíveis:")
    print("   • Sistema de filtragem avançada")
    print("   • Cache inteligente (6h de validade)")
    print("   • Rate limiting adaptativo")
    print("   • Navegação por múltiplas páginas")
    print("   • Processamento paralelo")
    print("   • Análise automática de dados")
    print("   • Múltiplos formatos de saída\n")
    
    # Configurar filtros
    print("Deseja aplicar filtros às vagas? (s/n)")
    apply_filters = input().strip().lower() in ['s', 'sim', 'y', 'yes']
    
    filters_config = {}
    if apply_filters:
        filters_config = get_filter_configuration()
    else:
        print("✓ Nenhum filtro será aplicado - todas as vagas serão coletadas")
    
    # Configurar performance
    print("\n⚡ CONFIGURAÇÃO DE PERFORMANCE:")
    print("Quantas vagas processar simultaneamente? (1-5, padrão: 3)")
    try:
        max_concurrent = int(input("Digite o número: ").strip() or "3")
        max_concurrent = max(1, min(5, max_concurrent))
    except:
        max_concurrent = 3
    
    print(f"✓ Processamento paralelo: {max_concurrent} vagas simultâneas")
    
    # Configurar páginas
    print("\n📄 CONFIGURAÇÃO DE PÁGINAS:")
    print("Quantas páginas analisar? (1-10, padrão: 5)")
    try:
        max_pages = int(input("Digite o número: ").strip() or "5")
        max_pages = max(1, min(10, max_pages))
    except:
        max_pages = 5
    
    print(f"✓ Navegação configurada: até {max_pages} páginas")
    
    # Executando o scraper
    print(f"\n{'='*60}")
    print("INICIANDO COLETA COM ARQUITETURA MODULAR...")
    print(f"{'='*60}")
    
    jobs = await scrape_catho_jobs(max_concurrent_jobs=max_concurrent, max_pages=max_pages)
    
    if jobs:
        print(f"\n{'='*60}")
        print(f"DADOS COLETADOS: {len(jobs)} vagas encontradas")
        print(f"{'='*60}")
        
        # Aplicar filtros e análise
        print("\nAplicando filtros e análise...")
        job_filter = JobFilter()
        
        if filters_config:
            filtered_jobs = job_filter.apply_filters(jobs, filters_config)
            print(f"✓ Filtros aplicados: {len(filtered_jobs)} vagas selecionadas")
        else:
            # Aplicar apenas análise sem filtros
            filtered_jobs = job_filter.apply_filters(jobs, {})
            print(f"✓ Análise aplicada a todas as {len(filtered_jobs)} vagas")
        
        jobs = filtered_jobs
        
        if jobs:
            print(f"\n{'='*60}")
            print(f"RESULTADO FINAL: {len(jobs)} vagas processadas")
            print(f"{'='*60}")
            
            # Salvando resultados
            save_results(jobs, filters_config)
            
            print(f"\n✅ PROCESSAMENTO CONCLUÍDO COM SUCESSO!")
            print(f"📁 Arquivos organizados em subdiretórios")
            
            # Preview dos resultados
            print(f"\n🔥 PREVIEW DOS RESULTADOS:")
            if jobs:
                # Tecnologias mais demandadas
                all_techs = {}
                for job in jobs:
                    for tech in job.get('tecnologias_detectadas', []):
                        all_techs[tech] = all_techs.get(tech, 0) + 1
                
                if all_techs:
                    print(f"   💻 Top 5 tecnologias:")
                    for tech, count in sorted(all_techs.items(), key=lambda x: x[1], reverse=True)[:5]:
                        print(f"      - {tech}: {count} vagas")
                
                # Análise de níveis
                niveis = {}
                for job in jobs:
                    nivel = job.get('nivel_categorizado', 'Não categorizado')
                    niveis[nivel] = niveis.get(nivel, 0) + 1
                
                if niveis:
                    print(f"   📊 Distribuição por nível:")
                    for nivel, count in sorted(niveis.items(), key=lambda x: x[1], reverse=True)[:3]:
                        print(f"      - {nivel.replace('_', ' ').title()}: {count} vagas")
        else:
            print("\n⚠ Nenhuma vaga atendeu aos critérios de filtro especificados.")
            print("Tente ajustar os filtros ou executar sem filtros.")
    else:
        print("\n✗ Nenhuma vaga foi encontrada no site.")


if __name__ == "__main__":
    asyncio.run(main())