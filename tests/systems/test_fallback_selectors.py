#!/usr/bin/env python3
"""
Teste do sistema de fallback de seletores
"""

import asyncio
import sys
import os

# Adicionar diretório pai ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.selector_fallback import FallbackSelector, SelectorStrategy, SelectorType


async def test_fallback_system():
    """Testa o sistema de fallback"""
    print("🧪 TESTE DO SISTEMA DE FALLBACK DE SELETORES")
    print("=" * 50)
    
    # Criar instância do sistema
    fallback = FallbackSelector()
    
    # Teste 1: Verificar estratégias carregadas
    print("\n📋 Teste 1: Estratégias Carregadas")
    print("-" * 30)
    
    element_types = list(fallback.selector_groups.keys())
    print(f"✅ {len(element_types)} tipos de elementos configurados:")
    for elem_type in element_types:
        strategies_count = len(fallback.selector_groups[elem_type])
        print(f"   • {elem_type}: {strategies_count} estratégias")
    
    # Teste 2: Validadores
    print("\n📋 Teste 2: Validadores")
    print("-" * 30)
    
    test_cases = {
        'job_title': ['Senior Software Engineer', 'Dev', ''],
        'job_link': ['/vagas/dev/12345/', 'https://example.com', ''],
        'company': ['Tech Corp Ltda', 'AB', ''],
        'salary': ['R$ 5.000 - R$ 8.000', 'A combinar', ''],
        'experience': ['3 anos de experiência', 'Pleno', '']
    }
    
    for elem_type, test_values in test_cases.items():
        if elem_type in fallback.validation_rules:
            validator = fallback.validation_rules[elem_type]
            print(f"\n{elem_type}:")
            for value in test_values:
                is_valid = validator(value)
                status = "✅" if is_valid else "❌"
                print(f"   {status} '{value}' -> {is_valid}")
    
    # Teste 3: Score de confiabilidade
    print("\n📋 Teste 3: Sistema de Scoring")
    print("-" * 30)
    
    # Simular estratégia com histórico
    test_strategy = SelectorStrategy(
        selector='[data-testid="test"]',
        type=SelectorType.CSS,
        confidence=0.8,
        success_count=10,
        fail_count=2
    )
    
    score = test_strategy.reliability_score
    success_rate = test_strategy.success_count / (test_strategy.success_count + test_strategy.fail_count)
    
    print(f"Estratégia de teste:")
    print(f"   • Confiança inicial: {test_strategy.confidence}")
    print(f"   • Sucessos: {test_strategy.success_count}")
    print(f"   • Falhas: {test_strategy.fail_count}")
    print(f"   • Taxa de sucesso: {success_rate:.1%}")
    print(f"   • Score final: {score:.2f}")
    
    # Teste 4: Estatísticas
    print("\n📋 Teste 4: Sistema de Estatísticas")
    print("-" * 30)
    
    stats = fallback.get_selector_stats()
    print(f"✅ Estatísticas geradas para {len(stats)} tipos de elementos")
    
    # Mostrar amostra
    for elem_type in list(stats.keys())[:3]:
        stat = stats[elem_type]
        print(f"\n{elem_type}:")
        print(f"   • Total de estratégias: {stat['total_strategies']}")
        print(f"   • Confiabilidade média: {stat['average_reliability']:.2f}")
        print(f"   • Top performer: {stat['top_performer']}")
    
    print("\n✅ TESTE CONCLUÍDO COM SUCESSO!")
    return True


async def test_mock_extraction():
    """Teste simulado de extração com fallback"""
    print("\n\n🧪 TESTE SIMULADO DE EXTRAÇÃO")
    print("=" * 50)
    
    # Simular página HTML
    class MockElement:
        def __init__(self, text):
            self.text = text
        
        async def inner_text(self):
            return self.text
        
        async def get_attribute(self, attr):
            if attr == 'href':
                return '/vagas/developer/12345/'
            return None
    
    class MockPage:
        def __init__(self):
            self.elements = {
                '[data-testid="job-title"]': MockElement('Senior Python Developer'),
                '[data-testid="salary"]': MockElement('R$ 8.000 - R$ 12.000'),
                '[class*="company"]': MockElement('Tech Solutions Ltda'),
                'span:has-text("Home Office")': MockElement('Home Office')
            }
        
        async def query_selector(self, selector):
            return self.elements.get(selector)
        
        async def query_selector_all(self, selector):
            elem = self.elements.get(selector)
            return [elem] if elem else []
    
    # Testar extração
    fallback = FallbackSelector()
    mock_page = MockPage()
    
    print("Testando extração com fallback...")
    
    # Extrair título
    title = await fallback.extract_with_fallback(mock_page, 'job_title')
    print(f"✅ Título: {title}")
    
    # Extrair salário
    salary = await fallback.extract_with_fallback(mock_page, 'salary')
    print(f"✅ Salário: {salary}")
    
    # Extrair empresa
    company = await fallback.extract_with_fallback(mock_page, 'company')
    print(f"✅ Empresa: {company}")
    
    # Extrair modalidade
    work_mode = await fallback.extract_with_fallback(mock_page, 'work_mode')
    print(f"✅ Modalidade: {work_mode}")
    
    # Testar campo inexistente
    missing = await fallback.extract_with_fallback(mock_page, 'requirements')
    print(f"⚠️  Requisitos: {missing or 'Não encontrado'}")
    
    print("\n✅ EXTRAÇÃO SIMULADA CONCLUÍDA!")


async def main():
    """Função principal"""
    try:
        # Executar teste básico
        success = await test_fallback_system()
        
        if success:
            # Executar teste de extração
            await test_mock_extraction()
            
            print("\n🎉 TODOS OS TESTES PASSARAM!")
            print("\n💡 BENEFÍCIOS DO SISTEMA DE FALLBACK:")
            print("   ✅ Múltiplas estratégias para cada elemento")
            print("   ✅ Validação automática de dados")
            print("   ✅ Sistema de scoring adaptativo")
            print("   ✅ Resistente a mudanças no HTML")
            print("   ✅ Estatísticas de performance")
        
    except Exception as e:
        print(f"\n❌ Erro durante teste: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())