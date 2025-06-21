"""
Sistema de Machine Learning para Otimização de URLs

Este módulo implementa aprendizado automático para identificar
as URLs mais produtivas e otimizar o processo de scraping.
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from collections import defaultdict
import numpy as np
from pathlib import Path


class URLOptimizer:
    """
    Otimizador inteligente de URLs usando Machine Learning
    
    Funcionalidades:
    - Tracking de performance por URL
    - Identificação de padrões temporais
    - Score automático de produtividade
    - Recomendações de otimização
    """
    
    def __init__(self, history_file: str = "data/ml/url_performance_history.json"):
        self.history_file = history_file
        self.history_dir = os.path.dirname(history_file)
        
        # Criar diretório se não existir
        os.makedirs(self.history_dir, exist_ok=True)
        
        # Carregar histórico
        self.performance_data = self._load_history()
        
        # Métricas para análise
        self.metrics = {
            "new_jobs_count": 1.0,      # Peso para quantidade de vagas novas
            "unique_jobs_ratio": 0.8,    # Peso para taxa de vagas únicas
            "diversity_score": 0.6,      # Peso para diversidade
            "time_efficiency": 0.4,      # Peso para eficiência temporal
            "error_rate": -1.0          # Peso negativo para taxa de erro
        }
    
    def _load_history(self) -> Dict:
        """Carrega histórico de performance"""
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        
        return {
            "urls": {},
            "sessions": [],
            "patterns": {},
            "last_optimization": None
        }
    
    def _save_history(self):
        """Salva histórico de performance"""
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self.performance_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Erro ao salvar histórico ML: {e}")
    
    def record_url_performance(self, url: str, metrics: Dict):
        """
        Registra performance de uma URL
        
        Args:
            url: URL processada
            metrics: Métricas coletadas {
                'new_jobs': int,
                'total_jobs': int,
                'processing_time': float,
                'errors': int,
                'diversity_contribution': float
            }
        """
        if url not in self.performance_data["urls"]:
            self.performance_data["urls"][url] = {
                "total_runs": 0,
                "total_new_jobs": 0,
                "total_jobs_seen": 0,
                "total_time": 0,
                "total_errors": 0,
                "hourly_performance": {},
                "daily_performance": {},
                "last_run": None,
                "performance_score": 0.5
            }
        
        url_data = self.performance_data["urls"][url]
        
        # Atualizar métricas totais
        url_data["total_runs"] += 1
        url_data["total_new_jobs"] += metrics.get("new_jobs", 0)
        url_data["total_jobs_seen"] += metrics.get("total_jobs", 0)
        url_data["total_time"] += metrics.get("processing_time", 0)
        url_data["total_errors"] += metrics.get("errors", 0)
        url_data["last_run"] = datetime.now().isoformat()
        
        # Registrar performance por hora
        hour = datetime.now().hour
        if str(hour) not in url_data["hourly_performance"]:
            url_data["hourly_performance"][str(hour)] = {
                "runs": 0,
                "new_jobs": 0,
                "avg_new_jobs": 0
            }
        
        hourly = url_data["hourly_performance"][str(hour)]
        hourly["runs"] += 1
        hourly["new_jobs"] += metrics.get("new_jobs", 0)
        hourly["avg_new_jobs"] = hourly["new_jobs"] / hourly["runs"]
        
        # Registrar performance por dia da semana
        weekday = datetime.now().strftime("%A")
        if weekday not in url_data["daily_performance"]:
            url_data["daily_performance"][weekday] = {
                "runs": 0,
                "new_jobs": 0,
                "avg_new_jobs": 0
            }
        
        daily = url_data["daily_performance"][weekday]
        daily["runs"] += 1
        daily["new_jobs"] += metrics.get("new_jobs", 0)
        daily["avg_new_jobs"] = daily["new_jobs"] / daily["runs"]
        
        # Calcular score de performance
        url_data["performance_score"] = self._calculate_url_score(url_data)
        
        self._save_history()
    
    def _calculate_url_score(self, url_data: Dict) -> float:
        """Calcula score de performance de uma URL (0-1)"""
        if url_data["total_runs"] == 0:
            return 0.5
        
        # Métricas normalizadas
        avg_new_jobs = url_data["total_new_jobs"] / url_data["total_runs"]
        unique_ratio = url_data["total_new_jobs"] / max(url_data["total_jobs_seen"], 1)
        avg_time = url_data["total_time"] / url_data["total_runs"]
        error_rate = url_data["total_errors"] / url_data["total_runs"]
        
        # Normalizar métricas (0-1)
        normalized_new_jobs = min(avg_new_jobs / 50, 1.0)  # Assumindo máx 50 vagas novas
        normalized_unique = unique_ratio
        normalized_time = 1.0 - min(avg_time / 60, 1.0)  # Assumindo máx 60 segundos
        normalized_errors = 1.0 - min(error_rate, 1.0)
        
        # Calcular score ponderado
        score = (
            normalized_new_jobs * 0.4 +
            normalized_unique * 0.3 +
            normalized_time * 0.2 +
            normalized_errors * 0.1
        )
        
        return round(min(max(score, 0), 1), 3)
    
    def get_optimized_urls(self, num_urls: int, current_hour: Optional[int] = None) -> List[str]:
        """
        Retorna URLs otimizadas baseado em performance histórica
        
        Args:
            num_urls: Número de URLs desejadas
            current_hour: Hora atual (para otimização temporal)
            
        Returns:
            Lista de URLs ordenadas por performance
        """
        if not self.performance_data["urls"]:
            # Sem dados históricos, retornar URLs padrão
            from ..utils.settings_manager import settings_manager
            return settings_manager.get_active_urls()[:num_urls]
        
        # Calcular scores considerando hora do dia
        url_scores = []
        current_hour = current_hour or datetime.now().hour
        
        for url, data in self.performance_data["urls"].items():
            base_score = data["performance_score"]
            
            # Bonus por performance na hora atual
            hourly_bonus = 0
            if str(current_hour) in data["hourly_performance"]:
                hourly_data = data["hourly_performance"][str(current_hour)]
                if hourly_data["runs"] > 0:
                    hourly_avg = hourly_data["avg_new_jobs"]
                    overall_avg = data["total_new_jobs"] / max(data["total_runs"], 1)
                    if hourly_avg > overall_avg:
                        hourly_bonus = 0.2 * (hourly_avg / max(overall_avg, 1) - 1)
            
            # Penalidade por não rodar recentemente
            recency_penalty = 0
            if data["last_run"]:
                last_run = datetime.fromisoformat(data["last_run"])
                days_since = (datetime.now() - last_run).days
                if days_since > 7:
                    recency_penalty = 0.1 * min(days_since / 30, 1)
            
            final_score = base_score + hourly_bonus - recency_penalty
            url_scores.append((url, final_score))
        
        # Ordenar por score e retornar top N
        url_scores.sort(key=lambda x: x[1], reverse=True)
        return [url for url, score in url_scores[:num_urls]]
    
    def get_best_hours_for_url(self, url: str) -> List[int]:
        """Retorna melhores horários para uma URL específica"""
        if url not in self.performance_data["urls"]:
            return list(range(8, 18))  # Horário comercial padrão
        
        url_data = self.performance_data["urls"][url]
        hourly_perf = url_data["hourly_performance"]
        
        if not hourly_perf:
            return list(range(8, 18))
        
        # Ordenar horas por performance
        hour_scores = []
        for hour, data in hourly_perf.items():
            if data["runs"] > 0:
                score = data["avg_new_jobs"]
                hour_scores.append((int(hour), score))
        
        hour_scores.sort(key=lambda x: x[1], reverse=True)
        return [hour for hour, score in hour_scores[:5]]
    
    def get_optimization_insights(self) -> Dict:
        """Gera insights de otimização baseados nos dados"""
        insights = {
            "best_urls": [],
            "worst_urls": [],
            "best_hours": [],
            "best_days": [],
            "recommendations": []
        }
        
        if not self.performance_data["urls"]:
            insights["recommendations"].append("Colete mais dados para gerar insights")
            return insights
        
        # Top 5 melhores URLs
        url_scores = [(url, data["performance_score"]) 
                      for url, data in self.performance_data["urls"].items()]
        url_scores.sort(key=lambda x: x[1], reverse=True)
        
        insights["best_urls"] = [
            {"url": url, "score": score} 
            for url, score in url_scores[:5]
        ]
        
        insights["worst_urls"] = [
            {"url": url, "score": score} 
            for url, score in url_scores[-3:] if score < 0.3
        ]
        
        # Melhores horários globais
        hourly_totals = defaultdict(lambda: {"runs": 0, "new_jobs": 0})
        for url_data in self.performance_data["urls"].values():
            for hour, data in url_data["hourly_performance"].items():
                hourly_totals[int(hour)]["runs"] += data["runs"]
                hourly_totals[int(hour)]["new_jobs"] += data["new_jobs"]
        
        hour_avgs = []
        for hour, totals in hourly_totals.items():
            if totals["runs"] > 0:
                avg = totals["new_jobs"] / totals["runs"]
                hour_avgs.append((hour, avg))
        
        hour_avgs.sort(key=lambda x: x[1], reverse=True)
        insights["best_hours"] = [hour for hour, avg in hour_avgs[:5]]
        
        # Recomendações
        if insights["worst_urls"]:
            insights["recommendations"].append(
                f"Considere remover {len(insights['worst_urls'])} URLs com baixa performance"
            )
        
        if insights["best_hours"]:
            best_hour = insights["best_hours"][0]
            insights["recommendations"].append(
                f"Execute scraping preferencialmente às {best_hour}h"
            )
        
        # Detectar URLs que não rodam há muito tempo
        stale_urls = []
        for url, data in self.performance_data["urls"].items():
            if data["last_run"]:
                last_run = datetime.fromisoformat(data["last_run"])
                if (datetime.now() - last_run).days > 14:
                    stale_urls.append(url)
        
        if stale_urls:
            insights["recommendations"].append(
                f"{len(stale_urls)} URLs não são executadas há mais de 14 dias"
            )
        
        return insights
    
    def auto_optimize_settings(self, settings_manager) -> Dict:
        """
        Otimiza automaticamente as configurações baseado em aprendizado
        
        Returns:
            Dicionário com configurações otimizadas
        """
        optimization = {
            "urls": [],
            "best_hour": None,
            "urls_per_session": 3,
            "changes_made": []
        }
        
        # Obter URLs otimizadas
        num_urls = settings_manager.settings.scraping.urls_per_session
        optimization["urls"] = self.get_optimized_urls(num_urls)
        
        # Determinar melhor horário
        insights = self.get_optimization_insights()
        if insights["best_hours"]:
            optimization["best_hour"] = insights["best_hours"][0]
            optimization["changes_made"].append(
                f"Melhor horário identificado: {optimization['best_hour']}h"
            )
        
        # Ajustar número de URLs baseado em performance
        if len(self.performance_data["urls"]) > 10:
            high_performers = [
                url for url, data in self.performance_data["urls"].items()
                if data["performance_score"] > 0.7
            ]
            
            if len(high_performers) >= 5:
                optimization["urls_per_session"] = min(len(high_performers), 8)
                optimization["changes_made"].append(
                    f"URLs por sessão ajustado para {optimization['urls_per_session']}"
                )
        
        return optimization
    
    def print_performance_report(self):
        """Imprime relatório visual de performance"""
        from ..utils.menu_system import Colors
        
        print(f"\n{Colors.CYAN}📊 RELATÓRIO DE PERFORMANCE DE URLs (ML){Colors.RESET}")
        print("=" * 70)
        
        if not self.performance_data["urls"]:
            print(f"{Colors.YELLOW}⚠️ Sem dados históricos ainda. Execute alguns scrapings primeiro.{Colors.RESET}")
            return
        
        # Top performers
        url_scores = [(url, data["performance_score"], data["total_new_jobs"], data["total_runs"]) 
                      for url, data in self.performance_data["urls"].items()]
        url_scores.sort(key=lambda x: x[1], reverse=True)
        
        print(f"\n{Colors.GREEN}🏆 TOP 5 URLs MAIS PRODUTIVAS:{Colors.RESET}")
        for i, (url, score, new_jobs, runs) in enumerate(url_scores[:5], 1):
            # Extrair nome da URL
            url_name = url.split("/")[-2] if url.endswith("/") else url.split("/")[-1]
            avg_jobs = new_jobs / max(runs, 1)
            
            # Barra de performance
            bar_size = int(score * 20)
            bar = "█" * bar_size + "░" * (20 - bar_size)
            
            print(f"{i}. {url_name:<25} [{bar}] {score:.2f}")
            print(f"   {Colors.DIM}Média: {avg_jobs:.1f} vagas/run | Total runs: {runs}{Colors.RESET}")
        
        # Insights
        insights = self.get_optimization_insights()
        
        if insights["best_hours"]:
            print(f"\n{Colors.YELLOW}⏰ MELHORES HORÁRIOS:{Colors.RESET}")
            hours_str = ", ".join([f"{h}h" for h in insights["best_hours"][:3]])
            print(f"  {hours_str}")
        
        if insights["recommendations"]:
            print(f"\n{Colors.CYAN}💡 RECOMENDAÇÕES:{Colors.RESET}")
            for rec in insights["recommendations"]:
                print(f"  • {rec}")
        
        print("\n" + "=" * 70)


# Instância global do otimizador
url_optimizer = URLOptimizer()