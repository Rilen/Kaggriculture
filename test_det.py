import subprocess
import os

env_vars = os.environ.copy()
env_vars["PYTHONHASHSEED"] = "0"

def run_agent(seed, agent_name):
    cmd = f'python -c "from kaggle_environments import make; from forensics_pathing_v17_2 import {agent_name}; env = make(\'kaggriculture\', configuration={{\'episodeSteps\': 3000, \'randomSeed\': {seed}}}); print(env.run([[lambda o: {agent_name}()(o), \'random\']])[0][-1][0].get(\'reward\', 0))"'
    res = subprocess.check_output(cmd, env=env_vars)
    return float(res.decode('utf-8').strip().split('\n')[-1])

print("Baseline Run 1:", run_agent(42, "KaggricultureAgentV17"))
print("Baseline Run 2:", run_agent(42, "KaggricultureAgentV17"))
print("Inst Run 1:", run_agent(42, "InstrumentedAgentV17"))
