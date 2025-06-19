"""
Sistema de Validação Robusta de Dados

Este módulo implementa validação, correção automática e detecção
de anomalias para garantir a qualidade dos dados extraídos.

Funcionalidades:
- Schemas de validação para cada campo
- Correção automática de dados malformados
- Detecção de anomalias e valores suspeitos
- Relatório detalhado de qualidade
"""

import re
import statistics
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict
import unicodedata

try:
    from .structured_logger import structured_logger, Component, LogLevel
except ImportError:
    # Fallback se o logger não estiver disponível
    structured_logger = None
    Component = None
    LogLevel = None


@dataclass
class ValidationResult:
    """Resultado da validação de um campo"""
    field_name: str
    original_value: Any
    cleaned_value: Any
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    corrections_applied: List[str] = field(default_factory=list)
    quality_score: float = 1.0


@dataclass
class QualityReport:
    """Relatório de qualidade dos dados"""
    total_records: int
    valid_records: int
    overall_quality: float
    field_stats: Dict[str, Dict[str, Any]]
    anomalies: List[Dict[str, Any]]
    corrections_summary: Dict[str, int]
    timestamp: datetime = field(default_factory=datetime.now)


class DataCleaner:
    """Classe para limpeza e normalização de dados"""
    
    @staticmethod
    def normalize_text(text: str) -> str:
        """Normaliza texto removendo caracteres especiais e espaços extras"""
        if not text:
            return ""
        
        # Remove caracteres de controle e normaliza unicode
        text = ''.join(ch for ch in text if unicodedata.category(ch)[0] != 'C')
        text = unicodedata.normalize('NFKD', text)
        
        # Remove espaços múltiplos
        text = ' '.join(text.split())
        
        return text.strip()
    
    @staticmethod
    def fix_capitalization(text: str) -> str:
        """Corrige capitalização (Title Case inteligente)"""
        if not text:
            return ""
        
        # Lista de palavras que devem ficar em minúsculas
        lowercase_words = {'de', 'da', 'do', 'em', 'e', 'para', 'com', 'a', 'o'}
        
        words = text.lower().split()
        result = []
        
        for i, word in enumerate(words):
            # Primeira palavra sempre capitalizada
            if i == 0 or word not in lowercase_words:
                result.append(word.capitalize())
            else:
                result.append(word)
        
        return ' '.join(result)
    
    @staticmethod
    def extract_salary_range(text: str) -> Optional[Tuple[float, float]]:
        """Extrai valores numéricos de salário"""
        if not text:
            return None
        
        # Remove pontos de milhar e substitui vírgula por ponto
        text = text.replace('.', '').replace(',', '.')
        
        # Busca por padrões de valores
        pattern = r'R?\$?\s*(\d+(?:\.\d+)?)'
        matches = re.findall(pattern, text)
        
        if not matches:
            return None
        
        values = [float(match) for match in matches]
        
        if len(values) == 1:
            return (values[0], values[0])
        elif len(values) >= 2:
            return (min(values), max(values))
        
        return None
    
    @staticmethod
    def normalize_date(text: str) -> Optional[datetime]:
        """Normaliza datas para formato padrão"""
        if not text:
            return None
        
        text = text.lower()
        today = datetime.now()
        
        # Padrões relativos
        if 'hoje' in text:
            return today
        elif 'ontem' in text:
            return today - timedelta(days=1)
        
        # "há X dias"
        days_match = re.search(r'há\s*(\d+)\s*dias?', text)
        if days_match:
            days = int(days_match.group(1))
            return today - timedelta(days=days)
        
        # Data formato DD/MM/YYYY
        date_match = re.search(r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})', text)
        if date_match:
            try:
                day, month, year = map(int, date_match.groups())
                return datetime(year, month, day)
            except ValueError:
                pass
        
        return None


