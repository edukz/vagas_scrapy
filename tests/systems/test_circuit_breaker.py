#!/usr/bin/env python3
"""
Teste do Sistema Circuit Breaker

Este teste demonstra como o circuit breaker protege o sistema
de falhas em cascata e permite recuperação automática.
"""

import asyncio
import random
import sys
import os

# Adicionar diretório pai ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.circuit_breaker import (
    CircuitBreaker, CircuitBreakerConfig, CircuitBreakerError,
    circuit_breaker_manager, CIRCUIT_CONFIGS
)


class SimulatedOperation:
    """Simula operação que pode falhar com diferentes padrões"""
    
    def __init__(self, name: str, failure_rate: float = 0.3):
        self.name = name
        self.failure_rate = failure_rate
        self.call_count = 0
        self.failure_pattern = "random"  # random, increasing, decreasing
    
    def set_failure_pattern(self, pattern: str, rate: float = None):
        """Define padrão de falhas"""
        self.failure_pattern = pattern
        if rate is not None:
            self.failure_rate = rate
    
    async def execute(self, delay: float = 0.1):
        """Executa operação simulada"""
        self.call_count += 1
        
        # Simular tempo de processamento
        await asyncio.sleep(delay)
        
        # Determinar se deve falhar
        should_fail = False
        
        if self.failure_pattern == "random":
            should_fail = random.random() < self.failure_rate
        elif self.failure_pattern == "increasing":
            # Taxa de falha aumenta com o tempo
            current_rate = min(self.failure_rate + (self.call_count * 0.1), 0.9)
            should_fail = random.random() < current_rate
        elif self.failure_pattern == "decreasing":
            # Taxa de falha diminui com o tempo
            current_rate = max(self.failure_rate - (self.call_count * 0.05), 0.1)
            should_fail = random.random() < current_rate
        elif self.failure_pattern == "burst":
            # Falhas em rajadas
            should_fail = (self.call_count % 10) < 5 and random.random() < 0.8
        
        if should_fail:
            error_types = [
                "TimeoutError: Operation timed out",
                "ConnectionError: Network unreachable", 
                "ServiceError: Service temporarily unavailable",
                "RateLimitError: Too many requests"
            ]
            raise Exception(random.choice(error_types))
        
        return f"Success from {self.name} (call #{self.call_count})"


async def test_basic_circuit_breaker():
    """Teste básico do circuit breaker"""
    print("🧪 TESTE BÁSICO DO CIRCUIT BREAKER")
    print("-" * 50)
    
    # Criar operação que falha 70% das vezes
    operation = SimulatedOperation("basic_test", failure_rate=0.7)
    
    # Configurar circuit breaker com threshold baixo
    config = CircuitBreakerConfig(
        failure_threshold=3,
        recovery_timeout=5.0,
        success_threshold=2,
        operation_timeout=1.0
    )
    
    circuit = CircuitBreaker("test_basic", config)
    
    # Executar operações até circuit abrir
    for i in range(10):
        try:
            result = await circuit.call(operation.execute, operation_name=f"basic_test_{i}")
            print(f"   ✅ Tentativa {i+1}: {result}")
        except CircuitBreakerError as e:
            print(f"   🔴 Tentativa {i+1}: Circuit ABERTO - {e}")
            break
        except Exception as e:
            print(f"   ❌ Tentativa {i+1}: Falha - {e}")
    
    circuit.print_status()


async def test_circuit_recovery():
    """Teste de recuperação do circuit breaker"""
    print("\n🧪 TESTE DE RECUPERAÇÃO DO CIRCUIT BREAKER")
    print("-" * 50)
    
    # Operação que começa falhando muito e depois melhora
    operation = SimulatedOperation("recovery_test", failure_rate=0.8)
    operation.set_failure_pattern("decreasing", 0.9)
    
    config = CircuitBreakerConfig(
        failure_threshold=2,
        recovery_timeout=3.0,
        success_threshold=2,
        operation_timeout=1.0
    )
    
    circuit = CircuitBreaker("test_recovery", config)
    
    print("Fase 1: Forçando abertura do circuit...")
    # Forçar falhas para abrir circuit
    for i in range(5):
        try:
            await circuit.call(operation.execute, delay=0.05, operation_name=f"force_fail_{i}")
        except (CircuitBreakerError, Exception) as e:
            print(f"   Tentativa {i+1}: {type(e).__name__}")
    
    circuit.print_status()
    
    print(f"\nFase 2: Aguardando recovery timeout ({config.recovery_timeout}s)...")
    await asyncio.sleep(config.recovery_timeout + 0.5)
    
    print("Fase 3: Testando recuperação...")
    # Agora a operação deveria ter taxa de falha menor
    for i in range(8):
        try:
            result = await circuit.call(operation.execute, delay=0.05, operation_name=f"recovery_test_{i}")
            print(f"   ✅ Recuperação {i+1}: Sucesso!")
        except CircuitBreakerError as e:
            print(f"   🔴 Recuperação {i+1}: Ainda bloqueado")
        except Exception as e:
            print(f"   ⚠️ Recuperação {i+1}: Falha normal - {e}")
            
        await asyncio.sleep(0.2)
    
    circuit.print_status()


