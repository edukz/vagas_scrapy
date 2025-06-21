"""
Analisador de Padrões Temporais

Este módulo analisa padrões temporais para identificar
os melhores momentos para executar o scraping.
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from collections import defaultdict
import statistics


class TemporalAnalyzer:
    """
    Analisa padrões temporais de publicação de vagas
    
    Funcionalidades:
    - Detecção de horários de pico
    - Análise por dia da semana
    - Previsão de melhores momentos
    - Otimização de agendamento
    """
    
    def __init__(self, data_file: str = "data/ml/temporal_patterns.json"):
        self.data_file = data_file
        self.data_dir = os.path.dirname(data_file)
        
        # Criar diretório se não existir
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Carregar dados
        self.temporal_data = self._load_data()
        
        # Configurações de análise
        self.min_samples = 5  # Mínimo de amostras para considerar padrão
        self.confidence_threshold = 0.7  # Confiança mínima para recomendações
    
    def _load_data(self) -> Dict:
        """Carrega dados de padrões temporais"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        
        return {
            "hourly_patterns": defaultdict(list),
            "daily_patterns": defaultdict(list),
            "weekly_patterns": defaultdict(list),
            "monthly_patterns": defaultdict(list),
            "special_events": [],
            "last_analysis": None
        }
    
    def _save_data(self):
        """Salva dados de padrões temporais"""
        try:
            # Converter defaultdicts para dicts normais
            save_data = {
                "hourly_patterns": dict(self.temporal_data["hourly_patterns"]),
                "daily_patterns": dict(self.temporal_data["daily_patterns"]),
                "weekly_patterns": dict(self.temporal_data["weekly_patterns"]),
                "monthly_patterns": dict(self.temporal_data["monthly_patterns"]),
                "special_events": self.temporal_data["special_events"],
                "last_analysis": self.temporal_data["last_analysis"]
            }
            
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Erro ao salvar dados temporais: {e}")
    
    def record_scraping_session(self, timestamp: datetime, metrics: Dict):
        """
        Registra uma sessão de scraping para análise temporal
        
        Args:
            timestamp: Momento da execução
            metrics: {
                'new_jobs': int,
                'total_jobs': int,
                'urls_processed': int,
                'duration_seconds': float
            }
        """
        # Padrões por hora
        hour = timestamp.hour
        self.temporal_data["hourly_patterns"][str(hour)].append({
            "timestamp": timestamp.isoformat(),
            "new_jobs": metrics.get("new_jobs", 0),
            "efficiency": metrics.get("new_jobs", 0) / max(metrics.get("duration_seconds", 1), 1)
        })
        
        # Padrões por dia da semana
        weekday = timestamp.strftime("%A")
        self.temporal_data["daily_patterns"][weekday].append({
            "timestamp": timestamp.isoformat(),
            "hour": hour,
            "new_jobs": metrics.get("new_jobs", 0)
        })
        
        # Padrões semanais (número da semana no ano)
        week_num = timestamp.isocalendar()[1]
        self.temporal_data["weekly_patterns"][str(week_num)].append({
            "timestamp": timestamp.isoformat(),
            "new_jobs": metrics.get("new_jobs", 0)
        })
        
        # Padrões mensais
        day_of_month = timestamp.day
        self.temporal_data["monthly_patterns"][str(day_of_month)].append({
            "timestamp": timestamp.isoformat(),
            "new_jobs": metrics.get("new_jobs", 0)
        })
        
        self.temporal_data["last_analysis"] = datetime.now().isoformat()
        self._save_data()
    
    def get_best_hours(self, confidence_only: bool = True) -> List[Tuple[int, float]]:
        """
        Retorna melhores horários para scraping
        
        Returns:
            Lista de tuplas (hora, score)
        """
        hour_scores = []
        
        for hour_str, sessions in self.temporal_data["hourly_patterns"].items():
            if len(sessions) < self.min_samples and confidence_only:
                continue
            
            # Calcular média de novas vagas
            new_jobs_avg = statistics.mean([s["new_jobs"] for s in sessions])
            
            # Calcular eficiência média
            efficiency_avg = statistics.mean([s["efficiency"] for s in sessions])
            
            # Score combinado
            score = (new_jobs_avg * 0.7) + (efficiency_avg * 10 * 0.3)
            
            hour_scores.append((int(hour_str), score))
        
        # Ordenar por score
        hour_scores.sort(key=lambda x: x[1], reverse=True)
        
        return hour_scores
    
    def get_best_weekdays(self) -> List[Tuple[str, float]]:
        """Retorna melhores dias da semana para scraping"""
        day_scores = []
        
        for day, sessions in self.temporal_data["daily_patterns"].items():
            if len(sessions) < self.min_samples:
                continue
            
            # Média de novas vagas
            avg_new_jobs = statistics.mean([s["new_jobs"] for s in sessions])
            
            day_scores.append((day, avg_new_jobs))
        
        day_scores.sort(key=lambda x: x[1], reverse=True)
        return day_scores
    
    def predict_next_best_time(self, horizon_hours: int = 24) -> Optional[datetime]:
        """
        Prevê próximo melhor momento para scraping
        
        Args:
            horizon_hours: Quantas horas à frente considerar
            
        Returns:
            Datetime do próximo melhor momento
        """
        best_hours = self.get_best_hours()
        if not best_hours:
            return None
        
        # Top 3 melhores horários
        top_hours = [hour for hour, score in best_hours[:3]]
        
        # Verificar próximas ocorrências
        now = datetime.now()
        candidates = []
        
        for h in range(horizon_hours):
            future_time = now + timedelta(hours=h)
            if future_time.hour in top_hours:
                # Bonus se for um bom dia da semana
                weekday_bonus = 0
                best_days = self.get_best_weekdays()
                if best_days:
                    weekday = future_time.strftime("%A")
                    if weekday == best_days[0][0]:
                        weekday_bonus = 0.2
                
                # Score baseado em quão próximo está
                proximity_score = 1.0 - (h / horizon_hours)
                
                # Score do horário
                hour_score = next((score for hour, score in best_hours if hour == future_time.hour), 0)
                
                total_score = hour_score + weekday_bonus + (proximity_score * 0.1)
                candidates.append((future_time, total_score))
        
        if not candidates:
            return None
        
        # Retornar melhor candidato
        candidates.sort(key=lambda x: x[1], reverse=True)
        return candidates[0][0]
    
    def get_temporal_insights(self) -> Dict:
        """Gera insights sobre padrões temporais"""
        insights = {
            "best_hours": [],
            "best_weekdays": [],
            "patterns": [],
            "recommendations": [],
            "next_best_time": None
        }
        
        # Melhores horários
        best_hours = self.get_best_hours(confidence_only=False)
        if best_hours:
            insights["best_hours"] = [
                {"hour": hour, "score": round(score, 2)}
                for hour, score in best_hours[:5]
            ]
            
            # Detectar padrões
            morning_hours = [h for h, s in best_hours if 6 <= h <= 11]
            afternoon_hours = [h for h, s in best_hours if 12 <= h <= 17]
            evening_hours = [h for h, s in best_hours if 18 <= h <= 23]
            
            if len(morning_hours) > len(afternoon_hours) and len(morning_hours) > len(evening_hours):
                insights["patterns"].append("Manhãs são mais produtivas")
            elif len(afternoon_hours) > len(morning_hours) and len(afternoon_hours) > len(evening_hours):
                insights["patterns"].append("Tardes são mais produtivas")
            elif len(evening_hours) > len(morning_hours) and len(evening_hours) > len(afternoon_hours):
                insights["patterns"].append("Noites são mais produtivas")
        
        # Melhores dias
        best_days = self.get_best_weekdays()
        if best_days:
            insights["best_weekdays"] = [
                {"day": day, "avg_jobs": round(avg, 1)}
                for day, avg in best_days[:3]
            ]
            
            # Detectar padrões semanais
            if best_days[0][0] in ["Monday", "Tuesday"]:
                insights["patterns"].append("Início da semana tem mais vagas")
            elif best_days[0][0] in ["Thursday", "Friday"]:
                insights["patterns"].append("Final da semana tem mais vagas")
        
        # Próximo melhor momento
        next_time = self.predict_next_best_time()
        if next_time:
            insights["next_best_time"] = {
                "datetime": next_time.isoformat(),
                "readable": next_time.strftime("%d/%m %H:%M"),
                "in_hours": round((next_time - datetime.now()).total_seconds() / 3600, 1)
            }
        
        # Recomendações
        if insights["best_hours"]:
            top_hour = insights["best_hours"][0]["hour"]
            insights["recommendations"].append(
                f"Agende scraping para às {top_hour}h para melhores resultados"
            )
        
        if insights["best_weekdays"]:
            top_day = insights["best_weekdays"][0]["day"]
            insights["recommendations"].append(
                f"{top_day} é o melhor dia para encontrar novas vagas"
            )
        
        # Análise de consistência
        total_samples = sum(len(sessions) for sessions in self.temporal_data["hourly_patterns"].values())
        if total_samples < 50:
            insights["recommendations"].append(
                f"Colete mais dados ({total_samples}/50 amostras) para melhorar previsões"
            )
        
        return insights
    
    def should_run_now(self) -> Tuple[bool, str]:
        """
        Determina se é um bom momento para executar scraping
        
        Returns:
            (should_run, reason)
        """
        now = datetime.now()
        current_hour = now.hour
        current_day = now.strftime("%A")
        
        # Verificar se temos dados suficientes
        best_hours = self.get_best_hours()
        if not best_hours:
            return True, "Sem dados históricos - coletando informações"
        
        # Verificar se é um bom horário
        hour_ranks = {hour: rank for rank, (hour, score) in enumerate(best_hours)}
        current_rank = hour_ranks.get(current_hour, len(best_hours))
        
        if current_rank < 3:
            return True, f"Excelente horário! (#{current_rank + 1} melhor horário)"
        elif current_rank < 6:
            return True, f"Bom horário (#{current_rank + 1})"
        
        # Verificar dia da semana
        best_days = self.get_best_weekdays()
        if best_days:
            day_ranks = {day: rank for rank, (day, avg) in enumerate(best_days)}
            day_rank = day_ranks.get(current_day, len(best_days))
            
            if day_rank == 0:
                return True, f"Melhor dia da semana ({current_day})"
        
        # Se não é um bom momento, sugerir próximo
        next_best = self.predict_next_best_time(12)
        if next_best:
            hours_until = (next_best - now).total_seconds() / 3600
            return False, f"Aguarde {hours_until:.1f}h - melhor às {next_best.strftime('%H:%M')}"
        
        return True, "Momento aceitável para execução"


# Instância global do analisador temporal
temporal_analyzer = TemporalAnalyzer()