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
    
    # Opção de busca no cache
    print("\n🔍 MODO DE OPERAÇÃO:")
    print("Escolha uma opção:")
    print("  1. Fazer novo scraping")
    print("  2. Buscar no cache existente")
    print("  3. Limpar cache/checkpoint e fazer scraping completo")
    print("  4. Limpar duplicatas em arquivos existentes")
    print("Opção (1-4, padrão: 1): ", end="")
    
    try:
        mode_choice = input().strip() or "1"
        mode_choice = int(mode_choice)
        mode_choice = max(1, min(4, mode_choice))
    except:
        mode_choice = 1
    
    if mode_choice == 2:
        # Modo de busca no cache
        from src.compressed_cache import CompressedCache
        cache = CompressedCache()
        
        print("\n🔍 BUSCA NO CACHE:")
        print("Escolha o tipo de busca:")
        print("  1. Listar todas as entradas")
        print("  2. Buscar por empresa")
        print("  3. Buscar por tecnologia")
        print("  4. Buscar por localização")
        print("  5. Estatísticas do cache")
        print("  6. Top empresas e tecnologias")
        print("Opção (1-6, padrão: 1): ", end="")
        
        try:
            search_choice = int(input().strip() or "1")
            search_choice = max(1, min(6, search_choice))
        except:
            search_choice = 1
        
        criteria = {}
        
        if search_choice == 2:  # Buscar por empresa
            company = input("Digite o nome da empresa: ").strip()
            if company:
                criteria['companies'] = [company]
        elif search_choice == 3:  # Buscar por tecnologia
            tech = input("Digite a tecnologia: ").strip()
            if tech:
                criteria['technologies'] = [tech]
        elif search_choice == 4:  # Buscar por localização
            location = input("Digite a localização: ").strip()
            if location:
                criteria['locations'] = [location]
        elif search_choice == 5:  # Estatísticas
            cache.print_compression_report()
            cache.index.print_summary()
            return
        elif search_choice == 6:  # Top empresas e tecnologias
            print("\n🏢 TOP 10 EMPRESAS:")
            top_companies = cache.get_top_companies(10)
            for i, (company, count) in enumerate(top_companies, 1):
                print(f"   {i:2d}. {company}: {count} vagas")
            
            print("\n💻 TOP 10 TECNOLOGIAS:")
            top_techs = cache.get_top_technologies(10)
            for i, (tech, count) in enumerate(top_techs, 1):
                print(f"   {i:2d}. {tech}: {count} vagas")
            return
        
        # Realizar busca
        results = cache.search_cache(criteria)
        
        print(f"\n📊 RESULTADOS DA BUSCA: {len(results)} entradas encontradas")
        print("=" * 60)
        
        for i, entry in enumerate(results[:10], 1):  # Mostrar apenas 10 primeiros
            print(f"\n{i:2d}. {entry.url[:60]}...")
            print(f"     📅 Data: {entry.timestamp.strftime('%Y-%m-%d %H:%M')}")
            print(f"     💼 Vagas: {entry.job_count}")
            print(f"     🏢 Empresas: {', '.join(entry.companies[:3])}{'...' if len(entry.companies) > 3 else ''}")
            print(f"     💻 Tecnologias: {', '.join(entry.technologies[:3])}{'...' if len(entry.technologies) > 3 else ''}")
            print(f"     📍 Localizações: {', '.join(entry.locations[:3])}{'...' if len(entry.locations) > 3 else ''}")
            print(f"     💾 Tamanho: {entry.file_size / 1024:.1f} KB → {entry.compressed_size / 1024:.1f} KB ({entry.compression_ratio:.1f}% compressão)")
        
        if len(results) > 10:
            print(f"\n... e mais {len(results) - 10} entradas")
        
        return
    
    elif mode_choice == 3:
        # Modo de limpeza de cache
        print("\n🗑️ LIMPEZA DE CACHE E CHECKPOINT:")
        print("⚠️  ATENÇÃO: Isso removerá todos os dados armazenados!")
        print("Tem certeza? (s/n): ", end="")
        
        confirm = input().strip().lower()
        if confirm in ['s', 'sim', 'y', 'yes']:
            import shutil
            
            # Remover diretórios de cache e checkpoint
            directories_to_clean = [
                "data/cache",
                "data/checkpoints"
            ]
            
            cleaned = 0
            for directory in directories_to_clean:
                if os.path.exists(directory):
                    try:
                        shutil.rmtree(directory)
                        print(f"✅ {directory} removido")
                        cleaned += 1
                    except Exception as e:
                        print(f"❌ Erro ao remover {directory}: {e}")
            
            if cleaned > 0:
                print(f"✅ Cache limpo! {cleaned} diretórios removidos")
                print("🔄 Agora o scraping processará todas as páginas do zero")
            else:
                print("ℹ️  Nenhum cache encontrado para limpar")
        else:
            print("❌ Limpeza cancelada")
            return
    
    elif mode_choice == 4:
        # Modo de limpeza de duplicatas
        print("\n🧹 LIMPEZA DE DUPLICATAS:")
        print("Esta operação irá:")
        print("  • Escanear todos os arquivos JSON em data/")
        print("  • Remover vagas duplicadas")
        print("  • Criar backup dos arquivos originais (.bak)")
        print("  • Exibir relatório detalhado")
        print("\nDeseja continuar? (s/n): ", end="")
        
        confirm = input().strip().lower()
        if confirm in ['s', 'sim', 'y', 'yes']:
            from src.deduplicator import JobDeduplicator
            
            deduplicator = JobDeduplicator()
            removed_count = deduplicator.clean_existing_files("data")
            
            if removed_count > 0:
                print(f"\n✅ Limpeza concluída: {removed_count} duplicatas removidas!")
                deduplicator.print_stats()
            else:
                print("ℹ️  Nenhuma duplicata encontrada ou nenhum arquivo para processar")
        else:
            print("❌ Limpeza cancelada")
        
        return
    
    # Configurar otimizações (apenas para novo scraping)
    print("\n⚡ OTIMIZAÇÕES DE PERFORMANCE:")
    print("Escolha a versão do scraper:")
    print("  1. Básica - Arquitetura modular (sem otimizações)")
    print("  2. Otimizada - Cache comprimido + Incremental (recomendado para dados novos)")
    print("  3. Máxima Performance - Pool de Conexões + Todas otimizações (mais rápido)")
    print("Opção (1-3, padrão: 3): ", end="")
    
    try:
        choice = input().strip() or "3"
        choice = int(choice)
        choice = max(1, min(3, choice))
    except:
        choice = 3
    
    # Executando o scraper
    print(f"\n{'='*60}")
    if choice == 1:
        print("INICIANDO COLETA COM ARQUITETURA MODULAR...")
        print(f"{'='*60}")
        jobs = await scrape_catho_jobs(max_concurrent_jobs=max_concurrent, max_pages=max_pages)
    elif choice == 2:
        print("INICIANDO COLETA OTIMIZADA (COMPRESSÃO + INCREMENTAL)...")
        print(f"{'='*60}")
        
        # Opção de forçar processamento completo
        print("⚡ MODO INCREMENTAL:")
        print("  1. Inteligente - Para quando encontra vagas conhecidas")
        print("  2. Forçado - Processa todas as páginas mesmo com vagas conhecidas")
        print("Opção (1-2, padrão: 1): ", end="")
        
        try:
            incremental_mode = int(input().strip() or "1")
            force_full = incremental_mode == 2
        except:
            force_full = False
        
        if force_full:
            print("🔄 Modo forçado ativado - processará todas as páginas")
        
        from src.scraper_optimized import scrape_catho_jobs_optimized
        jobs = await scrape_catho_jobs_optimized(
            max_concurrent_jobs=max_concurrent, 
            max_pages=max_pages,
            incremental=not force_full,  # Desabilita incremental se forçado
            show_compression_stats=True,
            enable_deduplication=True  # Deduplicação sempre ativada
        )
    else:  # choice == 3
        print("INICIANDO COLETA MÁXIMA PERFORMANCE (POOL + TODAS OTIMIZAÇÕES)...")
        print(f"{'='*60}")
        
        # Opção de forçar processamento completo
        print("⚡ MODO INCREMENTAL:")
        print("  1. Inteligente - Para quando encontra vagas conhecidas")
        print("  2. Forçado - Processa todas as páginas mesmo com vagas conhecidas")
        print("Opção (1-2, padrão: 1): ", end="")
        
        try:
            incremental_mode = int(input().strip() or "1")
            force_full = incremental_mode == 2
        except:
            force_full = False
        
        if force_full:
            print("🔄 Modo forçado ativado - processará todas as páginas")
        
        from src.scraper_pooled import scrape_catho_jobs_pooled
        jobs = await scrape_catho_jobs_pooled(
            max_concurrent_jobs=max_concurrent, 
            max_pages=max_pages,
            incremental=not force_full,  # Desabilita incremental se forçado
            show_compression_stats=True,
            show_pool_stats=True,
            pool_min_size=2,
            pool_max_size=max_concurrent + 2,
            enable_deduplication=True  # Deduplicação sempre ativada
        )
    
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