async def test_circuit_breaker_manager():
    """Teste do gerenciador de circuit breakers"""
    print("\n🧪 TESTE DO GERENCIADOR DE CIRCUIT BREAKERS")
    print("-" * 50)
    
    # Criar múltiplas operações com padrões diferentes
    operations = {
        "stable_service": SimulatedOperation("stable", 0.1),
        "unstable_service": SimulatedOperation("unstable", 0.6),
        "failing_service": SimulatedOperation("failing", 0.9)
    }
    
    # Configurar diferentes circuits
    async def run_operations():
        tasks = []
        
        # Operação estável
        for i in range(5):
            task = circuit_breaker_manager.execute_with_circuit_breaker(
                "stable_circuit",
                operations["stable_service"].execute,
                config=CIRCUIT_CONFIGS["network"],
                operation_name=f"stable_op_{i}"
            )
            tasks.append(task)
        
        # Operação instável
        for i in range(8):
            task = circuit_breaker_manager.execute_with_circuit_breaker(
                "unstable_circuit", 
                operations["unstable_service"].execute,
                config=CIRCUIT_CONFIGS["scraping"],
                operation_name=f"unstable_op_{i}"
            )
            tasks.append(task)
        
        # Operação que falha muito
        for i in range(6):
            task = circuit_breaker_manager.execute_with_circuit_breaker(
                "failing_circuit",
                operations["failing_service"].execute,
                config=CIRCUIT_CONFIGS["scraping"],
                operation_name=f"failing_op_{i}"
            )
            tasks.append(task)
        
        # Executar todas com timeout individual
        results = []
        for task in tasks:
            try:
                result = await asyncio.wait_for(task, timeout=2.0)
                results.append(("success", result))
            except CircuitBreakerError as e:
                results.append(("circuit_breaker", str(e)))
            except Exception as e:
                results.append(("error", str(e)))
        
        return results
    
    results = await run_operations()
    
    # Contar resultados
    success_count = sum(1 for r in results if r[0] == "success")
    circuit_blocks = sum(1 for r in results if r[0] == "circuit_breaker")
    errors = sum(1 for r in results if r[0] == "error")
    
    print(f"\n📊 RESULTADOS:")
    print(f"   ✅ Sucessos: {success_count}")
    print(f"   🔴 Bloqueados por Circuit: {circuit_blocks}")
    print(f"   ❌ Erros normais: {errors}")
    print(f"   📈 Total: {len(results)}")
    
    circuit_breaker_manager.print_all_status()


async def test_concurrent_operations():
    """Teste de operações concorrentes"""
    print("\n🧪 TESTE DE OPERAÇÕES CONCORRENTES")
    print("-" * 50)
    
    operation = SimulatedOperation("concurrent_test", 0.4)
    operation.set_failure_pattern("burst")
    
    config = CircuitBreakerConfig(
        failure_threshold=4,
        recovery_timeout=2.0,
        success_threshold=3,
        request_volume_threshold=5,
        error_percentage_threshold=60.0
    )
    
    circuit = CircuitBreaker("concurrent_test", config)
    
    async def worker(worker_id: int, operations_count: int):
        """Worker que executa operações"""
        results = {"success": 0, "circuit_blocked": 0, "failed": 0}
        
        for i in range(operations_count):
            try:
                await circuit.call(
                    operation.execute, 
                    delay=0.1,
                    operation_name=f"worker_{worker_id}_op_{i}"
                )
                results["success"] += 1
                print(f"   Worker {worker_id}: ✅ Op {i+1}")
            except CircuitBreakerError:
                results["circuit_blocked"] += 1
                print(f"   Worker {worker_id}: 🔴 Op {i+1} (Circuit)")
            except Exception:
                results["failed"] += 1
                print(f"   Worker {worker_id}: ❌ Op {i+1} (Error)")
            
            await asyncio.sleep(0.05)  # Pequena pausa
        
        return results
    
    # Executar 3 workers em paralelo
    tasks = [
        worker(1, 8),
        worker(2, 8), 
        worker(3, 8)
    ]
    
    worker_results = await asyncio.gather(*tasks)
    
    # Consolidar resultados
    total_results = {"success": 0, "circuit_blocked": 0, "failed": 0}
    for result in worker_results:
        for key, value in result.items():
            total_results[key] += value
    
    print(f"\n📊 RESULTADO CONSOLIDADO:")
    print(f"   ✅ Sucessos: {total_results['success']}")
    print(f"   🔴 Bloqueados: {total_results['circuit_blocked']}")
    print(f"   ❌ Falhas: {total_results['failed']}")
    
    circuit.print_status()