class FieldValidator:
    """Validador para campos individuais"""
    
    def __init__(self):
        self.cleaner = DataCleaner()
        self.schemas = self._initialize_schemas()
    
    def _initialize_schemas(self) -> Dict[str, Dict[str, Any]]:
        """Inicializa schemas de validação para cada campo"""
        return {
            'titulo': {
                'min_length': 5,
                'max_length': 200,
                'required': True,
                'blacklist_patterns': [
                    r'CLIQUE\s*AQUI', r'URGENTE', r'\$\$+', r'!!!+',
                    r'teste', r'test', r'xxx', r'delete'
                ],
                'must_contain_any': [
                    'desenvolvedor', 'developer', 'analista', 'analyst',
                    'engenheiro', 'engineer', 'designer', 'gerente', 'manager',
                    'coordenador', 'coordinator', 'especialista', 'specialist',
                    'consultor', 'consultant', 'arquiteto', 'architect',
                    'cientista', 'scientist', 'técnico', 'technician',
                    'auxiliar', 'assistente', 'assistant', 'estagiário'
                ]
            },
            'empresa': {
                'min_length': 3,
                'max_length': 100,
                'required': True,
                'blacklist_exact': ['Não informada', 'N/A', '-', 'null', 'undefined'],
                'blacklist_patterns': [r'^test', r'^\d+$', r'^[^a-zA-Z]+$'],
                'must_match_any': [r'[a-zA-Z]{2,}']  # Pelo menos 2 letras
            },
            'salario': {
                'formats': [
                    r'R?\$?\s*\d+\.?\d*(?:\s*-\s*R?\$?\s*\d+\.?\d*)?',
                    r'(?i)a\s*combinar',
                    r'(?i)competitive',
                    r'(?i)compatível'
                ],
                'min_value': 1000,
                'max_value': 100000,
                'anomaly_thresholds': {
                    'junior_max': 8000,
                    'pleno_min': 5000,
                    'pleno_max': 15000,
                    'senior_min': 8000
                }
            },
            'localizacao': {
                'min_length': 2,
                'max_length': 100,
                'required': True,
                'valid_patterns': [
                    r'(?i)home\s*office',
                    r'(?i)remoto',
                    r'(?i)híbrido',
                    r'(?i)presencial',
                    r'[A-Za-z\s-]+,?\s*-?\s*[A-Z]{2}'  # Cidade - UF
                ]
            },
            'descricao': {
                'min_length': 20,
                'max_length': 10000,
                'required': False,
                'quality_indicators': [
                    'responsabilidades', 'requisitos', 'benefícios',
                    'experiência', 'conhecimentos', 'habilidades'
                ]
            },
            'requisitos': {
                'min_length': 10,
                'max_length': 5000,
                'required': False,
                'should_contain_any': [
                    'experiência', 'conhecimento', 'formação',
                    'habilidade', 'domínio', 'fluência'
                ]
            },
            'beneficios': {
                'min_length': 5,
                'max_length': 2000,
                'required': False,
                'common_benefits': [
                    'vale', 'plano', 'auxílio', 'convênio',
                    'desconto', 'bônus', 'férias', 'seguro'
                ]
            },
            'nivel_experiencia': {
                'valid_values': [
                    'júnior', 'junior', 'pleno', 'sênior', 'senior',
                    'trainee', 'estagiário', 'especialista'
                ],
                'patterns': [r'\d+\s*anos?', r'(?i)experiência']
            },
            'modalidade': {
                'valid_values': [
                    'home office', 'remoto', 'presencial', 'híbrido',
                    'remote', 'hybrid', 'on-site'
                ]
            },
            'data_publicacao': {
                'max_days_ago': 90,
                'date_patterns': [
                    r'há\s*\d+\s*dias?',
                    r'hoje',
                    r'ontem',
                    r'\d{1,2}[/-]\d{1,2}[/-]\d{4}'
                ]
            }
        }
    
    def validate_field(self, field_name: str, value: Any) -> ValidationResult:
        """Valida um campo individual"""
        result = ValidationResult(
            field_name=field_name,
            original_value=value,
            cleaned_value=value,
            is_valid=True
        )
        
        # Limpar e normalizar
        if isinstance(value, str):
            cleaned = self.cleaner.normalize_text(value)
            result.cleaned_value = cleaned
            
            if cleaned != value:
                result.corrections_applied.append("texto_normalizado")
        else:
            cleaned = str(value) if value is not None else ""
            result.cleaned_value = cleaned
        
        # Obter schema
        schema = self.schemas.get(field_name, {})
        
        # Validações específicas por campo
        if field_name == 'titulo':
            result = self._validate_titulo(cleaned, schema, result)
        elif field_name == 'empresa':
            result = self._validate_empresa(cleaned, schema, result)
        elif field_name == 'salario':
            result = self._validate_salario(cleaned, schema, result)
        elif field_name == 'localizacao':
            result = self._validate_localizacao(cleaned, schema, result)
        elif field_name == 'data_publicacao':
            result = self._validate_data(cleaned, schema, result)
        else:
            # Validação genérica
            result = self._validate_generic(cleaned, schema, result)
        
        # Calcular score de qualidade
        result.quality_score = self._calculate_quality_score(result)
        
        return result
    
    def _validate_titulo(self, value: str, schema: Dict, result: ValidationResult) -> ValidationResult:
        """Valida título da vaga"""
        # Comprimento
        if len(value) < schema.get('min_length', 0):
            result.errors.append(f"Título muito curto ({len(value)} caracteres)")
            result.is_valid = False
        elif len(value) > schema.get('max_length', 999):
            result.errors.append(f"Título muito longo ({len(value)} caracteres)")
            result.is_valid = False
        
        # Blacklist
        for pattern in schema.get('blacklist_patterns', []):
            if re.search(pattern, value, re.IGNORECASE):
                result.errors.append(f"Título contém padrão inválido: {pattern}")
                result.is_valid = False
        
        # Must contain
        keywords = schema.get('must_contain_any', [])
        if keywords and not any(kw.lower() in value.lower() for kw in keywords):
            result.warnings.append("Título não contém palavras-chave esperadas")
        
        # Correção de capitalização
        if value.isupper() or value.islower():
            result.cleaned_value = self.cleaner.fix_capitalization(value)
            result.corrections_applied.append("capitalização_corrigida")
        
        return result
    
    def _validate_empresa(self, value: str, schema: Dict, result: ValidationResult) -> ValidationResult:
        """Valida nome da empresa"""
        # Valores inválidos exatos
        if value in schema.get('blacklist_exact', []):
            result.errors.append("Nome de empresa inválido")
            result.is_valid = False
            return result
        
        # Comprimento
        if len(value) < schema.get('min_length', 0):
            result.errors.append(f"Nome muito curto ({len(value)} caracteres)")
            result.is_valid = False
        
        # Padrões inválidos
        for pattern in schema.get('blacklist_patterns', []):
            if re.match(pattern, value):
                result.errors.append("Nome de empresa suspeito")
                result.is_valid = False
        
        # Deve conter letras
        if not re.search(r'[a-zA-Z]{2,}', value):
            result.errors.append("Nome deve conter pelo menos 2 letras")
            result.is_valid = False
        
        return result
    
    def _validate_salario(self, value: str, schema: Dict, result: ValidationResult) -> ValidationResult:
        """Valida salário"""
        if not value or value.lower() in ['a combinar', 'competitive', 'compatível']:
            # Válido mas sem valor específico
            return result
        
        # Extrair valores
        salary_range = self.cleaner.extract_salary_range(value)
        
        if salary_range:
            min_sal, max_sal = salary_range
            
            # Verificar limites
            if min_sal < schema.get('min_value', 0):
                result.warnings.append(f"Salário abaixo do mínimo esperado: R$ {min_sal}")
            
            if max_sal > schema.get('max_value', float('inf')):
                result.warnings.append(f"Salário acima do máximo esperado: R$ {max_sal}")
                result.errors.append("Possível erro de digitação no salário")
            
            # Formatar salário
            if min_sal == max_sal:
                result.cleaned_value = f"R$ {min_sal:,.2f}".replace(',', '.')
            else:
                result.cleaned_value = f"R$ {min_sal:,.2f} - R$ {max_sal:,.2f}".replace(',', '.')
            
            if result.cleaned_value != value:
                result.corrections_applied.append("formato_salario_padronizado")
        else:
            # Não conseguiu extrair valores
            valid_formats = schema.get('formats', [])
            if not any(re.match(fmt, value, re.IGNORECASE) for fmt in valid_formats):
                result.warnings.append("Formato de salário não reconhecido")
        
        return result
    
    def _validate_localizacao(self, value: str, schema: Dict, result: ValidationResult) -> ValidationResult:
        """Valida localização"""
        if len(value) < schema.get('min_length', 0):
            result.errors.append("Localização muito curta")
            result.is_valid = False
        
        # Padronizar formatos comuns
        replacements = {
            r'(?i)home\s*office': 'Home Office',
            r'(?i)remoto': 'Remoto',
            r'(?i)híbrido': 'Híbrido',
            r'(?i)presencial': 'Presencial'
        }
        
        cleaned = value
        for pattern, replacement in replacements.items():
            if re.search(pattern, value):
                cleaned = re.sub(pattern, replacement, value)
                break
        
        if cleaned != value:
            result.cleaned_value = cleaned
            result.corrections_applied.append("localização_padronizada")
        
        return result
    
    def _validate_data(self, value: str, schema: Dict, result: ValidationResult) -> ValidationResult:
        """Valida data de publicação"""
        if not value:
            result.warnings.append("Data não informada")
            return result
        
        # Normalizar data
        normalized_date = self.cleaner.normalize_date(value)
        
        if normalized_date:
            # Verificar se não é futura
            if normalized_date > datetime.now():
                result.errors.append("Data futura detectada")
                result.is_valid = False
            
            # Verificar idade máxima
            days_ago = (datetime.now() - normalized_date).days
            if days_ago > schema.get('max_days_ago', 90):
                result.warnings.append(f"Vaga muito antiga ({days_ago} dias)")
            
            # Formatar data
            result.cleaned_value = normalized_date.strftime('%Y-%m-%d')
            if result.cleaned_value != value:
                result.corrections_applied.append("data_normalizada")
        else:
            result.warnings.append("Formato de data não reconhecido")
        
        return result
    
    def _validate_generic(self, value: str, schema: Dict, result: ValidationResult) -> ValidationResult:
        """Validação genérica para outros campos"""
        # Comprimento
        min_len = schema.get('min_length', 0)
        max_len = schema.get('max_length', 999999)
        
        if len(value) < min_len:
            result.warnings.append(f"Valor muito curto ({len(value)} caracteres)")
        elif len(value) > max_len:
            result.warnings.append(f"Valor muito longo ({len(value)} caracteres)")
        
        return result
    
    def _calculate_quality_score(self, result: ValidationResult) -> float:
        """Calcula score de qualidade (0.0 a 1.0)"""
        if not result.is_valid:
            return 0.0
        
        score = 1.0
        
        # Penalizar por erros e avisos
        score -= len(result.errors) * 0.3
        score -= len(result.warnings) * 0.1
        
        # Bonus por correções aplicadas com sucesso
        score += len(result.corrections_applied) * 0.05
        
        return max(0.0, min(1.0, score))


