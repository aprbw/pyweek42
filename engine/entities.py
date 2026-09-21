"""Entities, Kinematics, Hitboxes, and Particle Physics."""
import math
import random
from typing import List, Tuple


def aabb_overlap(
    x1: float, y1: float, w1: float, h1: float,
    x2: float, y2: float, w2: float, h2: float
) -> bool:
    """Centered AABB collision test."""
    return (
        abs(x1 - x2) * 2.0 < (w1 + w2) and
        abs(y1 - y2) * 2.0 < (h1 + h2)
    )


class Particle:
    def __init__(self, x: float, y: float, vx: float, vy: float, color: int, life: int):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.color = color
        self.max_life = life
        self.life = life

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.life -= 1

    @property
    def is_alive(self) -> bool:
        return self.life > 0


class HourglassPlayer:
    WIDTH: int = 8
    HEIGHT: int = 12

    def __init__(self, screen_w: int = 120, screen_h: int = 160):
        self.screen_w = screen_w
        self.screen_h = screen_h
        self.x: float = screen_w / 2.0
        self.base_y: float = 40.0
        self.y: float = self.base_y
        self.vx: float = 0.0
        self.friction: float = 0.82
        self.base_accel: float = 1.35
        self.min_x: float = 8.0
        self.max_x: float = screen_w - 8.0
        self.sand_drain_phase: float = 0.0

    def reset(self):
        self.x = self.screen_w / 2.0
        self.y = self.base_y
        self.vx = 0.0
        self.sand_drain_phase = 0.0

    def apply_input(self, left: bool, right: bool, up: bool, down: bool, speed_mod: float = 1.0):
        ax = 0.0
        effective_accel = self.base_accel * speed_mod
        if left and not right:
            ax = -effective_accel
        elif right and not left:
            ax = effective_accel

        self.vx = (self.vx + ax) * self.friction
        self.x += self.vx
        self.x = max(self.min_x, min(self.max_x, self.x))

        # Vertical visual shift for dive / brake
        target_y = self.base_y
        if down:
            target_y += 5.0
        elif up:
            target_y -= 4.0
        self.y += (target_y - self.y) * 0.25

        # Animate sand draining
        self.sand_drain_phase += 0.1

    def get_hitbox(self) -> Tuple[float, float, float, float]:
        """Returns (center_x, center_y, width, height)"""
        return (self.x, self.y, float(self.WIDTH), float(self.HEIGHT))


class SandGrain:
    WIDTH: float = 2.0
    HEIGHT: float = 2.0
    HITBOX_W: float = 6.0
    HITBOX_H: float = 6.0

    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y
        self.alive = True
        self.bypassed = False
        self.shimmer_phase = random.uniform(0, 6.28)

    def update(self, scroll_speed: float, player_x: float, player_y: float,
               repel_radius: float = 0.0, attract_radius: float = 0.0):
        self.y -= scroll_speed
        self.shimmer_phase += 0.2

        # Physics fields (Envy Repel / Lust Attract)
        dx = self.x - player_x
        dy = self.y - player_y
        dist_sq = dx * dx + dy * dy
        dist = math.sqrt(dist_sq) if dist_sq > 0 else 0.001

        if attract_radius > 0 and dist < attract_radius:
            # Lust Boon: Magnet pull toward player
            pull = 1.8 * (1.0 - dist / attract_radius)
            self.x -= (dx / dist) * pull
            self.y -= (dy / dist) * pull

        elif repel_radius > 0 and dist < repel_radius:
            # Envy Curse: Repulsion push away from player
            push = 2.2 * (1.0 - dist / repel_radius)
            self.x += (dx / dist) * push

        if self.y < -8:
            self.alive = False
            self.bypassed = True

    def get_hitbox(self) -> Tuple[float, float, float, float]:
        return (self.x, self.y, self.HITBOX_W, self.HITBOX_H)


class GlassShard:
    WIDTH: float = 4.0
    HEIGHT: float = 8.0
    HITBOX_W: float = 4.0
    HITBOX_H: float = 6.0

    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y
        self.alive = True
        self.rotation_angle = random.uniform(0, 6.28)
        self.spin_speed = random.choice([-0.12, -0.08, 0.08, 0.12])
        self.lateral_drift = random.uniform(-0.25, 0.25)

    def update(self, scroll_speed: float, hazard_speed_mod: float,
               player_x: float, player_y: float, attract_radius: float = 0.0):
        effective_speed = scroll_speed * hazard_speed_mod
        self.y -= effective_speed
        self.x += self.lateral_drift
        self.rotation_angle += self.spin_speed

        # Lust Curse: Glass shards pulled toward player
        if attract_radius > 0:
            dx = self.x - player_x
            dy = self.y - player_y
            dist = math.sqrt(dx * dx + dy * dy)
            if 0 < dist < attract_radius:
                pull = 1.4 * (1.0 - dist / attract_radius)
                self.x -= (dx / dist) * pull
                self.y -= (dy / dist) * pull

        if self.y < -12:
            self.alive = False

    def get_hitbox(self) -> Tuple[float, float, float, float]:
        return (self.x, self.y, self.HITBOX_W, self.HITBOX_H)


