# UWAGA: Ta gra tekstowa to rozbudowana wersja "RPG samochodowego".
# Zawiera ekwipunek, questy, crafting, mapę, pogodę, bossów, NPC, system losowych wydarzeń itd.

import random
import time
import sys

# ---------------------------------------
# SYSTEM POGODY
# ---------------------------------------
class Weather:
    CONDITIONS = ["słonecznie", "deszcz", "mgła", "śnieg", "burza", "wiatr", "upał", "zimno"]

    def __init__(self):
        self.condition = random.choice(self.CONDITIONS)
        self.temp = random.randint(-10, 35)

    def change(self):
        self.condition = random.choice(self.CONDITIONS)
        self.temp = random.randint(-10, 35)

    def describe(self):
        return f"Obecna pogoda: {self.condition}, temperatura: {self.temp}°C"

# ---------------------------------------
# KLASA KIEROWCY
# ---------------------------------------
class Driver:
    def __init__(self, name, hp, speed, defense, inventory=None, level=1, exp=0):
        self.name = name
        self.max_hp = hp
        self.hp = hp
        self.speed = speed
        self.defense = defense
        self.inventory = inventory if inventory else []
        self.level = level
        self.exp = exp
        self.equipment = {"engine": None, "tires": None, "body": None, "gps": None, "nitro": None}
        self.talents = []
        self.used_talents = []
        self.journal = []
        self.position = "Garaż"
        self.gold = 0
        self.weather_effect = None
        self.team = []
        self.license = False

    def is_alive(self):
        return self.hp > 0

    def take_damage(self, damage):
        damage_taken = max(0, damage - self.defense)
        self.hp -= damage_taken
        print(f"{self.name} traci {damage_taken} wytrzymałości! (Stan auta: {self.hp}/{self.max_hp})")
        log_event(self, f"Stracono {damage_taken} wytrzymałości.")
        return damage_taken

    def attack_rival(self, rival):
        actual_speed, _ = get_equipped_stats(self)
        weather_bonus = 0
        if self.weather_effect == "przyczepność+":
            actual_speed += 2
        if self.weather_effect == "przyczepność-":
            actual_speed -= 2
        damage = random.randint(actual_speed - 2, actual_speed + 2)
        print(f"{self.name} próbuje wyprzedzić {rival.name} i zadaje {damage} presji!")
        return rival.take_damage(damage)

    def gain_exp(self, amount):
        print(f"{self.name} zdobywa {amount} doświadczenia.")
        self.exp += amount
        while self.exp >= self.level * 100:
            self.exp -= self.level * 100
            self.level_up()

    def level_up(self):
        self.level += 1
        self.max_hp += 10
        self.speed += 2
        self.defense += 1
        self.hp = self.max_hp
        print(f"{self.name} awansuje na poziom {self.level}! Auto ulepszone.")
        log_event(self, f"Osiągnięto poziom {self.level}.")

    def use_item(self, item_name):
        for item in self.inventory:
            if item.name == item_name:
                print(f"{self.name} używa: {item.name}.")
                item.apply(self)
                self.inventory.remove(item)
                log_event(self, f"Użyto przedmiotu: {item.name}.")
                return True
        print(f"{item_name} nie znajduje się w ekwipunku.")
        return False

    def show_inventory(self):
        print("Ekwipunek:")
        if not self.inventory:
            print(" (pusty)")
        for item in self.inventory:
            print(f" - {item.name}: {item.description}")

    def earn_gold(self, amount):
        self.gold += amount
        print(f"Otrzymujesz {amount} kredytów.")
        log_event(self, f"Zyskano {amount} kredytów.")

    def spend_gold(self, amount):
        if self.gold >= amount:
            self.gold -= amount
            print(f"Wydano {amount} kredytów.")
            log_event(self, f"Wydano {amount} kredytów.")
            return True
        else:
            print("Za mało kredytów!")
            return False

    def add_team_member(self, ally):
        self.team.append(ally)
        print(f"{ally.name} dołącza do twojego zespołu!")
        log_event(self, f"Sojusznik: {ally.name} dołączył do zespołu.")

# ---------------------------------------
# KLASA CZĘŚCI I PRZEDMIOTÓW
# ---------------------------------------
class Item:
    def __init__(self, name, description, effect_function):
        self.name = name
        self.description = description
        self.effect_function = effect_function

    def apply(self, target):
        self.effect_function(target)

class ShopItem(Item):
    def __init__(self, name, description, effect_function, price):
        super().__init__(name, description, effect_function)
        self.price = price

class Collectible(Item):
    def __init__(self, name, description, effect_function, rarity):
        super().__init__(name, description, effect_function)
        self.rarity = rarity

# ---------------------------------------
# FUNKCJE POMOCNICZE
# ---------------------------------------
def repair_20(driver):
    repair_amount = min(20, driver.max_hp - driver.hp)
    driver.hp += repair_amount
    print(f"{driver.name} naprawia auto o {repair_amount} punktów wytrzymałości.")
    log_event(driver, f"Naprawa: {repair_amount} wytrzymałości.")

