from api import ArazimBattlesBot, Emote, Exceptions, Monkeys, Maps

# Only pick the cool emotes of course
EMOTES = [Emote.NONE, Emote.COOL, Emote.LAUGHING, Emote.LOVE]

UPGRADES = {
    Monkeys.DART_MONKEY : (3,0),
    Monkeys.TACK_SHOOTER : (0,2),
    Monkeys.NINJA_MONKEY : (3,0),
    Monkeys.SNIPER_MONKEY : (1,1),
    Monkeys.SUPER_MONKEY : (1,1),
    Monkeys.BOMB_TOWER : (1,0)
}

LOCATIONS = {
    Maps.YELLOW_BRICK: [
        [230, 448],
        [430, 176],
        [345, 182],
        [262, 256],
        [282, 445],
        [306, 219],
        [248, 186],
        [394, 137],
        [323, 264],
        [325, 419],
        [372, 223],
        [225, 141],
        [153, 383],
    ],
    Maps.TEMPLE: [
        [74, 531],
        [166, 420],
        [127, 483],
        [227, 378],
        [268, 312],
        [333, 250],
        [178, 480],
        [282, 373],
        [65, 474],
        [227, 438],
        [168, 367],
    ],
    Maps.SHAPES: [
        [212, 282],
        [122, 350],
        [68, 568],
        [184, 371],
        [178, 318],
        [236, 401],
        [122, 287],
        [71, 167],
    ],
    Maps.INTERCHANGE: [
        [216, 272],
        [146, 415],
        [289, 490],
        [318, 289],
        [106, 348],
        [207, 364],
        [256, 346],
        [196, 485],
    ],
}
MONKEY_PREFERENCE = [Monkeys.DART_MONKEY, Monkeys.NINJA_MONKEY, Monkeys.SNIPER_MONKEY, Monkeys.SUPER_MONKEY]

class MyBot(ArazimBattlesBot):
    monkey_count = 0
    monkey_levels = []
    attempted_position = 0
    emote_index = 0

    monkey_types = []
    to_upgrade = False
    monkey_to_upgrade = 0
    

    def setup(self) -> None:
        self.context.ban_monkey(Monkeys.NINJA_MONKEY)

    def get_monkey(self) -> Monkeys:
        if self.context.get_current_time() == 0:
            return
        banned = set(self.context.get_banned_monkeys())
        unbanned = list(set(MONKEY_PREFERENCE) - banned)
        chosen = min(unbanned, key=lambda m: MONKEY_PREFERENCE.index(m))
        return chosen

    def place(self):
        self.context.log_info(self.context.get_map())
        positions = LOCATIONS[self.context.get_map()]
        m_type = self.get_monkey()
        result = self.context.place_monkey(
            m_type,
            (
                positions[self.attempted_position][0],
                positions[self.attempted_position][1],
            )
            if self.attempted_position < len(positions)
            else (
                (24 * self.attempted_position) % 400 + 24,
                200 + 24 * (24 * self.attempted_position) // 400,
            ),
        )
        if result == Exceptions.OK:
            self.monkey_count += 1
            self.monkey_levels.append([0,0])
            self.monkey_types.append(m_type)
            
        elif (
            result == Exceptions.OUT_OF_MAP
            or result == Exceptions.TOO_CLOSE_TO_BLOON_ROUTE
            or result == Exceptions.TOO_CLOSE_TO_OTHER_MONKEY
        ):
            self.context.log_warning(f"Couldn't place monkey because of: {result}")
            self.attempted_position += 1

    def upgrade(self, monkey_index):
        m_type = self.monkey_types[monkey_index]
        if self.monkey_levels[monkey_index][0] < UPGRADES[m_type][0]:
            if self.context.upgrade_monkey(monkey_index, True):
                self.monkey_levels[monkey_index][0] += 1
                return True
            
        if self.monkey_levels[monkey_index][1] < UPGRADES[m_type][1]:
            if self.context.upgrade_monkey(monkey_index, False):
                self.monkey_levels[monkey_index][1] += 1
                return True
            
        return False

    def place_and_upgrade(self):
        if not self.to_upgrade:
            self.place()
            self.to_upgrade = True
        else:
            self.upgrade(self.monkey_to_upgrade)
            self.monkey_to_upgrade += 1
            self.monkey_to_upgrade %= self.monkey_count()
            self.to_upgrade = False
    

    def run(self) -> None:
        if self.context.get_current_time() % 5 == 0:
            self.context.log_info("Placing Monkeys!")

            # Place Monkeys
            result = self.context.place_monkey(
                Monkeys.SNIPER_MONKEY, (24 * self.attempted_position + 24, 400)
            )
            if result == Exceptions.OK:
                self.monkey_count += 1
                self.monkey_levels.append([0,0])
            elif (
                result == Exceptions.OUT_OF_MAP
                or result == Exceptions.TOO_CLOSE_TO_BLOON_ROUTE
                or result == Exceptions.TOO_CLOSE_TO_OTHER_MONKEY
            ):
                self.context.log_warning(f"Couldn't place monkey because of: {result}")
                self.attempted_position += 1

        if self.context.get_current_time() % 1 == 0:
            self.context.display_emote(EMOTES[self.emote_index])
            self.emote_index = (self.emote_index + 1) % len(EMOTES)

        if self.context.get_current_time() in [75, 90, 105]:
            self.context.tower_boost()
        if self.context.get_current_time() in [80, 95, 110]:
            self.context.bloon_boost()

        for monkey_index in range(self.monkey_count):
            # Upgrade Monkeys
            if self.context.get_current_time() > 20:
                self.upgrade(monkey_index)

            # Target Bloons
            targets = self.context.get_monkey_targets(monkey_index)
            if len(targets) > 0:
                self.context.target_bloon(monkey_index, targets[0].index)
