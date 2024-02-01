from api import EcoBloons, Bloons
from api import ArazimBattlesBot, Emote, Exceptions, Monkeys, Maps

# Only pick the cool emotes of course
EMOTES = [Emote.THUMBS_DOWN]

BLOON_HEALTH: dict[Bloons, int] = {
    Bloons.RED: 1,
    Bloons.BLUE: 2,
    Bloons.GREEN: 3,
    Bloons.YELLOW: 4,
    Bloons.PINK: 5,
    Bloons.BLACK: 11,
    Bloons.WHITE: 11,
    Bloons.LEAD: 23,
    Bloons.ZEBRA: 23,
    Bloons.RAINBOW: 47,
    Bloons.CERAMIC: 104,
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

MONKEY_PREFERENCE = [Monkeys.DART_MONKEY, Monkeys.NINJA_MONKEY, Monkeys.SNIPER_MONKEY]

BLOON_COST: dict[EcoBloons, int] = {
    EcoBloons.GROUPED_RED: 25,
    EcoBloons.SPACED_BLUE: 25,
    EcoBloons.GROUPED_BLUE: 42,
    EcoBloons.SPACED_PINK: 42,
    EcoBloons.GROUPED_GREEN: 60,
    EcoBloons.GROUPED_YELLOW: 75,
    EcoBloons.SPACED_WHITE: 90,
    EcoBloons.GROUPED_PINK: 90,
    EcoBloons.SPACED_LEAD: 90,
    EcoBloons.GROUPED_WHITE: 125,
    EcoBloons.SPACED_ZEBRA: 125,
    EcoBloons.GROUPED_BLACK: 150,
}


class MyBot(ArazimBattlesBot):
    monkey_count = 0
    monkey_levels = []
    attempted_position = 0
    emote_index = 0

    def get_monkey(self) -> Monkeys:
        if self.context.get_current_time() == 0:
            return
        banned = set(self.context.get_banned_monkeys())
        unbanned = list(set(MONKEY_PREFERENCE) - banned)
        chosen = min(unbanned, key=lambda m: MONKEY_PREFERENCE.index(m))
        return chosen

    def setup(self) -> None:
        self.context.ban_monkey(Monkeys.DART_MONKEY)

    def run(self) -> None:
        spent = self.send_bloons(self.context.get_money())
        if spent:
            # self.context.log_info(f"spent {spent}.")
            pass

        if self.context.get_current_time() % 5 == 0:
            self.context.log_info("Placing Monkeys!")

            # Place Monkeys
            self.context.log_info(self.context.get_map())
            positions = LOCATIONS[self.context.get_map()]

            result = self.context.place_monkey(
                self.get_monkey(),
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
                self.monkey_levels.append(0)
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
                if self.monkey_levels[monkey_index] < 4:
                    if self.context.upgrade_monkey(monkey_index, True):
                        self.monkey_levels[monkey_index] += 1

            # Target Bloons
            targets = self.context.get_monkey_targets(monkey_index)
            if len(targets) > 0:
                self.context.target_bloon(monkey_index, targets[0].index)

    def send_bloons(self, money: int) -> int:
        """
        Sends bloons with up to `money` cost, returns how much money was
        actually spent.
        """
        time = self.context.get_current_time()
        players = set(range(self.context.get_player_count()))
        enemies = players - {self.context.get_current_player_index()}
        index = list(enemies)[0]
        if time < 29:
            return 0

        elif 29 <= time < 68:
            send_bloon = EcoBloons.SPACED_BLUE

        elif 68 <= time < 161:
            send_bloon = EcoBloons.SPACED_PINK

        elif 161 <= time:
            send_bloon = EcoBloons.GROUPED_YELLOW

        spent = 0
        while money >= BLOON_COST[send_bloon]:
            result = self.context.send_bloons(index, send_bloon)
            spent += BLOON_COST[send_bloon]
            self.context.log_info(f"Sending {send_bloon}: {result}")
            money -= BLOON_COST[send_bloon]

        return spent
