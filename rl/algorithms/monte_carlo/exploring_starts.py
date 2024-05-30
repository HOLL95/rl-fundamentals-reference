"""
TODO:
    - Figure out why plots not exactly the same as Sutton and Barto
"""


from rl.algorithms.monte_carlo.viz import plot_results
from rl.algorithms.common.mc_agent import MonteCarloAgent
from rl.common.policy import DeterministicPolicy

import gymnasium as gym
import numpy as np
from typing import Union
from gymnasium import Env


# TODO refactor: move to utils.general
def _is_subelement_present(subelement, my_list):
    """
    Helps check if a subelement is present in a list of tuples. Used to check if state has already been seen.

    Simple example:
    _is_subelement_present((1, 2), [(1, 2, 3), (4, 5, 6)])
        True
    """
    for tpl in my_list:
        if subelement == tpl[:len(subelement)]:
            return True
    return False


class MCExploringStartsAgent(MonteCarloAgent):

    def __init__(self, env: Union[Env, object], gamma: float, random_seed: Union[None, int] = None) -> None:
        super().__init__(env, gamma, random_seed)

        # Initialise Monte Carlo-specific attributes
        self.name = "MC Exploring Starts"  # For plotting

        self.policy = None
        self.returns = None

        self.reset()

    def _init_policy(self, state_shape):
        """
        Use the target_policy initialisation from Sutton and Barto, pp. 93:
        - If player sum == 20 or 21, stick (0)
        - Otherwise, hit (1)
        """
        # TODO: environment-specific. Refactor to be more general
        # TODO: refactor to a common policy class?
        self.policy = DeterministicPolicy(state_shape)

        # Overwrite with initial policy from Sutton and Barto
        self.policy.value[:19, :, :] = 1

    def reset(self):

        super().reset()

        # Initialise q-values, target_policy, and returns
        self._init_policy(self.state_shape)

    def act(self, state):
        """Deterministic policy"""
        return self.policy.select_action(state)

    def learn(self, num_episodes=10000):

        for episode_idx in range(num_episodes):

            # Print progress
            if episode_idx % 1000 == 0:
                print(f"Episode {episode_idx}")

            # Generate an episode
            episode = self._generate_episode(exploring_starts=True)

            # Loop through the episode in reverse order, updating the q-values and policy
            g = 0
            for t, (state, action, reward) in enumerate(reversed(episode)):
                g = self.gamma * g + reward

                # If the S_t, A_t pair has been seen before, continue.
                if _is_subelement_present((state, action), episode[:len(episode) - t - 1]):
                    continue

                # Update the q-value for this state-action pair
                # NewEstimate <- OldEstimate + 1/N(St, At) * (Return - OldEstimate)
                mc_error = g - self.q_values.get(state, action)
                self.state_action_counts.update(state, action)
                step_size = 1 / self.state_action_counts.get(state, action)
                new_value = self.q_values.get(state, action) + step_size * mc_error
                self.q_values.update(state, action, new_value)

                # Update the target_policy
                self.policy.update(state, self.q_values)


def run():

    # Run parameters
    train_episodes = 10000

    # Instantiate and learn the agent
    env = gym.make("Blackjack-v1", sab=True)  # `sab` means rules following Sutton and Barto
    mc_control = MCExploringStartsAgent(env, gamma=1.0)
    mc_control.learn(num_episodes=train_episodes)

    # Plot the results
    plot_results(mc_control)


if __name__ == "__main__":
    run()