def refuel(driver):
    driver.hp = min(driver.max_hp, driver.hp + 10)
    print(f"{driver.name} tankuje paliwo. (+10 wytrzymałości)")
    log_event(driver, "Tankowanie paliwa.")

def turbo_boost(driver):
    driver.speed += 5
    print(f"{driver.name} używa turbo! (+5 prędkości na wyścig)")
    log_event(driver, "Użyto turbo.")

def weather_grip_plus(driver):
    driver.weather_effect = "przyczepność+"
    print(f"Nowa opona! Przyczepność wzrosła na tę trasę.")

def weather_grip_minus(driver):
    driver.weather_effect = "przyczepność-"
    print(f"Używasz letnich opon w trudnych warunkach! Przyczepność spada.")

def fix_gps(driver):
    print("Twój GPS prowadzi cię najkrótszą trasą.")
    log_event(driver, "GPS aktywowany.")

def license_boost(driver):
    driver.license = True
    print("Otrzymujesz oficjalne prawo jazdy!")
    log_event(driver, "Prawo jazdy zdobyte.")

def create_basic_items():
    kit = Item("Zestaw Naprawczy", "Naprawia 20 punktów wytrzymałości", repair_20)
    fuel = Item("Kanister Paliwa", "Dodaje 10 wytrzymałości", refuel)
    turbo = Item("Turbo", "Zwiększa prędkość o 5 na wyścig", turbo_boost)
    gps = Item("GPS", "Pokazuje najkrótszą trasę", fix_gps)
    tire = Item("Opona Całoroczna", "Poprawia przyczepność w każdej pogodzie", weather_grip_plus)
    lic = Item("Prawo Jazdy", "Oficjalna licencja kierowcy", license_boost)
    return [kit, fuel, turbo, gps, tire, lic]

# ---------------------------------------
# KLASA RYWALI
# ---------------------------------------
class Rival(Driver):
    def __init__(self, name, hp, speed, defense, exp_reward):
        super().__init__(name, hp, speed, defense)
        self.exp_reward = exp_reward

    def taunt(self):
        taunts = [
            f"{self.name}: Myślisz, że mnie pokonasz?",
            f"{self.name}: Przygotuj się na porażkę!",
            f"{self.name}: Jadę po zwycięstwo!",
            f"{self.name}: To moja trasa!"
        ]
        print(random.choice(taunts))

# ---------------------------------------
# KLASA POLICJI
# ---------------------------------------
class Police(Rival):
    def __init__(self, name, hp, speed, defense, exp_reward, badge_number):
        super().__init__(name, hp, speed, defense, exp_reward)
        self.badge_number = badge_number

    def siren(self):
        print(f"🚨 {self.name} [{self.badge_number}] włącza syrenę i rozpoczyna pościg!")

# ---------------------------------------
# WYŚCIG
# ---------------------------------------
def race(driver, rival, weather=None, police_chase=False):
    print(f"\n--- WYŚCIG: {driver.name} VS {rival.name} ---")
    if weather:
        print(weather.describe())
    if isinstance(rival, Police):
        rival.siren()
        police_chase = True
    while driver.is_alive() and rival.is_alive():
        input("ENTER, aby rozpocząć rundę wyścigu...")
        driver.attack_rival(rival)
        if rival.is_alive():
            rival.attack_rival(driver)
    if driver.is_alive():
        print(f"{driver.name} pokonał {rival.name}!")
        driver.gain_exp(rival.exp_reward)
        reward = random.randint(50, 150)
        driver.earn_gold(reward)
        return True
    else:
        print(f"{driver.name} przegrał wyścig z {rival.name}...")
        if police_chase:
            print("Policja konfiskuje twój samochód! Gra zakończona.")
            sys.exit()
        return False

# ---------------------------------------
# KLASA LOKACJI
# ---------------------------------------
class Location:
    def __init__(self, name, description, rivals=None, items=None, connected=None, quest=None, weather=None, shop=None):
        self.name = name
        self.description = description
        self.rivals = rivals if rivals else []
        self.items = items if items else []
        self.connected = connected if connected else {}
        self.quest = quest
        self.npcs = []
        self.weather = weather if weather else Weather()
        self.shop = shop

    def show_info(self):
        print(f"\ Miejsce: {self.name}")
        print(self.description)
        print(self.weather.describe())
        if self.rivals:
            print("Rywale na miejscu: " + ", ".join(r.name for r in self.rivals))
        if self.items:
            print("Dostępne części: " + ", ".join(i.name for i in self.items))
        if self.quest:
            print(f"Zadanie dostępne: {self.quest.name}")
        if self.shop:
            print("🛒 W tej lokalizacji znajduje się sklep z częściami.")
        if self.npcs:
            print("NPC: " + ", ".join(n.name for n in self.npcs))
