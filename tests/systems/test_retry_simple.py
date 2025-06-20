#!/usr/bin/env python3
"""
Teste simples e rápido do sistema de retry
"""

import asyncio
from src.retry_system import RetrySystem, STRATEGIES

# Contador global para simular falha intermitente
attempt_counter = 0

async def test_intermittent_failure():
    """Falha nas 2 primeiras tentativas, sucesso na 3ª"""
    global attempt_counter
    attempt_counter += 1
    
    print(f"   🔄 Executando tentativa {attempt_counter}")
    
    if attempt_counter < 3:
        raise ConnectionError(f"Falha simulada - tentativa {attempt_counter}")
    
    return {"message": "Sucesso após retry!", "tentativas": attempt_counter}

async def test_timeout():
    """Simula timeout constante"""
    print("   ⏰ Simulando timeout...")
    raise asyncio.TimeoutError("Timeout simulado")

async def test_success():
    """Operação que funciona imediatamente"""
    print("   ✨ Operação bem-sucedida")
    return {"status": "success"}

async def main():
    print("🧪 TESTE RÁPIDO DO SISTEMA DE RETRY")
    print("=" * 50)
    
    retry_system = RetrySystem()
    
    # Teste 1: Sucesso imediato
    print("\n📋 Teste 1: Operação bem-sucedida")
    print("-" * 30)
    result = await retry_system.execute_with_retry(
        test_success,
        strategy=STRATEGIES['standard'],
        operation_name="teste_sucesso"
    )
    print(f"✅ Resultado: {result.success}")
    
    # Teste 2: Falha intermitente
    print("\n📋 Teste 2: Falha intermitente (3 tentativas)")
    print("-" * 30)
    global attempt_counter
    attempt_counter = 0  # Reset
    
    result = await retry_system.execute_with_retry(
        test_intermittent_failure,
        strategy=STRATEGIES['standard'],
        operation_name="teste_intermitente"
    )
    print(f"✅ Resultado: {result.success}")
    if result.success:
        print(f"📊 Dados: {result.result}")
    
    # Teste 3: Timeout (falha permanente)
    print("\n📋 Teste 3: Timeout constante")
    print("-" * 30)
    result = await retry_system.execute_with_retry(
        test_timeout,
        strategy=STRATEGIES['conservative'],
        operation_name="teste_timeout"
    )
    print(f"❌ Resultado: {result.success} (esperado)")
    
    # Mostrar métricas
    print("\n📊 MÉTRICAS FINAIS")
    print("=" * 50)
    retry_system.print_metrics()
    
    print("\n🏁 Teste concluído!")

if __name__ == "__main__":
    asyncio.run(main())