class AnomalyDetector:
    """Detector de anomalias nos dados"""
    
    def __init__(self):
        self.historical_data = defaultdict(list)
        self.thresholds = {
            'salary_std_dev': 2.5,  # Desvios padrão para salário
            'title_length_std_dev': 3,
            'min_company_frequency': 0.001,  # Empresas muito raras
            'max_company_frequency': 0.1,    # Empresas com muitas vagas
        }
    
    def detect_anomalies(self, jobs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detecta anomalias em um conjunto de vagas"""
        anomalies = []
        
        # Coletar estatísticas
        salaries = []
        title_lengths = []
        company_counts = defaultdict(int)
        
        for job in jobs:
            # Salários
            if 'salario' in job and job['salario'] not in ['A combinar', 'Não informado']:
                salary_range = DataCleaner.extract_salary_range(job['salario'])
                if salary_range:
                    salaries.append(statistics.mean(salary_range))
            
            # Comprimento dos títulos
            if 'titulo' in job:
                title_lengths.append(len(job['titulo']))
            
            # Contagem de empresas
            if 'empresa' in job:
                company_counts[job['empresa']] += 1
        
        # Detectar anomalias de salário
        if len(salaries) > 2:
            mean_salary = statistics.mean(salaries)
            std_salary = statistics.stdev(salaries)
            
            for i, job in enumerate(jobs):
                if 'salario' in job and job['salario'] not in ['A combinar', 'Não informado']:
                    salary_range = DataCleaner.extract_salary_range(job['salario'])
                    if salary_range:
                        avg_salary = statistics.mean(salary_range)
                        z_score = abs((avg_salary - mean_salary) / std_salary) if std_salary > 0 else 0
                        
                        if z_score > self.thresholds['salary_std_dev']:
                            anomalies.append({
                                'type': 'salary_outlier',
                                'job_index': i,
                                'job_title': job.get('titulo', 'N/A'),
                                'value': job['salario'],
                                'z_score': z_score,
                                'severity': 'high' if z_score > 3 else 'medium'
                            })
        
        # Detectar títulos anômalos
        if len(title_lengths) > 2:
            mean_length = statistics.mean(title_lengths)
            std_length = statistics.stdev(title_lengths)
            
            for i, job in enumerate(jobs):
                if 'titulo' in job:
                    length = len(job['titulo'])
                    z_score = abs((length - mean_length) / std_length) if std_length > 0 else 0
                    
                    if z_score > self.thresholds['title_length_std_dev']:
                        anomalies.append({
                            'type': 'title_length_anomaly',
                            'job_index': i,
                            'job_title': job['titulo'][:50] + '...' if len(job['titulo']) > 50 else job['titulo'],
                            'length': length,
                            'severity': 'low'
                        })
        
        # Detectar empresas suspeitas
        total_jobs = len(jobs)
        for company, count in company_counts.items():
            frequency = count / total_jobs
            
            if frequency > self.thresholds['max_company_frequency']:
                anomalies.append({
                    'type': 'company_flooding',
                    'company': company,
                    'count': count,
                    'percentage': f"{frequency*100:.1f}%",
                    'severity': 'medium'
                })
        
        # Detectar padrões suspeitos
        for i, job in enumerate(jobs):
            # Vagas com muitos caracteres especiais
            if 'titulo' in job:
                special_chars = len(re.findall(r'[!@#$%^&*()+=\[\]{}|\\:;"<>?]', job['titulo']))
                if special_chars > 5:
                    anomalies.append({
                        'type': 'suspicious_title',
                        'job_index': i,
                        'job_title': job['titulo'],
                        'reason': 'excessive_special_chars',
                        'severity': 'medium'
                    })
            
            # Empresas genéricas
            if 'empresa' in job:
                generic_patterns = ['empresa', 'company', 'confidencial', 'sigiloso']
                if any(pattern in job['empresa'].lower() for pattern in generic_patterns):
                    anomalies.append({
                        'type': 'generic_company',
                        'job_index': i,
                        'company': job['empresa'],
                        'severity': 'low'
                    })
        
        return anomalies


class DataValidator:
    """Validador principal que orquestra todo o processo"""
    
    def __init__(self):
        self.field_validator = FieldValidator()
        self.anomaly_detector = AnomalyDetector()
        self.validation_history = []
    
    def validate_job(self, job: Dict[str, Any]) -> Dict[str, Any]:
        """Valida uma vaga individual"""
        validated_job = job.copy()
        field_results = {}
        total_score = 0
        field_count = 0
        
        # Validar cada campo
        for field_name, value in job.items():
            if field_name in self.field_validator.schemas:
                result = self.field_validator.validate_field(field_name, value)
                field_results[field_name] = result
                
                # Aplicar valor limpo
                validated_job[field_name] = result.cleaned_value
                
                # Acumular score
                total_score += result.quality_score
                field_count += 1
        
        # Calcular score geral
        overall_score = total_score / field_count if field_count > 0 else 0
        
        # Adicionar metadados de validação
        validated_job['_validation'] = {
            'timestamp': datetime.now().isoformat(),
            'quality_score': overall_score,
            'field_results': field_results,
            'is_valid': all(r.is_valid for r in field_results.values())
        }
        
        return validated_job
    
    def validate_batch(self, jobs: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], QualityReport]:
        """Valida um lote de vagas e gera relatório"""
        if structured_logger:
            structured_logger.validation_log(
                f"Starting batch validation of {len(jobs)} jobs",
                operation="validate_batch",
                context={'job_count': len(jobs)}
            )
        
        validated_jobs = []
        field_stats = defaultdict(lambda: {
            'total': 0,
            'valid': 0,
            'errors': 0,
            'warnings': 0,
            'corrections': 0
        })
        corrections_summary = defaultdict(int)
        
        # Validar cada vaga
        for job in jobs:
            validated_job = self.validate_job(job)
            validated_jobs.append(validated_job)
            
            # Coletar estatísticas
            for field_name, result in validated_job['_validation']['field_results'].items():
                stats = field_stats[field_name]
                stats['total'] += 1
                if result.is_valid:
                    stats['valid'] += 1
                stats['errors'] += len(result.errors)
                stats['warnings'] += len(result.warnings)
                stats['corrections'] += len(result.corrections_applied)
                
                # Contar correções
                for correction in result.corrections_applied:
                    corrections_summary[correction] += 1
        
        # Detectar anomalias
        anomalies = self.anomaly_detector.detect_anomalies(validated_jobs)
        
        # Calcular estatísticas finais
        valid_jobs = [j for j in validated_jobs if j['_validation']['is_valid']]
        overall_quality = len(valid_jobs) / len(validated_jobs) if validated_jobs else 0
        
        # Calcular qualidade por campo
        for field_name, stats in field_stats.items():
            stats['quality_percentage'] = (stats['valid'] / stats['total'] * 100) if stats['total'] > 0 else 0
        
        # Gerar relatório
        report = QualityReport(
            total_records=len(jobs),
            valid_records=len(valid_jobs),
            overall_quality=overall_quality,
            field_stats=dict(field_stats),
            anomalies=anomalies,
            corrections_summary=dict(corrections_summary)
        )
        
        # Armazenar no histórico
        self.validation_history.append(report)
        
        return validated_jobs, report
    
    def print_quality_report(self, report: QualityReport):
        """Imprime relatório de qualidade formatado"""
        print("\n📊 RELATÓRIO DE QUALIDADE DOS DADOS")
        print("=" * 50)
        print(f"📅 Data: {report.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🔍 Total de vagas analisadas: {report.total_records}")
        print(f"\n✅ QUALIDADE GERAL: {report.overall_quality:.1%}")
        print(f"   Vagas válidas: {report.valid_records}/{report.total_records}")
        
        # Estatísticas por campo
        print("\n📋 POR CAMPO:")
        for field_name, stats in sorted(report.field_stats.items()):
            quality = stats['quality_percentage']
            symbol = "✅" if quality >= 80 else "⚠️" if quality >= 60 else "❌"
            print(f"   {symbol} {field_name}: {quality:.0f}% válidos", end="")
            
            if stats['corrections'] > 0:
                print(f" ({stats['corrections']} corrigidos)", end="")
            if stats['warnings'] > 0:
                print(f" [{stats['warnings']} avisos]", end="")
            print()
        
        # Anomalias
        if report.anomalies:
            print(f"\n⚠️  ANOMALIAS DETECTADAS: {len(report.anomalies)}")
            
            # Agrupar por tipo
            anomaly_types = defaultdict(list)
            for anomaly in report.anomalies:
                anomaly_types[anomaly['type']].append(anomaly)
            
            for atype, items in anomaly_types.items():
                print(f"   • {atype}: {len(items)} casos")
                # Mostrar exemplos (máx 2)
                for item in items[:2]:
                    if 'job_title' in item:
                        print(f"     - {item['job_title'][:50]}...")
                    elif 'company' in item:
                        print(f"     - {item['company']}")
        
        # Correções aplicadas
        if report.corrections_summary:
            print(f"\n🔧 CORREÇÕES AUTOMÁTICAS: {sum(report.corrections_summary.values())}")
            for correction, count in sorted(report.corrections_summary.items(), 
                                          key=lambda x: x[1], reverse=True):
                print(f"   • {correction}: {count}")
        
        # Tendências (se houver histórico)
        if len(self.validation_history) > 1:
            prev_report = self.validation_history[-2]
            quality_change = report.overall_quality - prev_report.overall_quality
            
            print("\n📈 TENDÊNCIAS:")
            if quality_change > 0:
                print(f"   ✅ Qualidade melhorou {quality_change:.1%} vs. última execução")
            elif quality_change < 0:
                print(f"   ⚠️  Qualidade piorou {abs(quality_change):.1%} vs. última execução")
            else:
                print("   ➡️  Qualidade mantida vs. última execução")


# Instância global para uso
data_validator = DataValidator()