class EntityManager:
    def __init__(self, screen_w: int = 120, screen_h: int = 160):
        self.screen_w = screen_w
        self.screen_h = screen_h
        self.player = HourglassPlayer(screen_w, screen_h)
        self.sands: List[SandGrain] = []
        self.shards: List[GlassShard] = []
        self.particles: List[Particle] = []
        self.bypassed_sand_pool: int = 0
        self.spawn_accumulator: float = 0.0

    def reset(self):
        self.player.reset()
        self.sands.clear()
        self.shards.clear()
        self.particles.clear()
        self.bypassed_sand_pool = 0
        self.spawn_accumulator = 0.0

    def spawn_particles(self, x: float, y: float, count: int, colors: List[int], speed_range=(0.5, 2.0)):
        for _ in range(count):
            angle = random.uniform(0, 6.28)
            spd = random.uniform(*speed_range)
            vx = math.cos(angle) * spd
            vy = math.sin(angle) * spd
            color = random.choice(colors)
            life = random.randint(8, 16)
            self.particles.append(Particle(x, y, vx, vy, color, life))

    def wipe_all_hazards(self):
        for shard in self.shards:
            self.spawn_particles(shard.x, shard.y, 6, [6, 7])
        self.shards.clear()

    def reclaim_bypassed_sand(self) -> int:
        count = self.bypassed_sand_pool
        self.bypassed_sand_pool = 0
        return count

    def spawn_wave(self, spawn_rate_mult: float, wrath_active: bool):
        if wrath_active:
            return

        self.spawn_accumulator += spawn_rate_mult
        while self.spawn_accumulator >= 1.0:
            self.spawn_accumulator -= 1.0
            spawn_y = self.screen_h + random.uniform(4, 18)
            spawn_x = random.uniform(16, self.screen_w - 16)

            # 60% chance sand grain, 40% chance glass shard
            if random.random() < 0.60:
                self.sands.append(SandGrain(spawn_x, spawn_y))
            else:
                self.shards.append(GlassShard(spawn_x, spawn_y))

    def update(self, state):
        if state.current_state != state.current_state.__class__.CHRONOS:
            return

        # Player input & motion
        self.player.apply_input(
            left=getattr(state, "_input_left", False),
            right=getattr(state, "_input_right", False),
            up=getattr(state, "_input_up", False),
            down=getattr(state, "_input_down", False),
            speed_mod=state.sloth_player_speed_mod,
        )

        # Spawning
        wrath_active = (state.wrath_wipe_timer > 0)
        self.spawn_wave(state.spawn_rate_multiplier, wrath_active)

        # Update Sand grains
        px, py = self.player.x, self.player.y
        px_box = self.player.get_hitbox()

        remaining_sands = []
        for sand in self.sands:
            sand.update(
                scroll_speed=state.scroll_speed,
                player_x=px,
                player_y=py,
                repel_radius=state.envy_repel_radius,
                attract_radius=state.lust_attract_radius,
            )
            if not sand.alive:
                if sand.bypassed:
                    self.bypassed_sand_pool += 1
                continue

            # Check collection collision with player
            sb = sand.get_hitbox()
            if aabb_overlap(px_box[0], px_box[1], px_box[2], px_box[3], sb[0], sb[1], sb[2], sb[3]):
                state.add_score(base_points=100)
                self.spawn_particles(sand.x, sand.y, 5, [9, 10], speed_range=(0.8, 1.8))
                continue

            remaining_sands.append(sand)
        self.sands = remaining_sands

        # Update Glass shards
        remaining_shards = []
        for shard in self.shards:
            shard.update(
                scroll_speed=state.scroll_speed,
                hazard_speed_mod=state.sloth_hazard_speed_mod,
                player_x=px,
                player_y=py,
                attract_radius=state.lust_hazard_attract_radius,
            )
            if not shard.alive:
                state.total_shards_dodged += 1
                continue

            # Collision test with player
            shb = shard.get_hitbox()
            if aabb_overlap(px_box[0], px_box[1], px_box[2], px_box[3], shb[0], shb[1], shb[2], shb[3]):
                damaged = state.damage_player()
                if damaged:
                    self.spawn_particles(shard.x, shard.y, 8, [6, 7, 8], speed_range=(1.2, 2.8))
                continue

            remaining_shards.append(shard)
        self.shards = remaining_shards

        # Update particles
        self.particles = [p for p in self.particles if p.is_alive]
        for p in self.particles:
            p.update()

        # Hourglass sand drip trail particles
        if random.random() < 0.35:
            self.particles.append(
                Particle(self.player.x + random.uniform(-1, 1), self.player.y + 4,
                         random.uniform(-0.2, 0.2), random.uniform(-0.5, -0.2), 10, 8)
            )
