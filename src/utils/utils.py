import asyncio
import time
import os
import csv
import json
from datetime import datetime
from typing import Dict, List


class RateLimiter:
    """
    Sistema de rate limiting automático e adaptativo
    """
    def __init__(self, 
                 requests_per_second: float = 2.0,
                 burst_limit: int = 5,
                 adaptive: bool = True):
        self.requests_per_second = requests_per_second
        self.burst_limit = burst_limit
        self.adaptive = adaptive
        
        self.request_times = []
        self.consecutive_errors = 0
        self.base_delay = 1.0 / requests_per_second
        self.current_delay = self.base_delay
        
    async def acquire(self) -> None:
        """
        Aguarda permissão para fazer uma requisição
        """
        now = time.time()
        
        # Remove requisições antigas (últimos 60 segundos)
        self.request_times = [t for t in self.request_times if now - t < 60]
        
        # Verifica se excedeu o burst limit
        recent_requests = len([t for t in self.request_times if now - t < 1.0])
        
        if recent_requests >= self.burst_limit:
            wait_time = self.current_delay * (recent_requests - self.burst_limit + 1)
            print(f"⏳ Rate limiting: aguardando {wait_time:.2f}s...")
            await asyncio.sleep(wait_time)
        
        # Aplica delay adaptativo
        if self.adaptive and self.current_delay > self.base_delay:
            await asyncio.sleep(self.current_delay - self.base_delay)
        
        self.request_times.append(time.time())
    
    def report_success(self) -> None:
        """
        Reporta sucesso - reduz delay adaptativo
        """
        if self.adaptive and self.consecutive_errors > 0:
            self.consecutive_errors = max(0, self.consecutive_errors - 1)
            self.current_delay = max(
                self.base_delay,
                self.current_delay * 0.9  # Reduz delay gradualmente
            )
    
    def report_error(self) -> None:
        """
        Reporta erro - aumenta delay adaptativo
        """
        if self.adaptive:
            self.consecutive_errors += 1
            self.current_delay = min(
                10.0,  # Máximo de 10 segundos
                self.current_delay * (1.5 + self.consecutive_errors * 0.1)
            )
            print(f"⚠ Erro detectado. Ajustando delay para {self.current_delay:.2f}s")


class PerformanceMonitor:
    """
    Monitor de performance para otimização automática
    """
    def __init__(self):
        self.start_time = None
        self.processed_jobs = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self.cache_hits = 0
        self.cache_misses = 0
    
    def start_monitoring(self):
        """Inicia monitoramento"""
        self.start_time = time.time()
        print("📊 Monitoramento de performance iniciado")
    
    def record_job_processed(self):
        """Registra vaga processada"""
        self.processed_jobs += 1
    
    def record_request_success(self):
        """Registra requisição bem-sucedida"""
        self.successful_requests += 1
    
    def record_request_failure(self):
        """Registra falha de requisição"""
        self.failed_requests += 1
    
    def record_cache_hit(self):
        """Registra acerto de cache"""
        self.cache_hits += 1
    
    def record_cache_miss(self):
        """Registra perda de cache"""
        self.cache_misses += 1
    
    def get_stats(self) -> Dict:
        """Retorna estatísticas de performance"""
        if not self.start_time:
            return {}
        
        elapsed_time = time.time() - self.start_time
        total_requests = self.successful_requests + self.failed_requests
        
        return {
            'tempo_execucao': f"{elapsed_time:.2f}s",
            'vagas_processadas': self.processed_jobs,
            'vagas_por_segundo': f"{self.processed_jobs / elapsed_time:.2f}" if elapsed_time > 0 else "0",
            'requisicoes_totais': total_requests,
            'taxa_sucesso': f"{(self.successful_requests / total_requests * 100):.1f}%" if total_requests > 0 else "0%",
            'cache_hits': self.cache_hits,
            'cache_misses': self.cache_misses,
            'taxa_cache': f"{(self.cache_hits / (self.cache_hits + self.cache_misses) * 100):.1f}%" if (self.cache_hits + self.cache_misses) > 0 else "0%"
        }
    
    def print_stats(self):
        """Imprime estatísticas formatadas"""
        stats = self.get_stats()
        if stats:
            print(f"\n📊 ESTATÍSTICAS DE PERFORMANCE:")
            print(f"   ⏱️  Tempo de execução: {stats['tempo_execucao']}")
            print(f"   📋 Vagas processadas: {stats['vagas_processadas']}")
            print(f"   ⚡ Vagas/segundo: {stats['vagas_por_segundo']}")
            print(f"   🌐 Requisições totais: {stats['requisicoes_totais']}")
            print(f"   ✅ Taxa de sucesso: {stats['taxa_sucesso']}")
            print(f"   💾 Cache hits: {stats['cache_hits']}")
            print(f"   ❌ Cache misses: {stats['cache_misses']}")
            print(f"   📈 Eficiência do cache: {stats['taxa_cache']}")


