"""
Spike-Timing-Dependent Plasticity (STDP) Learning Rule.

Strengthens synapses when the presynaptic neuron fires before
the postsynaptic neuron (causal timing), and weakens synapses
when the postsynaptic neuron fires first (anti-causal timing).
"""

from dataclasses import dataclass
import math

from brain.synapses.synapse import Synapse


@dataclass
class STDPRule:
    """STDP learning rule for modifying synapse weights.

    Attributes:
        a_plus: Maximum weight increase (LTP amplitude).
        a_minus: Maximum weight decrease (LTD amplitude).
        tau_plus: Time constant for potentiation (ms/timesteps).
        tau_minus: Time constant for depression (ms/timesteps).
        min_weight: Minimum synapse weight.
        max_weight: Maximum synapse weight.
    """

    a_plus: float = 0.01
    a_minus: float = 0.012
    tau_plus: float = 20.0
    tau_minus: float = 20.0
    min_weight: float = 0.0
    max_weight: float = 1.0

    def compute_weight_change(self, delta_t: int) -> float:
        """Compute the weight change based on spike timing difference.

        Args:
            delta_t: Time difference (t_post - t_pre).
                     Positive means pre fires before post (strengthen).
                     Negative means post fires before pre (weaken).

        Returns:
            Weight change value (positive for LTP, negative for LTD).
        """
        if delta_t > 0:
            # Pre fires before post: Long-Term Potentiation (LTP)
            return self.a_plus * math.exp(-delta_t / self.tau_plus)
        elif delta_t < 0:
            # Post fires before pre: Long-Term Depression (LTD)
            return -self.a_minus * math.exp(delta_t / self.tau_minus)
        else:
            # Simultaneous: no change
            return 0.0

    def apply(self, synapse: Synapse, current_time: int) -> float:
        """Apply STDP rule to a synapse based on recorded spike times.

        Args:
            synapse: The synapse to modify.
            current_time: Current simulation timestep.

        Returns:
            The weight change that was applied.
        """
        if synapse.last_pre_spike_time < 0 or synapse.last_post_spike_time < 0:
            return 0.0

        delta_t = synapse.last_post_spike_time - synapse.last_pre_spike_time
        weight_change = self.compute_weight_change(delta_t)

        if weight_change != 0.0:
            synapse.update_weight(
                weight_change,
                min_weight=self.min_weight,
                max_weight=self.max_weight,
            )

        return weight_change

    def __repr__(self) -> str:
        return (
            f"STDPRule(A+={self.a_plus}, A-={self.a_minus}, "
            f"tau+={self.tau_plus}, tau-={self.tau_minus})"
        )
