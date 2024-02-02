from api import ArazimBattlesBot, Emote, Exceptions, Monkeys, Maps

# Only pick the cool emotes of course
EMOTES = [Emote.NONE, Emote.COOL, Emote.LAUGHING, Emote.LOVE]

LOCATIONS = {
    Maps.YELLOW_BRICK: [[230,448],[430,176],[345,182],[262,256],[282,445],[306,219],[248,186],[394,137],[323,264],[325,419],[372,223],[225,141],[153,383]],
    Maps.TEMPLE: [[74,531],[166,420],[127,483],[227,378],[268,312],[333,250],[178,480],[282,373],[65,474],[227,438],[168,367]],
    Maps.SHAPES: [[212,282],[122,350],[68,568],[184,371],[178,318],[236,401],[122,287],[71,167]],
    Maps.INTERCHANGE: [[216,272],[146,415],[289,490],[318,289],[106,348],[207,364],[256,346],[196,485]]
}

class MyBot(ArazimBattlesBot):
    monkey_count = 0
    monkey_levels = []
    attempted_position = 0
    emote_index = 0

    def setup(self) -> None:
        self.context.ban_monkey(Monkeys.BOMB_TOWER)

    def run(self) -> None:
        if self.context.get_current_time() % 5 == 0:
            self.context.log_info("Placing Monkeys!")

            # Place Monkeys
            self.context.log_info(self.context.get_map())
            positions = LOCATIONS[self.context.get_map()]
            
            result = self.context.place_monkey(
                Monkeys.DART_MONKEY, (positions[self.attempted_position][0], positions[self.attempted_position][1])
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