# ---------------------------------------
# KLASA ZADAŃ
# ---------------------------------------
class Quest:
    def __init__(self, name, description, requirement, reward):
        self.name = name
        self.description = description
        self.requirement = requirement
        self.reward = reward
        self.completed = False

    def try_complete(self, driver):
        if not self.completed and self.requirement(driver):
            print(f"\n✅ Zadanie ukończone: {self.name}")
            self.reward(driver)
            self.completed = True
            log_event(driver, f"Ukończono zadanie: {self.name}.")
            return True
        return False

# ---------------------------------------
# SYSTEM SKLEPU
# ---------------------------------------
class Shop:
    def __init__(self, name, stock):
        self.name = name
        self.stock = stock

    def show(self):
        print(f"🛒 Sklep: {self.name}")
        for i, item in enumerate(self.stock):
            print(f"{i+1}. {item.name} ({item.price} kredytów) - {item.description}")

    def buy(self, driver):
        self.show()
        choice = input("Wybierz numer części do zakupu lub ENTER by wyjść: ")
        if not choice.strip():
            return
        if choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(self.stock):
                item = self.stock[idx]
                if driver.spend_gold(item.price):
                    driver.inventory.append(item)
                    print(f"Kupiłeś: {item.name}")
                    log_event(driver, f"Kupiono {item.name} w sklepie {self.name}.")
            else:
                print("Nieprawidłowy wybór.")
        else:
            print("Błędny format.")

# ---------------------------------------
# NPC I SYSTEM DIALOGÓW
# ---------------------------------------
class NPC:
    def __init__(self, name, dialog_lines, quest=None, shop=None, can_join=False):
        self.name = name
        self.dialog_lines = dialog_lines
        self.quest = quest
        self.dialog_index = 0
        self.shop = shop
        self.can_join = can_join

    def talk(self, driver):
        if self.dialog_index < len(self.dialog_lines):
            print(f"\n{self.name} mówi: \"{self.dialog_lines[self.dialog_index]}\"")
            self.dialog_index += 1
        else:
            print(f"{self.name} nie ma nic więcej do powiedzenia.")
        if self.quest and not self.quest.completed:
            if self.quest.try_complete(driver):
                print(f"{self.name}: Świetna robota, mistrzu!")

    def offer_shop(self, driver):
        if self.shop:
            self.shop.buy(driver)
        else:
            print(f"{self.name} nie prowadzi sklepu.")

    def offer_join(self, driver):
        if self.can_join:
            driver.add_team_member(Ally(self.name, 60, 10, 4))
            self.can_join = False

def add_npc_to_location(location, npc):
    location.npcs.append(npc)

def interact_with_npc(location, driver):
    if location.npcs:
        print("\nDostępni NPC:")
        for idx, npc in enumerate(location.npcs):
            print(f"{idx + 1}. {npc.name}")
        choice = input("Wybierz NPC do rozmowy (numer): ")
        if choice.isdigit():
            index = int(choice) - 1
            if 0 <= index < len(location.npcs):
                npc = location.npcs[index]
                npc.talk(driver)
                if npc.shop:
                    if input("Chcesz zobaczyć ofertę sklepu? (t/n): ").lower() == "t":
                        npc.offer_shop(driver)
                if npc.can_join:
                    if input("Zaprosić do zespołu? (t/n): ").lower() == "t":
                        npc.offer_join(driver)
            else:
                print("Nie ma takiego NPC.")
        else:
            print("Niepoprawny wybór.")
    else:
        print("Nie ma tu nikogo do rozmowy.")

# ---------------------------------------
# GENEROWANIE RYWALI, POLICJI, BOSSÓW
# ---------------------------------------
def generate_rival(name):
    stats = {
        "Rywal Zawodowiec": (25, 12, 3, 50),
        "Policjant Turbo": (30, 15, 4, 70),
        "Mechanik Rajdowy": (35, 10, 5, 60),
        "Boss Wyścigów": (60, 20, 10, 150),
        "Pustynny Mistrz": (50, 18, 8, 120),
        "Górski Potwór": (55, 16, 12, 140),
        "Portowy As": (45, 15, 7, 90),
        "Szef Policji": (80, 21, 14, 200)
    }
    if name in stats:
        hp, speed, defense, exp = stats[name]
        if "Policjant" in name or "Policja" in name:
            return Police(name, hp, speed, defense, exp, badge_number=random.randint(100,999))
        return Rival(name, hp, speed, defense, exp)
    else:
        return Rival("Anonimowy Rywal", 20, 8, 2, 25)

class Boss(Rival):
    def __init__(self):
        super().__init__("Mistrz Wyścigów", 120, 22, 12, 500)

class SuperBoss(Rival):
    def __init__(self):
        super().__init__("Król Kierownicy", 200, 30, 16, 1000)

# ---------------------------------------
# SYSTEM SOJUSZNIKÓW
# ---------------------------------------
class Ally(Driver):
    def __init__(self, name, hp, speed, defense):
        super().__init__(name, hp, speed, defense)

