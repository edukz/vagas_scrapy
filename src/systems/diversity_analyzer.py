"""
Sistema de Análise de Diversidade em Tempo Real

Este módulo analisa a diversidade das vagas coletadas e fornece
métricas detalhadas sobre a cobertura de diferentes categorias.
"""

from typing import Dict, List, Tuple, Set
from collections import defaultdict
from datetime import datetime


class DiversityAnalyzer:
    """
    Analisa diversidade de vagas em tempo real
    
    Métricas incluem:
    - Distribuição por modalidade (remoto, presencial, híbrido)
    - Distribuição geográfica (cidades e estados)
    - Distribuição por área profissional
    - Distribuição por senioridade
    - Score de diversidade geral
    """
    
    def __init__(self):
        self.stats = {
            "modalidade": defaultdict(int),
            "geografia": defaultdict(int),
            "profissional": defaultdict(int),
            "senioridade": defaultdict(int),
            "fonte_url": defaultdict(int),
            "total_vagas": 0,
            "timestamp": datetime.now()
        }
        
        # Mapas de categorização
        self.categoria_maps = {
            "modalidade": {
                "home office": ["home-office", "remoto", "remote"],
                "presencial": ["presencial", "on-site"],
                "híbrido": ["hibrido", "hybrid", "flexível"]
            },
            "profissional": {
                "tecnologia": ["tecnologia", "ti", "desenvolvimento", "programador", "software"],
                "administração": ["administracao", "administrativo", "gestao"],
                "vendas": ["vendas", "comercial", "sales"],
                "marketing": ["marketing", "publicidade", "propaganda"],
                "finanças": ["financas", "financeiro", "contabil"],
                "rh": ["recursos-humanos", "rh", "pessoas"],
                "engenharia": ["engenharia", "engenheiro"],
                "saúde": ["saude", "medicina", "enfermagem"],
                "educação": ["educacao", "professor", "ensino"],
                "jurídico": ["juridico", "advogado", "direito"]
            },
            "senioridade": {
                "estágio": ["estagio", "estagiario", "intern"],
                "trainee": ["trainee", "aprendiz"],
                "júnior": ["junior", "jr", "iniciante"],
                "pleno": ["pleno", "pl", "mid-level"],
                "sênior": ["senior", "sr", "especialista"],
                "liderança": ["coordenador", "gerente", "diretor", "supervisor", "head"]
            }
        }
    
    def analyze_job(self, job: Dict) -> None:
        """Analisa uma vaga e atualiza estatísticas"""
        self.stats["total_vagas"] += 1
        
        # Analisar fonte URL
        if "fonte_url" in job:
            self._analyze_fonte_url(job["fonte_url"])
        
        # Analisar título e descrição
        text = f"{job.get('titulo', '')} {job.get('descricao', '')} {job.get('regime', '')}".lower()
        
        # Categorizar modalidade
        modalidade = self._categorize_modalidade(text, job)
        if modalidade:
            self.stats["modalidade"][modalidade] += 1
        
        # Categorizar geografia
        geografia = self._categorize_geografia(job)
        if geografia:
            self.stats["geografia"][geografia] += 1
        
        # Categorizar área profissional
        area = self._categorize_profissional(text)
        if area:
            self.stats["profissional"][area] += 1
        
        # Categorizar senioridade
        senioridade = self._categorize_senioridade(text, job)
        if senioridade:
            self.stats["senioridade"][senioridade] += 1
    
    def _analyze_fonte_url(self, url: str) -> None:
        """Analisa a URL fonte da vaga"""
        if "home-office" in url:
            self.stats["fonte_url"]["home-office"] += 1
        elif "presencial" in url:
            self.stats["fonte_url"]["presencial"] += 1
        elif "hibrido" in url:
            self.stats["fonte_url"]["hibrido"] += 1
        elif any(city in url for city in ["-sp/", "-rj/", "-mg/", "-df/", "-pr/", "-rs/", "-pe/", "-ba/"]):
            self.stats["fonte_url"]["geografica"] += 1
        elif any(area in url for area in ["tecnologia", "administracao", "vendas", "marketing"]):
            self.stats["fonte_url"]["profissional"] += 1
        elif any(level in url for level in ["junior", "pleno", "senior", "estagio", "trainee"]):
            self.stats["fonte_url"]["senioridade"] += 1
        else:
            self.stats["fonte_url"]["geral"] += 1
    
    def _categorize_modalidade(self, text: str, job: Dict) -> str:
        """Categoriza modalidade de trabalho"""
        # Verificar campo específico primeiro
        regime = job.get("regime", "").lower()
        if regime:
            for categoria, keywords in self.categoria_maps["modalidade"].items():
                if any(kw in regime for kw in keywords):
                    return categoria
        
        # Verificar no texto
        for categoria, keywords in self.categoria_maps["modalidade"].items():
            if any(kw in text for kw in keywords):
                return categoria
        
        return "não especificado"
    
    def _categorize_geografia(self, job: Dict) -> str:
        """Categoriza localização geográfica"""
        localizacao = job.get("localizacao", "").lower()
        
        # Estados principais
        estados = {
            "são paulo": "SP", "sp": "SP",
            "rio de janeiro": "RJ", "rj": "RJ",
            "minas gerais": "MG", "mg": "MG",
            "distrito federal": "DF", "brasília": "DF", "df": "DF",
            "paraná": "PR", "curitiba": "PR", "pr": "PR",
            "rio grande do sul": "RS", "porto alegre": "RS", "rs": "RS",
            "pernambuco": "PE", "recife": "PE", "pe": "PE",
            "bahia": "BA", "salvador": "BA", "ba": "BA"
        }
        
        for estado_nome, sigla in estados.items():
            if estado_nome in localizacao:
                return sigla
        
        if "home office" in localizacao or "remoto" in localizacao:
            return "Remoto"
        
        return "Outros"
    
    def _categorize_profissional(self, text: str) -> str:
        """Categoriza área profissional"""
        for categoria, keywords in self.categoria_maps["profissional"].items():
            if any(kw in text for kw in keywords):
                return categoria
        return "outras"
    
    def _categorize_senioridade(self, text: str, job: Dict) -> str:
        """Categoriza nível de senioridade"""
        # Verificar campo específico
        nivel = job.get("nivel", "").lower()
        if nivel:
            for categoria, keywords in self.categoria_maps["senioridade"].items():
                if any(kw in nivel for kw in keywords):
                    return categoria
        
        # Verificar no texto
        for categoria, keywords in self.categoria_maps["senioridade"].items():
            if any(kw in text for kw in keywords):
                return categoria
        
        return "não especificado"
    
    def get_diversity_score(self) -> float:
        """
        Calcula score de diversidade (0-100)
        
        Baseado em:
        - Número de categorias diferentes
        - Distribuição equilibrada entre categorias
        - Cobertura de todas as dimensões
        """
        if self.stats["total_vagas"] == 0:
            return 0.0
        
        scores = []
        
        # Score por dimensão
        for dimension in ["modalidade", "geografia", "profissional", "senioridade"]:
            categorias = self.stats[dimension]
            if not categorias:
                scores.append(0)
                continue
            
            # Número de categorias únicas
            num_categorias = len(categorias)
            max_categorias = len(self.categoria_maps.get(dimension, {})) + 2  # +2 para "outros" e "não especificado"
            
            # Score de variedade (0-50)
            variedade_score = min(50, (num_categorias / max_categorias) * 50)
            
            # Score de distribuição (0-50)
            total_dimension = sum(categorias.values())
            if total_dimension > 0:
                # Calcular desvio padrão da distribuição
                media = total_dimension / num_categorias
                desvio = sum((count - media) ** 2 for count in categorias.values()) / num_categorias
                # Quanto menor o desvio, melhor a distribuição
                distribuicao_score = max(0, 50 - (desvio / media * 10)) if media > 0 else 0
            else:
                distribuicao_score = 0
            
            scores.append(variedade_score + distribuicao_score)
        
        # Média ponderada dos scores
        return sum(scores) / len(scores)
    
    def get_report(self) -> Dict:
        """Gera relatório completo de diversidade"""
        score = self.get_diversity_score()
        
        report = {
            "score_geral": round(score, 1),
            "total_vagas": self.stats["total_vagas"],
            "timestamp": self.stats["timestamp"].isoformat(),
            "distribuicoes": {},
            "recomendacoes": []
        }
        
        # Adicionar distribuições
        for dimension in ["modalidade", "geografia", "profissional", "senioridade"]:
            if self.stats[dimension]:
                total_dim = sum(self.stats[dimension].values())
                report["distribuicoes"][dimension] = {
                    cat: {"count": count, "percentual": round(count/total_dim * 100, 1)}
                    for cat, count in sorted(self.stats[dimension].items(), 
                                            key=lambda x: x[1], reverse=True)
                }
        
        # Gerar recomendações
        report["recomendacoes"] = self._generate_recommendations()
        
        return report
    
    def _generate_recommendations(self) -> List[str]:
        """Gera recomendações para melhorar diversidade"""
        recommendations = []
        
        # Verificar dimensões sub-representadas
        for dimension in ["modalidade", "geografia", "profissional", "senioridade"]:
            if not self.stats[dimension] or len(self.stats[dimension]) < 3:
                recommendations.append(f"Aumentar diversidade de {dimension}")
        
        # Verificar concentração excessiva
        for dimension, categorias in self.stats.items():
            if isinstance(categorias, defaultdict) and categorias:
                total = sum(categorias.values())
                for cat, count in categorias.items():
                    if total > 0 and count / total > 0.5:
                        recommendations.append(f"Reduzir concentração em {dimension}:{cat} (atualmente {count/total*100:.0f}%)")
        
        return recommendations[:5]  # Limitar a 5 recomendações
    
    def print_summary(self) -> None:
        """Imprime resumo visual da diversidade"""
        from ..utils.menu_system import Colors
        
        print(f"\n{Colors.CYAN}📊 ANÁLISE DE DIVERSIDADE EM TEMPO REAL{Colors.RESET}")
        print("=" * 60)
        
        score = self.get_diversity_score()
        
        # Score visual
        score_color = Colors.GREEN if score >= 70 else Colors.YELLOW if score >= 40 else Colors.RED
        print(f"\n{Colors.BOLD}Score Geral: {score_color}{score:.1f}/100{Colors.RESET}")
        
        # Barra de progresso
        filled = int(score / 10)
        bar = "█" * filled + "░" * (10 - filled)
        print(f"Diversidade: [{bar}]")
        
        # Estatísticas por dimensão
        print(f"\n{Colors.BOLD}Distribuição por Categoria:{Colors.RESET}")
        
        for dimension in ["modalidade", "geografia", "profissional", "senioridade"]:
            if self.stats[dimension]:
                print(f"\n{Colors.YELLOW}{dimension.capitalize()}:{Colors.RESET}")
                total = sum(self.stats[dimension].values())
                
                # Top 5 categorias
                for cat, count in sorted(self.stats[dimension].items(), 
                                        key=lambda x: x[1], reverse=True)[:5]:
                    percent = count / total * 100
                    bar_size = int(percent / 5)
                    bar = "▓" * bar_size + "░" * (20 - bar_size)
                    print(f"  {cat:<20} [{bar}] {percent:5.1f}% ({count})")
        
        # Recomendações
        recommendations = self._generate_recommendations()
        if recommendations:
            print(f"\n{Colors.BOLD}💡 Recomendações:{Colors.RESET}")
            for i, rec in enumerate(recommendations, 1):
                print(f"  {i}. {rec}")
        
        print("\n" + "=" * 60)


# Instância global do analisador
diversity_analyzer = DiversityAnalyzer()