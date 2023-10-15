from stable_baselines3.common.callbacks import BaseCallback

class RenderCallback(BaseCallback):
    def __init__(self, env, verbose=0):
        super(RenderCallback, self).__init__(verbose)
        self.env = env
        self.info = []

    def _on_step(self) -> bool:
        # Call the render function of the MicrogridEnv
        self.info.append(self.env.render())
        return True  # Continue training