def team_race(driver, allies, rival, weather=None):
    print(f"\n🤝 WYŚCIG DRUŻYNOWY: {driver.name} + zespół VS {rival.name}")
    while driver.is_alive() and rival.is_alive():
        input("ENTER by rozpocząć rundę...")
        participants = [driver] + allies
        for member in participants:
            if rival.is_alive():
                member.attack_rival(rival)
        if rival.is_alive():
            target = random.choice(participants)
            rival.attack_rival(target)
        if not driver.is_alive():
            print("Kierowca przegrał. Koniec gry.")
            sys.exit()
    print(f"{rival.name} pokonany!")
    driver.gain_exp(rival.exp_reward)
    driver.earn_gold(150)

# ---------------------------------------
# SYSTEM CRAFTINGU
# ---------------------------------------
class Recipe:
    def __init__(self, name, ingredients, result):
        self.name = name
        self.ingredients = ingredients
        self.result = result

def craft(driver, recipes):
    print("\n🔧 Dostępne przepisy:")
    for i, recipe in enumerate(recipes):
        print(f"{i+1}. {recipe.name} - części: {', '.join(recipe.ingredients)}")
    choice = input("Wybierz numer przepisu do stworzenia (ENTER by wyjść): ")
    if not choice.strip():
        return
    if choice.isdigit():
        index = int(choice) - 1
        if 0 <= index < len(recipes):
            recipe = recipes[index]
            inventory_names = [item.name for item in driver.inventory]
            if all(recipe.ingredients.count(ing) <= inventory_names.count(ing) for ing in recipe.ingredients):
                for ing in recipe.ingredients:
                    for item in driver.inventory:
                        if item.name == ing:
                            driver.inventory.remove(item)
                            break
                driver.inventory.append(recipe.result)
                print(f"Utworzono: {recipe.result.name}")
                log_event(driver, f"Stworzono {recipe.result.name} przez crafting.")
            else:
                print("Brakuje części!")
        else:
            print("Nieprawidłowy wybór.")
    else:
        print("Błąd formatu.")

def create_recipes():
    nitro = Item("Nitro", "Super przyspieszenie (+15 prędkości na wyścig)", lambda d: setattr(d, 'speed', d.speed + 15))
    all_season_tires = Item("Opony Całoroczne", "Przyczepność wzrasta na każdej trasie", weather_grip_plus)
    gps_pro = Item("GPS PRO", "Zawsze wybiera najlepszą trasę", fix_gps)
    license = Item("Międzynarodowe Prawo Jazdy", "Daje dostęp do nowych tras", license_boost)
    return [
        Recipe("Nitro", ["Turbo", "Kanister Paliwa"], nitro),
        Recipe("Super Opony", ["Opona Całoroczna", "Zestaw Naprawczy"], all_season_tires),
        Recipe("GPS PRO", ["GPS", "Turbo"], gps_pro),
        Recipe("Międzynarodowe Prawo Jazdy", ["Prawo Jazdy", "GPS"], license)
    ]

# ---------------------------------------
# SYSTEM EKWIPUNKU
# ---------------------------------------
class Equipment(Item):
    def __init__(self, name, description, slot, bonus_speed=0, bonus_defense=0, price=100):
        super().__init__(name, description, lambda d: None)
        self.slot = slot
        self.bonus_speed = bonus_speed
        self.bonus_defense = bonus_defense
        self.price = price

def create_equipment_items():
    return [
        Equipment("Silnik V8", "Mocny silnik (+10 prędkości)", "engine", bonus_speed=10, price=250),
        Equipment("Opony Sportowe", "Zwiększają przyczepność (+5 prędkości)", "tires", bonus_speed=5, price=120),
        Equipment("Wzmocniona Karoseria", "Zwiększa ochronę (+7 pancerza)", "body", bonus_defense=7, price=170),
        Equipment("System GPS", "Zawsze najszybsza trasa", "gps", bonus_speed=5, price=90),
        Equipment("System Nitro", "Mega przyspieszenie na wyścig", "nitro", bonus_speed=15, price=300)
    ]

def get_equipped_stats(driver):
    bonus_speed = driver.speed
    bonus_def = driver.defense
    for slot in driver.equipment:
        eq = driver.equipment[slot]
        if eq:
            bonus_speed += getattr(eq, "bonus_speed", 0)
            bonus_def += getattr(eq, "bonus_defense", 0)
    return bonus_speed, bonus_def

def equip_item(driver):
    parts = [item for item in driver.inventory if isinstance(item, Equipment)]
    if not parts:
        print("Nie masz części do zamontowania.")
        return
    print("\n🔧 Dostępne części do montażu:")
    for i, item in enumerate(parts):
        print(f"{i + 1}. {item.name} ({item.slot.upper()})")
    choice = input("Numer części do zamontowania: ")
    if choice.isdigit():
        index = int(choice) - 1
        if 0 <= index < len(parts):
            item = parts[index]
            driver.equipment[item.slot] = item
            print(f"{item.name} zamontowano w slocie {item.slot}.")
            log_event(driver, f"Zamontowano {item.name} ({item.slot})")
        else:
            print("Nieprawidłowy wybór.")
    else:
        print("Błędny format.")

