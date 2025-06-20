"""
Handler para operações de dados
"""

import os
import shutil
from typing import Dict, Optional

from ..utils.menu_system import MenuSystem, Colors


class DataHandler:
    """Gerencia operações de dados (limpeza, deduplicação)"""
    
    def __init__(self):
        self.menu = MenuSystem()
    
    async def handle_clean_data(self) -> None:
        """Limpa dados do sistema"""
        self.menu.print_warning_message("ATENÇÃO: Isso removerá todos os dados armazenados!")
        
        if self.menu.get_user_bool("Tem certeza que deseja continuar?", False):
            await self._clean_system_data()
        else:
            self.menu.print_info_message("Limpeza cancelada")
        
        print(f"\n{Colors.DIM}Pressione Enter para continuar...{Colors.RESET}")
        input()
    
    async def handle_deduplication(self) -> None:
        """Executa deduplicação de arquivos"""
        print(f"\n{Colors.BOLD}🧹 SISTEMA DE DEDUPLICAÇÃO{Colors.RESET}")
        print("Esta operação irá:")
        print("  • Escanear todos os arquivos JSON em data/")
        print("  • Remover vagas duplicadas")
        print("  • Criar backup dos arquivos originais (.bak)")
        print("  • Exibir relatório detalhado")
        
        if self.menu.get_user_bool("Deseja continuar?", True):
            await self._run_deduplication()
        else:
            self.menu.print_info_message("Deduplicação cancelada")
        
        print(f"\n{Colors.DIM}Pressione Enter para continuar...{Colors.RESET}")
        input()
    
    async def _clean_system_data(self) -> None:
        """Executa limpeza dos dados do sistema"""
        # Remover diretórios de cache e checkpoint
        directories_to_clean = [
            "data/cache",
            "data/checkpoints"
        ]
        
        # Remover também arquivos de deduplicação
        files_to_clean = [
            "data/deduplication_stats.json",
            "data/known_jobs.json"
        ]
        
        cleaned = 0
        
        for directory in directories_to_clean:
            if os.path.exists(directory):
                try:
                    shutil.rmtree(directory)
                    print(f"✅ {directory} removido")
                    cleaned += 1
                except Exception as e:
                    print(f"❌ Erro ao remover {directory}: {e}")
        
        # Remover arquivos de deduplicação
        for file_path in files_to_clean:
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    print(f"✅ {file_path} removido")
                    cleaned += 1
                except Exception as e:
                    print(f"❌ Erro ao remover {file_path}: {e}")
        
        if cleaned > 0:
            self.menu.print_success_message(f"Cache limpo! {cleaned} itens removidos")
            print("🔄 Agora o scraping processará todas as páginas do zero")
        else:
            self.menu.print_info_message("Nenhum cache encontrado para limpar")
    
    async def _run_deduplication(self) -> None:
        """Executa processo de deduplicação"""
        try:
            from ..systems.deduplicator import JobDeduplicator
            
            deduplicator = JobDeduplicator()
            removed_count = deduplicator.clean_existing_files("data")
            
            if removed_count > 0:
                self.menu.print_success_message(f"Deduplicação concluída: {removed_count} duplicatas removidas!")
                deduplicator.print_stats()
            else:
                self.menu.print_info_message("Nenhuma duplicata encontrada ou nenhum arquivo para processar")
        except Exception as e:
            self.menu.print_error_message(f"Erro durante deduplicação: {e}")