class FileManager:
    """
    Gerenciador inteligente de arquivos - evita spam e organiza resultados
    """
    def __init__(self, results_dir: str = "data/resultados"):
        self.results_dir = results_dir
        self.max_files_per_type = 5  # Manter apenas os 5 mais recentes de cada tipo
        
        # Criar diretório se não existir
        os.makedirs(results_dir, exist_ok=True)
        
        # Subdiretórios organizados
        self.subdirs = {
            'json': os.path.join(results_dir, 'json'),
            'txt': os.path.join(results_dir, 'txt'), 
            'csv': os.path.join(results_dir, 'csv'),
            'relatorios': os.path.join(results_dir, 'relatorios')
        }
        
        for subdir in self.subdirs.values():
            os.makedirs(subdir, exist_ok=True)
    
    def cleanup_old_files(self, file_pattern: str, max_files: int = 5):
        """Remove arquivos antigos mantendo apenas os mais recentes"""
        try:
            import glob
            files = glob.glob(file_pattern)
            if len(files) > max_files:
                # Ordenar por data de modificação (mais antigos primeiro)
                files.sort(key=os.path.getmtime)
                files_to_remove = files[:-max_files]
                
                for file_path in files_to_remove:
                    os.remove(file_path)
                    print(f"🗑️ Arquivo antigo removido: {os.path.basename(file_path)}")
        except Exception as e:
            pass  # Silencioso para não poluir logs
    
    def get_latest_filename(self, base_name: str, extension: str, subdir: str) -> str:
        """Gera nome de arquivo inteligente - sobrescreve se for do mesmo dia"""
        today = datetime.now().strftime("%Y%m%d")
        
        # Verificar se já existe arquivo de hoje
        existing_pattern = os.path.join(self.subdirs[subdir], f"{base_name}_{today}*{extension}")
        
        try:
            import glob
            existing_files = glob.glob(existing_pattern)
            if existing_files:
                # Usar o arquivo existente de hoje (sobrescrever)
                return existing_files[0]
        except:
            pass
        
        # Criar novo arquivo com timestamp completo apenas se necessário
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        return os.path.join(self.subdirs[subdir], f"{base_name}_{timestamp}{extension}")


