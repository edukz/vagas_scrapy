import asyncio
from main import scrape_catho_jobs, JobFilter
from notification_system import NotificationSystem, UserPreferencesManager
import schedule
import time
from datetime import datetime
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class EnhancedJobScraper:
    """
    Versão melhorada do scraper com notificações e agendamento
    """
    
    def __init__(self):
        self.notification_system = NotificationSystem()
        self.preferences_manager = UserPreferencesManager()
        self.job_filter = JobFilter()
        self.last_run_time = None
        
    async def run_scheduled_scraping(self):
        """
        Executa scraping agendado e notifica usuários
        """
        logger.info("Iniciando scraping agendado...")
        
        try:
            # Coletar vagas
            all_jobs = await scrape_catho_jobs(max_concurrent_jobs=3, max_pages=5)
            logger.info(f"Total de vagas coletadas: {len(all_jobs)}")
            
            # Processar notificações para cada usuário
            active_users = self.preferences_manager.get_all_active_users()
            
            for user_id, user_prefs in active_users.items():
                logger.info(f"Processando usuário: {user_id}")
                
                # Aplicar filtros do usuário
                user_filters = {
                    'tecnologias': user_prefs.get('required_technologies', []),
                    'salario_minimo': user_prefs.get('minimum_salary', 0),
                    'niveis_experiencia': user_prefs.get('experience_levels', []),
                    'tipos_empresa': user_prefs.get('company_types', []),
                    'palavras_chave': user_prefs.get('keywords', [])
                }
                
                # Filtrar vagas
                filtered_jobs = self.job_filter.apply_filters(all_jobs, user_filters)
                logger.info(f"Vagas após filtros do usuário {user_id}: {len(filtered_jobs)}")
                
                # Enviar notificações
                if filtered_jobs:
                    result = await self.notification_system.notify_new_jobs(
                        filtered_jobs, 
                        user_prefs
                    )
                    logger.info(f"Notificações enviadas para {user_id}: {result}")
            
            self.last_run_time = datetime.now()
            logger.info("Scraping agendado concluído com sucesso!")
            
        except Exception as e:
            logger.error(f"Erro no scraping agendado: {e}")
    
    def schedule_jobs(self):
        """
        Configura agendamento de tarefas
        """
        # Executar a cada 4 horas
        schedule.every(4).hours.do(lambda: asyncio.run(self.run_scheduled_scraping()))
        
        # Executar diariamente às 9h e 18h
        schedule.every().day.at("09:00").do(lambda: asyncio.run(self.run_scheduled_scraping()))
        schedule.every().day.at("18:00").do(lambda: asyncio.run(self.run_scheduled_scraping()))
        
        logger.info("Agendamento configurado!")
        logger.info("Próximas execuções:")
        for job in schedule.jobs:
            logger.info(f"  - {job}")
    
    def run_scheduler(self):
        """
        Executa o scheduler em loop
        """
        self.schedule_jobs()
        
        # Executar primeira vez imediatamente
        asyncio.run(self.run_scheduled_scraping())
        
        # Loop do scheduler
        while True:
            schedule.run_pending()
            time.sleep(60)  # Verificar a cada minuto


def setup_example_users():
    """
    Configura usuários de exemplo
    """
    manager = UserPreferencesManager()
    
    # Usuário 1: Desenvolvedor Python Sênior
    manager.add_user('python_senior_dev', {
        'email': 'python.dev@example.com',
        'email_notifications': True,
        'telegram_chat_id': '123456789',
        'telegram_notifications': True,
        'required_technologies': ['python', 'django', 'fastapi'],
        'minimum_salary': 10000,
        'experience_levels': ['senior', 'especialista'],
        'keywords': ['remoto', 'home office', 'CLT'],
        'company_types': ['startup', 'financeiro', 'ecommerce'],
        'notifications_enabled': True
    })
    
    # Usuário 2: Full Stack JavaScript
    manager.add_user('fullstack_js', {
        'email': 'js.dev@example.com',
        'email_notifications': True,
        'required_technologies': ['javascript', 'react', 'node'],
        'minimum_salary': 7000,
        'experience_levels': ['pleno', 'senior'],
        'keywords': ['full stack', 'typescript'],
        'notifications_enabled': True
    })
    
    # Usuário 3: DevOps/Cloud
    manager.add_user('devops_engineer', {
        'email': 'devops@example.com',
        'email_notifications': True,
        'required_technologies': ['aws', 'kubernetes', 'docker'],
        'minimum_salary': 12000,
        'experience_levels': ['senior', 'especialista'],
        'keywords': ['devops', 'cloud', 'SRE'],
        'notifications_enabled': True
    })
    
    logger.info("Usuários de exemplo configurados!")


async def test_immediate_run():
    """
    Testa execução imediata com notificações
    """
    scraper = EnhancedJobScraper()
    await scraper.run_scheduled_scraping()


def main():
    """
    Função principal com menu de opções
    """
    print("\n=== SCRAPER CATHO ENHANCED ===")
    print("1. Executar scraping uma vez (com notificações)")
    print("2. Executar com agendamento automático")
    print("3. Configurar usuários de exemplo")
    print("4. Executar scraping básico (sem notificações)")
    print("5. Sair")
    
    choice = input("\nEscolha uma opção: ").strip()
    
    if choice == "1":
        print("\nExecutando scraping único com notificações...")
        asyncio.run(test_immediate_run())
        
    elif choice == "2":
        print("\nIniciando modo agendado...")
        print("O scraper será executado:")
        print("- A cada 4 horas")
        print("- Diariamente às 9h e 18h")
        print("\nPressione Ctrl+C para parar")
        
        scraper = EnhancedJobScraper()
        try:
            scraper.run_scheduler()
        except KeyboardInterrupt:
            print("\nAgendador interrompido pelo usuário")
            
    elif choice == "3":
        print("\nConfigurando usuários de exemplo...")
        setup_example_users()
        print("✓ Usuários configurados! Execute opção 1 ou 2 para testar.")
        
    elif choice == "4":
        print("\nExecutando scraping básico...")
        from main import main as basic_main
        asyncio.run(basic_main())
        
    elif choice == "5":
        print("Saindo...")
        return
    
    else:
        print("Opção inválida!")


if __name__ == "__main__":
    main()