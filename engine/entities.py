"""Entities, Kinematics, Hitboxes, and Particle Physics for 600x800 resolution."""
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
    def __init__(self, x: float, y: float, vx: float, vy: float, color: int, life: int, size: int = 2):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.color = color
        self.max_life = life
        self.life = life
        self.size = size

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.life -= 1

    @property
    def is_alive(self) -> bool:
        return self.life > 0


class HourglassPlayer:
    WIDTH: int = 60
    HEIGHT: int = 40

    def __init__(self, screen_w: int = 600, screen_h: int = 800):
        self.screen_w = screen_w
        self.screen_h = screen_h
        self.x: float = screen_w / 2.0
        self.base_y: float = 200.0
        self.y: float = self.base_y
        self.vx: float = 0.0
        self.friction: float = 0.82
        self.base_accel: float = 6.0
        self.min_x: float = 45.0
        self.max_x: float = screen_w - 45.0
        self.sand_drain_phase: float = 0.0

    def reset(self):
        self.x = self.screen_w / 2.0
        self.y = self.base_y
        self.vx = 0.0
        self.sand_drain_phase = 0.0

    def apply_input(self, left: bool, right: bool, speed_mod: float = 1.0):
        """Only lateral A/D and Left/Right arrow controls (Infinite Arena - no wall clamping)."""
        ax = 0.0
        effective_accel = self.base_accel * speed_mod
        if left and not right:
            ax = -effective_accel
        elif right and not left:
            ax = effective_accel

        self.vx = (self.vx + ax) * self.friction
        self.x += self.vx

        # Steady vertical reference frame
        self.y = self.base_y

        # Animate sand draining
        self.sand_drain_phase += 0.15

    def get_hitbox(self) -> Tuple[float, float, float, float]:
        """Returns (center_x, center_y, width, height)"""
        return (self.x, self.y, float(self.WIDTH), float(self.HEIGHT))


class SandGrain:
    WIDTH: float = 10.0
    HEIGHT: float = 10.0
    HITBOX_W: float = 30.0
    HITBOX_H: float = 30.0

    def __init__(self, x: float, y: float, speed_variance: float = None,
                 lateral_drift: float = None, shimmer_phase: float = None):
        self.x = x
        self.y = y
        self.speed_variance = speed_variance if speed_variance is not None else random.uniform(0.85, 1.15)
        self.alive = True
        self.bypassed = False
        self.shimmer_phase = shimmer_phase if shimmer_phase is not None else random.uniform(0, 6.28)
        self.lateral_drift = lateral_drift if lateral_drift is not None else random.uniform(-0.4, 0.4)

    def update(self, scroll_speed: float, player_x: float, player_y: float,
               repel_radius: float = 0.0, attract_radius: float = 0.0):
        self.y -= scroll_speed * self.speed_variance
        self.shimmer_phase += 0.2

        # Small x-axis motion (gentle drift + oscillation - infinite arena)
        self.x += self.lateral_drift + math.sin(self.shimmer_phase * 0.4) * 0.4

        # Physics fields (Envy Repel / Lust Attract)
        dx = self.x - player_x
        dy = self.y - player_y
        dist_sq = dx * dx + dy * dy
        dist = math.sqrt(dist_sq) if dist_sq > 0 else 0.001

        if attract_radius > 0 and dist < attract_radius:
            # Lust Boon: Magnet pull toward player
            pull = 8.5 * (1.0 - dist / attract_radius)
            self.x -= (dx / dist) * pull
            self.y -= (dy / dist) * pull

        elif repel_radius > 0 and dist < repel_radius:
            # Envy Curse: Repulsion push away from player
            push = 10.0 * (1.0 - dist / repel_radius)
            self.x += (dx / dist) * push

        if self.y < -40 or abs(self.x - player_x) > 3500.0:
            self.alive = False
            self.bypassed = True

    def get_hitbox(self) -> Tuple[float, float, float, float]:
        return (self.x, self.y, self.HITBOX_W, self.HITBOX_H)


class GlassShard:
    WIDTH: float = 20.0
    HEIGHT: float = 40.0
    HITBOX_W: float = 20.0
    HITBOX_H: float = 30.0

    def __init__(self, x: float, y: float, speed_variance: float = None):
        self.x = x
        self.y = y
        self.speed_variance = speed_variance if speed_variance is not None else random.uniform(0.85, 1.18)
        self.alive = True
        self.rotation_angle = random.uniform(0, 6.28)
        self.spin_speed = random.choice([-0.12, -0.08, 0.08, 0.12])
        self.lateral_drift = random.uniform(-1.0, 1.0)

    def update(self, scroll_speed: float, hazard_speed_mod: float,
               player_x: float, player_y: float, attract_radius: float = 0.0):
        effective_speed = scroll_speed * hazard_speed_mod * self.speed_variance
        self.y -= effective_speed

        # Small x-axis motion (drift + flutter - infinite arena)
        self.x += self.lateral_drift + math.sin(self.rotation_angle) * 0.6
        self.rotation_angle += self.spin_speed

        # Lust Curse: Glass shards pulled toward player
        if attract_radius > 0:
            dx = self.x - player_x
            dy = self.y - player_y
            dist = math.sqrt(dx * dx + dy * dy)
            if 0 < dist < attract_radius:
                pull = 6.5 * (1.0 - dist / attract_radius)
                self.x -= (dx / dist) * pull
                self.y -= (dy / dist) * pull

        if self.y < -60 or abs(self.x - player_x) > 3500.0:
            self.alive = False

    def get_hitbox(self) -> Tuple[float, float, float, float]:
        return (self.x, self.y, self.HITBOX_W, self.HITBOX_H)


