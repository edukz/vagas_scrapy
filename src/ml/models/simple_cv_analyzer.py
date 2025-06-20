"""
Analisador de Currículos Simplificado
====================================

Versão sem dependências externas pesadas para funcionar em qualquer ambiente.
Foca na extração de informações e criação de perfis sem Machine Learning complexo.
"""

import re
import json
import io
from typing import Dict, List, Tuple, Optional, Union
from dataclasses import dataclass, asdict
from pathlib import Path
from collections import Counter, defaultdict
from datetime import datetime

# Imports opcionais para suporte a PDF/DOCX
try:
    import PyPDF2
    HAS_PDF_SUPPORT = True
except ImportError:
    HAS_PDF_SUPPORT = False

try:
    import pdfplumber
    HAS_PDFPLUMBER = True
except ImportError:
    HAS_PDFPLUMBER = False

try:
    import docx
    HAS_DOCX_SUPPORT = True
except ImportError:
    HAS_DOCX_SUPPORT = False

# Imports para OCR (reconhecimento de imagens)
try:
    import easyocr
    from PIL import Image
    import fitz  # PyMuPDF - mais independente que pdf2image
    HAS_OCR_SUPPORT = True
    OCR_ENGINE = "easyocr"
except ImportError:
    try:
        import pytesseract
        from PIL import Image
        try:
            import pdf2image
        except ImportError:
            import fitz  # Fallback para PyMuPDF
        HAS_OCR_SUPPORT = True
        OCR_ENGINE = "tesseract"
    except ImportError:
        HAS_OCR_SUPPORT = False
        OCR_ENGINE = None


@dataclass
class SimpleCVResult:
    """Resultado simplificado da análise do currículo"""
    personal_info: Dict[str, str]
    skills: Dict[str, List[str]]
    experience: Dict[str, Union[int, str, List]]
    education: Dict[str, Union[str, List]]
    preferences: Dict[str, Union[str, List]]
    seniority_level: str
    estimated_salary_range: Dict[str, float]
    confidence_score: float
    
    def to_dict(self) -> Dict:
        return asdict(self)