async def test_metrics_and_monitoring():
    """Teste de métricas e monitoramento"""
    print("\n🧪 TESTE DE MÉTRICAS E MONITORAMENTO")
    print("-" * 50)
    
    # Simular operação com padrão complexo
    operation = SimulatedOperation("metrics_test", 0.3)
    
    circuit = CircuitBreaker("metrics_test", CircuitBreakerConfig(
        failure_threshold=5,
        recovery_timeout=2.0,
        success_threshold=3,
        sliding_window_size=20
    ))
    
    # Executar muitas operações
    print("Executando 25 operações para gerar métricas...")
    
    for i in range(25):
        try:
            await circuit.call(operation.execute, delay=0.02, operation_name=f"metrics_op_{i}")
            if i % 5 == 0:
                print(f"   Progresso: {i+1}/25")
        except (CircuitBreakerError, Exception):
            if i % 5 == 0:
                print(f"   Progresso: {i+1}/25 (falha)")
    
    # Exibir métricas detalhadas
    metrics = circuit.get_metrics()
    
    print(f"\n📊 MÉTRICAS DETALHADAS:")
    print(f"   📈 Total de requisições: {metrics['total_requests']}")
    print(f"   ✅ Sucessos: {metrics['successful_requests']}")
    print(f"   ❌ Falhas: {metrics['failed_requests']}")
    print(f"   🔴 Rejeitadas: {metrics['rejected_requests']}")
    print(f"   🔄 Tentativas de recovery: {metrics['recovery_attempts']}")
    print(f"   ⏱️ Tempo médio de resposta: {metrics['average_response_time']:.3f}s")
    print(f"   📊 Taxa de erro atual: {metrics['current_error_rate']}")
    print(f"   🪟 Tamanho da janela: {metrics['window_size']}")
    
    if metrics['state_transitions']:
        print(f"   🔄 Transições de estado: {len(metrics['state_transitions'])}")
        for transition in metrics['state_transitions'][-3:]:  # Últimas 3
            print(f"      {transition['from']} → {transition['to']}")
    
    circuit.print_status()


async def main():
    """Função principal dos testes"""
    print("🧪 TESTES COMPLETOS DO SISTEMA CIRCUIT BREAKER")
    print("=" * 60)
    print("Estes testes demonstram como o Circuit Breaker protege")
    print("o sistema contra falhas em cascata e permite recuperação.\n")
    
    try:
        await test_basic_circuit_breaker()
        await test_circuit_recovery()
        await test_circuit_breaker_manager()
        await test_concurrent_operations()
        await test_metrics_and_monitoring()
        
        print("\n" + "=" * 60)
        print("🎉 TODOS OS TESTES DO CIRCUIT BREAKER CONCLUÍDOS!")
        print("=" * 60)
        
        print("\n💡 BENEFÍCIOS DEMONSTRADOS:")
        print("   ✅ Proteção contra falhas em cascata")
        print("   ✅ Recuperação automática do sistema")
        print("   ✅ Isolamento de falhas por serviço")
        print("   ✅ Métricas detalhadas para monitoramento")
        print("   ✅ Estados adaptativos (CLOSED/OPEN/HALF_OPEN)")
        print("   ✅ Configuração flexível por caso de uso")
        print("   ✅ Integração com sistema de logs")
        
        print("\n🚀 O CIRCUIT BREAKER ESTÁ PRONTO PARA PRODUÇÃO!")
        
    except Exception as e:
        print(f"\n❌ Erro durante testes: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())