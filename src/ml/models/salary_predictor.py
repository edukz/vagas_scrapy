"""
Preditor de Salários baseado em Machine Learning
===============================================

Prediz faixas salariais baseado em:
- Tecnologias requeridas
- Nível de senioridade
- Localização
- Tamanho da empresa
- Benefícios oferecidos
"""

import re
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Union
from dataclasses import dataclass
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split
import joblib
from pathlib import Path


@dataclass 
class SalaryRange:
    """Faixa salarial predita"""
    min_salary: float
    max_salary: float
    median_salary: float
    confidence: float
    currency: str = "BRL"
    
    def __str__(self):
        return f"R$ {self.min_salary:,.0f} - R$ {self.max_salary:,.0f}"
    
    @property
    def formatted(self) -> str:
        """Retorna faixa formatada"""
        if self.max_salary < 1000:
            return "Menos de R$ 1.000"
        elif self.min_salary > 50000:
            return "Mais de R$ 50.000"
        else:
            return f"R$ {self.min_salary:,.0f} - R$ {self.max_salary:,.0f}"


class SalaryPredictor:
    """
    Preditor de salários usando Gradient Boosting
    
    Features utilizadas:
    - Tecnologias e sua valorização no mercado
    - Senioridade (júnior, pleno, sênior, etc)
    - Localização (cidade/estado)
    - Modalidade (presencial, híbrido, remoto)
    - Tipo de contrato (CLT, PJ)
    - Benefícios oferecidos
    """
    
    def __init__(self, model_path: Optional[str] = None):
        self.model_path = model_path or "data/ml_models/salary_predictor.pkl"
        self.scaler_path = "data/ml_models/salary_scaler.pkl"
        self.encoders_path = "data/ml_models/salary_encoders.pkl"
        
        # Tecnologias e seus valores relativos no mercado
        self.tech_values = {
            # Linguagens
            'python': 1.0,
            'java': 1.1,
            'javascript': 0.9,
            'typescript': 1.0,
            'go': 1.3,
            'rust': 1.4,
            'scala': 1.5,
            'kotlin': 1.2,
            'c++': 1.2,
            'c#': 1.0,
            'php': 0.8,
            'ruby': 1.0,
            'swift': 1.3,
            
            # Frameworks e Libraries
            'react': 1.0,
            'angular': 1.0,
            'vue': 0.9,
            'node.js': 0.9,
            'django': 1.0,
            'flask': 0.9,
            'spring': 1.1,
            '.net': 1.0,
            'rails': 1.0,
            
            # Data & ML
            'tensorflow': 1.5,
            'pytorch': 1.5,
            'scikit-learn': 1.3,
            'pandas': 1.2,
            'spark': 1.6,
            'hadoop': 1.4,
            
            # Cloud & DevOps
            'aws': 1.3,
            'azure': 1.3,
            'gcp': 1.3,
            'docker': 1.2,
            'kubernetes': 1.4,
            'terraform': 1.4,
            'jenkins': 1.1,
            
            # Databases
            'mysql': 0.9,
            'postgresql': 1.0,
            'mongodb': 1.0,
            'redis': 1.1,
            'elasticsearch': 1.3,
            'cassandra': 1.4,
            'oracle': 1.2
        }
        
        # Multiplicadores por senioridade
        self.seniority_multipliers = {
            'estagiario': 0.15,
            'junior': 0.4,
            'pleno': 1.0,
            'senior': 1.8,
            'especialista': 2.5,
            'gerente': 2.8,
            'diretor': 3.5
        }
        
        # Multiplicadores por localização
        self.location_multipliers = {
            # Estados
            'sp': 1.2,  # São Paulo
            'rj': 1.1,  # Rio de Janeiro
            'mg': 0.9,  # Minas Gerais
            'rs': 0.95, # Rio Grande do Sul
            'pr': 0.9,  # Paraná
            'sc': 0.95, # Santa Catarina
            'df': 1.1,  # Distrito Federal
            'ba': 0.85, # Bahia
            'pe': 0.85, # Pernambuco
            'ce': 0.8,  # Ceará
            
            # Cidades principais
            'são paulo': 1.25,
            'rio de janeiro': 1.15,
            'belo horizonte': 0.95,
            'porto alegre': 1.0,
            'curitiba': 0.95,
            'florianópolis': 1.0,
            'brasília': 1.15,
            'campinas': 1.1,
            'remoto': 1.05,  # Trabalho remoto
            'home office': 1.05
        }
        
        # Base salarial por categoria (CLT mensal)
        self.base_salaries = {
            'junior': 3500,
            'pleno': 7000,
            'senior': 12000,
            'especialista': 18000,
            'gerente': 22000
        }
        
        self.model = None
        self.scaler = None
        self.encoders = {}
        self._load_or_create_model()
    
    def _load_or_create_model(self):
        """Carrega modelo existente ou cria um novo"""
        try:
            self.model = joblib.load(self.model_path)
            self.scaler = joblib.load(self.scaler_path)
            self.encoders = joblib.load(self.encoders_path)
            print("✅ Modelo de salários carregado com sucesso")
        except:
            print("📊 Criando novo modelo de predição de salários...")
            self._create_default_model()
    
    def _create_default_model(self):
        """Cria modelo com dados sintéticos de mercado"""
        # Gerar dados sintéticos baseados no mercado brasileiro
        training_data = self._generate_market_data()
        
        # Preparar features
        X = self._prepare_features(training_data)
        y = training_data['salary'].values
        
        # Dividir dados
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        # Escalar features
        self.scaler = StandardScaler()
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Treinar modelo
        self.model = GradientBoostingRegressor(
            n_estimators=100,
            learning_rate=0.1,
            max_depth=5,
            random_state=42
        )
        
        self.model.fit(X_train_scaled, y_train)
        
        # Avaliar
        train_score = self.model.score(X_train_scaled, y_train)
        test_score = self.model.score(X_test_scaled, y_test)
        
        print(f"✅ Modelo treinado - R² Train: {train_score:.3f}, Test: {test_score:.3f}")
        
        # Salvar modelo
        self._save_model()
    
    def _generate_market_data(self) -> pd.DataFrame:
        """Gera dados sintéticos baseados no mercado real"""
        data = []
        
        # Combinações de características
        seniority_levels = ['junior', 'pleno', 'senior', 'especialista']
        locations = ['sp', 'rj', 'mg', 'rs', 'pr', 'remoto']
        contract_types = ['clt', 'pj']
        
        # Gerar amostras
        np.random.seed(42)
        
        for _ in range(5000):
            # Características aleatórias
            seniority = np.random.choice(seniority_levels)
            location = np.random.choice(locations)
            contract = np.random.choice(contract_types)
            
            # Tecnologias (1-5 techs por vaga)
            n_techs = np.random.randint(1, 6)
            available_techs = list(self.tech_values.keys())
            techs = np.random.choice(available_techs, n_techs, replace=False)
            
            # Calcular salário base
            base = self.base_salaries.get(seniority, 7000)
            
            # Aplicar multiplicadores
            tech_multiplier = np.mean([self.tech_values.get(t, 1.0) for t in techs])
            location_multiplier = self.location_multipliers.get(location, 1.0)
            seniority_multiplier = self.seniority_multipliers.get(seniority, 1.0)
            
            # PJ geralmente paga mais
            contract_multiplier = 1.3 if contract == 'pj' else 1.0
            
            # Calcular salário final com variação
            salary = base * tech_multiplier * location_multiplier * contract_multiplier
            salary *= (1 + np.random.normal(0, 0.15))  # Variação de ±15%
            
            # Features numéricas
            sample = {
                'salary': max(1500, salary),  # Mínimo de 1500
                'seniority': seniority,
                'location': location,
                'contract_type': contract,
                'n_technologies': n_techs,
                'tech_score': tech_multiplier,
                'has_cloud': any(t in ['aws', 'azure', 'gcp'] for t in techs),
                'has_ml': any(t in ['tensorflow', 'pytorch', 'scikit-learn'] for t in techs),
                'has_web': any(t in ['react', 'angular', 'vue'] for t in techs),
                'remote': location == 'remoto',
                'years_experience': {
                    'junior': np.random.randint(0, 3),
                    'pleno': np.random.randint(3, 6),
                    'senior': np.random.randint(6, 10),
                    'especialista': np.random.randint(8, 15)
                }[seniority]
            }
            
            data.append(sample)
        
        return pd.DataFrame(data)
    
    def _prepare_features(self, df: pd.DataFrame) -> np.ndarray:
        """Prepara features para o modelo"""
        # Encoders para variáveis categóricas
        if not self.encoders:
            self.encoders['seniority'] = LabelEncoder()
            self.encoders['location'] = LabelEncoder()
            self.encoders['contract'] = LabelEncoder()
            
            df['seniority_encoded'] = self.encoders['seniority'].fit_transform(df['seniority'])
            df['location_encoded'] = self.encoders['location'].fit_transform(df['location'])
            df['contract_encoded'] = self.encoders['contract'].fit_transform(df['contract_type'])
        else:
            df['seniority_encoded'] = self.encoders['seniority'].transform(df['seniority'])
            df['location_encoded'] = self.encoders['location'].transform(df['location'])
            df['contract_encoded'] = self.encoders['contract'].transform(df['contract_type'])
        
        # Features finais
        features = [
            'seniority_encoded',
            'location_encoded', 
            'contract_encoded',
            'n_technologies',
            'tech_score',
            'has_cloud',
            'has_ml',
            'has_web',
            'remote',
            'years_experience'
        ]
        
        return df[features].values
    
    def predict(self, job_data: Dict) -> SalaryRange:
        """
        Prediz faixa salarial para uma vaga
        
        Args:
            job_data: Dados da vaga incluindo título, descrição, tecnologias, etc
            
        Returns:
            SalaryRange com predição
        """
        # Extrair features
        features = self._extract_job_features(job_data)
        
        # Preparar dados
        df = pd.DataFrame([features])
        
        # Tratar valores desconhecidos
        for col, encoder in self.encoders.items():
            if col == 'seniority':
                if features['seniority'] not in encoder.classes_:
                    features['seniority'] = 'pleno'  # Default
            elif col == 'location':
                if features['location'] not in encoder.classes_:
                    features['location'] = 'sp'  # Default
            elif col == 'contract':
                if features['contract_type'] not in encoder.classes_:
                    features['contract_type'] = 'clt'  # Default
        
        # Preparar features
        X = self._prepare_features(df)
        X_scaled = self.scaler.transform(X)
        
        # Predição
        predicted_salary = self.model.predict(X_scaled)[0]
        
        # Calcular intervalo de confiança
        # Usar árvores individuais para estimar incerteza
        if hasattr(self.model, 'estimators_'):
            predictions = np.array([
                tree.predict(X_scaled)[0] 
                for tree in self.model.estimators_.flatten()
            ])
            
            confidence = 1 - (np.std(predictions) / np.mean(predictions))
            min_salary = np.percentile(predictions, 20)
            max_salary = np.percentile(predictions, 80)
        else:
            confidence = 0.7  # Default
            min_salary = predicted_salary * 0.85
            max_salary = predicted_salary * 1.15
        
        # Ajustar para valores realistas
        min_salary = round(min_salary / 100) * 100  # Arredondar para centenas
        max_salary = round(max_salary / 100) * 100
        median_salary = round(predicted_salary / 100) * 100
        
        return SalaryRange(
            min_salary=max(1500, min_salary),  # Mínimo de 1500
            max_salary=min(50000, max_salary),  # Máximo de 50000
            median_salary=median_salary,
            confidence=confidence
        )
    
    def _extract_job_features(self, job_data: Dict) -> Dict:
        """Extrai features de uma vaga"""
        title = job_data.get('titulo', '').lower()
        description = job_data.get('descricao', '').lower()
        technologies = job_data.get('tecnologias_detectadas', [])
        location = job_data.get('localizacao', '').lower()
        
        # Detectar senioridade
        seniority = self._detect_seniority(title, description)
        
        # Detectar localização
        location_key = self._extract_location_key(location)
        
        # Detectar tipo de contrato
        contract_type = self._detect_contract_type(description)
        
        # Calcular tech score
        tech_score = self._calculate_tech_score(technologies)
        
        # Detectar categorias de tecnologia
        has_cloud = any(t.lower() in ['aws', 'azure', 'gcp', 'docker', 'kubernetes'] 
                       for t in technologies)
        has_ml = any(t.lower() in ['tensorflow', 'pytorch', 'machine learning', 'ml'] 
                    for t in technologies)
        has_web = any(t.lower() in ['react', 'angular', 'vue', 'javascript', 'frontend'] 
                     for t in technologies)
        
        # Estimar anos de experiência
        years_exp = self._estimate_experience(description, seniority)
        
        return {
            'seniority': seniority,
            'location': location_key,
            'contract_type': contract_type,
            'n_technologies': len(technologies),
            'tech_score': tech_score,
            'has_cloud': has_cloud,
            'has_ml': has_ml,
            'has_web': has_web,
            'remote': 'remoto' in location or 'home office' in location,
            'years_experience': years_exp
        }
    
    def _detect_seniority(self, title: str, description: str) -> str:
        """Detecta nível de senioridade"""
        text = f"{title} {description}".lower()
        
        patterns = {
            'estagiario': r'est[aá]gi[aá]rio|trainee|aprendiz',
            'junior': r'j[uú]nior|jr\.|iniciante',
            'pleno': r'pleno|analista|desenvolvedor(?!\s*(j[uú]nior|s[eê]nior))',
            'senior': r's[eê]nior|sr\.|especialista',
            'especialista': r'arquiteto|tech\s*lead|principal|staff'
        }
        
        for level, pattern in patterns.items():
            if re.search(pattern, text):
                return level
        
        # Default baseado em anos de experiência mencionados
        years_match = re.search(r'(\d+)\s*anos?\s*(?:de\s*)?experi[eê]ncia', text)
        if years_match:
            years = int(years_match.group(1))
            if years <= 2:
                return 'junior'
            elif years <= 5:
                return 'pleno'
            else:
                return 'senior'
        
        return 'pleno'  # Default
    
    def _extract_location_key(self, location: str) -> str:
        """Extrai chave de localização"""
        location = location.lower()
        
        # Verificar estados
        states = {
            'são paulo|sp': 'sp',
            'rio de janeiro|rj': 'rj',
            'minas gerais|mg': 'mg',
            'rio grande do sul|rs': 'rs',
            'paraná|pr': 'pr',
            'santa catarina|sc': 'sc',
            'distrito federal|df|brasília': 'df'
        }
        
        for pattern, key in states.items():
            if re.search(pattern, location):
                return key
        
        # Verificar cidades principais
        if 'são paulo' in location:
            return 'são paulo'
        elif 'rio de janeiro' in location:
            return 'rio de janeiro'
        elif 'remoto' in location or 'home office' in location:
            return 'remoto'
        
        return 'sp'  # Default
    
    def _detect_contract_type(self, description: str) -> str:
        """Detecta tipo de contrato"""
        description = description.lower()
        
        if 'pj' in description or 'pessoa jurídica' in description:
            return 'pj'
        elif 'clt' in description or 'carteira assinada' in description:
            return 'clt'
        
        return 'clt'  # Default
    
    def _calculate_tech_score(self, technologies: List[str]) -> float:
        """Calcula score baseado nas tecnologias"""
        if not technologies:
            return 1.0
        
        scores = []
        for tech in technologies:
            tech_lower = tech.lower()
            # Procurar correspondência parcial
            for key, value in self.tech_values.items():
                if key in tech_lower or tech_lower in key:
                    scores.append(value)
                    break
            else:
                scores.append(1.0)  # Default
        
        return np.mean(scores) if scores else 1.0
    
    def _estimate_experience(self, description: str, seniority: str) -> int:
        """Estima anos de experiência"""
        # Procurar menção explícita
        years_match = re.search(r'(\d+)\s*anos?\s*(?:de\s*)?experi[eê]ncia', description.lower())
        if years_match:
            return int(years_match.group(1))
        
        # Estimar baseado na senioridade
        defaults = {
            'estagiario': 0,
            'junior': 1,
            'pleno': 4,
            'senior': 7,
            'especialista': 10
        }
        
        return defaults.get(seniority, 4)
    
    def _save_model(self):
        """Salva modelo e preprocessadores"""
        Path(self.model_path).parent.mkdir(parents=True, exist_ok=True)
        
        joblib.dump(self.model, self.model_path)
        joblib.dump(self.scaler, self.scaler_path)
        joblib.dump(self.encoders, self.encoders_path)
        
        print(f"✅ Modelo de salários salvo em: {self.model_path}")
    
    def batch_predict(self, jobs: List[Dict]) -> List[Dict]:
        """Prediz salários para múltiplas vagas"""
        results = []
        
        for job in jobs:
            try:
                salary_range = self.predict(job)
                
                job_with_salary = job.copy()
                job_with_salary['predicted_salary'] = {
                    'range': salary_range.formatted,
                    'min': salary_range.min_salary,
                    'max': salary_range.max_salary,
                    'median': salary_range.median_salary,
                    'confidence': salary_range.confidence
                }
                
                results.append(job_with_salary)
            except Exception as e:
                print(f"Erro ao predizer salário: {e}")
                results.append(job)
        
        return results
    
    def analyze_market_trends(self, jobs: List[Dict]) -> Dict:
        """Analisa tendências salariais do mercado"""
        predictions = []
        by_seniority = {}
        by_location = {}
        by_tech = {}
        
        for job in jobs:
            try:
                features = self._extract_job_features(job)
                salary = self.predict(job)
                
                predictions.append(salary.median_salary)
                
                # Agrupar por senioridade
                seniority = features['seniority']
                if seniority not in by_seniority:
                    by_seniority[seniority] = []
                by_seniority[seniority].append(salary.median_salary)
                
                # Agrupar por localização
                location = features['location']
                if location not in by_location:
                    by_location[location] = []
                by_location[location].append(salary.median_salary)
                
                # Agrupar por tecnologia
                for tech in job.get('tecnologias_detectadas', []):
                    tech_lower = tech.lower()
                    if tech_lower not in by_tech:
                        by_tech[tech_lower] = []
                    by_tech[tech_lower].append(salary.median_salary)
                    
            except:
                continue
        
        # Calcular estatísticas
        market_stats = {
            'total_analyzed': len(predictions),
            'overall': {
                'median': np.median(predictions) if predictions else 0,
                'mean': np.mean(predictions) if predictions else 0,
                'min': np.min(predictions) if predictions else 0,
                'max': np.max(predictions) if predictions else 0,
                'std': np.std(predictions) if predictions else 0
            },
            'by_seniority': {
                level: {
                    'median': np.median(salaries),
                    'mean': np.mean(salaries),
                    'count': len(salaries)
                }
                for level, salaries in by_seniority.items()
                if salaries
            },
            'by_location': {
                loc: {
                    'median': np.median(salaries),
                    'mean': np.mean(salaries),
                    'count': len(salaries)
                }
                for loc, salaries in by_location.items()
                if len(salaries) >= 3  # Mínimo 3 amostras
            },
            'top_paying_technologies': sorted(
                [
                    (tech, np.median(salaries))
                    for tech, salaries in by_tech.items()
                    if len(salaries) >= 5  # Mínimo 5 amostras
                ],
                key=lambda x: x[1],
                reverse=True
            )[:10]
        }
        
        return market_stats


# Exemplo de uso
if __name__ == "__main__":
    predictor = SalaryPredictor()
    
    # Exemplo de vaga
    job_example = {
        'titulo': 'Desenvolvedor Python Sênior',
        'descricao': '''
        Empresa de tecnologia busca Desenvolvedor Python Sênior.
        
        Requisitos:
        - 5+ anos de experiência com Python
        - Conhecimento em Django e FastAPI  
        - Experiência com AWS
        - PostgreSQL e Redis
        
        Oferecemos:
        - Contratação CLT
        - Trabalho remoto
        - Benefícios completos
        ''',
        'tecnologias_detectadas': ['Python', 'Django', 'FastAPI', 'AWS', 'PostgreSQL', 'Redis'],
        'localizacao': 'São Paulo - SP (Remoto)'
    }
    
    # Predizer salário
    salary = predictor.predict(job_example)
    
    print(f"Faixa salarial prevista: {salary.formatted}")
    print(f"Mediana: R$ {salary.median_salary:,.2f}")
    print(f"Confiança: {salary.confidence:.1%}")