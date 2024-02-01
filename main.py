from api import EcoBloons, Bloons
from api import ArazimBattlesBot, Emote, Exceptions, Monkeys, Maps

# Only pick the cool emotes of course
EMOTES = [Emote.THUMBS_DOWN]

UPGRADES = {
    Monkeys.DART_MONKEY: (3, 0),
    Monkeys.TACK_SHOOTER: (0, 2),
    Monkeys.NINJA_MONKEY: (3, 0),
    Monkeys.SNIPER_MONKEY: (1, 1),
    Monkeys.SUPER_MONKEY: (1, 1),
    Monkeys.BOMB_TOWER: (1, 0),
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

MONKEY_PREFERENCE = [Monkeys.DART_MONKEY, Monkeys.NINJA_MONKEY, Monkeys.TACK_SHOOTER]


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
    EcoBloons.SPACED_CERAMIC: 300,
}


PLACE_COST: dict[Monkeys, int] = {
    Monkeys.DART_MONKEY: 200,
    Monkeys.TACK_SHOOTER: 360,
    Monkeys.NINJA_MONKEY: 500,
    Monkeys.SUPER_MONKEY: 3000,
    Monkeys.BOMB_TOWER: 650,
    Monkeys.SNIPER_MONKEY: 350,
}


UPGRADE_COST: dict[Monkeys, tuple[list[int], list[int]]] = {
    Monkeys.DART_MONKEY: ([90, 160, 500, 1900], [140, 170, 475]),
    Monkeys.TACK_SHOOTER: ([210, 300], [75, 175]),
    Monkeys.NINJA_MONKEY: ([300, 250, 700, 3000], []),
    Monkeys.SUPER_MONKEY: ([3000, 4000], [800, 1200]),
    Monkeys.BOMB_TOWER: ([200], [400, 400]),
    Monkeys.SNIPER_MONKEY: ([300, 1800, 3500], [350, 300, 2400]),
}


class MyBot(ArazimBattlesBot):
    monkey_count = 0
    monkey_levels = []
    attempted_position = 0
    emote_index = 0
    sending_money = 0
    monkey_money = 0

    monkey_types = []
    to_upgrade = False
    monkey_to_upgrade = 0

    def setup(self) -> None:
        self.context.ban_monkey(Monkeys.NINJA_MONKEY)

    def get_monkey(self) -> Monkeys:
        if self.context.get_current_time() == 0:
            return None
        banned = set(self.context.get_banned_monkeys())
        unbanned = list(set(MONKEY_PREFERENCE) - banned)
        chosen = min(unbanned, key=lambda m: MONKEY_PREFERENCE.index(m))
        return chosen

    def place(self):
        positions = LOCATIONS[self.context.get_map()]
        m_type = self.get_monkey()
        result = self.context.place_monkey(
            m_type,
            (
                (
                    positions[self.attempted_position][0],
                    positions[self.attempted_position][1],
                )
                if self.attempted_position < len(positions)
                else (
                    (24 * self.attempted_position) % 400 + 24,
                    200 + 24 * (24 * self.attempted_position) // 400,
                )
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
                return True

        if self.monkey_levels[monkey_index][1] < UPGRADES[m_type][1]:
            if self.context.upgrade_monkey(monkey_index, False):
                self.monkey_levels[monkey_index][1] += 1
                return True

        return False

    def update_current_money(self) -> tuple[int, int]:
        def get_money_split(money_diff):
            return int(0.5 * money_diff), money_diff - int(0.5 * money_diff)

        money_diff = self.context.get_money() - (self.sending_money + self.monkey_money)
        current_sending_money, current_monkey_money = get_money_split(money_diff)

        self.sending_money += current_sending_money
        self.monkey_money += current_monkey_money

    def place_and_upgrade(self):
        current_money = self.context.get_money()
        if not self.to_upgrade:
            self.place()
            self.to_upgrade = True
        else:
            self.upgrade(self.monkey_to_upgrade)
            self.monkey_to_upgrade += 1
            self.monkey_to_upgrade %= self.monkey_count
            self.to_upgrade = False
        return current_money - self.context.get_money()

    def eco_push(self) -> bool:
        return self.context.get_eco() > 600

    def sending_push(self) -> bool:
        if self.eco_push():
            return False
        time = self.context.get_current_time()
        if time < 50:
            return False

        return time % 25 == 0

    def run(self) -> None:
        self.update_current_money()

        self.sending_money -= self.send_eco(self.sending_money)
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

    def send_bloons(self, money) -> int:
        if self.eco_push():
            return self.send_eco(money)
        if self.sending_push():
            return self.send_push(money)

    def send_eco(self, money: int) -> int:
        """
        Sends bloons with up to `money` cost, returns how much money was
        actually spent.
        """
        starting_money = self.context.get_money()
        time = self.context.get_current_time()
        enemy = self.get_player_to_attack()
        if time < 29:
            return 0

        elif 29 <= time < 68:
            send_bloon = EcoBloons.SPACED_BLUE
        elif 68 <= time < 161:
            send_bloon = EcoBloons.SPACED_PINK
        elif 161 <= time < 196:
            send_bloon = EcoBloons.GROUPED_YELLOW
        elif 196 <= time:
            send_bloon = EcoBloons.GROUPED_PINK

        spent = 0
        while money >= BLOON_COST[send_bloon]:
            if self.context.send_bloons(enemy, send_bloon) != Exceptions.OK:
                return spent
            spent += BLOON_COST[send_bloon]
            # self.context.log_info(f"Sending {send_bloon}: {result}")
            money -= BLOON_COST[send_bloon]

        return spent

    def send_push(self, money) -> int:
        SEND_AMOUNT = 5
        send_bloon = EcoBloons.SPACED_CERAMIC
        enemy = self.get_player_to_attack()
        spent = 0
        if money < SEND_AMOUNT * BLOON_COST[send_bloon]:
            return 0

        while money >= BLOON_COST[send_bloon]:
            if self.context.send_bloons(enemy, send_bloon) != Exceptions.OK:
                return spent
            spent += BLOON_COST[send_bloon]
            # self.context.log_info(f"Sending {send_bloon}: {result}")
            money -= BLOON_COST[send_bloon]

        return spent

    def get_player_to_attack(self):
        players = set(range(self.context.get_player_count()))
        enemies = players - {self.context.get_current_player_index()}
        enemies = {
            player for player in enemies if self.context.is_player_active(player)
        }
        return list(enemies)[0]
