# coding=utf-8

__author__ = 'Gareth Coles'

mods = {
    "No mods": 0x0,
    "NF": 0x1,
    "EZ": 0x2,
    # "No Video": 0x4,  # Not used
    "HD": 0x8,
    "HR": 0x10,
    "SD": 0x20,
    "DT": 0x40,
    "Relax": 0x80,
    "HT": 0x100,
    "NC": 0x200,  # Only appears with Double Time
    "FL": 0x400,
    "Auto": 0x800,  # osubot
    "Spun Out": 0x1000,
    "Autopilot": 0x2000,
    "PF": 0x4000,  # Only appears with sudden death
    "4K": 0x8000,
    "5K": 0x10000,
    "6K": 0x20000,
    "7K": 0x40000,
    "8K": 0x80000,
    # "Modded Keys": 0xF8000,  # 4K | 5K | 6K | 7K | 8K
    "FI": 0x100000,
    "Random": 0x200000,
    # "Last Mod": 0x400000,
    # "Free Mod Allowed": 0xFF5FF,  # NoFail | Easy | Hidden | HardRock |
    #                                 SuddenDeath | Flashlight | FadeIn |
    #                                 Relax | Relax2 | SpunOut | ModdedKeys
    "9K": 0x1000000,
    "10K": 0x2000000,
    "1K": 0x4000000,
    "3K": 0x8000000,
    "2K": 0x10000000
}


def get_mods(integer):
    found = []

    for k, v in mods.items():
        if integer & v:
            found.append(k)

    # Exceptions and special cases
    if "NC" in found and "DT" in found:
        found.remove("DT")

    if "PF" in found and "SD" in found:
        found.remove("SD")

    if not found:
        found = ["No mods"]

    return found
