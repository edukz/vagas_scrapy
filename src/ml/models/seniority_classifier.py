"""
Classificador de Senioridade de Vagas
=====================================

Utiliza ML para classificar automaticamente vagas em:
- Estagiário
- Júnior
- Pleno
- Sênior
- Especialista/Arquiteto
"""

import re
import json
import pickle
import numpy as np
from typing import Dict, List, Tuple, Optional
from pathlib import Path
from dataclasses import dataclass
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
import joblib


@dataclass
class SeniorityLevel:
    """Níveis de senioridade com scores"""
    INTERN = "estagiario"
    JUNIOR = "junior"
    MID = "pleno"
    SENIOR = "senior"
    EXPERT = "especialista"
    
    # Mapeamento de scores
    LEVEL_SCORES = {
        "estagiario": 0,
        "junior": 1,
        "pleno": 2,
        "senior": 3,
        "especialista": 4
    }


class SeniorityClassifier:
    """
    Classificador de senioridade baseado em ML
    
    Features utilizadas:
    - Palavras-chave no título
    - Padrões na descrição
    - Requisitos técnicos
    - Anos de experiência mencionados
    - Complexidade das responsabilidades
    """
    
    def __init__(self, model_path: Optional[str] = None):
        self.model_path = model_path or "data/ml_models/seniority_classifier.pkl"
        self.vectorizer_path = "data/ml_models/seniority_vectorizer.pkl"
        
        # Padrões de regex para extração de features
        self.patterns = {
            'years_experience': re.compile(r'(\d+)\s*(?:anos?|years?)\s*(?:de\s*)?(?:experiência|experience)', re.I),
            'education': re.compile(r'(?:superior|graduação|formado|cursando|bachelor|master|phd|doutorado|mestrado)', re.I),
            'leadership': re.compile(r'(?:lideran[çc]a|gest[ãa]o|coordena[çc][ãa]o|gerente|manager|lead|architect)', re.I),
            'seniority_keywords': {
                'junior': re.compile(r'(?:j[úu]nior|jr\.?|iniciante|trainee|est[áa]gi[áa]rio|intern)', re.I),
                'pleno': re.compile(r'(?:pleno|mid[\s-]?level|intermediate)', re.I),
                'senior': re.compile(r'(?:s[êe]nior|sr\.?|experiente|specialist)', re.I),
                'expert': re.compile(r'(?:especialista|arquiteto|expert|principal|staff)', re.I)
            }
        }
        
        # Keywords por nível
        self.level_keywords = {
            'estagiario': ['estágio', 'estagiário', 'trainee', 'aprendiz', 'universitário', 'cursando'],
            'junior': ['júnior', 'jr', 'iniciante', 'assistente', 'auxiliar', 'básico'],
            'pleno': ['pleno', 'analista', 'desenvolvedor', 'programador'],
            'senior': ['sênior', 'sr', 'experiente', 'avançado', 'especialista'],
            'especialista': ['arquiteto', 'tech lead', 'principal', 'staff', 'gerente técnico', 'coordenador']
        }
        
        # Tecnologias e sua complexidade relativa
        self.tech_complexity = {
            'básico': ['html', 'css', 'javascript', 'python', 'java', 'sql'],
            'intermediário': ['react', 'angular', 'vue', 'django', 'spring', 'node.js'],
            'avançado': ['kubernetes', 'terraform', 'kafka', 'elasticsearch', 'microservices', 'machine learning'],
            'expert': ['arquitetura', 'distributed systems', 'system design', 'blockchain', 'quantum']
        }
        
        self.model = None
        self.vectorizer = None
        self._load_or_create_model()
    
    def _load_or_create_model(self):
        """Carrega modelo existente ou cria um novo"""
        try:
            self.model = joblib.load(self.model_path)
            self.vectorizer = joblib.load(self.vectorizer_path)
            print("✅ Modelo de senioridade carregado com sucesso")
        except:
            print("📊 Criando novo modelo de senioridade...")
            self._create_default_model()
    
    def _create_default_model(self):
        """Cria modelo padrão com dados sintéticos"""
        # Criar dados de treino sintéticos
        training_data = self._generate_synthetic_training_data()
        
        # Preparar features e labels
        texts = [d['text'] for d in training_data]
        labels = [d['level'] for d in training_data]
        features = [self._extract_features(d['title'], d['description']) for d in training_data]
        
        # Vetorizar textos
        self.vectorizer = TfidfVectorizer(
            max_features=1000,
            ngram_range=(1, 3),
            min_df=2
        )
        
        # Combinar features de texto com features numéricas
        text_features = self.vectorizer.fit_transform(texts)
        numeric_features = np.array(features)
        
        # Concatenar features
        X = np.hstack([text_features.toarray(), numeric_features])
        
        # Treinar modelo
        self.model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42
        )
        
        X_train, X_test, y_train, y_test = train_test_split(
            X, labels, test_size=0.2, random_state=42
        )
        
        self.model.fit(X_train, y_train)
        
        # Avaliar modelo
        y_pred = self.model.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        print(f"✅ Modelo treinado com acurácia: {accuracy:.2f}")
        
        # Salvar modelo
        self._save_model()
    
    def _extract_features(self, title: str, description: str) -> List[float]:
        """Extrai features numéricas do texto"""
        features = []
        full_text = f"{title} {description}".lower()
        
        # 1. Anos de experiência mencionados
        years_match = self.patterns['years_experience'].search(full_text)
        years = int(years_match.group(1)) if years_match else 0
        features.append(min(years, 10))  # Cap em 10 anos
        
        # 2. Presença de palavras de liderança
        has_leadership = 1 if self.patterns['leadership'].search(full_text) else 0
        features.append(has_leadership)
        
        # 3. Nível educacional mencionado
        has_education = 1 if self.patterns['education'].search(full_text) else 0
        features.append(has_education)
        
        # 4. Contagem de tecnologias por complexidade
        tech_counts = {'básico': 0, 'intermediário': 0, 'avançado': 0, 'expert': 0}
        for level, techs in self.tech_complexity.items():
            for tech in techs:
                if tech.lower() in full_text:
                    tech_counts[level] += 1
        
        features.extend(tech_counts.values())
        
        # 5. Comprimento da descrição (vagas sênior tendem a ser mais detalhadas)
        features.append(len(description) / 1000)  # Normalizado por 1000 caracteres
        
        # 6. Número de responsabilidades (contando bullets/linhas)
        responsibilities = len(re.findall(r'[•\-\*]\s*', description))
        features.append(responsibilities)
        
        # 7. Presença de palavras-chave específicas de nível
        for level in ['junior', 'pleno', 'senior', 'expert']:
            pattern = self.patterns['seniority_keywords'].get(level)
            if pattern:
                features.append(1 if pattern.search(full_text) else 0)
        
        return features
    
    def classify(self, title: str, description: str, 
                 technologies: List[str] = None) -> Dict[str, any]:
        """
        Classifica uma vaga quanto à senioridade
        
        Args:
            title: Título da vaga
            description: Descrição completa
            technologies: Lista de tecnologias detectadas
            
        Returns:
            Dict com classificação e probabilidades
        """
        # Preparar texto
        full_text = f"{title} {description}"
        if technologies:
            full_text += " " + " ".join(technologies)
        
        # Extrair features
        numeric_features = self._extract_features(title, description)
        
        # Vetorizar texto
        text_features = self.vectorizer.transform([full_text])
        
        # Combinar features
        X = np.hstack([text_features.toarray(), np.array([numeric_features])])
        
        # Predição
        prediction = self.model.predict(X)[0]
        probabilities = self.model.predict_proba(X)[0]
        
        # Criar resultado
        classes = self.model.classes_
        prob_dict = {cls: float(prob) for cls, prob in zip(classes, probabilities)}
        
        # Análise adicional
        confidence = float(max(probabilities))
        reasoning = self._generate_reasoning(title, description, prediction)
        
        return {
            'level': prediction,
            'confidence': confidence,
            'probabilities': prob_dict,
            'reasoning': reasoning,
            'score': SeniorityLevel.LEVEL_SCORES.get(prediction, 0)
        }
    
    def _generate_reasoning(self, title: str, description: str, 
                           predicted_level: str) -> List[str]:
        """Gera explicação para a classificação"""
        reasons = []
        full_text = f"{title} {description}".lower()
        
        # Anos de experiência
        years_match = self.patterns['years_experience'].search(full_text)
        if years_match:
            years = int(years_match.group(1))
            reasons.append(f"Requer {years} anos de experiência")
        
        # Palavras-chave de senioridade
        for level, pattern in self.patterns['seniority_keywords'].items():
            if pattern.search(full_text):
                reasons.append(f"Contém termos indicativos de nível {level}")
        
        # Liderança
        if self.patterns['leadership'].search(full_text):
            reasons.append("Menciona responsabilidades de liderança")
        
        # Tecnologias avançadas
        advanced_techs = []
        for tech in self.tech_complexity.get('avançado', []) + self.tech_complexity.get('expert', []):
            if tech.lower() in full_text:
                advanced_techs.append(tech)
        
        if advanced_techs:
            reasons.append(f"Requer tecnologias avançadas: {', '.join(advanced_techs[:3])}")
        
        return reasons
    
    def _generate_synthetic_training_data(self) -> List[Dict]:
        """Gera dados sintéticos para treino inicial"""
        training_data = []
        
        # Templates por nível
        templates = {
            'estagiario': [
                {
                    'title': 'Estágio em Desenvolvimento {tech}',
                    'description': 'Buscamos estudante de {curso} para estágio em desenvolvimento. '
                                 'Conhecimentos básicos em {tech}. Cursando a partir do 3º semestre. '
                                 'Bolsa auxílio + benefícios.'
                },
                {
                    'title': 'Trainee Desenvolvedor {tech}',
                    'description': 'Programa de trainee para recém-formados. '
                                 'Conhecimento em {tech} é diferencial. '
                                 'Treinamento completo será fornecido.'
                }
            ],
            'junior': [
                {
                    'title': 'Desenvolvedor {tech} Júnior',
                    'description': 'Vaga para desenvolvedor júnior com conhecimentos em {tech}. '
                                 '1-2 anos de experiência. Trabalhar em equipe no desenvolvimento '
                                 'de aplicações. Conhecimento em {tech2} é diferencial.'
                },
                {
                    'title': 'Programador Jr - {tech}',
                    'description': 'Buscamos profissional iniciante para atuar com {tech}. '
                                 'Experiência mínima de 1 ano. Participar do desenvolvimento '
                                 'de sistemas sob supervisão.'
                }
            ],
            'pleno': [
                {
                    'title': 'Desenvolvedor {tech} Pleno',
                    'description': 'Profissional com 3-5 anos de experiência em {tech}. '
                                 'Desenvolvimento de features complexas. Conhecimento em {tech2}, '
                                 '{tech3} e metodologias ágeis. Capacidade de trabalhar com autonomia.'
                },
                {
                    'title': 'Analista Desenvolvedor {tech}',
                    'description': 'Requer 4 anos de experiência. Responsável por '
                                 'desenvolvimento e manutenção de sistemas em {tech}. '
                                 'Conhecimento em {tech2}, {tech3} e padrões de projeto.'
                }
            ],
            'senior': [
                {
                    'title': 'Desenvolvedor {tech} Sênior',
                    'description': 'Mínimo 6 anos de experiência em {tech}. '
                                 'Liderar tecnicamente projetos complexos. Definir arquitetura '
                                 'e padrões. Experiência com {tech2}, {tech3}, microserviços '
                                 'e cloud computing. Mentoria de desenvolvedores juniores.'
                },
                {
                    'title': 'Software Engineer Sr - {tech}',
                    'description': 'Experiência de 7+ anos em desenvolvimento. '
                                 'Arquitetura de sistemas distribuídos. Liderança técnica. '
                                 'Conhecimento avançado em {tech}, {tech2}, Kubernetes e AWS.'
                }
            ],
            'especialista': [
                {
                    'title': 'Arquiteto de Software {tech}',
                    'description': '10+ anos de experiência. Definir arquitetura '
                                 'de sistemas complexos. Liderança de equipes técnicas. '
                                 'Experiência com {tech}, microserviços, event-driven architecture, '
                                 'e system design. Definir roadmap técnico.'
                },
                {
                    'title': 'Tech Lead - {tech}',
                    'description': 'Liderar time de desenvolvimento. 8+ anos de experiência. '
                                 'Responsável por decisões arquiteturais. Expertise em {tech}, '
                                 '{tech2}, distributed systems e DevOps. Gestão técnica de projetos.'
                }
            ]
        }
        
        # Tecnologias para preencher templates
        tech_combinations = [
            ['Python', 'Django', 'PostgreSQL'],
            ['Java', 'Spring', 'MongoDB'],
            ['JavaScript', 'React', 'Node.js'],
            ['C#', '.NET', 'SQL Server'],
            ['Go', 'Kubernetes', 'gRPC']
        ]
        
        # Gerar dados
        for level, level_templates in templates.items():
            for template in level_templates:
                for techs in tech_combinations:
                    data = {
                        'title': template['title'].format(tech=techs[0]),
                        'description': template['description'].format(
                            tech=techs[0],
                            tech2=techs[1],
                            tech3=techs[2],
                            curso='Ciência da Computação'
                        ),
                        'text': '',
                        'level': level
                    }
                    data['text'] = f"{data['title']} {data['description']}"
                    training_data.append(data)
        
        return training_data
    
    def _save_model(self):
        """Salva modelo e vetorizador"""
        Path(self.model_path).parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self.model, self.model_path)
        joblib.dump(self.vectorizer, self.vectorizer_path)
        print(f"✅ Modelo salvo em: {self.model_path}")
    
    def batch_classify(self, jobs: List[Dict]) -> List[Dict]:
        """Classifica múltiplas vagas em batch"""
        results = []
        
        for job in jobs:
            title = job.get('titulo', '')
            description = job.get('descricao', '')
            technologies = job.get('tecnologias_detectadas', [])
            
            classification = self.classify(title, description, technologies)
            
            # Adicionar classificação ao job
            job_with_ml = job.copy()
            job_with_ml['ml_seniority'] = classification
            job_with_ml['nivel_ml'] = classification['level']
            job_with_ml['nivel_confianca'] = classification['confidence']
            
            results.append(job_with_ml)
        
        return results
    
    def evaluate_model(self, test_data: List[Dict]) -> Dict:
        """Avalia performance do modelo com dados de teste"""
        true_labels = []
        predictions = []
        
        for item in test_data:
            true_label = item.get('true_level')
            if true_label:
                prediction = self.classify(
                    item.get('titulo', ''),
                    item.get('descricao', '')
                )
                
                true_labels.append(true_label)
                predictions.append(prediction['level'])
        
        if true_labels:
            accuracy = accuracy_score(true_labels, predictions)
            report = classification_report(
                true_labels, 
                predictions,
                output_dict=True
            )
            
            return {
                'accuracy': accuracy,
                'classification_report': report,
                'sample_size': len(true_labels)
            }
        
        return {'error': 'No labeled data for evaluation'}
    
    def get_feature_importance(self) -> Dict[str, float]:
        """Retorna importância das features para interpretabilidade"""
        if not self.model or not hasattr(self.model, 'feature_importances_'):
            return {}
        
        # Nomes das features
        feature_names = []
        
        # Features do TF-IDF
        if self.vectorizer:
            feature_names.extend(self.vectorizer.get_feature_names_out())
        
        # Features numéricas
        numeric_features = [
            'years_experience',
            'has_leadership',
            'has_education',
            'tech_basic_count',
            'tech_intermediate_count',
            'tech_advanced_count',
            'tech_expert_count',
            'description_length',
            'responsibilities_count',
            'has_junior_keywords',
            'has_pleno_keywords',
            'has_senior_keywords',
            'has_expert_keywords'
        ]
        
        feature_names.extend(numeric_features)
        
        # Importâncias
        importances = self.model.feature_importances_
        
        # Criar dicionário ordenado
        feature_importance = {
            name: float(importance) 
            for name, importance in zip(feature_names, importances)
        }
        
        # Ordenar por importância
        return dict(sorted(
            feature_importance.items(),
            key=lambda x: x[1],
            reverse=True
        )[:20])  # Top 20 features


# Exemplo de uso
if __name__ == "__main__":
    # Criar classificador
    classifier = SeniorityClassifier()
    
    # Exemplo de classificação
    job_example = {
        'titulo': 'Desenvolvedor Python Sênior',
        'descricao': '''
        Buscamos desenvolvedor Python com 5+ anos de experiência.
        Responsabilidades:
        - Arquitetura de microserviços
        - Liderança técnica do time
        - Code review e mentoria
        - Implementação de CI/CD
        
        Requisitos:
        - Python avançado
        - Django/FastAPI
        - Docker e Kubernetes
        - AWS ou GCP
        - Metodologias ágeis
        '''
    }
    
    result = classifier.classify(
        job_example['titulo'],
        job_example['descricao']
    )
    
    print(f"\nClassificação: {result['level']}")
    print(f"Confiança: {result['confidence']:.2%}")
    print(f"\nProbabilidades:")
    for level, prob in result['probabilities'].items():
        print(f"  {level}: {prob:.2%}")
    print(f"\nRazões:")
    for reason in result['reasoning']:
        print(f"  - {reason}")