# ---------------------------------------
# TALENTY KIEROWCY
# ---------------------------------------
class Talent:
    def __init__(self, name, description, effect):
        self.name = name
        self.description = description
        self.effect = effect

def quick_repair(driver):
    driver.hp = min(driver.max_hp, driver.hp + 50)
    print(f"{driver.name} używa zdolności: Ekspresowa Naprawa (+50 wytrzymałości)!")
    log_event(driver, "Ekspresowa Naprawa użyta.")

def focus_mode(driver):
    driver.speed += 10
    print(f"{driver.name} wchodzi w tryb skupienia! (+10 prędkości na wyścig)")
    log_event(driver, "Tryb Skupienia aktywowany.")

def rain_master(driver):
    driver.weather_effect = "przyczepność+"
    print("Jesteś mistrzem jazdy w deszczu! Deszcz nie przeszkadza.")
    log_event(driver, "Mistrz Deszczu aktywowany.")

def police_evader(driver):
    driver.defense += 7
    print("Jesteś mistrzem ucieczki przed policją! (+7 obrony)")
    log_event(driver, "Talent: Ucieczka przed policją.")

def create_talents():
    return [
        Talent("Ekspresowa Naprawa", "Natychmiastowo naprawia 50 wytrzymałości", quick_repair),
        Talent("Tryb Skupienia", "Zwiększa prędkość o 10 na jedną rundę", focus_mode),
        Talent("Mistrz Deszczu", "Zwiększa przyczepność w deszczu", rain_master),
        Talent("Ucieczka przed Policją", "Zwiększa obronę w pościgu", police_evader)
    ]

def use_talent(driver):
    if not driver.talents:
        print("Brak dostępnych talentów.")
        return
    print("\n🧠 Twoje umiejętności:")
    for i, t in enumerate(driver.talents):
        print(f"{i + 1}. {t.name} - {t.description}")
    choice = input("Wybierz talent do użycia: ")
    if choice.isdigit():
        index = int(choice) - 1
        if 0 <= index < len(driver.talents):
            talent = driver.talents[index]
            if talent.name in driver.used_talents:
                print("Ten talent już został użyty w tej walce.")
            else:
                talent.effect(driver)
                driver.used_talents.append(talent.name)
        else:
            print("Nieprawidłowy wybór.")
    else:
        print("Błąd formatu.")

def reset_talents(driver):
    driver.used_talents = []

# ---------------------------------------
# DZIENNIK KIEROWCY
# ---------------------------------------
def log_event(driver, text):
    entry = f"[{time.strftime('%H:%M:%S')}] {text}"
    driver.journal.append(entry)

def show_journal(driver):
    print("\n📘 Dziennik:")
    if not driver.journal:
        print("Brak zapisanych wydarzeń.")
    else:
        for line in driver.journal[-10:]:
            print(line)

# ---------------------------------------
# MINI-MAPA
# ---------------------------------------
def show_map(driver):
    print("\n🗺️ Mini-Mapa:")
    print(f"Obecna lokalizacja: {driver.position}")
    print("Legenda: Garaż, Tor, Autostrada, Warsztat, Rajd, Boss, Pustynia, Góry, Port, Centrum, Stacja, Salon, Arena")
    print("Odkrywaj kolejne miejsca i pokonuj rywali!")

# ---------------------------------------
# SYSTEM LOSOWYCH WYDARZEŃ
# ---------------------------------------
def random_event(driver):
    events = [
        "Spotykasz sponsora i dostajesz Zestaw Naprawczy.",
        "Wpadłeś w dziurę – auto traci 10 wytrzymałości!",
        "Odnajdujesz ukryty pakiet tuningowy – +100 EXP!",
        "Policja próbuje cię zatrzymać – walcz lub uciekaj!",
        "Pomagasz staruszce naprawić auto – otrzymujesz 50 kredytów.",
        "Kupujesz używaną oponę na bazarze.",
        "Nic się nie wydarzyło...",
        "Zostajesz zaproszony na wyścig uliczny – możesz zdobyć złoto!"
    ]
    choice = random.choice(events)
    print(f"🔮 Wydarzenie: {choice}")
    if "Zestaw Naprawczy" in choice:
        driver.inventory.append(Item("Zestaw Naprawczy", "Naprawia 20 punktów", repair_20))
    elif "dziurę" in choice:
        driver.hp = max(driver.hp - 10, 0)
    elif "pakiet" in choice:
        driver.gain_exp(100)
    elif "Policja" in choice:
        rival = generate_rival("Policjant Turbo")
        race(driver, rival, police_chase=True)
    elif "staruszce" in choice:
        driver.earn_gold(50)
    elif "oponę" in choice:
        driver.inventory.append(Item("Opona Używana", "Może się przydać do craftingu", lambda d: None))
    elif "wyścig uliczny" in choice:
        rival = generate_rival("Rywal Zawodowiec")
        if race(driver, rival):
            driver.earn_gold(120)
    # "Nic się nie wydarzyło..." - brak akcji

