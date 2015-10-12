# coding=utf-8

__author__ = 'Gareth Coles'

mods = {
    "None": 0x0,
    "No Fail": 0x1,
    "Easy": 0x2,
    "No Video": 0x4,
    "Hidden": 0x8,
    "Hard Rock": 0x10,
    "Sudden Death": 0x20,
    "Double Time": 0x40,
    "Relax": 0x80,
    "Half Time": 0x100,
    "Nightcore": 0x200,  # Only set with Double Time
    "Flashlight": 0x400,
    "Autoplay": 0x800,
    "Spun Out": 0x1000,
    "Relax 2": 0x2000,  # ???
    "Perfect": 0x4000,
    "4K": 0x8000,
    "5K": 0x10000,
    "6K": 0x20000,
    "7K": 0x40000,
    "8K": 0x80000,
    "Modded Keys": 0xF8000,  # 4K | 5K | 6K | 7K | 8K
    "Fade In": 0x100000,
    "Random": 0x200000,
    "Last Mod": 0x300000,
    "Free Mod Allowed": 0xFF5FF,  # NoFail | Easy | Hidden | HardRock |
                                  # SuddenDeath | Flashlight | FadeIn |
                                  # Relax | Relax2 | SpunOut | ModdedKeys
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

    return found
