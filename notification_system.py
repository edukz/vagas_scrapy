import smtplib
import asyncio
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Optional
import aiohttp
import json
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

class NotificationSystem:
    """
    Sistema de notificações multi-canal para alertar sobre novas vagas
    """
    
    def __init__(self):
        # Configurações de email
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.smtp_user = os.getenv('SMTP_USER')
        self.smtp_password = os.getenv('SMTP_PASSWORD')
        
        # Configurações do Telegram
        self.telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.telegram_base_url = f"https://api.telegram.org/bot{self.telegram_token}"
        
        # Configurações de webhook
        self.webhook_urls = os.getenv('WEBHOOK_URLS', '').split(',')
        
        # Cache de vagas já notificadas
        self.notified_jobs = set()
        self._load_notified_cache()
    
    def _load_notified_cache(self):
        """Carrega cache de vagas já notificadas"""
        try:
            if os.path.exists('cache/notified_jobs.json'):
                with open('cache/notified_jobs.json', 'r') as f:
                    self.notified_jobs = set(json.load(f))
        except:
            self.notified_jobs = set()
    
    def _save_notified_cache(self):
        """Salva cache de vagas notificadas"""
        try:
            os.makedirs('cache', exist_ok=True)
            with open('cache/notified_jobs.json', 'w') as f:
                json.dump(list(self.notified_jobs), f)
        except:
            pass
    
    async def notify_new_jobs(self, jobs: List[Dict], user_preferences: Dict) -> Dict:
        """
        Notifica sobre novas vagas que atendem aos critérios do usuário
        """
        new_jobs = []
        
        # Filtrar apenas vagas novas
        for job in jobs:
            job_id = job.get('link', '')
            if job_id and job_id not in self.notified_jobs:
                if self._matches_preferences(job, user_preferences):
                    new_jobs.append(job)
                    self.notified_jobs.add(job_id)
        
        if not new_jobs:
            return {'status': 'no_new_jobs', 'count': 0}
        
        # Enviar notificações
        results = {
            'total_new_jobs': len(new_jobs),
            'notifications_sent': {}
        }
        
        # Email
        if user_preferences.get('email_notifications'):
            email_result = await self.send_email_notification(
                new_jobs, 
                user_preferences.get('email')
            )
            results['notifications_sent']['email'] = email_result
        
        # Telegram
        if user_preferences.get('telegram_notifications'):
            telegram_result = await self.send_telegram_notification(
                new_jobs,
                user_preferences.get('telegram_chat_id')
            )
            results['notifications_sent']['telegram'] = telegram_result
        
        # Webhook
        if user_preferences.get('webhook_notifications'):
            webhook_result = await self.send_webhook_notification(
                new_jobs,
                user_preferences.get('webhook_url')
            )
            results['notifications_sent']['webhook'] = webhook_result
        
        # Salvar cache
        self._save_notified_cache()
        
        return results
    
    def _matches_preferences(self, job: Dict, preferences: Dict) -> bool:
        """Verifica se a vaga atende às preferências do usuário"""
        # Tecnologias obrigatórias
        if preferences.get('required_technologies'):
            job_techs = set(job.get('tecnologias_detectadas', []))
            required_techs = set(preferences['required_technologies'])
            if not required_techs.intersection(job_techs):
                return False
        
        # Salário mínimo
        if preferences.get('minimum_salary'):
            job_salary = job.get('faixa_salarial', {})
            if job_salary.get('min', 0) < preferences['minimum_salary']:
                return False
        
        # Nível de experiência
        if preferences.get('experience_levels'):
            if job.get('nivel_categorizado') not in preferences['experience_levels']:
                return False
        
        # Palavras-chave obrigatórias
        if preferences.get('keywords'):
            job_text = f"{job.get('titulo', '')} {job.get('descricao', '')}".lower()
            if not any(kw.lower() in job_text for kw in preferences['keywords']):
                return False
        
        # Empresas blacklist
        if preferences.get('blacklist_companies'):
            if job.get('empresa', '').lower() in [c.lower() for c in preferences['blacklist_companies']]:
                return False
        
        return True
    
    async def send_email_notification(self, jobs: List[Dict], to_email: str) -> Dict:
        """Envia notificação por email"""
        try:
            # Criar mensagem HTML
            html_content = self._create_email_html(jobs)
            
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f'🚀 {len(jobs)} novas vagas encontradas!'
            msg['From'] = self.smtp_user
            msg['To'] = to_email
            
            msg.attach(MIMEText(html_content, 'html'))
            
            # Enviar email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
            
            return {'status': 'success', 'jobs_count': len(jobs)}
            
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def _create_email_html(self, jobs: List[Dict]) -> str:
        """Cria template HTML para email"""
        html = """
        <html>
        <head>
            <style>
                body { font-family: Arial, sans-serif; background-color: #f4f4f4; }
                .container { max-width: 600px; margin: 0 auto; background: white; padding: 20px; }
                .job-card { border: 1px solid #ddd; padding: 15px; margin: 10px 0; border-radius: 8px; }
                .job-title { color: #2c5282; font-size: 18px; font-weight: bold; }
                .job-company { color: #666; margin: 5px 0; }
                .job-salary { color: #2d8659; font-weight: bold; }
                .job-tech { display: inline-block; background: #e2e8f0; padding: 2px 8px; margin: 2px; border-radius: 12px; font-size: 12px; }
                .btn { display: inline-block; padding: 10px 20px; background: #3182ce; color: white; text-decoration: none; border-radius: 5px; margin-top: 10px; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🎯 Novas Oportunidades!</h1>
                <p>Encontramos <strong>{count}</strong> novas vagas que correspondem ao seu perfil:</p>
        """.format(count=len(jobs))
        
        for job in jobs[:10]:  # Limitar a 10 vagas no email
            salary_info = job.get('faixa_salarial', {})
            salary_text = job.get('salario', 'A combinar')
            if salary_info.get('min'):
                salary_text = f"R$ {salary_info['min']:,.2f}"
                if salary_info.get('max') and salary_info['max'] != salary_info['min']:
                    salary_text += f" - R$ {salary_info['max']:,.2f}"
            
            html += f"""
                <div class="job-card">
                    <div class="job-title">{job.get('titulo', 'Sem título')}</div>
                    <div class="job-company">🏢 {job.get('empresa', 'Não informada')}</div>
                    <div class="job-salary">💰 {salary_text}</div>
                    <div class="job-location">📍 {job.get('localizacao', 'Não informada')}</div>
                    <div style="margin: 10px 0;">
            """
            
            for tech in job.get('tecnologias_detectadas', [])[:5]:
                html += f'<span class="job-tech">{tech}</span>'
            
            html += f"""
                    </div>
                    <a href="{job.get('link', '#')}" class="btn">Ver Vaga</a>
                </div>
            """
        
        if len(jobs) > 10:
            html += f"<p><em>... e mais {len(jobs) - 10} vagas!</em></p>"
        
        html += """
                <hr style="margin: 30px 0;">
                <p style="color: #666; font-size: 12px;">
                    Você está recebendo este email porque se inscreveu para alertas de vagas.
                    Para cancelar, responda com "PARAR".
                </p>
            </div>
        </body>
        </html>
        """
        
        return html
    
    async def send_telegram_notification(self, jobs: List[Dict], chat_id: str) -> Dict:
        """Envia notificação via Telegram"""
        try:
            message = f"🚀 *{len(jobs)} novas vagas encontradas!*\n\n"
            
            for i, job in enumerate(jobs[:5], 1):  # Limitar a 5 vagas
                salary_text = job.get('salario', 'A combinar')
                techs = ', '.join(job.get('tecnologias_detectadas', [])[:3])
                
                message += f"*{i}. {job.get('titulo', 'Sem título')}*\n"
                message += f"🏢 {job.get('empresa', 'Não informada')}\n"
                message += f"💰 {salary_text}\n"
                if techs:
                    message += f"💻 {techs}\n"
                message += f"🔗 [Ver vaga]({job.get('link', '')})\n\n"
            
            if len(jobs) > 5:
                message += f"_... e mais {len(jobs) - 5} vagas!_"
            
            async with aiohttp.ClientSession() as session:
                url = f"{self.telegram_base_url}/sendMessage"
                data = {
                    'chat_id': chat_id,
                    'text': message,
                    'parse_mode': 'Markdown',
                    'disable_web_page_preview': True
                }
                
                async with session.post(url, json=data) as response:
                    result = await response.json()
                    
                    if result.get('ok'):
                        return {'status': 'success', 'jobs_count': len(jobs)}
                    else:
                        return {'status': 'error', 'message': result.get('description', 'Unknown error')}
                        
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    async def send_webhook_notification(self, jobs: List[Dict], webhook_url: str) -> Dict:
        """Envia notificação via webhook"""
        try:
            payload = {
                'event': 'new_jobs',
                'timestamp': datetime.now().isoformat(),
                'jobs_count': len(jobs),
                'jobs': jobs
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(webhook_url, json=payload, timeout=10) as response:
                    if response.status < 300:
                        return {'status': 'success', 'jobs_count': len(jobs)}
                    else:
                        return {'status': 'error', 'http_status': response.status}
                        
        except Exception as e:
            return {'status': 'error', 'message': str(e)}


class UserPreferencesManager:
    """
    Gerencia preferências de notificação dos usuários
    """
    
    def __init__(self, db_path: str = "user_preferences.json"):
        self.db_path = db_path
        self.preferences = self._load_preferences()
    
    def _load_preferences(self) -> Dict:
        """Carrega preferências do arquivo"""
        try:
            if os.path.exists(self.db_path):
                with open(self.db_path, 'r') as f:
                    return json.load(f)
        except:
            pass
        return {}
    
    def save_preferences(self):
        """Salva preferências no arquivo"""
        with open(self.db_path, 'w') as f:
            json.dump(self.preferences, f, indent=2)
    
    def add_user(self, user_id: str, preferences: Dict) -> bool:
        """Adiciona novo usuário com preferências"""
        self.preferences[user_id] = {
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            **preferences
        }
        self.save_preferences()
        return True
    
    def update_user(self, user_id: str, preferences: Dict) -> bool:
        """Atualiza preferências do usuário"""
        if user_id in self.preferences:
            self.preferences[user_id].update({
                'updated_at': datetime.now().isoformat(),
                **preferences
            })
            self.save_preferences()
            return True
        return False
    
    def get_user(self, user_id: str) -> Optional[Dict]:
        """Obtém preferências do usuário"""
        return self.preferences.get(user_id)
    
    def get_all_active_users(self) -> Dict:
        """Retorna todos os usuários com notificações ativas"""
        active_users = {}
        for user_id, prefs in self.preferences.items():
            if prefs.get('notifications_enabled', True):
                active_users[user_id] = prefs
        return active_users


# Exemplo de uso
async def demo_notification_system():
    """
    Demonstração do sistema de notificações
    """
    # Configurar sistema
    notifier = NotificationSystem()
    prefs_manager = UserPreferencesManager()
    
    # Adicionar usuário de exemplo
    user_preferences = {
        'email': 'user@example.com',
        'email_notifications': True,
        'telegram_chat_id': '123456789',
        'telegram_notifications': True,
        'webhook_url': 'https://example.com/webhook',
        'webhook_notifications': False,
        'required_technologies': ['python', 'django'],
        'minimum_salary': 5000,
        'experience_levels': ['pleno', 'senior'],
        'keywords': ['remoto', 'home office'],
        'blacklist_companies': [],
        'notifications_enabled': True
    }
    
    prefs_manager.add_user('user_001', user_preferences)
    
    # Simular novas vagas
    new_jobs = [
        {
            'titulo': 'Desenvolvedor Python Sênior',
            'empresa': 'Tech Company',
            'link': 'https://example.com/job1',
            'salario': 'R$ 12.000 - R$ 15.000',
            'faixa_salarial': {'min': 12000, 'max': 15000},
            'tecnologias_detectadas': ['python', 'django', 'postgresql'],
            'nivel_categorizado': 'senior',
            'localizacao': 'Home Office'
        },
        {
            'titulo': 'Python Developer Pleno',
            'empresa': 'Startup XYZ',
            'link': 'https://example.com/job2',
            'salario': 'R$ 8.000 - R$ 10.000',
            'faixa_salarial': {'min': 8000, 'max': 10000},
            'tecnologias_detectadas': ['python', 'flask', 'aws'],
            'nivel_categorizado': 'pleno',
            'localizacao': 'Remoto'
        }
    ]
    
    # Enviar notificações
    for user_id, user_prefs in prefs_manager.get_all_active_users().items():
        print(f"\nProcessando notificações para usuário: {user_id}")
        result = await notifier.notify_new_jobs(new_jobs, user_prefs)
        print(f"Resultado: {result}")


if __name__ == "__main__":
    # Para testar, criar arquivo .env com:
    # SMTP_SERVER=smtp.gmail.com
    # SMTP_PORT=587
    # SMTP_USER=seu_email@gmail.com
    # SMTP_PASSWORD=sua_senha_app
    # TELEGRAM_BOT_TOKEN=seu_token_bot
    
    asyncio.run(demo_notification_system())