# ---------------------------------------
# TWORZENIE ROZBUDOWANEGO ŚWIATA
# ---------------------------------------
def build_full_world():
    # Lokacje
    garage = Location(
        "Garaż Startowy",
        "Twój domowy garaż, pełen części i narzędzi.",
        items=create_basic_items()
    )
    city_track = Location(
        "Miejski Tor",
        "Zakręcony tor miejski, tłum kibiców i silna konkurencja.",
        rivals=[generate_rival("Rywal Miejski")],
        weather=Weather()
    )
    highway = Location(
        "Autostrada",
        "Szeroka autostrada, idealna na wysokie prędkości.",
        rivals=[generate_rival("Policjant Turbo")],
        weather=Weather()
    )
    workshop = Location(
        "Warsztat",
        "Profesjonalny warsztat, gdzie możesz ulepszyć auto.",
        items=[Item("Super Turbo", "Zwiększa prędkość o 10 na wyścig", turbo_boost)],
        shop=Shop("Warsztatowy Sklep", create_equipment_items())
    )
    desert = Location(
        "Pustynia Driftu",
        "Gorąca pustynia, tylko najlepsi tu jeżdżą.",
        rivals=[generate_rival("Pustynny Mistrz")],
        weather=Weather()
    )
    mountains = Location(
        "Górski Szlak",
        "Strome podjazdy i serpentyny – prawdziwe wyzwanie.",
        rivals=[generate_rival("Górski Potwór")],
        weather=Weather()
    )
    port = Location(
        "Port Tuningowy",
        "Tutaj znajdziesz części z całego świata.",
        items=[Item("Japoński Spoiler", "Zwiększa prędkość na torze", lambda d: setattr(d, 'speed', d.speed + 3))],
        weather=Weather(),
        shop=Shop("Portowy Sklep", [
            Equipment("Turbosprężarka", "Turbo z importu (+8 prędkości)", "engine", bonus_speed=8, price=210),
            Equipment("Opony Drift", "Idealne na pustynię (+6 prędkości)", "tires", bonus_speed=6, price=140)
        ])
    )
    tuning_center = Location(
        "Centrum Tuningu",
        "Najlepsze miejsce do tuningu auta.",
        items=[Item("Lakier Chameleon", "Wyjątkowy wygląd!", lambda d: None)],
        weather=Weather(),
        shop=Shop("Centrum Tuningu", [
            Equipment("Karbonowa Mask", "Zmniejsza masę (+3 prędkości)", "body", bonus_speed=3, price=90),
            Equipment("Wydech Sportowy", "Dodaje stylu (+2 prędkości)", "engine", bonus_speed=2, price=60)
        ])
    )
    police_hq = Location(
        "Komenda Policji",
        "Tu rezyduje Szef Policji.",
        rivals=[generate_rival("Szef Policji")],
        weather=Weather()
    )
    boss_zone = Location(
        "Strefa Bossa",
        "Mityczne miejsce, gdzie spotkasz największego rywala.",
        rivals=[generate_rival("Boss Wyścigów")],
        weather=Weather()
    )
    arena = Location(
        "Arena Mistrzów",
        "Największy tor, gdzie czeka Mistrz Wyścigów.",
        rivals=[Boss()],
        weather=Weather()
    )
    super_boss_arena = Location(
        "Sala Króla Kierownicy",
        "Ostatnia arena! Tu staniesz przed Królem Kierownicy.",
        rivals=[SuperBoss()],
        weather=Weather()
    )
    car_dealer = Location(
        "Salon Samochodowy",
        "Możesz tu kupić nowe auta lub sprzedać stare części.",
        shop=Shop("Salon", [
            Equipment("Supersamochód", "Najwyższa klasa (+20 prędkości)", "engine", bonus_speed=20, price=900)
        ])
    )

    # Połączenia
    garage.connected = {"tor": city_track, "warsztat": workshop, "port": port, "centrum": tuning_center, "dealer": car_dealer}
    city_track.connected = {"garaż": garage, "autostrada": highway, "pustynia": desert}
    highway.connected = {"tor": city_track, "góry": mountains, "komenda": police_hq}
    workshop.connected = {"garaż": garage, "centrum": tuning_center}
    desert.connected = {"tor": city_track, "boss": boss_zone}
    boss_zone.connected = {"pustynia": desert, "arena": arena}
    arena.connected = {"boss": boss_zone, "superboss": super_boss_arena}
    super_boss_arena.connected = {"arena": arena}
    mountains.connected = {"autostrada": highway, "port": port}
    port.connected = {"góry": mountains, "garaż": garage}
    tuning_center.connected = {"warsztat": workshop, "garaż": garage}
    police_hq.connected = {"autostrada": highway}
    car_dealer.connected = {"garaż": garage}

    # Zadania
    def quest1_cond(driver):
        return driver.level >= 2

    def quest1_reward(driver):
        driver.inventory.append(Item("Wyścigowe Turbo", "Mega przyspieszenie!", turbo_boost))
        print("Otrzymano Wyścigowe Turbo!")

    garage.quest = Quest(
        "Pierwszy Wyścig",
        "Wygraj wyścig na Miejskim Torze i osiągnij poziom 2.",
        quest1_cond,
        quest1_reward
    )

    # NPC
    npc1 = NPC(
        "Stary Mechanik",
        ["Witaj w garażu młody!", "Tuning to klucz do sukcesu.", "Turbo to podstawa na torze."],
        quest=garage.quest
    )
    add_npc_to_location(garage, npc1)

    npc2 = NPC(
        "Portowy Sprzedawca",
        ["Części z Japonii, USA, Niemiec – co wybierasz?", "Mam coś specjalnego pod ladą."],
        shop=port.shop
    )
    add_npc_to_location(port, npc2)

    npc3 = NPC(
        "Mistrz Driftu",
        ["Pustynia to mój żywioł.", "Pokaż, na co cię stać w piasku!"],
        can_join=True
    )
    add_npc_to_location(desert, npc3)

    npc4 = NPC(
        "Policjant Janusz",
        ["Złamałeś przepisy?", "Dziś ci się upiekło..."],
        quest=Quest(
            "Policjantowa Przysługa",
            "Pomóż policjantowi naprawić radiowóz.",
            lambda d: any(i.name == "Zestaw Naprawczy" for i in d.inventory),
            lambda d: d.earn_gold(100)
        )
    )
    add_npc_to_location(police_hq, npc4)

    npc5 = NPC(
        "Stylista",
        ["Wygląd to połowa sukcesu na trasie!", "Przemaluję ci auto za 80 kredytów."],
        shop=tuning_center.shop
    )
    add_npc_to_location(tuning_center, npc5)

    return garage

