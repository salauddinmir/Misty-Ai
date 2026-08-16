"""
Synaptic Network using Sparse Matrices.

Provides a SynapticNetwork class that manages connections between
VectorizedPopulation instances using scipy.sparse matrices for
memory-efficient storage and fast matrix-vector multiplication.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import numpy as np
from scipy.sparse import csr_matrix, lil_matrix

from brain.neurons.vectorized import VectorizedPopulation, NeuronType


@dataclass
class ConnectionInfo:
    """Metadata about a connection between populations.

    Attributes:
        source_name: Name of the source population.
        target_name: Name of the target population.
        weight_matrix: Sparse CSR matrix of connection weights.
        probability: Connection probability used when creating.
    """

    source_name: str
    target_name: str
    weight_matrix: csr_matrix
    probability: float


class SynapticNetwork:
    """Manages sparse synaptic connections between VectorizedPopulations.

    Uses scipy.sparse.csr_matrix for weight storage, enabling efficient
    spike propagation via sparse matrix-vector multiplication. Supports
    both feed-forward connections between populations and recurrent
    (self) connections within a single population.

    Excitatory neurons produce positive weights, while inhibitory neurons
    produce negative weights, enforcing Dale's law.

    Attributes:
        populations: Dictionary of registered populations by name.
        connections: List of ConnectionInfo for all established connections.
    """

    def __init__(self) -> None:
        """Initialize an empty synaptic network."""
        self.populations: Dict[str, VectorizedPopulation] = {}
        self.connections: List[ConnectionInfo] = []

    def add_population(self, population: VectorizedPopulation) -> None:
        """Register a population with the network.

        Args:
            population: The VectorizedPopulation to add.

        Raises:
            ValueError: If a population with the same name already exists.
        """
        if population.name in self.populations:
            raise ValueError(
                f"Population '{population.name}' already registered in network."
            )
        self.populations[population.name] = population

    def connect_populations(
        self,
        source: VectorizedPopulation,
        target: VectorizedPopulation,
        probability: float = 0.1,
        weight_range: Tuple[float, float] = (0.01, 0.1),
        seed: Optional[int] = None,
    ) -> ConnectionInfo:
        """Create feed-forward connections from source to target population.

        Each potential connection (source neuron i -> target neuron j) is
        created with the given probability. Weights are drawn uniformly
        from weight_range. Excitatory source neurons get positive weights,
        inhibitory source neurons get negative weights (Dale's law).

        Args:
            source: The pre-synaptic population.
            target: The post-synaptic population.
            probability: Probability of each connection existing (0-1).
            weight_range: Tuple of (min_weight, max_weight) for absolute weight values.
            seed: Optional random seed for reproducibility.

        Returns:
            ConnectionInfo describing the created connection.
        """
        rng = np.random.default_rng(seed)

        # Ensure populations are registered
        if source.name not in self.populations:
            self.add_population(source)
        if target.name not in self.populations:
            self.add_population(target)

        # Build connection matrix using lil_matrix for efficient construction
        weight_mat = lil_matrix((target.size, source.size), dtype=np.float64)

        # Generate random connection mask
        conn_mask = rng.random((target.size, source.size)) < probability

        # Generate random weights in the given range
        weights = rng.uniform(
            weight_range[0], weight_range[1], size=(target.size, source.size)
        )

        # Apply Dale's law: sign determined by source neuron type
        # source.type_array shape is (source.size,), broadcast across rows
        signed_weights = weights * source.type_array[np.newaxis, :]

        # Apply connection mask
        weight_mat[conn_mask] = signed_weights[conn_mask]

        # Convert to CSR for efficient arithmetic
        csr_weights = csr_matrix(weight_mat)

        connection = ConnectionInfo(
            source_name=source.name,
            target_name=target.name,
            weight_matrix=csr_weights,
            probability=probability,
        )
        self.connections.append(connection)
        return connection

    def connect_self(
        self,
        population: VectorizedPopulation,
        probability: float = 0.05,
        weight_range: Tuple[float, float] = (0.01, 0.05),
        allow_autapse: bool = False,
        seed: Optional[int] = None,
    ) -> ConnectionInfo:
        """Create recurrent (self) connections within a single population.

        Similar to connect_populations but source and target are the same
        population. Optionally disallows autapses (self-connections from
        a neuron to itself).

        Args:
            population: The population to create recurrent connections in.
            probability: Probability of each connection existing (0-1).
            weight_range: Tuple of (min_weight, max_weight) for absolute weight values.
            allow_autapse: If False, diagonal (self-to-self) connections are zeroed out.
            seed: Optional random seed for reproducibility.

        Returns:
            ConnectionInfo describing the created recurrent connection.
        """
        rng = np.random.default_rng(seed)

        # Ensure population is registered
        if population.name not in self.populations:
            self.add_population(population)

        n = population.size
        weight_mat = lil_matrix((n, n), dtype=np.float64)

        # Generate random connection mask
        conn_mask = rng.random((n, n)) < probability

        # Remove autapses if not allowed
        if not allow_autapse:
            np.fill_diagonal(conn_mask, False)

        # Generate random weights
        weights = rng.uniform(weight_range[0], weight_range[1], size=(n, n))

        # Apply Dale's law: sign determined by source (column) neuron type
        signed_weights = weights * population.type_array[np.newaxis, :]

        # Apply connection mask
        weight_mat[conn_mask] = signed_weights[conn_mask]

        # Convert to CSR
        csr_weights = csr_matrix(weight_mat)

        connection = ConnectionInfo(
            source_name=population.name,
            target_name=population.name,
            weight_matrix=csr_weights,
            probability=probability,
        )
        self.connections.append(connection)
        return connection

    def propagate(
        self,
        source: VectorizedPopulation,
        target: VectorizedPopulation,
        spikes: np.ndarray,
    ) -> np.ndarray:
        """Propagate spikes from source to target through all matching connections.

        Computes the post-synaptic current for each target neuron by multiplying
        the sparse weight matrix by the spike vector from the source population.

        Args:
            source: The pre-synaptic population that produced spikes.
            target: The post-synaptic population receiving input.
            spikes: Boolean array of shape (source.size,) indicating which neurons fired.

        Returns:
            Array of shape (target.size,) with post-synaptic currents.
        """
        post_currents = np.zeros(target.size, dtype=np.float64)
        spike_vector = spikes.astype(np.float64)

        for conn in self.connections:
            if conn.source_name == source.name and conn.target_name == target.name:
                # Sparse matrix-vector multiply: W @ spikes
                post_currents += conn.weight_matrix.dot(spike_vector)

        return post_currents

    def propagate_all(
        self,
        spike_dict: Dict[str, np.ndarray],
    ) -> Dict[str, np.ndarray]:
        """Propagate all spikes through all connections in the network.

        For each connection, multiplies the weight matrix by the source
        spike vector and accumulates the result into the target's current.

        Args:
            spike_dict: Dictionary mapping population names to their spike arrays.

        Returns:
            Dictionary mapping population names to their accumulated input currents.
        """
        currents: Dict[str, np.ndarray] = {}

        # Initialize current arrays for all populations
        for name, pop in self.populations.items():
            currents[name] = np.zeros(pop.size, dtype=np.float64)

        # Propagate through all connections
        for conn in self.connections:
            if conn.source_name in spike_dict:
                spike_vector = spike_dict[conn.source_name].astype(np.float64)
                currents[conn.target_name] += conn.weight_matrix.dot(spike_vector)

        return currents

    @property
    def total_synapses(self) -> int:
        """Total number of non-zero synaptic connections in the network."""
        return sum(conn.weight_matrix.nnz for conn in self.connections)

    def __repr__(self) -> str:
        return (
            f"SynapticNetwork(populations={len(self.populations)}, "
            f"connections={len(self.connections)}, "
            f"total_synapses={self.total_synapses})"
        )
