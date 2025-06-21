"""
Sistema de Auto-Ajuste de Configurações

Este módulo usa Machine Learning para otimizar automaticamente
as configurações do sistema baseado em performance histórica.
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any
from .url_optimizer import url_optimizer
from .temporal_analyzer import temporal_analyzer


class AutoTuner:
    """
    Sistema de auto-ajuste baseado em Machine Learning
    
    Funcionalidades:
    - Otimização automática de configurações
    - Ajuste de parâmetros baseado em performance
    - Recomendações de melhorias
    - Backup de configurações anteriores
    """
    
    def __init__(self, tuning_file: str = "data/ml/auto_tuning_history.json"):
        self.tuning_file = tuning_file
        self.tuning_dir = os.path.dirname(tuning_file)
        
        # Criar diretório se não existir
        os.makedirs(self.tuning_dir, exist_ok=True)
        
        # Carregar histórico de ajustes
        self.tuning_history = self._load_tuning_history()
        
        # Configurações que podem ser otimizadas
        self.tunable_params = {
            "urls_per_session": {
                "min": 2,
                "max": 8,
                "type": "int",
                "impact": "high"
            },
            "max_pages": {
                "min": 2,
                "max": 10,
                "type": "int", 
                "impact": "medium"
            },
            "requests_per_second": {
                "min": 0.5,
                "max": 3.0,
                "type": "float",
                "impact": "medium"
            },
            "diversity_mode": {
                "options": ["balanced", "geographic", "professional", "seniority", "complete"],
                "type": "choice",
                "impact": "high"
            }
        }
    
    def _load_tuning_history(self) -> Dict:
        """Carrega histórico de ajustes"""
        if os.path.exists(self.tuning_file):
            try:
                with open(self.tuning_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        
        return {
            "adjustments": [],
            "performance_baseline": None,
            "best_configuration": None,
            "last_tuning": None
        }
    
    def _save_tuning_history(self):
        """Salva histórico de ajustes"""
        try:
            with open(self.tuning_file, 'w', encoding='utf-8') as f:
                json.dump(self.tuning_history, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Erro ao salvar histórico de ajustes: {e}")
    
    def analyze_current_performance(self) -> Dict:
        """Analisa performance atual do sistema"""
        performance = {
            "url_efficiency": 0,
            "temporal_optimization": 0,
            "diversity_score": 0,
            "overall_score": 0,
            "bottlenecks": [],
            "strengths": []
        }
        
        # Analisar eficiência de URLs
        if url_optimizer.performance_data["urls"]:
            url_scores = [data["performance_score"] 
                         for data in url_optimizer.performance_data["urls"].values()]
            performance["url_efficiency"] = sum(url_scores) / len(url_scores)
            
            if performance["url_efficiency"] < 0.3:
                performance["bottlenecks"].append("URLs com baixa performance")
            elif performance["url_efficiency"] > 0.7:
                performance["strengths"].append("URLs bem otimizadas")
        
        # Analisar otimização temporal
        temporal_insights = temporal_analyzer.get_temporal_insights()
        if temporal_insights["best_hours"]:
            # Se temos dados de horários, consideramos otimizado
            performance["temporal_optimization"] = 0.8
            performance["strengths"].append("Padrões temporais identificados")
        else:
            performance["temporal_optimization"] = 0.2
            performance["bottlenecks"].append("Poucos dados temporais")
        
        # Score geral
        performance["overall_score"] = (
            performance["url_efficiency"] * 0.5 +
            performance["temporal_optimization"] * 0.3 +
            performance["diversity_score"] * 0.2
        )
        
        return performance
    
    def suggest_optimizations(self, settings_manager) -> Dict:
        """Sugere otimizações baseadas em análise ML"""
        suggestions = {
            "urgent": [],
            "recommended": [],
            "optional": [],
            "configuration_changes": {}
        }
        
        # Analisar performance atual
        performance = self.analyze_current_performance()
        current_settings = settings_manager.settings.scraping
        
        # Otimizações baseadas em URLs
        url_insights = url_optimizer.get_optimization_insights()
        
        if url_insights["worst_urls"]:
            suggestions["urgent"].append({
                "action": "remove_low_performance_urls",
                "description": f"Remover {len(url_insights['worst_urls'])} URLs com baixa performance",
                "impact": "high",
                "implementation": "automatic"
            })
        
        # Otimizações baseadas em padrões temporais
        temporal_insights = temporal_analyzer.get_temporal_insights()
        
        if temporal_insights["best_hours"]:
            best_hour = temporal_insights["best_hours"][0]["hour"]
            suggestions["recommended"].append({
                "action": "schedule_optimization",
                "description": f"Agendar execuções para às {best_hour}h",
                "impact": "medium",
                "implementation": "manual"
            })
        
        # Ajustar número de URLs por sessão
        if performance["url_efficiency"] > 0.7:
            # Performance boa, pode aumentar URLs
            if current_settings.urls_per_session < 6:
                suggestions["configuration_changes"]["urls_per_session"] = min(
                    current_settings.urls_per_session + 1, 6
                )
                suggestions["recommended"].append({
                    "action": "increase_urls_per_session",
                    "description": "Aumentar URLs por sessão para aproveitar boa performance",
                    "impact": "medium"
                })
        elif performance["url_efficiency"] < 0.3:
            # Performance ruim, reduzir URLs
            if current_settings.urls_per_session > 3:
                suggestions["configuration_changes"]["urls_per_session"] = max(
                    current_settings.urls_per_session - 1, 3
                )
                suggestions["urgent"].append({
                    "action": "decrease_urls_per_session", 
                    "description": "Reduzir URLs por sessão para melhorar qualidade",
                    "impact": "high"
                })
        
        # Sugerir mudança de modo de diversidade
        if performance["diversity_score"] < 0.5:
            if current_settings.diversity_mode != "complete":
                suggestions["configuration_changes"]["diversity_mode"] = "complete"
                suggestions["recommended"].append({
                    "action": "switch_to_complete_mode",
                    "description": "Mudar para modo 'complete' para máxima diversidade",
                    "impact": "high"
                })
        
        return suggestions
    
    def auto_apply_optimizations(self, settings_manager, apply_urgent: bool = True, apply_recommended: bool = False) -> Dict:
        """
        Aplica otimizações automaticamente
        
        Args:
            settings_manager: Gerenciador de configurações
            apply_urgent: Se deve aplicar correções urgentes
            apply_recommended: Se deve aplicar recomendações
            
        Returns:
            Relatório das mudanças aplicadas
        """
        suggestions = self.suggest_optimizations(settings_manager)
        applied_changes = {
            "timestamp": datetime.now().isoformat(),
            "changes": [],
            "backup_created": False
        }
        
        # Criar backup das configurações atuais
        try:
            settings_manager._create_backup()
            applied_changes["backup_created"] = True
        except:
            pass
        
        # Aplicar mudanças urgentes
        if apply_urgent:
            for change in suggestions["urgent"]:
                try:
                    if change["action"] == "decrease_urls_per_session":
                        old_value = settings_manager.settings.scraping.urls_per_session
                        new_value = suggestions["configuration_changes"]["urls_per_session"]
                        settings_manager.settings.scraping.urls_per_session = new_value
                        applied_changes["changes"].append({
                            "parameter": "urls_per_session",
                            "old_value": old_value,
                            "new_value": new_value,
                            "reason": "Melhorar qualidade com menos URLs"
                        })
                except Exception as e:
                    print(f"Erro ao aplicar mudança urgente: {e}")
        
        # Aplicar mudanças recomendadas
        if apply_recommended:
            for change in suggestions["recommended"]:
                try:
                    if change["action"] == "increase_urls_per_session":
                        old_value = settings_manager.settings.scraping.urls_per_session
                        new_value = suggestions["configuration_changes"]["urls_per_session"]
                        settings_manager.settings.scraping.urls_per_session = new_value
                        applied_changes["changes"].append({
                            "parameter": "urls_per_session", 
                            "old_value": old_value,
                            "new_value": new_value,
                            "reason": "Aproveitar boa performance para coletar mais"
                        })
                    
                    elif change["action"] == "switch_to_complete_mode":
                        old_value = settings_manager.settings.scraping.diversity_mode
                        new_value = "complete"
                        settings_manager.settings.scraping.diversity_mode = new_value
                        applied_changes["changes"].append({
                            "parameter": "diversity_mode",
                            "old_value": old_value,
                            "new_value": new_value,
                            "reason": "Maximizar diversidade de vagas"
                        })
                except Exception as e:
                    print(f"Erro ao aplicar mudança recomendada: {e}")
        
        # Salvar configurações se houve mudanças
        if applied_changes["changes"]:
            try:
                settings_manager.save_settings()
                
                # Registrar no histórico
                self.tuning_history["adjustments"].append(applied_changes)
                self.tuning_history["last_tuning"] = datetime.now().isoformat()
                self._save_tuning_history()
                
            except Exception as e:
                print(f"Erro ao salvar configurações ajustadas: {e}")
        
        return applied_changes
    
    def get_tuning_report(self) -> Dict:
        """Gera relatório de auto-ajustes"""
        report = {
            "total_adjustments": len(self.tuning_history["adjustments"]),
            "last_tuning": self.tuning_history["last_tuning"],
            "recent_changes": [],
            "performance_trend": "stable",
            "next_tuning_recommended": None
        }
        
        # Últimas 5 mudanças
        if self.tuning_history["adjustments"]:
            report["recent_changes"] = self.tuning_history["adjustments"][-5:]
        
        # Determinar quando fazer próximo ajuste
        if self.tuning_history["last_tuning"]:
            last_tuning = datetime.fromisoformat(self.tuning_history["last_tuning"])
            days_since = (datetime.now() - last_tuning).days
            
            if days_since >= 7:
                report["next_tuning_recommended"] = "now"
            else:
                report["next_tuning_recommended"] = f"in_{7-days_since}_days"
        else:
            report["next_tuning_recommended"] = "now"
        
        return report
    
    def print_tuning_report(self):
        """Imprime relatório visual de auto-ajustes"""
        from ..utils.menu_system import Colors
        
        print(f"\n{Colors.CYAN}🎛️ RELATÓRIO DE AUTO-AJUSTES (ML){Colors.RESET}")
        print("=" * 60)
        
        performance = self.analyze_current_performance()
        suggestions = self.suggest_optimizations(
            # Precisaríamos passar settings_manager, por ora simular
            type('Settings', (), {'settings': type('Scraping', (), {
                'scraping': type('Config', (), {
                    'urls_per_session': 3,
                    'diversity_mode': 'complete'
                })()
            })()})()
        )
        
        # Performance atual
        print(f"\n{Colors.YELLOW}📊 Performance Atual:{Colors.RESET}")
        
        score_color = Colors.GREEN if performance["overall_score"] >= 0.7 else Colors.YELLOW if performance["overall_score"] >= 0.4 else Colors.RED
        print(f"Score Geral: {score_color}{performance['overall_score']:.2f}/1.00{Colors.RESET}")
        
        if performance["strengths"]:
            print(f"\n{Colors.GREEN}✅ Pontos Fortes:{Colors.RESET}")
            for strength in performance["strengths"]:
                print(f"  • {strength}")
        
        if performance["bottlenecks"]:
            print(f"\n{Colors.RED}⚠️ Gargalos Identificados:{Colors.RESET}")
            for bottleneck in performance["bottlenecks"]:
                print(f"  • {bottleneck}")
        
        # Sugestões
        if suggestions["urgent"]:
            print(f"\n{Colors.RED}🚨 Otimizações Urgentes:{Colors.RESET}")
            for suggestion in suggestions["urgent"]:
                print(f"  • {suggestion['description']}")
        
        if suggestions["recommended"]:
            print(f"\n{Colors.YELLOW}💡 Recomendações:{Colors.RESET}")
            for suggestion in suggestions["recommended"]:
                print(f"  • {suggestion['description']}")
        
        # Histórico
        report = self.get_tuning_report()
        if report["total_adjustments"] > 0:
            print(f"\n{Colors.CYAN}📈 Histórico:{Colors.RESET}")
            print(f"  • Total de ajustes realizados: {report['total_adjustments']}")
            print(f"  • Último ajuste: {report['last_tuning'][:10] if report['last_tuning'] else 'Nunca'}")
        
        print("\n" + "=" * 60)


# Instância global do auto-tuner
auto_tuner = AutoTuner()