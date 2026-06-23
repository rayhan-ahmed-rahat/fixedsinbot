import json
import os

# Shared local data file configuration paths
SETTINGS_FILE = "guild_settings.json"
BOOST_COUNTS_FILE = "boost_counts.json"
BOOST_KEYS_FILE = "boost_keys.json"

def get_settings():
    if not os.path.exists(SETTINGS_FILE):
        return {}
    try:
        with open(SETTINGS_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {}

def save_settings(data):
    try:
        with open(SETTINGS_FILE, "w") as f:
            json.dump(data, f, indent=4)
    except Exception:
        pass

def get_guild(data, guild_id):
    gid = str(guild_id)
    if gid not in data:
        data[gid] = {}
    return data[gid]

def get_boost_counts():
    if not os.path.exists(BOOST_COUNTS_FILE):
        return {}
    try:
        with open(BOOST_COUNTS_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {}

def save_boost_counts(data):
    try:
        with open(BOOST_COUNTS_FILE, "w") as f:
            json.dump(data, f, indent=4)
    except Exception:
        pass

def get_keys():
    if not os.path.exists(BOOST_KEYS_FILE):
        return {}
    try:
        with open(BOOST_KEYS_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {}

def save_keys(data):
    try:
        with open(BOOST_KEYS_FILE, "w") as f:
            json.dump(data, f, indent=4)
    except Exception:
        pass

async def setup(bot):
    # Cog is completely moved to boost.py to resolve the duplication crash
    pass