# ---------------------------------------
# SYSTEM ZAKOŃCZEŃ
# ---------------------------------------
def grand_finale(driver):
    print("\n🎉 Gratulacje! Pokonałeś Króla Kierownicy i zostałeś legendą motoryzacji!")
    print("Twoje osiągnięcia:")
    print(f"- Poziom: {driver.level}")
    print(f"- EXP: {driver.exp}")
    print(f"- Liczba części w ekwipunku: {len(driver.inventory)}")
    print(f"- Liczba ukończonych zadań: {sum(1 for quest in completed_quests if quest)}")
    print(f"- Zespół: {', '.join(a.name for a in driver.team) if driver.team else 'Brak'}")
    if driver.level >= 20:
        print("\n🏆 Zakończenie: Król Kierownicy")
        print("Twój rekord nie zostanie pobity przez dekady!")
    elif driver.level >= 10:
        print("\n🏆 Zakończenie: Legendarny Kierowca")
        print("Twoje imię będzie wspominane przez dekady!")
    elif driver.level >= 6:
        print("\n🏆 Zakończenie: Mistrz Ulic")
        print("Zdobywasz szacunek na mieście.")
    else:
        print("\n🏆 Zakończenie: Początkujący Rajdowiec")
        print("Masz potencjał na więcej. Próbuj dalej!")
    print("\nDzięki za grę!")

