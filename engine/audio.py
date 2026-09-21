"""Procedural Audio Synthesis Matrix for Pyxel."""
import sys


class AudioManager:
    SND_COLLECT: int = 0
    SND_IMPACT: int = 1
    SND_KAIROS: int = 2
    SND_DEATH: int = 3

    def __init__(self):
        self.initialized: bool = False

    def init_sounds(self, pyxel_module=None):
        """Initialize procedural 4-channel retro synth sounds."""
        if pyxel_module is None:
            try:
                import pyxel
                pyxel_module = pyxel
            except ImportError:
                return

        try:
            # Sound 0 (Sand Collect): High-pitch arpeggio ping
            pyxel_module.sounds[self.SND_COLLECT].set(
                notes="c3e3g3c4",
                tones="t",
                volumes="4321",
                effects="n",
                speed=4,
            )

            # Sound 1 (Shard Impact): Noise crunch collision
            pyxel_module.sounds[self.SND_IMPACT].set(
                notes="f2d2b1g1",
                tones="n",
                volumes="7642",
                effects="f",
                speed=6,
            )

            # Sound 2 (Kairos Chime): Resonant low celestial chord
            pyxel_module.sounds[self.SND_KAIROS].set(
                notes="c2g2c3",
                tones="s",
                volumes="6543",
                effects="s",
                speed=15,
            )

            # Sound 3 (Death Shatter): Extended descending noise burst
            pyxel_module.sounds[self.SND_DEATH].set(
                notes="g2d2a1d1",
                tones="n",
                volumes="7764",
                effects="f",
                speed=12,
            )
            self.initialized = True
        except Exception:
            # Fail gracefully if headless or uninitialized
            self.initialized = False

    def play_collect(self, pyxel_module=None):
        self._play(pyxel_module, 0, self.SND_COLLECT)

    def play_impact(self, pyxel_module=None):
        self._play(pyxel_module, 1, self.SND_IMPACT)

    def play_kairos(self, pyxel_module=None):
        self._play(pyxel_module, 2, self.SND_KAIROS)

    def play_death(self, pyxel_module=None):
        self._play(pyxel_module, 0, self.SND_DEATH)

    def _play(self, pyxel_module, channel: int, snd: int):
        if not self.initialized:
            return
        if pyxel_module is None:
            try:
                import pyxel
                pyxel_module = pyxel
            except ImportError:
                return
        try:
            pyxel_module.play(channel, snd)
        except Exception:
            pass
