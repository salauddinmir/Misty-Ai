"""
Neuron Simulation Performance Benchmark.

Benchmarks neuron simulation speed at different scales:
- 100, 1,000, 10,000, 100,000 neurons
- Compares VectorizedPopulation vs NeuronPopulation (at 1000)
- Target: 10,000 neurons simulated in < 10ms per timestep
"""

import sys
import time

import numpy as np

from brain.neurons.populations import NeuronPopulation
from brain.neurons.vectorized import VectorizedPopulation


def benchmark_vectorized(size: int, n_steps: int = 100) -> float:
    """Benchmark VectorizedPopulation at a given size.

    Args:
        size: Number of neurons.
        n_steps: Number of timesteps to simulate.

    Returns:
        Average time per step in milliseconds.
    """
    pop = VectorizedPopulation(size=size, threshold_val=1.0, decay_val=0.9)
    inputs = np.random.uniform(0.0, 1.2, size=size)

    # Warm-up
    pop.step(inputs)
    pop.reset()

    # Timed run
    start = time.perf_counter()
    for _ in range(n_steps):
        pop.step(inputs)
    elapsed = time.perf_counter() - start

    return (elapsed / n_steps) * 1000  # ms per step


def benchmark_original(size: int, n_steps: int = 100) -> float:
    """Benchmark original NeuronPopulation at a given size.

    Args:
        size: Number of neurons.
        n_steps: Number of timesteps to simulate.

    Returns:
        Average time per step in milliseconds.
    """
    pop = NeuronPopulation(name="benchmark")
    pop.create_neurons(count=size, threshold=1.0, decay=0.9)
    neuron_ids = list(pop.neurons.keys())

    # Create random inputs
    input_values = np.random.uniform(0.0, 1.2, size=size)
    inputs = {nid: float(input_values[i]) for i, nid in enumerate(neuron_ids)}

    # Warm-up
    pop.step(inputs)
    pop.reset()

    # Timed run
    start = time.perf_counter()
    for _ in range(n_steps):
        pop.step(inputs)
    elapsed = time.perf_counter() - start

    return (elapsed / n_steps) * 1000  # ms per step


def main() -> None:
    """Run all benchmarks and print results."""
    print("=" * 70)
    print("MISTY Neural Simulation Benchmark")
    print("=" * 70)
    print()

    # Vectorized population benchmarks
    sizes = [100, 1_000, 10_000, 100_000]
    print("VectorizedPopulation Performance:")
    print("-" * 50)
    print(f"{'Neurons':<12} {'ms/step':<12} {'steps/sec':<12} {'Status'}")
    print("-" * 50)

    for size in sizes:
        n_steps = 100 if size <= 10_000 else 20
        ms_per_step = benchmark_vectorized(size, n_steps)
        steps_per_sec = 1000.0 / ms_per_step
        target = "< 10ms" if size == 10_000 else ""
        status = ""
        if size == 10_000:
            status = "PASS" if ms_per_step < 10.0 else "FAIL"
        print(f"{size:<12} {ms_per_step:<12.3f} {steps_per_sec:<12.1f} {status} {target}")

    print()

    # Comparison at 1000 neurons
    print("Comparison at 1000 neurons (Vectorized vs Original):")
    print("-" * 50)

    vec_time = benchmark_vectorized(1000, 100)
    orig_time = benchmark_original(1000, 100)
    speedup = orig_time / vec_time

    print(f"  Vectorized: {vec_time:.3f} ms/step")
    print(f"  Original:   {orig_time:.3f} ms/step")
    print(f"  Speedup:    {speedup:.1f}x")
    print()

    # Summary
    target_met = benchmark_vectorized(10_000, 50) < 10.0
    print("=" * 70)
    print(f"Target (10K neurons < 10ms/step): {'ACHIEVED' if target_met else 'NOT MET'}")
    print("=" * 70)

    if not target_met:
        sys.exit(1)


if __name__ == "__main__":
    main()
