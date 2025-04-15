import platform
import os

def get_env_info():
    return {
        "os": platform.system(),
        "version": platform.version(),
        "hostname": platform.node(),
        "cwd": os.getcwd()
    }
