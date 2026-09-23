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

    @property
    def tilt(self) -> float:
        """Tilt angle in radians based on horizontal velocity (clamped to +/- 22 degrees)."""
        return max(-0.38, min(0.38, self.vx * 0.038))

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

        # Animate sand draining: direction & speed proportional to how tilted it is
        self.sand_drain_phase += self.tilt * 0.45

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
        self.vx: float = 0.0
        self.vy: float = 0.0
        self.speed_variance = speed_variance if speed_variance is not None else random.uniform(0.85, 1.15)
        self.alive = True
        self.bypassed = False
        self.shimmer_phase = shimmer_phase if shimmer_phase is not None else random.uniform(0, 6.28)
        self.lateral_drift = lateral_drift if lateral_drift is not None else random.uniform(-0.4, 0.4)

    def update(self, scroll_speed: float, player_x: float, player_y: float,
               repel_radius: float = 0.0, attract_radius: float = 0.0,
               mega_attract_radius: float = 0.0):
        self.shimmer_phase += 0.2
        base_vy = -scroll_speed * self.speed_variance
        base_vx = self.lateral_drift + math.sin(self.shimmer_phase * 0.4) * 0.4

        # Physics fields: acceleration vectors (Envy Mega Lust / Lust Attract / Envy Repel)
        dx = self.x - player_x
        dy = self.y - player_y
        dist_sq = dx * dx + dy * dy
        dist = math.sqrt(dist_sq) if dist_sq > 0 else 0.001
        ux = -dx / dist
        uy = -dy / dist

        ax = 0.0
        ay = 0.0

        if mega_attract_radius > 0 and dist < mega_attract_radius:
            # Envy Boon: Temporary Mega Lust strongly accelerates all grains within 2x vignette radius
            accel = max(4.0, 10.0 * (1.0 - dist / mega_attract_radius))
            ax += ux * accel
            ay += uy * accel

        elif attract_radius > 0 and dist < attract_radius:
            # Lust Boon: Magnet pull acceleration toward player
            accel = 2.4 * (1.0 - dist / attract_radius)
            ax += ux * accel
            ay += uy * accel

        elif repel_radius > 0 and dist < repel_radius:
            # Envy Curse: Repulsion acceleration away from player
            accel = 2.8 * (1.0 - dist / repel_radius)
            ax -= ux * accel
            ay -= uy * accel

        # Integrate acceleration into velocity (momentum)
        self.vx += ax
        self.vy += ay

        # Viscous drag / damping so momentum carries through smoothly after fields end
        self.vx *= 0.94
        self.vy *= 0.94

        # Terminal velocity clamp to keep simulation stable
        spd_sq = self.vx * self.vx + self.vy * self.vy
        if spd_sq > 50.0 * 50.0:
            spd = math.sqrt(spd_sq)
            self.vx = (self.vx / spd) * 50.0
            self.vy = (self.vy / spd) * 50.0

        # Integrate velocity into position
        self.x += base_vx + self.vx
        self.y += base_vy + self.vy

        # World bounds: simulate 10+ seconds down (up to y=6000.0) so pushed-down entities catch up
        if self.y < -40 or self.y > 6000.0 or abs(self.x - player_x) > 4500.0:
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
        self.vx: float = 0.0
        self.vy: float = 0.0
        self.speed_variance = speed_variance if speed_variance is not None else random.uniform(0.85, 1.18)
        self.alive = True
        self.rotation_angle = random.uniform(0, 6.28)
        spin_direction = random.choice([-1.0, 1.0])
        self.spin_speed = spin_direction * random.uniform(0.04, 0.18)
        self.lateral_drift = random.uniform(-1.0, 1.0)

        # Generate unique randomized scalene/acute triangle (never a right-angled triangle)
        tip_x = random.uniform(-6.0, 6.0)
        tip_y = random.uniform(-25.0, -15.0)
        b1_x = random.uniform(7.0, 17.0)
        b1_y = random.uniform(10.0, 22.0)
        b2_x = random.uniform(-17.0, -7.0)
        b2_y = random.uniform(8.0, 20.0)

        # Guarantee non-right-angled triangle: check dot products of all 3 corners
        d1 = (b1_x - tip_x) * (b2_x - tip_x) + (b1_y - tip_y) * (b2_y - tip_y)
        d2 = (tip_x - b1_x) * (b2_x - b1_x) + (tip_y - b1_y) * (b2_y - b1_y)
        d3 = (tip_x - b2_x) * (b1_x - b2_x) + (tip_y - b2_y) * (b1_y - b2_y)
        if any(abs(d) < 8.0 for d in (d1, d2, d3)):
            tip_x += 3.5

        self.vertices: List[Tuple[float, float]] = [(tip_x, tip_y), (b1_x, b1_y), (b2_x, b2_y)]

    def update(self, scroll_speed: float, hazard_speed_mod: float,
               player_x: float, player_y: float, attract_radius: float = 0.0):
        effective_speed = scroll_speed * hazard_speed_mod * self.speed_variance
        base_vy = -effective_speed
        base_vx = self.lateral_drift + math.sin(self.rotation_angle) * 0.6
        self.rotation_angle += self.spin_speed

        ax = 0.0
        ay = 0.0

        # Lust Curse: Glass shards accelerated toward player
        if attract_radius > 0:
            dx = self.x - player_x
            dy = self.y - player_y
            dist = math.sqrt(dx * dx + dy * dy)
            if 0 < dist < attract_radius:
                accel = 1.8 * (1.0 - dist / attract_radius)
                ax += (-dx / dist) * accel
                ay += (-dy / dist) * accel

        # Integrate acceleration into velocity (momentum)
        self.vx += ax
        self.vy += ay

        # Viscous drag / damping
        self.vx *= 0.93
        self.vy *= 0.93

        # Terminal velocity clamp (allows high explosive momentum up to 50.0)
        spd_sq = self.vx * self.vx + self.vy * self.vy
        if spd_sq > 50.0 * 50.0:
            spd = math.sqrt(spd_sq)
            self.vx = (self.vx / spd) * 50.0
            self.vy = (self.vy / spd) * 50.0

        # Integrate velocity into position
        self.x += base_vx + self.vx
        self.y += base_vy + self.vy

        # World bounds: simulate 10+ seconds down (up to y=6000.0) so pushed-down consequences catch up
        if self.y < -60 or self.y > 6000.0 or abs(self.x - player_x) > 4500.0:
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

    def wrath_explosion(self, explosion_radius: float = 1200.0, impulse_strength: float = 46.0) -> Tuple[int, int]:
        """Wrath Boon: Massive radial explosion centered at the player.
        Everything (both sand and shards) within 1200 pixels radius
        is given an instant HUGE acceleration / impulse away from the player.
        """
        px, py = self.player.x, self.player.y
        rad_sq = explosion_radius * explosion_radius

        shards_affected = 0
        for shard in self.shards:
            if not shard.alive:
                continue
            dx = shard.x - px
            dy = shard.y - py
            dist_sq = dx * dx + dy * dy
            if dist_sq <= rad_sq:
                dist = math.sqrt(dist_sq) if dist_sq > 0 else 0.001
                ux = dx / dist
                uy = dy / dist
                impulse = impulse_strength * (1.0 - 0.4 * (dist / explosion_radius))
                shard.vx += ux * impulse
                shard.vy += uy * impulse
                shard.spin_speed *= 2.5
                self.spawn_particles(shard.x, shard.y, 8, [7, 6, 8], speed_range=(4.0, 10.0), size=3)
                shards_affected += 1

        sands_affected = 0
        for sand in self.sands:
            if not sand.alive:
                continue
            dx = sand.x - px
            dy = sand.y - py
            dist_sq = dx * dx + dy * dy
            if dist_sq <= rad_sq:
                dist = math.sqrt(dist_sq) if dist_sq > 0 else 0.001
                ux = dx / dist
                uy = dy / dist
                impulse = impulse_strength * (1.0 - 0.4 * (dist / explosion_radius))
                sand.vx += ux * impulse
                sand.vy += uy * impulse
                self.spawn_particles(sand.x, sand.y, 8, [9, 10, 7], speed_range=(4.0, 10.0), size=3)
                sands_affected += 1

        # Central blast shockwave particles around player
        self.spawn_particles(px, py, 24, [7, 10, 8, 2], speed_range=(6.0, 14.0), size=4)
        return (shards_affected, sands_affected)

    def sloth_hurl_shards_downward(self, screen_width_factor: float = 3.0, impulse_speed: float = 38.0) -> int:
        """Sloth Boon: Sloth means lazy; lazy means doing nothing.
        In a single high acceleration frame, all shards below the player within 2-3 screens wide
        are thrown downward toward the bottom horizon, creating ~2s of safe empty space below the player
        where they can literally do nothing to survive, while shards clump up dangerously at the bottom.
        """
        px, py = self.player.x, self.player.y
        half_width = (self.screen_w * screen_width_factor) / 2.0

        thrown = 0
        for shard in self.shards:
            if not shard.alive:
                continue
            # Target shards below the player (oncoming hazards: shard.y > py)
            if shard.y > py and abs(shard.x - px) <= half_width:
                self.spawn_particles(shard.x, shard.y, 6, [7, 6, 8], speed_range=(3.0, 8.0), size=3)
                shard.y = max(shard.y, py + 520.0)
                shard.vy = max(shard.vy + impulse_speed, impulse_speed)
                shard.spin_speed *= 2.5
                thrown += 1

        return thrown

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
        self.spawn_accumulator += (spawn_rate_mult * 0.225 * density_scale)
        while self.spawn_accumulator >= 1.0:
            self.spawn_accumulator -= 1.0
            spawn_y = self.screen_h + random.uniform(20, 80)
            spawn_x = random.uniform(camera_x - margin, camera_x + self.screen_w + margin)

            # 55% chance sand grain, 45% chance glass shard
            if random.random() < 0.55:
                # In Pride, sands come in organic randomized clusters: 1st pride=pair (2), etc.
                group_size = 1 + pride_level
                shared_spd = random.uniform(0.85, 1.15)
                shared_drift = random.uniform(-0.4, 0.4)
                shared_shimmer = random.uniform(0, 6.28)

                offsets = [(0.0, 0.0)]
                for _ in range(group_size - 1):
                    for _attempt in range(15):
                        rand_angle = random.uniform(0, 2.0 * math.pi)
                        rand_r = random.uniform(14.0, 36.0)
                        cand_ox = math.cos(rand_angle) * rand_r
                        cand_oy = math.sin(rand_angle) * (rand_r * 0.8)
                        if all(math.hypot(cand_ox - ex_ox, cand_oy - ex_oy) >= 12.0 for ex_ox, ex_oy in offsets):
                            offsets.append((cand_ox, cand_oy))
                            break
                    else:
                        offsets.append((random.uniform(-25.0, 25.0), random.uniform(-25.0, 25.0)))

                for ox, oy in offsets:
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
                mega_attract_radius=state.envy_mega_lust_radius,
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

        # Hourglass sand drip trail particles:
        # Direction and speed of the falling sand is proportional to how tilted it is
        tilt = self.player.tilt
        tilt_mag = abs(tilt)
        if random.random() < (0.15 + tilt_mag * 1.8):
            origin_lx = math.sin(tilt) * 18.0
            ox = self.player.x + origin_lx * math.cos(tilt)
            oy = self.player.y + origin_lx * math.sin(tilt) + 16.0
            vx = math.sin(tilt) * 8.0 + random.uniform(-0.4, 0.4)
            vy = -1.5 - tilt_mag * 3.5 + random.uniform(-0.5, 0.5)
            self.particles.append(
                Particle(ox, oy, vx, vy, random.choice([9, 10, 7]), random.randint(8, 16), size=2)
            )