class EntityManager:
    def __init__(self, screen_w: int = 600, screen_h: int = 800):
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

    def spawn_particles(self, x: float, y: float, count: int, colors: List[int], speed_range=(2.0, 8.0), size=3):
        for _ in range(count):
            angle = random.uniform(0, 6.28)
            spd = random.uniform(*speed_range)
            vx = math.cos(angle) * spd
            vy = math.sin(angle) * spd
            color = random.choice(colors)
            life = random.randint(10, 20)
            self.particles.append(Particle(x, y, vx, vy, color, life, size=size))

    def wipe_all_hazards(self):
        for shard in self.shards:
            self.spawn_particles(shard.x, shard.y, 10, [6, 7], size=4)
        self.shards.clear()

    def reclaim_bypassed_sand(self) -> int:
        count = self.bypassed_sand_pool
        self.bypassed_sand_pool = 0
        return count

    def collect_all_screen_sands(self, camera_x: float = None) -> int:
        """Collect all sand grains currently visible on the screen."""
        if camera_x is None:
            camera_x = self.player.x - self.screen_w / 2.0
        min_x = camera_x
        max_x = camera_x + self.screen_w
        min_y = 0.0
        max_y = float(self.screen_h)

        collected = 0
        remaining = []
        for s in self.sands:
            if min_x <= s.x <= max_x and min_y <= s.y <= max_y:
                collected += 1
                self.spawn_particles(s.x, s.y, 8, [9, 10, 7], size=3)
            else:
                remaining.append(s)
        self.sands = remaining
        return collected

    def spawn_wave(self, spawn_rate_mult: float, wrath_active: bool, camera_x: float = None, pride_level: int = 0):
        if wrath_active:
            return

        if camera_x is None:
            camera_x = self.player.x - self.screen_w / 2.0

        # Kinematic Spawn Horizon Math:
        # v_x_max = (6.0 * 0.82) / (1 - 0.82) = 27.33 px/frame
        # t_fall = (850 - 200) / 7.5 = 86.7 frames
        # Max travel dx = 86.7 * 27.33 = 2369 px (~3.95 screens)
        # Margin = 4.5 screens = 2700.0 px on either side of camera
        margin = 2700.0
        span_w = self.screen_w + 2.0 * margin
        density_scale = span_w / 880.0
        self.spawn_accumulator += (spawn_rate_mult * 0.45 * density_scale)
        while self.spawn_accumulator >= 1.0:
            self.spawn_accumulator -= 1.0
            spawn_y = self.screen_h + random.uniform(20, 80)
            spawn_x = random.uniform(camera_x - margin, camera_x + self.screen_w + margin)

            # 55% chance sand grain, 45% chance glass shard
            if random.random() < 0.55:
                # In Pride, sands come in groups: 1st pride=pair (2), 2nd pride=triplet (3), etc.
                group_size = 1 + pride_level
                shared_spd = random.uniform(0.85, 1.15)
                shared_drift = random.uniform(-0.4, 0.4)
                shared_shimmer = random.uniform(0, 6.28)
                cluster_radius = 22.0 if group_size > 1 else 0.0

                for gi in range(group_size):
                    if group_size > 1:
                        angle = (2.0 * math.pi * gi) / group_size
                        ox = math.cos(angle) * cluster_radius
                        oy = math.sin(angle) * (cluster_radius * 0.7)
                    else:
                        ox, oy = 0.0, 0.0
                    self.sands.append(
                        SandGrain(
                            spawn_x + ox,
                            spawn_y + oy,
                            speed_variance=shared_spd,
                            lateral_drift=shared_drift,
                            shimmer_phase=shared_shimmer,
                        )
                    )
            else:
                self.shards.append(GlassShard(spawn_x, spawn_y))
                # 20% chance to spawn an offset hazard cluster pair for weaving challenge
                if random.random() < 0.20:
                    offset_x = spawn_x + random.choice([-55.0, 55.0])
                    offset_y = spawn_y + random.uniform(20.0, 45.0)
                    self.shards.append(GlassShard(offset_x, offset_y))

    def update(self, state):
        if state.current_state != state.current_state.__class__.CHRONOS:
            return

        # Player input & motion (Only lateral left/right)
        bot_handicap = getattr(state, "_bot_speed_handicap", 1.0)
        self.player.apply_input(
            left=getattr(state, "_input_left", False),
            right=getattr(state, "_input_right", False),
            speed_mod=state.sloth_player_speed_mod * bot_handicap,
        )

        # Spawning across camera horizon
        wrath_active = (state.wrath_wipe_timer > 0)
        cam_x = self.player.x - self.screen_w / 2.0
        self.spawn_wave(state.spawn_rate_multiplier, wrath_active, cam_x, pride_level=getattr(state, "pride_level", 0))

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

            # Check collection collision with player (1 sand is 1 point!)
            sb = sand.get_hitbox()
            if aabb_overlap(px_box[0], px_box[1], px_box[2], px_box[3], sb[0], sb[1], sb[2], sb[3]):
                state.add_score(base_points=1)
                self.spawn_particles(sand.x, sand.y, 8, [9, 10], speed_range=(3.0, 7.0), size=3)
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
                    self.spawn_particles(shard.x, shard.y, 14, [6, 7, 8], speed_range=(5.0, 12.0), size=4)
                continue

            remaining_shards.append(shard)
        self.shards = remaining_shards

        # Update particles
        self.particles = [p for p in self.particles if p.is_alive]
        for p in self.particles:
            p.update()

        # Hourglass sand drip trail particles
        if random.random() < 0.40:
            self.particles.append(
                Particle(self.player.x + random.uniform(-4, 4), self.player.y + 20,
                         random.uniform(-0.6, 0.6), random.uniform(-2.0, -0.8), 10, 10, size=2)
            )