# ---------------------------------------
# EKPLORACJA ŚWIATA
# ---------------------------------------
completed_quests = []
def explore(driver, location):
    recipes = create_recipes()
    ally_added = False
    ally = None

    driver.position = location.name
    log_event(driver, f"Odwiedzono: {location.name}")
    random_event(driver)

    while True:
        location.show_info()
        if location.npcs:
            print("NPC są dostępni.")
        if hasattr(location, 'ally') and not ally_added:
            print(f"Sojusznik {location.ally.name} dołącza do zespołu!")
            ally = location.ally
            ally_added = True

        print("\nCo chcesz zrobić?")
        print("1. Przeszukaj okolicę")
        print("2. Ścigaj się z rywalem")
        print("3. Jedź do innej lokalizacji")
        print("4. Ekwipunek")
        print("5. Użyj części")
        print("6. Statystyki")
        print("7. Rozmowa z NPC")
        print("8. Crafting")
        print("9. Użyj talentu")
        print("10. Załóż część")
        print("11. Pokaż mapę")
        print("12. Dziennik")
        print("13. Sklep (jeśli jest)")
        print("14. Zakończ grę")

        choice = input("Wybór: ")
        if choice == "1":
            if location.items:
                item = location.items.pop()
                driver.inventory.append(item)
                print(f"Znalazłeś: {item.name}!")
                log_event(driver, f"Znaleziono część: {item.name}")
            else:
                print("Nic nie znalazłeś.")
        elif choice == "2":
            if location.rivals:
                rival = location.rivals[0]
                print(f"🏎️ Wyścig z: {rival.name}")
                if isinstance(rival, (Boss, SuperBoss)):
                    if ally:
                        team_race(driver, [ally], rival, location.weather)
                    else:
                        race(driver, rival, location.weather)
                    if not rival.is_alive():
                        location.rivals.remove(rival)
                        grand_finale(driver)
                        sys.exit()
                else:
                    if ally:
                        team_race(driver, [ally], rival, location.weather)
                    else:
                        race(driver, rival, location.weather)
                    location.rivals.remove(rival)
            else:
                print("Brak rywali.")
        elif choice == "3":
            if location.connected:
                print("Dostępne trasy:")
                for key in location.connected:
                    print(f"- {key}")
                dest = input("Gdzie jedziesz? ").lower()
                if dest in location.connected:
                    return location.connected[dest]
                else:
                    print("Nieznana lokalizacja.")
            else:
                print("Brak przejazdów.")
        elif choice == "4":
            driver.show_inventory()
        elif choice == "5":
            part_name = input("Nazwa części: ")
            driver.use_item(part_name)
        elif choice == "6":
            s, d = get_equipped_stats(driver)
            print(f"{driver.name} - Poziom {driver.level} | Wytrzymałość: {driver.hp}/{driver.max_hp}")
            print(f"Prędkość: {s}, Obrona: {d}, EXP: {driver.exp}/{driver.level * 100}")
            print(f"Kredyty: {driver.gold}")
        elif choice == "7":
            interact_with_npc(location, driver)
        elif choice == "8":
            craft(driver, recipes)
        elif choice == "9":
            use_talent(driver)
        elif choice == "10":
            equip_item(driver)
        elif choice == "11":
            show_map(driver)
        elif choice == "12":
            show_journal(driver)
        elif choice == "13":
            if location.shop:
                location.shop.buy(driver)
            else:
                print("Brak sklepu w tej lokalizacji.")
        elif choice == "14":
            print("Koniec gry. Do zobaczenia na trasie!")
            sys.exit()
        else:
            print("Niepoprawny wybór.")

# ---------------------------------------
# START GRY
# ---------------------------------------
def start_game():
    print("===================================")
    print("      WITAJ W WYŚCIGOWYM RPG      ")
    print("===================================")
    name = input("Podaj imię kierowcy: ")
    driver = Driver(name, 100, 12, 3, inventory=create_basic_items())
    driver.talents = create_talents()
    current_location = build_full_world()

    print(f"\nWitaj, {driver.name}! Twoja samochodowa przygoda się zaczyna...\n")
    while True:
        current_location = explore(driver, current_location)

if __name__ == "__main__":
    start_game()
    # ---------------------------------------
# ZAKOŃCZENIE GRY I POŻEGNANIE
# ---------------------------------------

def grand_finale(driver):
    print("\n" + "="*40)
    print("🏁🏆 ZAKOŃCZENIE GRY 🏆🏁")
    print("="*40)
    print(f"\n{driver.name}, twoja przygoda na trasach dobiegła końca!\n")
    print("Osiągnięcia i statystyki:")
    print(f"  - Poziom końcowy: {driver.level}")
    print(f"  - Zebrane doświadczenie: {driver.exp}")
    print(f"  - Liczba części w ekwipunku: {len(driver.inventory)}")
    print(f"  - Liczba ukończonych zadań: {sum(1 for quest in completed_quests if quest)}")
    print(f"  - Zespół: {', '.join(a.name for a in driver.team) if driver.team else 'Brak'}")
    print(f"  - Zgromadzone kredyty: {driver.gold}")

    if driver.level >= 20:
        print("\n🏅 Tytuł: Król Kierownicy")
        print("Twój rekord przejdzie do historii światowych wyścigów!")
    elif driver.level >= 10:
        print("\n🏅 Tytuł: Legendarny Kierowca")
        print("Jesteś inspiracją dla przyszłych pokoleń kierowców.")
    elif driver.level >= 6:
        print("\n🏅 Tytuł: Mistrz Ulic")
        print("Ludzie na mieście mówią o twoich wyczynach.")
    else:
        print("\n🏅 Tytuł: Początkujący Rajdowiec")
        print("Wielka kariera jeszcze przed tobą!")

    if len(driver.inventory) > 15:
        print("🛠️ Kolekcjoner części – twój garaż pęka w szwach!")

    print("\nDziękujemy za udział w motoryzacyjnej przygodzie!")
    print("Stworzył: Vanpl33 i AI Copilot")
    print("Wersja gry: 1.0    Rok: 2025")
    print("\nZajrzyj ponownie, by odkryć nowe trasy, pojazdy i wyzwania!")
    print("="*40 + "\n")
    sys.exit()

# ZAMIANA DOTYCHCZASOWEGO check_ending NA grand_finale W MIEJSCACH WYWOŁANIA!