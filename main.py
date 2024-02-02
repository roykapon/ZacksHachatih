from api import EcoBloons, Bloons
from api import ArazimBattlesBot, Emote, Exceptions, Monkeys, Maps

# Only pick the cool emotes of course
EMOTES = [Emote.THUMBS_DOWN]

MONKEYTYPE_TO_STRING = {
    Monkeys.DART_MONKEY: "dart",
    Monkeys.TACK_SHOOTER: "tack",
    Monkeys.NINJA_MONKEY: "dart",
    Monkeys.SUPER_MONKEY: "dart",
    Monkeys.SNIPER_MONKEY: "dart",
    Monkeys.BOMB_TOWER: "tack"
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
    Maps.YELLOW_BRICK: {"dart": [[230,448],[430,176],[345,182],[262,256],[282,445],[306,219],[248,186],[394,137],[323,264],[325,419],[372,223],[225,141],[153,383]],
                        "tack": [[346,189],[152,189],[156,384],[247,375],[248,183],[112,432],[383,242],[55,180],[296,231],[326,290]]},
    Maps.TEMPLE: {"dart": [[74,531],[166,420],[127,483],[227,378],[268,312],[333,250],[178,480],[282,373],[65,474],[227,438],[168,367]],
                  "tack": [[134,503],[373,163],[261,296],[233,376],[160,412],[337,255],[199,502],[308,179],[333,320],[260,230]]},
    Maps.SHAPES: {"dart": [[212,282],[122,350],[68,568],[184,371],[178,318],[236,401],[122,287],[71,167]],
                  "tack": [[363,226],[108,236],[193,308],[218,527],[110,301],[185,153],[273,320],[173,382],[183,226],[268,236],[105,509],[334,508]]},
    Maps.INTERCHANGE: {"dart": [[216,272],[146,415],[289,490],[318,289],[106,348],[207,364],[256,346],[196,485]],
                       "tack": [[199,264],[223,364],[161,461],[262,187],[256,420],[165,208],[321,295],[100,348],[313,487],[226,80]]}
}

MONKEY_PREFERENCE = [Monkeys.DART_MONKEY, Monkeys.NINJA_MONKEY, Monkeys.SNIPER_MONKEY]


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

    def chose_type_to_place(self):
        banned = self.context.get_banned_monkeys()
        if self.attempted_position < 2:
            if Monkeys.TACK_SHOOTER not in banned:
                return Monkeys.TACK_SHOOTER
            elif Monkeys.DART_MONKEY not in banned:
                return Monkeys.DART_MONKEY
            else:
                return Monkeys.NINJA_MONKEY
            
        else:
            if Monkeys.DART_MONKEY not in banned:
                return Monkeys.DART_MONKEY
            elif Monkeys.NINJA_MONKEY not in banned:
                return Monkeys.NINJA_MONKEY
            else:
                return Monkeys.SNIPER_MONKEY
            
    
    def setup(self) -> None:
        self.context.ban_monkey(Monkeys.TACK_SHOOTER) # ! TO CHANGE

    def run(self) -> None:
        self.send_bloons()

        if self.context.get_current_time() % 5 == 0:
            self.context.log_info("Placing Monkeys!")

            # Place Monkeys
            self.context.log_info(self.context.get_map())
            
            monkey_type_place = self.chose_type_to_place()
            monkey_string_place = MONKEYTYPE_TO_STRING[monkey_type_place]
            positions = LOCATIONS[self.context.get_map()][monkey_string_place]

            result = self.context.place_monkey(
                monkey_type_place,
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

    def send_bloons(self):
        time = self.context.get_current_time()
        index = 1 - self.context.get_current_player_index()
        if time < 29:
            return

        if 29 < time < 68:
            if time % 5 != 0:
                return
            result = self.context.send_bloons(index, EcoBloons.SPACED_BLUE)
            self.context.log_info(f"Sending BLUE. {result}")
            return

        if 68 < time < 161:
            if time % 5 != 0:
                return
            result = self.context.send_bloons(index, EcoBloons.SPACED_PINK)
            self.context.log_info(f"Sending PINK. {result}")
            return

        if 161 < time:
            if self.context.get_money() < 150:
                return
            result = self.context.send_bloons(index, EcoBloons.GROUPED_YELLOW)
            self.context.log_info(f"Sending YELLOW. {result}")