class SimpleCVAnalyzer:
    """
    Analisador de currículos simplificado sem dependências externas
    """
    
    def __init__(self):
        # Tecnologias por categoria (versão ampliada para OCR)
        self.tech_categories = {
            'linguagens': {
                'python', 'java', 'javascript', 'typescript', 'c++', 'c#', 'php', 
                'ruby', 'go', 'rust', 'kotlin', 'swift', 'scala', 'r', 'sql'
            },
            'frontend': {
                'react', 'angular', 'vue', 'svelte', 'html', 'css', 'sass',
                'jquery', 'bootstrap', 'tailwind', 'tkinter'
            },
            'backend': {
                'node.js', 'express', 'django', 'flask', 'spring', 'laravel',
                'rails', '.net', 'fastapi'
            },
            'mobile': {
                'react native', 'flutter', 'ionic', 'xamarin', 'android', 'ios'
            },
            'databases': {
                'mysql', 'postgresql', 'mongodb', 'redis', 'sqlite', 'oracle',
                'cassandra', 'elasticsearch'
            },
            'cloud_devops': {
                'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'terraform',
                'jenkins', 'gitlab ci', 'github actions'
            },
            'data_science': {
                'pandas', 'numpy', 'scikit-learn', 'tensorflow', 'pytorch',
                'tableau', 'power bi', 'jupyter', 'spark', 'matplotlib', 'plotly'
            },
            'tools_libs': {
                'opencv', 'selenium', 'beautiful soup', 'pyautogui', 'streamlit',
                'yolo', 'cnn', 'etl', 'api'
            },
            'web_scraping': {
                'selenium', 'beautiful soup', 'scrapy', 'requests', 'web scraping'
            },
            'automation': {
                'automation', 'bot', 'pyautogui', 'rpa'
            }
        }
        
        # Todas as tecnologias em um set
        self.all_technologies = set()
        for category in self.tech_categories.values():
            self.all_technologies.update(category)
        
        # Soft skills
        self.soft_skills = {
            'liderança', 'comunicação', 'trabalho em equipe', 'gestão de projetos',
            'resolução de problemas', 'criatividade', 'adaptabilidade', 'organização',
            'proatividade', 'autonomia', 'colaboração', 'mentoria'
        }
        
        # Padrões regex para extração
        self.patterns = {
            'email': re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
            'phone': re.compile(r'(?:\+55\s?)?(?:\(?[1-9][1-9]\)?\s?)?(?:9\s?)?[0-9]{4}[-\s]?[0-9]{4}'),
            'linkedin': re.compile(r'linkedin\.com/in/([A-Za-z0-9-]+)'),
            'github': re.compile(r'github\.com/([A-Za-z0-9-]+)'),
            'years_experience': re.compile(r'(\d+)\s*(?:anos?|years?)\s*(?:de\s*)?(?:experiência|experience)', re.I),
            'salary': re.compile(r'(?:R\$|salário)[\s]*(\d{1,3}(?:\.\d{3})*(?:,\d{2})?)', re.I),
        }
        
        # Níveis de senioridade
        self.seniority_keywords = {
            'estagiario': ['estagiário', 'trainee', 'aprendiz', 'intern'],
            'junior': ['júnior', 'junior', 'jr', 'iniciante'],
            'pleno': ['pleno', 'analista', 'desenvolvedor'],
            'senior': ['sênior', 'senior', 'sr', 'especialista'],
            'lider': ['arquiteto', 'tech lead', 'líder técnico', 'coordenador'],
            'gerente': ['gerente', 'manager', 'diretor']
        }
    
    def analyze_cv(self, file_path: str, user_id: str = None) -> SimpleCVResult:
        """Analisa um currículo e retorna informações extraídas"""
        print(f"📄 Analisando currículo: {file_path}")
        
        # Extrair texto
        text = self._extract_text(file_path)
        if not text:
            raise ValueError("Não foi possível extrair texto do arquivo")
        
        # Extrair informações
        personal_info = self._extract_personal_info(text)
        skills = self._extract_skills(text)
        experience = self._extract_experience(text)
        education = self._extract_education(text)
        preferences = self._extract_preferences(text)
        
        # Determinar senioridade
        seniority = self._determine_seniority(text, experience)
        
        # Estimar salário
        salary_range = self._estimate_salary(skills, seniority, personal_info.get('location'))
        
        # Calcular confiança
        confidence = self._calculate_confidence(personal_info, skills, experience)
        
        result = SimpleCVResult(
            personal_info=personal_info,
            skills=skills,
            experience=experience,
            education=education,
            preferences=preferences,
            seniority_level=seniority,
            estimated_salary_range=salary_range,
            confidence_score=confidence
        )
        
        print(f"✅ Análise concluída com {confidence:.1%} de confiança")
        return result
    
    def _extract_text(self, file_path: str) -> str:
        """Extrai texto do arquivo (TXT, PDF, DOCX)"""
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {file_path}")
        
        ext = file_path.suffix.lower()
        
        if ext == '.txt':
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        
        elif ext == '.pdf':
            return self._extract_from_pdf(file_path)
        
        elif ext in ['.docx', '.doc']:
            return self._extract_from_docx(file_path)
        
        else:
            raise ValueError(f"Formato não suportado: {ext}")
    
    def _extract_from_pdf(self, file_path: Path) -> str:
        """Extrai texto de PDF com múltiplas bibliotecas"""
        text = ""
        
        # Método 1: Tentar pdfplumber primeiro (melhor qualidade)
        if HAS_PDFPLUMBER:
            try:
                import pdfplumber
                with pdfplumber.open(file_path) as pdf:
                    for page in pdf.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + "\n"
                if text.strip():
                    print("✅ PDF extraído com pdfplumber")
                    return text
            except Exception as e:
                print(f"⚠️ pdfplumber falhou: {e}")
        
        # Método 2: Fallback para PyPDF2
        if HAS_PDF_SUPPORT and not text.strip():
            try:
                with open(file_path, 'rb') as file:
                    reader = PyPDF2.PdfReader(file)
                    text = ""
                    for page in reader.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + "\n"
                if text.strip():
                    print("✅ PDF extraído com PyPDF2")
                    return text
            except Exception as e:
                print(f"⚠️ PyPDF2 falhou: {e}")
        
        # Método 3: Tentar OCR se PDF parece ser uma imagem
        if not text.strip() and HAS_OCR_SUPPORT:
            print("🔍 PDF sem texto detectado. Tentando OCR...")
            try:
                text = self._extract_with_ocr(file_path)
                if text.strip():
                    print("✅ Texto extraído com OCR!")
                    return text
            except Exception as e:
                print(f"⚠️ OCR falhou: {e}")
        
        # Método 4: Erro se nada funcionou
        if not text.strip():
            if not HAS_PDF_SUPPORT and not HAS_PDFPLUMBER:
                raise ValueError("❌ Nenhuma biblioteca PDF instalada. Execute: pip install PyPDF2 pdfplumber")
            elif not HAS_OCR_SUPPORT:
                raise ValueError(f"❌ PDF '{file_path.name}' parece ser uma imagem escaneada.\n"
                               f"   💡 Soluções:\n"
                               f"   • Instale OCR: pip install pytesseract Pillow pdf2image\n"
                               f"   • Use um PDF com texto ou converta para TXT\n"
                               f"   • Para PDFs escaneados, o OCR pode extrair o texto")
            else:
                raise ValueError(f"❌ Não foi possível extrair texto do PDF '{file_path.name}'.\n"
                               f"   💡 Possíveis causas:\n"
                               f"   • PDF está corrompido ou protegido\n"
                               f"   • Qualidade da imagem muito baixa para OCR\n"
                               f"   • Tente converter para TXT ou usar outro arquivo")
        
        return text
    
    def _extract_with_ocr(self, file_path: Path) -> str:
        """Extrai texto de PDF usando OCR (para PDFs escaneados)"""
        if not HAS_OCR_SUPPORT:
            raise ValueError("OCR não disponível")
        
        try:
            # Converter PDF para imagens usando PyMuPDF
            print("🔄 Convertendo PDF para imagens...")
            doc = fitz.open(file_path)
            pages = []
            
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                # Converter para imagem PIL
                pix = page.get_pixmap()
                img_data = pix.tobytes("ppm")
                img = Image.open(io.BytesIO(img_data))
                pages.append(img)
            
            doc.close()
            print(f"✅ {len(pages)} página(s) convertida(s)")
            
            text = ""
            
            if OCR_ENGINE == "easyocr":
                # Usar EasyOCR (mais fácil, não precisa de Tesseract instalado)
                print("🤖 Usando EasyOCR para extração de texto...")
                reader = easyocr.Reader(['pt', 'en'], gpu=False)  # português e inglês
                
                for i, page in enumerate(pages):
                    print(f"🔍 Processando página {i+1}/{len(pages)} com EasyOCR...")
                    
                    # Converter PIL Image para numpy array
                    import numpy as np
                    page_array = np.array(page)
                    
                    # Extrair texto
                    results = reader.readtext(page_array)
                    
                    page_text = ""
                    for (bbox, text_detected, confidence) in results:
                        if confidence > 0.4:  # Baixar threshold para capturar mais
                            # Adicionar quebra de linha baseada na posição vertical
                            page_text += text_detected + "\n"
                    
                    if page_text.strip():
                        text += page_text + "\n"
                        print(f"   ✅ {len(page_text)} caracteres extraídos")
                    else:
                        print("   ⚠️ Nenhum texto detectado nesta página")
            
            elif OCR_ENGINE == "tesseract":
                # Usar Tesseract (precisa estar instalado)
                import subprocess
                try:
                    subprocess.run(['tesseract', '--version'], capture_output=True, check=True)
                except (subprocess.CalledProcessError, FileNotFoundError):
                    raise ValueError("❌ Tesseract OCR não está instalado.\n"
                                   "   💡 Para instalar:\n"
                                   "   • Ubuntu/Debian: sudo apt install tesseract-ocr tesseract-ocr-por\n"
                                   "   • Windows: baixe de https://github.com/UB-Mannheim/tesseract/wiki\n"
                                   "   • macOS: brew install tesseract")
                
                print("🤖 Usando Tesseract para extração de texto...")
                
                for i, page in enumerate(pages):
                    print(f"🔍 Processando página {i+1}/{len(pages)} com Tesseract...")
                    
                    try:
                        page_text = pytesseract.image_to_string(page, lang='por+eng')
                    except:
                        page_text = pytesseract.image_to_string(page, lang='eng')
                    
                    if page_text.strip():
                        text += page_text + "\n"
            
            if text.strip():
                print(f"✅ OCR concluído: {len(text)} caracteres extraídos com {OCR_ENGINE}")
                return text
            else:
                print("⚠️ OCR não encontrou texto legível")
                return ""
                
        except Exception as e:
            print(f"❌ Erro no OCR: {e}")
            raise ValueError(f"Erro no OCR: {e}")
    
    def _extract_from_docx(self, file_path: Path) -> str:
        """Extrai texto de DOCX"""
        if not HAS_DOCX_SUPPORT:
            raise ValueError("❌ python-docx não instalado. Execute: pip install python-docx")
        
        try:
            doc = docx.Document(file_path)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            print("✅ DOCX extraído com python-docx")
            return text
        except Exception as e:
            raise ValueError(f"❌ Erro ao ler DOCX: {e}")
    
    def _extract_personal_info(self, text: str) -> Dict[str, str]:
        """Extrai informações pessoais"""
        info = {}
        
        # Email - padrão mais flexível para OCR
        email_patterns = [
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            r'\b[A-Za-z0-9._%+-]+\s*@\s*[A-Za-z0-9.-]+\s*\.\s*[A-Za-z]{2,}\b',  # Com espaços
            r'([A-Za-z0-9._%+-]+)\s*@\s*([A-Za-z0-9.-]+)\s+com\b',  # "@gmail com"
            r'([A-Za-z0-9._%+-]+)\s+com\b'  # "edukz93@gmail com"
        ]
        
        for pattern in email_patterns:
            email_match = re.search(pattern, text, re.I)
            if email_match:
                email_text = email_match.group()
                
                # Corrigir variações de OCR
                if '@' not in email_text and ' com' in email_text:
                    # Caso "edukz93 gmail com" ou similar
                    email_parts = email_text.replace(' com', '.com').split()
                    if len(email_parts) >= 2:
                        email = email_parts[0] + '@' + email_parts[1]
                    else:
                        continue
                else:
                    email = email_text.replace(' com', '.com').replace(' ', '')
                
                if '@' in email and '.' in email and len(email) > 5:
                    info['email'] = email
                    break
        
        # Telefone - padrão mais flexível
        phone_patterns = [
            r'(?:\+55\s?)?(?:\(?[1-9][1-9]\)?\s?)?(?:9\s?)?[0-9]{4}[-\s]?[0-9]{4}',
            r'\(\s*\d{2}\s*\)\s*\d{4,5}[-\s]?\d{4}',  # (18) 98199-5533
            r'\d{1}\s*\(\s*\d{2}\s*\)\s*\d{4,5}[-\s]?\d{4}'  # 0 (18) 98199-5533
        ]
        
        for pattern in phone_patterns:
            phone_match = re.search(pattern, text)
            if phone_match:
                info['phone'] = phone_match.group().strip()
                break
        
        # LinkedIn
        linkedin_patterns = [
            r'linkedin\.com/in/([A-Za-z0-9-]+)',
            r'linkedin\s+com\s*/in/([A-Za-z0-9-]+)',  # OCR pode adicionar espaços
            r'/in/([A-Za-z0-9-]+)'
        ]
        
        for pattern in linkedin_patterns:
            linkedin_match = re.search(pattern, text, re.I)
            if linkedin_match:
                info['linkedin'] = linkedin_match.group(1)
                break
        
        # GitHub
        github_patterns = [
            r'github\.com/([A-Za-z0-9-]+)',
            r'github\s+com/([A-Za-z0-9-]+)'  # OCR pode adicionar espaços
        ]
        
        for pattern in github_patterns:
            github_match = re.search(pattern, text, re.I)
            if github_match:
                info['github'] = github_match.group(1)
                break
        
        # Nome - buscar padrões mais específicos
        lines = text.split('\n')
        
        # Primeiro buscar padrão específico "EDUARDO K. INAGAKI" no texto
        name_pattern = r'\b[A-ZÁÉÍÓÚÂÊÎÔÛÃÕÇ][A-Za-záéíóúâêîôûãõç]+(?:\s+[A-ZÁÉÍÓÚÂÊÎÔÛÃÕÇ]\.?)?\s+[A-ZÁÉÍÓÚÂÊÎÔÛÃÕÇ][A-Za-záéíóúâêîôûãõç]+\b'
        name_match = re.search(name_pattern, text)
        if name_match:
            name_candidate = name_match.group().strip()
            # Verificar se não é cargo
            if not any(word in name_candidate.upper() for word in ['DESENVOLVEDOR', 'ENGENHEIRO', 'ANALISTA', 'CIENTISTA', 'GERENTE', 'BACK-END', 'DADOS']):
                words = name_candidate.split()
                if 2 <= len(words) <= 4:
                    info['name'] = name_candidate
        
        # Segundo tentar encontrar nomes em maiúscula no início das linhas
        if 'name' not in info:
            for line in lines[:10]:
                line = line.strip()
                # Nome em maiúscula com 2-4 palavras
                if re.match(r'^[A-ZÁÉÍÓÚÂÊÎÔÛÃÕÇ][A-ZÁÉÍÓÚÂÊÎÔÛÃÕÇ\s\.]{5,40}$', line):
                    # Verificar se não é um título/cargo
                    if not any(word in line.upper() for word in ['DESENVOLVEDOR', 'ENGENHEIRO', 'ANALISTA', 'CIENTISTA', 'GERENTE']):
                        words = line.split()
                        if 2 <= len(words) <= 4:
                            info['name'] = line
                            break
        
        # Se não encontrou, buscar padrão normal
        if 'name' not in info:
            for line in lines[:5]:
                line = line.strip()
                if line and len(line.split()) >= 2 and len(line) < 60:
                    if not any(char.isdigit() for char in line):
                        # Verificar se parece com nome (não é cargo ou descrição)
                        if not any(word in line.upper() for word in ['DESENVOLVEDOR', 'BACK-END', 'CIENTISTA', 'CONTATO']):
                            info['name'] = line
                            break
        
        # Localização - padrões mais flexíveis
        location_patterns = [
            r'São Paulo[,\s]*Brasil',
            r'([A-ZÁÉÍÓÚÂÊÎÔÛÃÕÇ][a-záéíóúâêîôûãõç]+(?:\s+[A-ZÁÉÍÓÚÂÊÎÔÛÃÕÇ][a-záéíóúâêîôûãõç]+)*)[,\s]*[-]\s*([A-Z]{2})',
            r'([A-ZÁÉÍÓÚÂÊÎÔÛÃÕÇ][a-záéíóúâêîôûãõç]+)[,\s]+([A-ZÁÉÍÓÚÂÊÎÔÛÃÕÇ][a-záéíóúâêîôûãõç]+)',
            r'(?:localização|cidade):\s*([^,\n]+)'
        ]
        
        for pattern in location_patterns:
            match = re.search(pattern, text, re.I)
            if match:
                if 'São Paulo' in match.group():
                    info['location'] = 'São Paulo, Brasil'
                else:
                    info['location'] = match.group(1).strip()
                break
        
        return info
    
    def _extract_skills(self, text: str) -> Dict[str, List[str]]:
        """Extrai habilidades técnicas e soft skills"""
        # Normalizar texto para OCR (remover espaços extras, etc.)
        text_normalized = re.sub(r'\s+', ' ', text.lower())
        
        skills = {
            'technical': [],
            'soft': [],
            'by_category': {}
        }
        
        # Tecnologias por categoria - busca mais flexível para OCR
        for category, techs in self.tech_categories.items():
            found_techs = []
            for tech in techs:
                # Busca exata
                if tech in text_normalized:
                    found_techs.append(tech)
                    skills['technical'].append(tech)
                # Busca com variações de OCR
                elif self._find_tech_variations(tech, text_normalized):
                    found_techs.append(tech)
                    skills['technical'].append(tech)
            
            if found_techs:
                skills['by_category'][category] = found_techs
        
        # Soft skills
        for skill in self.soft_skills:
            if skill in text_normalized:
                skills['soft'].append(skill)
        
        # Remover duplicatas
        skills['technical'] = list(set(skills['technical']))
        skills['soft'] = list(set(skills['soft']))
        
        return skills
    
    def _find_tech_variations(self, tech: str, text: str) -> bool:
        """Encontra variações de tecnologias considerando erros de OCR"""
        # Variações comuns de OCR
        variations = {
            'python': ['python', 'pythan', 'pyfhon', 'pytlon'],
            'javascript': ['javascript', 'java script', 'javascriot', 'javascr1pt'],
            'tensorflow': ['tensorflow', 'tensor flow', 'tensorflaw', 'tensorllow'],
            'opencv': ['opencv', 'open cv', 'opency', 'openc v'],
            'postgresql': ['postgresql', 'postgres ql', 'postgre sql', 'postg resql'],
            'mongodb': ['mongodb', 'mongo db', 'mongodo', 'mongo do'],
            'beautiful soup': ['beautiful soup', 'beautifulsoup', 'beautiul soup', 'beutiful soup'],
            'scikit-learn': ['scikit-learn', 'scikit learn', 'scikit-leam', 'scikit-lern'],
            'machine learning': ['machine learning', 'machinelearning', 'machine leaming', 'machine learming'],
            'web scraping': ['web scraping', 'webscraping', 'web scrapping', 'web scrapmg']
        }
        
        # Se existe variação específica, usar ela
        if tech in variations:
            return any(var in text for var in variations[tech])
        
        # Senão, busca padrão flexível (permite algumas diferenças)
        # Remove caracteres especiais e espaços
        tech_clean = re.sub(r'[^a-z0-9]', '', tech)
        
        # Busca versões com espaços
        tech_spaced = tech.replace('-', ' ').replace('.', ' ')
        if tech_spaced in text:
            return True
        
        # Busca versão sem caracteres especiais
        text_clean = re.sub(r'[^a-z0-9\s]', '', text)
        if tech_clean in text_clean.replace(' ', ''):
            return True
        
        return False
    
    def _extract_experience(self, text: str) -> Dict[str, Union[int, str, List]]:
        """Extrai experiência profissional"""
        experience = {
            'total_years': 0,
            'companies': [],
            'positions': [],
            'current_position': ''
        }
        
        # Anos de experiência
        years_match = self.patterns['years_experience'].search(text)
        if years_match:
            experience['total_years'] = int(years_match.group(1))
        
        # Empresas e posições (padrões simples)
        company_patterns = [
            r'([A-Z][a-z\s&]+(?:S\.?A\.?|LTDA\.?|Inc\.?|Corp\.?))',
            r'(?:empresa|company):\s*([^,\n]+)'
        ]
        
        position_patterns = [
            r'((?:Desenvolvedor|Analista|Gerente|Coordenador|Diretor)[^,\n]*)',
            r'(?:cargo|position):\s*([^,\n]+)'
        ]
        
        for pattern in company_patterns:
            matches = re.findall(pattern, text, re.I)
            experience['companies'].extend([m.strip() for m in matches])
        
        for pattern in position_patterns:
            matches = re.findall(pattern, text, re.I)
            experience['positions'].extend([m.strip() for m in matches])
        
        if experience['positions']:
            experience['current_position'] = experience['positions'][-1]
        
        return experience
    
    def _extract_education(self, text: str) -> Dict[str, Union[str, List]]:
        """Extrai informações educacionais"""
        education = {
            'degree': '',
            'institution': '',
            'courses': []
        }
        
        # Formação
        degree_patterns = [
            r'(?:graduação em|bacharel em|degree in)\s*([^,\n]+)',
            r'((?:Engenharia|Ciência|Bacharelado)[^,\n]*)'
        ]
        
        for pattern in degree_patterns:
            match = re.search(pattern, text, re.I)
            if match:
                education['degree'] = match.group(1).strip()
                break
        
        # Instituição
        institution_patterns = [
            r'(?:universidade|faculdade|university)\s*([^,\n]+)',
            r'([A-Z]{3,}(?:\s+[A-Z]{2,})*)'
        ]
        
        for pattern in institution_patterns:
            match = re.search(pattern, text, re.I)
            if match:
                education['institution'] = match.group(1).strip()
                break
        
        return education
    
    def _extract_preferences(self, text: str) -> Dict[str, Union[str, List]]:
        """Extrai preferências de trabalho"""
        preferences = {
            'work_mode': 'hibrido',
            'salary_expectation': None
        }
        
        text_lower = text.lower()
        
        # Modalidade de trabalho
        if any(word in text_lower for word in ['remoto', 'remote', 'home office']):
            preferences['work_mode'] = 'remoto'
        elif any(word in text_lower for word in ['híbrido', 'hybrid', 'flexível']):
            preferences['work_mode'] = 'hibrido'
        elif any(word in text_lower for word in ['presencial', 'escritório']):
            preferences['work_mode'] = 'presencial'
        
        # Expectativa salarial
        salary_match = self.patterns['salary'].search(text)
        if salary_match:
            try:
                salary_str = salary_match.group(1).replace('.', '').replace(',', '.')
                preferences['salary_expectation'] = float(salary_str)
            except ValueError:
                pass
        
        return preferences
    
    def _determine_seniority(self, text: str, experience: Dict) -> str:
        """Determina nível de senioridade"""
        text_lower = text.lower()
        
        # Buscar palavras-chave
        for level, keywords in self.seniority_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                return level
        
        # Basear em anos de experiência
        years = experience.get('total_years', 0)
        if years <= 2:
            return 'junior'
        elif years <= 5:
            return 'pleno'
        elif years <= 8:
            return 'senior'
        else:
            return 'lider'
    
    def _estimate_salary(self, skills: Dict, seniority: str, location: str = None) -> Dict[str, float]:
        """Estima faixa salarial"""
        base_salaries = {
            'estagiario': 1500,
            'junior': 3500,
            'pleno': 7000,
            'senior': 12000,
            'lider': 18000,
            'gerente': 25000
        }
        
        base = base_salaries.get(seniority, 7000)
        
        # Multiplicador por tecnologias
        tech_count = len(skills.get('technical', []))
        tech_multiplier = 1 + (tech_count * 0.05)  # 5% por tecnologia
        
        # Multiplicador por localização
        location_multiplier = 1.0
        if location:
            location_lower = location.lower()
            if 'são paulo' in location_lower:
                location_multiplier = 1.25
            elif 'rio de janeiro' in location_lower:
                location_multiplier = 1.15
            elif 'remoto' in location_lower:
                location_multiplier = 1.05
        
        estimated = base * tech_multiplier * location_multiplier
        
        return {
            'min': round(estimated * 0.85, -2),
            'max': round(estimated * 1.15, -2),
            'median': round(estimated, -2)
        }
    
    def _calculate_confidence(self, personal_info: Dict, skills: Dict, experience: Dict) -> float:
        """Calcula confiança na análise"""
        confidence = 0.0
        
        # Informações pessoais (+30%)
        if personal_info.get('email'):
            confidence += 0.1
        if personal_info.get('name'):
            confidence += 0.1
        if personal_info.get('phone'):
            confidence += 0.1
        
        # Habilidades (+40%)
        tech_count = len(skills.get('technical', []))
        if tech_count >= 5:
            confidence += 0.4
        elif tech_count >= 3:
            confidence += 0.3
        elif tech_count >= 1:
            confidence += 0.2
        
        # Experiência (+30%)
        if experience.get('total_years', 0) > 0:
            confidence += 0.15
        if experience.get('companies'):
            confidence += 0.1
        if experience.get('current_position'):
            confidence += 0.05
        
        return min(1.0, confidence)
    
    def save_analysis(self, result: SimpleCVResult, output_path: str):
        """Salva análise em arquivo JSON"""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result.to_dict(), f, ensure_ascii=False, indent=2)
        
        print(f"✅ Análise salva em: {output_path}")


# Exemplo de uso
if __name__ == "__main__":
    analyzer = SimpleCVAnalyzer()
    
    # Teste com arquivo exemplo
    try:
        result = analyzer.analyze_cv("exemplo_curriculo.txt", "user123")
        
        print("\n=== RESULTADO DA ANÁLISE ===")
        print(f"Nome: {result.personal_info.get('name', 'N/A')}")
        print(f"Email: {result.personal_info.get('email', 'N/A')}")
        print(f"Senioridade: {result.seniority_level}")
        print(f"Anos de experiência: {result.experience['total_years']}")
        print(f"Tecnologias: {', '.join(result.skills['technical'][:10])}")
        print(f"Faixa salarial: R$ {result.estimated_salary_range['min']:,.0f} - R$ {result.estimated_salary_range['max']:,.0f}")
        print(f"Confiança: {result.confidence_score:.1%}")
        
    except Exception as e:
        print(f"Erro: {e}")