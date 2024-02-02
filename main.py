from api import ArazimBattlesBot, Emote, Exceptions, Monkeys

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

class MyBot(ArazimBattlesBot):
    monkey_count = 0
    monkey_levels = []
    attempted_position = 0
    emote_index = 0

    def setup(self) -> None:
        self.context.ban_monkey(Monkeys.NINJA_MONKEY)

    def upgrade(self, monkey_index):
        m_type = Monkeys.SNIPER_MONKEY
        if self.monkey_levels[monkey_index][0] < UPGRADES[m_type][0]:
            if self.context.upgrade_monkey(monkey_index, True):
                self.monkey_levels[monkey_index][0] += 1
        elif self.monkey_levels[monkey_index][1] < UPGRADES[m_type][1]:
            if self.context.upgrade_monkey(monkey_index, False):
                self.monkey_levels[monkey_index][1] += 1

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
