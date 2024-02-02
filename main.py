from api import EcoBloons, Bloons
from api import ArazimBattlesBot, Emote, Exceptions, Monkeys, Maps

# Only pick the cool emotes of course
EMOTES = [Emote.THUMBS_DOWN]

UPGRADES = {
    Monkeys.DART_MONKEY : (3,0),
    Monkeys.TACK_SHOOTER : (0,2),
    Monkeys.NINJA_MONKEY : (3,0),
    Monkeys.SNIPER_MONKEY : (1,1),
    Monkeys.SUPER_MONKEY : (1,1),
    Monkeys.BOMB_TOWER : (1,0)
}

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


class MyBot(ArazimBattlesBot):
    monkey_count = 0
    monkey_levels = []
    attempted_position = 0
    emote_index = 0
    sending_money = 0
    monkey_money = 0

    def get_monkey(self) -> Monkeys:
        if self.context.get_current_time() == 0:
            return None
        banned = set(self.context.get_banned_monkeys())
        unbanned = list(set(MONKEY_PREFERENCE) - banned)
        chosen = min(unbanned, key=lambda m: MONKEY_PREFERENCE.index(m))
        return chosen


    def setup(self) -> None:
        self.context.ban_monkey(Monkeys.DART_MONKEY)


    def update_current_money(self) -> tuple[int, int]:
        def get_money_split(money_diff):
            return int(0.5 * money_diff), money_diff - int(0.5 * money_diff)

        money_diff = self.context.get_money() - (self.sending_money + self.monkey_money)
        current_sending_money, current_monkey_money = get_money_split(money_diff)

        self.sending_money += current_sending_money
        self.monkey_money += current_monkey_money

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
            self.monkey_levels.append([0, 0])
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
        elif self.monkey_levels[monkey_index][1] < UPGRADES[m_type][1]:
            if self.context.upgrade_monkey(monkey_index, False):
                self.monkey_levels[monkey_index][1] += 1



    def place_and_upgrade(self):
        curr_money = self.context.get_money()
        self.upgrade()
        self.place()
        return curr_money - self.context.get_money()



    def run(self) -> None:
        self.update_current_money()

        self.sending_money -= self.send_bloons()
        self.monkey_money -= self.place_and_upgrade()

        if self.context.get_current_time() % 1 == 0:
            self.context.display_emote(EMOTES[self.emote_index])
            self.emote_index = (self.emote_index + 1) % len(EMOTES)

        if self.context.get_current_time() in [75, 90, 105]:
            self.context.tower_boost()
        if self.context.get_current_time() in [80, 95, 110]:
            self.context.bloon_boost()

        # Target Bloons
        self.target_monkeys()

    def target_monkeys(self) -> None:
        current_index = self.context.get_current_player_index()
        damage = {}
        for monkey_index in range(self.monkey_count):
            targets = self.context.get_monkey_targets(monkey_index)
            for target in targets:
                if target.uid not in damage:
                    damage[target.uid] = 0
            if BLOON_HEALTH[target.type] == damage[target.uid]:
                continue
            self.context.target_bloon(monkey_index, target.index)
            damage[target.uid] += 1


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

        elif 161 <= time < 196:
            send_bloon = EcoBloons.GROUPED_YELLOW
        elif 196 <= time < 237:
            send_bloon = EcoBloons.GROUPED_PINK
        elif 237 <= time < 275:
            send_bloon = EcoBloons.GROUPED_WHITE
        elif 275 <= time:
            send_bloon = EcoBloons.GROUPED_BLACK

        spent = 0
        while money >= BLOON_COST[send_bloon]:
            result = self.context.send_bloons(index, send_bloon)
            spent += BLOON_COST[send_bloon]
            # self.context.log_info(f"Sending {send_bloon}: {result}")
            money -= BLOON_COST[send_bloon]

        return spent