def save_results(jobs, filters_applied=None, ask_user_preference=True):
    """
    Salva os resultados de forma organizada e inteligente
    """
    if not jobs:
        print("Nenhuma vaga para salvar")
        return
    
    # Filtrar apenas dados válidos se houver validação
    valid_jobs = []
    invalid_jobs = []
    
    for job in jobs:
        if '_validation' in job:
            if job['_validation']['is_valid']:
                # Remover metadados de validação antes de salvar
                clean_job = {k: v for k, v in job.items() if k != '_validation'}
                valid_jobs.append(clean_job)
            else:
                invalid_jobs.append(job)
        else:
            # Dados não validados, incluir mesmo assim
            valid_jobs.append(job)
    
    if invalid_jobs:
        print(f"⚠️  {len(invalid_jobs)} vagas com dados inválidos foram filtradas")
    
    # Usar apenas vagas válidas
    jobs = valid_jobs
    
    if not jobs:
        print("⚠ Nenhuma vaga válida encontrada para salvar")
        return
    
    print(f"💾 Salvando {len(jobs)} vagas válidas...")
    
    # Perguntar preferência do usuário
    if ask_user_preference:
        print("\n💾 OPÇÕES DE SALVAMENTO:")
        print("1. Arquivo único (sobrescreve arquivo do dia)")
        print("2. Arquivo com timestamp (mantém histórico)")
        print("3. Não salvar arquivos (apenas exibir no terminal)")
        
        choice = input("Escolha uma opção (1-3, padrão: 1): ").strip() or "1"
        
        if choice == "3":
            print("✓ Resultados não salvos em arquivo")
            return
        
        use_timestamp = choice == "2"
    else:
        use_timestamp = False
    
    file_manager = FileManager()
    
    if use_timestamp:
        # Modo com timestamp (histórico completo)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        json_filename = os.path.join(file_manager.subdirs['json'], f"vagas_catho_{timestamp}.json")
        txt_filename = os.path.join(file_manager.subdirs['txt'], f"vagas_catho_{timestamp}.txt")
        csv_filename = os.path.join(file_manager.subdirs['csv'], f"vagas_catho_{timestamp}.csv")
        stats_filename = os.path.join(file_manager.subdirs['relatorios'], f"analise_{timestamp}.txt")
    else:
        # Modo arquivo único (sobrescreve arquivo do dia)
        json_filename = file_manager.get_latest_filename("vagas_catho", ".json", "json")
        txt_filename = file_manager.get_latest_filename("vagas_catho", ".txt", "txt")
        csv_filename = file_manager.get_latest_filename("vagas_catho", ".csv", "csv") 
        stats_filename = file_manager.get_latest_filename("analise_completa", ".txt", "relatorios")
    
    # Salvar JSON
    with open(json_filename, 'w', encoding='utf-8') as f:
        json.dump(jobs, f, ensure_ascii=False, indent=2)
    print(f"\n✓ Salvo: {os.path.relpath(json_filename)}")
    
    # Salvar TXT formatado de forma limpa e organizada
    with open(txt_filename, 'w', encoding='utf-8') as f:
        # Cabeçalho limpo
        f.write("VAGAS DE EMPREGO HOME OFFICE - CATHO\n")
        f.write("=" * 50 + "\n")
        f.write(f"Data da coleta: {datetime.now().strftime('%d/%m/%Y às %H:%M')}\n")
        f.write(f"Total de vagas: {len(jobs)}\n")
        
        if filters_applied:
            f.write(f"\nFiltros aplicados: {', '.join(f'{k}: {v}' for k, v in filters_applied.items())}\n")
        
        f.write("\n" + "=" * 50 + "\n\n")
        
        # Lista das vagas de forma mais limpa
        for i, job in enumerate(jobs, 1):
            # Cabeçalho da vaga mais simples
            f.write(f"{i:2d}. {job['titulo']}\n")
            f.write("-" * (len(f"{i:2d}. {job['titulo']}")) + "\n")
            
            # Informações organizadas em tabela simples
            empresa = job.get('empresa', 'Não informada')
            localizacao = job.get('localizacao', 'Não informada')
            salario = job.get('salario', 'Não informado')
            nivel = job.get('nivel_categorizado', 'Não especificado').replace('_', ' ').title()
            
            f.write(f"Empresa:     {empresa}\n")
            f.write(f"Local:       {localizacao}\n")
            f.write(f"Salário:     {salario}\n")
            f.write(f"Nível:       {nivel}\n")
            
            # Tecnologias em uma linha
            if job.get('tecnologias_detectadas'):
                techs = ', '.join(job['tecnologias_detectadas'])
                f.write(f"Tecnologias: {techs}\n")
            
            # Link
            f.write(f"Link:        {job['link']}\n")
            
            # Separador entre vagas
            f.write("\n" + "." * 50 + "\n\n")
        
        # Resumo estatístico no final
        f.write("RESUMO ESTATÍSTICO\n")
        f.write("=" * 50 + "\n\n")
        
        # Tecnologias mais usadas
        all_techs = {}
        for job in jobs:
            for tech in job.get('tecnologias_detectadas', []):
                all_techs[tech] = all_techs.get(tech, 0) + 1
        
        if all_techs:
            f.write("Tecnologias mais demandadas:\n")
            for tech, count in sorted(all_techs.items(), key=lambda x: x[1], reverse=True)[:10]:
                f.write(f"  {tech}: {count} vagas\n")
            f.write("\n")
        
        # Empresas com mais vagas
        empresas = {}
        for job in jobs:
            empresa = job.get('empresa', 'Não informada')
            if empresa != 'Não informada':
                empresas[empresa] = empresas.get(empresa, 0) + 1
        
        if empresas:
            f.write("Empresas com mais vagas:\n")
            for empresa, count in sorted(empresas.items(), key=lambda x: x[1], reverse=True)[:10]:
                f.write(f"  {empresa}: {count} vagas\n")
            f.write("\n")
        
        # Distribuição por nível
        niveis = {}
        for job in jobs:
            nivel = job.get('nivel_categorizado', 'Não especificado').replace('_', ' ').title()
            niveis[nivel] = niveis.get(nivel, 0) + 1
        
        f.write("Distribuição por nível:\n")
        for nivel, count in sorted(niveis.items(), key=lambda x: x[1], reverse=True):
            f.write(f"  {nivel}: {count} vagas\n")
    
    print(f"✓ Salvo: {os.path.relpath(txt_filename)}")
    
    # Salvar CSV limpo e organizado
    try:
        # Preparar dados limpos para CSV
        csv_data = []
        for job in jobs:
            # Limpar e organizar dados
            clean_row = {
                'Titulo': job.get('titulo', '').strip(),
                'Empresa': job.get('empresa', 'Não informada').strip(),
                'Localizacao': job.get('localizacao', 'Não informada').strip(),
                'Salario': job.get('salario', 'Não informado').strip(),
                'Salario_Min': job.get('faixa_salarial', {}).get('min', '') if job.get('faixa_salarial') else '',
                'Salario_Max': job.get('faixa_salarial', {}).get('max', '') if job.get('faixa_salarial') else '',
                'Nivel_Experiencia': job.get('nivel_categorizado', 'Não especificado').replace('_', ' ').title(),
                'Tipo_Empresa': job.get('tipo_empresa', 'Não categorizado').replace('_', ' ').title(),
                'Modalidade': job.get('modalidade', 'Não especificada').strip(),
                'Data_Publicacao': job.get('data_publicacao', 'Não informada').strip(),
                'Tecnologias': ', '.join(job.get('tecnologias_detectadas', [])),
                'Tem_Beneficios': 'Sim' if job.get('beneficios') and job.get('beneficios') != 'Não informados' else 'Não',
                'Link': job.get('link', '').strip()
            }
            
            # Adicionar apenas campos úteis para análise
            csv_data.append(clean_row)
        
        # Salvar CSV com cabeçalhos em português
        with open(csv_filename, 'w', newline='', encoding='utf-8-sig') as f:  # BOM para Excel
            if csv_data:
                fieldnames = [
                    'Titulo', 'Empresa', 'Localizacao', 'Salario', 
                    'Salario_Min', 'Salario_Max', 'Nivel_Experiencia', 
                    'Tipo_Empresa', 'Modalidade', 'Data_Publicacao', 
                    'Tecnologias', 'Tem_Beneficios', 'Link'
                ]
                
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(csv_data)
        
        print(f"✓ Salvo: {os.path.relpath(csv_filename)} (otimizado para Excel)")
    except Exception as e:
        print(f"⚠ Erro ao salvar CSV: {e}")
    
    # Salvar relatório estatístico simplificado
    with open(stats_filename, 'w', encoding='utf-8') as f:
        f.write("RELATÓRIO DE ANÁLISE - VAGAS HOME OFFICE\n")
        f.write("=" * 45 + "\n")
        f.write(f"Data: {datetime.now().strftime('%d/%m/%Y às %H:%M')}\n")
        f.write(f"Total de vagas: {len(jobs)}\n\n")
        
        if filters_applied:
            f.write("Filtros aplicados:\n")
            for key, value in filters_applied.items():
                f.write(f"  • {key}: {', '.join(value) if isinstance(value, list) else value}\n")
            f.write("\n")
        
        # Análise de tecnologias
        all_techs = {}
        for job in jobs:
            for tech in job.get('tecnologias_detectadas', []):
                all_techs[tech] = all_techs.get(tech, 0) + 1
        
        if all_techs:
            f.write("TECNOLOGIAS MAIS DEMANDADAS\n")
            f.write("-" * 30 + "\n")
            for tech, count in sorted(all_techs.items(), key=lambda x: x[1], reverse=True)[:10]:
                percentage = (count / len(jobs)) * 100
                f.write(f"{tech:<15} {count:>3} vagas ({percentage:>4.1f}%)\n")
            f.write("\n")
        
        # Análise salarial
        salaries = []
        for job in jobs:
            if job.get('faixa_salarial') and job['faixa_salarial'].get('min'):
                salaries.append(job['faixa_salarial']['min'])
        
        if salaries:
            f.write("ANÁLISE SALARIAL\n")
            f.write("-" * 15 + "\n")
            f.write(f"Menor salário:    R$ {min(salaries):>8,.2f}\n")
            f.write(f"Maior salário:    R$ {max(salaries):>8,.2f}\n")
            f.write(f"Salário médio:    R$ {sum(salaries)/len(salaries):>8,.2f}\n")
            f.write(f"Com salário info: {len(salaries):>3} de {len(jobs)} vagas ({(len(salaries)/len(jobs)*100):>4.1f}%)\n\n")
        
        # Top empresas
        empresas = {}
        for job in jobs:
            empresa = job.get('empresa', 'Não informada')
            if empresa != 'Não informada':
                empresas[empresa] = empresas.get(empresa, 0) + 1
        
        if empresas:
            f.write("EMPRESAS COM MAIS VAGAS\n")
            f.write("-" * 23 + "\n")
            for empresa, count in sorted(empresas.items(), key=lambda x: x[1], reverse=True)[:8]:
                f.write(f"{empresa:<25} {count:>2} vagas\n")
            f.write("\n")
        
        # Distribuições
        nivel_counts = {}
        tipo_counts = {}
        
        for job in jobs:
            nivel = job.get('nivel_categorizado', 'Não especificado').replace('_', ' ').title()
            nivel_counts[nivel] = nivel_counts.get(nivel, 0) + 1
            
            tipo = job.get('tipo_empresa', 'Não categorizado').replace('_', ' ').title()
            tipo_counts[tipo] = tipo_counts.get(tipo, 0) + 1
        
        f.write("DISTRIBUIÇÃO POR NÍVEL\n")
        f.write("-" * 21 + "\n")
        for nivel, count in sorted(nivel_counts.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / len(jobs)) * 100
            f.write(f"{nivel:<20} {count:>3} vagas ({percentage:>4.1f}%)\n")
        f.write("\n")
        
        f.write("TIPOS DE EMPRESA\n")
        f.write("-" * 16 + "\n")
        for tipo, count in sorted(tipo_counts.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / len(jobs)) * 100
            f.write(f"{tipo:<20} {count:>3} vagas ({percentage:>4.1f}%)\n")
    
    print(f"✓ Salvo: {os.path.relpath(stats_filename)}")
    
    # Limpeza automática de arquivos antigos (se usando timestamp)
    if use_timestamp:
        file_manager.cleanup_old_files(
            os.path.join(file_manager.subdirs['json'], "vagas_catho_*.json"), 5
        )
        file_manager.cleanup_old_files(
            os.path.join(file_manager.subdirs['txt'], "vagas_catho_*.txt"), 5
        )
        file_manager.cleanup_old_files(
            os.path.join(file_manager.subdirs['csv'], "vagas_catho_*.csv"), 5
        )
        file_manager.cleanup_old_files(
            os.path.join(file_manager.subdirs['relatorios'], "analise_*.txt"), 5
        )
    
    print(f"\n📁 Arquivos organizados no diretório: {file_manager.results_dir}/")
    print(f"   📄 {len(jobs)} vagas salvas em 3 formatos + relatório de análise")