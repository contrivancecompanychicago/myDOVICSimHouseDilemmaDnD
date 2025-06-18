import datetime
import json
import os
import random

# --- Configuration ---
SAVE_FILE = 'shire_health_quest_save.json'

# --- Shire Calendar Class ---
class ShireCalendar:
    """Manages the Shire Reckoning calendar."""
    SHIRE_MONTHS = [
        "Afteryule", "Solmath", "Rethe", "Astron", "Thrimidge", "Forelithe",
        "Lithe", "Overlithe", "Afterlithe", "Halimath", "Winterfilth", "Blotmath", "Foreyule"
    ]
    SHIRE_DAYS = [
        "Sunday", "Monday", "Trewsday", "Wedsday", "Thursday", "Freesday", "Saturday"
    ] # Note: Shire calendar days are slightly different, but we'll map to Gregorian for simplicity here

    def get_shire_date(self, gregorian_date):
        """Converts a Gregorian date to a simplified Shire date."""
        # This is a very simplified mapping. A full Shire calendar conversion is complex.
        # We'll just map the month and day of the week, and use the Gregorian day number.
        month_index = (gregorian_date.month - 1) % len(self.SHIRE_MONTHS)
        shire_month = self.SHIRE_MONTHS[month_index]
        shire_day_of_week = self.SHIRE_DAYS[gregorian_date.weekday()]
        return f"{gregorian_date.day} {shire_month}, {shire_day_of_week}"

# --- Player Class ---
class Player:
    """Represents the player's health stats and gamified progress."""
    def __init__(self, name="Adventurer"):
        self.name = name
        self.weight = 0.0
        self.blood_pressure = "0/0"
        self.eating_habits = ""
        self.shire_pennies = 0
        self.hobbit_points = 0
        self.achievements = []
        self.daily_deeds_completed = {} # Tracks today's deeds
        self.current_favors = {} # Tracks progress for character favors/challenges

    def add_sp(self, amount):
        self.shire_pennies += amount
        print(f"💰 You gained {amount} Shire Pennies! Total: {self.shire_pennies} SP")

    def add_hp(self, amount):
        old_hp = self.hobbit_points
        self.hobbit_points += amount
        print(f"✨ You gained {amount} Hobbit-Points! Total: {self.hobbit_points} HP")
        self._check_shire_status(old_hp)

    def add_achievement(self, achievement_name):
        if achievement_name not in self.achievements:
            self.achievements.append(achievement_name)
            print(f"\n🏆 Achievement Unlocked: {achievement_name}!")

    def _check_shire_status(self, old_hp):
        levels = {
            0: "Apprentice Gardener",
            251: "Green-hand Farmer",
            501: "Stout-hearted Traveller",
            1001: "Master of the Market",
            2001: "Elder of the Shire"
        }
        current_status = "Unknown"
        for threshold, status in sorted(levels.items()):
            if self.hobbit_points >= threshold:
                current_status = status
            if old_hp < threshold <= self.hobbit_points:
                print(f"\n🌟 Congratulations! You've advanced to Shire Status: {status}!")
        print(f"Current Shire Status: {current_status}")

    def to_dict(self):
        return {
            'name': self.name,
            'weight': self.weight,
            'blood_pressure': self.blood_pressure,
            'eating_habits': self.eating_habits,
            'shire_pennies': self.shire_pennies,
            'hobbit_points': self.hobbit_points,
            'achievements': self.achievements,
            'daily_deeds_completed': self.daily_deeds_completed,
            'current_favors': self.current_favors
        }

    @classmethod
    def from_dict(cls, data):
        player = cls(data['name'])
        player.weight = data.get('weight', 0.0)
        player.blood_pressure = data.get('blood_pressure', "0/0")
        player.eating_habits = data.get('eating_habits', "")
        player.shire_pennies = data.get('shire_pennies', 0)
        player.hobbit_points = data.get('hobbit_points', 0)
        player.achievements = data.get('achievements', [])
        player.daily_deeds_completed = data.get('daily_deeds_completed', {})
        player.current_favors = data.get('current_favors', {})
        return player

# --- Character Classes (NPCs) ---
class Character:
    """Base class for D&D module characters."""
    def __init__(self, name, description):
        self.name = name
        self.description = description

    def introduce(self):
        print(f"\n--- {self.name}: {self.description} ---")

class DaProvider(Character):
    def __init__(self):
        super().__init__(
            "Da Provider",
            "A new villager from Krebsville (Realistic Chicago), offering 'Krebsville Connections' for athleisure and healthy living, but always with a twist."
        )
        self.favors_offered = {
            "Smoothie Bar Blueprint": {
                "description": "Unlock a secret, power-packed smoothie recipe. Requires completing 'Fruit Orchard Harvest' (2 fruit) and 'Vegetable Patch Platter' (3 veggies) for 3 consecutive days.",
                "hp_reward": 25,
                "achievement": "Smoothie Bar Blueprint Unlocked",
                "check_func": self.check_smoothie_blueprint_favor
            },
            "Pop-Up Power-Walk Protocol": {
                "description": "Get a special 'Krebsville power-walk route'. Requires 'Water from the Well' (8 glasses water) and 'Vegetable Patch Platter' (3 veggies) for 2 consecutive days.",
                "hp_reward": 30,
                "achievement": "Pop-Up Power-Walk Protocol Mastered",
                "check_func": self.check_power_walk_favor
            }
        }

    def offer_favor(self, player, favor_name):
        if favor_name not in self.favors_offered:
            print(f"{self.name} doesn't offer that favor.")
            return

        favor_details = self.favors_offered[favor_name]
        print(f"\nDa Provider's Offer: {favor_name}")
        print(f"  {favor_details['description']}")
        print(f"  Complete this to earn {favor_details['hp_reward']} HP and the '{favor_details['achievement']}' achievement.")

        player.current_favors['Da Provider'] = {"favor_name": favor_name, "start_date": datetime.date.today().isoformat(), "progress": {}}
        print("You've accepted Da Provider's favor! Begin tracking your progress.")

    def check_favor_completion(self, player):
        if 'Da Provider' in player.current_favors:
            favor_data = player.current_favors['Da Provider']
            favor_name = favor_data["favor_name"]
            favor_details = self.favors_offered.get(favor_name)
            if not favor_details:
                return False # Favor not found

            if favor_details["check_func"](player, favor_data):
                print(f"\n--- Da Provider's Scene: Krebsville Connection ---")
                print("As your adventuring party passes by a bustling crossroads, you spot Da Provider, clad in surprisingly stylish (yet practical) gear, haggling over some exotic herbs with a local farmer. He spots you, offers a quick, knowing nod, and signals you closer.")
                print(f"\"Aye, a fine day for a bit o' trade, eh?\" he murmurs, his eyes assessing your party. \"Heard you folk are lookin' for ways to keep nimble and fueled on your journey. I got connections back in Krebsville... top-tier stuff. But not for free, mind you. I need to see yer commitment.\"")
                print(f"\n\"Aye, I see the glow of well-fed folk about ye,\" Da Provider says, a rare smile playing on his lips. He hands you a rolled-up parchment. \"Here's the '{favor_name}' I promised. It'll get ya what you need, quick and potent. Just know, some of those big-city ingredients take a bit more huntin' than your Shire greens.\"")
                player.add_hp(favor_details["hp_reward"])
                player.add_achievement(favor_details["achievement"])
                del player.current_favors['Da Provider'] # Favor completed
                # In-game D&D reward: Temporary +1 stat bonus to Dex or Con
                print("\n**In-Game D&D Reward:** Your party gains a new Consumable Item: 'Krebsville Power Smoothie Recipe'. When used, this recipe can grant a temporary +1 bonus to a chosen stat (e.g., Dexterity or Constitution) for the next D&D session, reflecting your improved vitality.")
                return True
        return False

    def check_smoothie_blueprint_favor(self, player, favor_data):
        today = datetime.date.today()
        start_date = datetime.date.fromisoformat(favor_data['start_date'])
        
        # Check consecutive days for fruit and veggie
        consecutive_days = 0
        for i in range(3): # Need 3 consecutive days
            check_date = today - datetime.timedelta(days=i)
            date_str = check_date.isoformat()
            if date_str >= start_date.isoformat(): # Only check from start date
                fruit_done = player.daily_deeds_completed.get(date_str, {}).get("Fruit Orchard Harvest", False)
                veggie_done = player.daily_deeds_completed.get(date_str, {}).get("Vegetable Patch Platter", False)
                if fruit_done and veggie_done:
                    consecutive_days += 1
                else:
                    consecutive_days = 0 # Break streak if any day fails
            else: # If we go before start_date, stop checking
                break

        return consecutive_days >= 3 # True if 3 consecutive days are met

    def check_power_walk_favor(self, player, favor_data):
        today = datetime.date.today()
        start_date = datetime.date.fromisoformat(favor_data['start_date'])
        
        consecutive_days = 0
        for i in range(2): # Need 2 consecutive days
            check_date = today - datetime.timedelta(days=i)
            date_str = check_date.isoformat()
            if date_str >= start_date.isoformat():
                water_done = player.daily_deeds_completed.get(date_str, {}).get("Water from the Well", False)
                veggie_done = player.daily_deeds_completed.get(date_str, {}).get("Vegetable Patch Platter", False)
                if water_done and veggie_done:
                    consecutive_days += 1
                else:
                    consecutive_days = 0
            else:
                break
        return consecutive_days >= 2


class DaStruggler(Character):
    def __init__(self):
        super().__init__(
            "Da Struggler",
            "Embodies the burdens of everyday life – lack of time, financial constraints, stress, exhaustion – that hinder healthy habits."
        )
        self.dilemmas_offered = {
            "Stress Snacker": {
                "description": "When feeling stressed, successfully complete 'Peaceful Pipeweed Moment' (10 mins mindfulness) AND avoid any unplanned unhealthy snacks.",
                "hp_reward": 25,
                "achievement": "Calm Hearth",
                "check_func": self.check_stress_snacker
            },
            # Add other dilemmas as needed
        }

    def present_dilemma(self, player, dilemma_name):
        if dilemma_name not in self.dilemmas_offered:
            print(f"{self.name} doesn't present that dilemma.")
            return

        dilemma_details = self.dilemmas_offered[dilemma_name]
        print(f"\nDa Struggler's Dilemma: {dilemma_name}")
        print(f"  {dilemma_details['description']}")
        print(f"  Overcoming this earns {dilemma_details['hp_reward']} HP and the '{dilemma_details['achievement']}' achievement.")
        player.current_favors['Da Struggler'] = {"dilemma_name": dilemma_name, "active": True}
        print("You've acknowledged Da Struggler's dilemma. Be ready to face it!")

    def check_dilemma_completion(self, player):
        if 'Da Struggler' in player.current_favors:
            dilemma_data = player.current_favors['Da Struggler']
            dilemma_name = dilemma_data["dilemma_name"]
            dilemma_details = self.dilemmas_offered.get(dilemma_name)
            if not dilemma_details or not dilemma_data.get("active"):
                return False

            if dilemma_details["check_func"](player):
                print(f"\n--- Da Struggler's Scene: Whispers of Weariness ---")
                print("As your party prepares for a short rest by a roadside, you hear a weary sigh from a nearby, slightly disheveled figure. It's Da Struggler, slumped against a tree, looking utterly drained. 'Ach, another day, another dozen troubles,' they mutter, pulling out a half-eaten, greasy-looking sausage roll from a crumpled wrapper. 'Just need somethin' to get through it, you know? Never any peace. Never any easy way.' Their words echo a familiar inner sentiment.")
                print(f"\nYou take a calm breath, unaffected by Da Struggler's indulgence. You might choose to offer them a piece of your own trail mix or simply offer a sympathetic, knowing nod. Da Struggler looks up, surprised by your composure. 'How do you do it?' they ask, genuinely curious. 'You just... find a way, don't you? Maybe there *is* another path.'")
                player.add_hp(dilemma_details["hp_reward"])
                player.add_achievement(dilemma_details["achievement"])
                del player.current_favors['Da Struggler'] # Dilemma overcome
                # In-game D&D reward: +1 Inspiration Point
                print("\n**In-Game D&D Reward:** Your party gains +1 Inspiration Point, reflecting your internal fortitude influencing the party's morale.")
                return True
        return False

    def check_stress_snacker(self, player):
        # This is harder to automate perfectly without a sophisticated mood tracker.
        # For the script, we'll ask the player if they faced and overcame it TODAY.
        today_str = datetime.date.today().isoformat()
        if player.daily_deeds_completed.get(today_str, {}).get("Peaceful Pipeweed Moment", False) and \
           player.daily_deeds_completed.get(today_str, {}).get("Avoid Unplanned Unhealthy Snacks", False):
            # This is where you might ask the player:
            # "Did you feel stressed today and still manage to do your Peaceful Pipeweed Moment and avoid unplanned unhealthy snacks? (y/n)"
            # For automation, we'll assume the deeds being done implies success if the dilemma is active.
            return True
        return False

class REX(Character):
    def __init__(self):
        super().__init__(
            "REX",
            "The spirit of unfiltered energy and impulse. REX embodies sudden urges – sometimes productive, sometimes disruptive."
        )
        self.impulses_offered = {
            "Rebellious Refusal": {
                "description": "Despite a strong urge to skip a planned healthy meal or exercise, successfully complete it.",
                "hp_reward": 30,
                "achievement": "Iron Will of the Shire",
                "check_func": self.check_rebellious_refusal
            },
            # Add other impulses as needed
        }

    def present_impulse(self, player, impulse_name):
        if impulse_name not in self.impulses_offered:
            print(f"{self.name} doesn't present that impulse.")
            return
        
        impulse_details = self.impulses_offered[impulse_name]
        print(f"\nREX's Impulse: {impulse_name}")
        print(f"  {impulse_details['description']}")
        print(f"  Overcoming this earns {impulse_details['hp_reward']} HP and the '{impulse_details['achievement']}' achievement.")
        player.current_favors['REX'] = {"impulse_name": impulse_name, "active": True}
        print("You've acknowledged REX's impulse. Be prepared to stand firm!")


    def check_impulse_completion(self, player):
        if 'REX' in player.current_favors:
            impulse_data = player.current_favors['REX']
            impulse_name = impulse_data["impulse_name"]
            impulse_details = self.impulses_offered.get(impulse_name)
            if not impulse_details or not impulse_data.get("active"):
                return False
            
            if impulse_details["check_func"](player):
                print(f"\n--- REX's Scene: Sudden Sprint or Steady Strides? ---")
                print("As your party crosses an open field, a sudden, inexplicable surge of energy hits you. You feel an overwhelming urge to just *run*, to leap, to do something wild and unrestrained. You glance over and see REX, who was previously calm, suddenly darting around, chasing butterflies with a boundless, almost reckless abandon. Their chaotic energy is contagious, whispering to your own impulses: 'Just let go! Go, go, GO!'")
                print(f"\nYou take a deep breath, acknowledge the surge of energy, but consciously choose to channel it. Perhaps you maintain a steady, powerful pace on your 'Stroll to Bywater' rather than a chaotic sprint, or you put that energy into meticulously preparing your healthy dinner.")
                player.add_hp(impulse_details["hp_reward"])
                player.add_achievement(impulse_details["achievement"])
                del player.current_favors['REX'] # Impulse overcome
                # In-game D&D reward: Advantage on next physical skill check
                print("\n**In-Game D&D Reward:** Your character gains Advantage on their next physical (Strength or Dexterity) skill check during the D&D session, reflecting your newfound control over your physical urges.")
                return True
        return False

    def check_rebellious_refusal(self, player):
        # This requires the player to confirm they pushed through a specific planned activity.
        # For script automation, we'll need to ask directly if they faced and overcame it.
        # Example check:
        today_str = datetime.date.today().isoformat()
        # This check is illustrative. In reality, you'd need confirmation from the user
        # that a *specific* planned meal/exercise was performed *despite* rebellion.
        # For simplicity, we'll assume if they log their daily deed and this impulse is active,
        # they faced it.
        if player.daily_deeds_completed.get(today_str, {}).get("Dinner at the Green Dragon (Healthy Edition)", False) or \
           player.daily_deeds_completed.get(today_str, {}).get("A Stroll to Bywater", False):
            # To make this truly robust, you'd need a way for the user to report *when* they felt the impulse
            # and what they did. For now, assume if the deed is logged, it counts towards overcoming.
            return True
        return False

# --- Game Class ---
class Game:
    def __init__(self):
        self.player = Player()
        self.shire_calendar = ShireCalendar()
        self.characters = {
            "Da Provider": DaProvider(),
            "Da Struggler": DaStruggler(),
            "REX": REX()
        }
        self.today = datetime.date.today()
        self.load_game()

        self.daily_deeds_list = {
            "Food Focus": [
                "Hobbit's Healthy Breakfast", "Second Breakfast of Sensibility", "No Elevenses Extra",
                "Lembas-Like Lunch", "Dinner at the Green Dragon (Healthy Edition)", "Water from the Well",
                "Vegetable Patch Platter", "Fruit Orchard Harvest"
            ],
            "Movement & Activity": [
                "A Stroll to Bywater", "Bag End Bending & Stretching"
            ],
            "Blood Pressure Management": [
                "Peaceful Pipeweed Moment", "Salt-Wise Supper", "Sleep in a Cozy Smial"
            ]
        }
        self.daily_deed_points = {
            "Hobbit's Healthy Breakfast": 5,
            "Second Breakfast of Sensibility": 10,
            "No Elevenses Extra": 5,
            "Lembas-Like Lunch": 15,
            "Dinner at the Green Dragon (Healthy Edition)": 20,
            "Water from the Well": 10,
            "Vegetable Patch Platter": 10,
            "Fruit Orchard Harvest": 5,
            "A Stroll to Bywater": 20,
            "Bag End Bending & Stretching": 5,
            "Peaceful Pipeweed Moment": 15,
            "Salt-Wise Supper": 10,
            "Sleep in a Cozy Smial": 15
        }

    def save_game(self):
        with open(SAVE_FILE, 'w') as f:
            json.dump(self.player.to_dict(), f, indent=4)
        print("Game saved!")

    def load_game(self):
        if os.path.exists(SAVE_FILE):
            with open(SAVE_FILE, 'r') as f:
                data = json.load(f)
                self.player = Player.from_dict(data)
            print("Game loaded!")
        else:
            print("No save file found. Starting new game.")
            self.setup_new_game()

    def setup_new_game(self):
        print("\n--- Welcome to Your Shire's Health Quest! ---")
        player_name = input("What is your Hobbit's name? (e.g., Bilbo, Frodo): ")
        self.player.name = player_name
        self.player.weight = float(input("Enter your current weight (lbs): "))
        self.player.blood_pressure = input("Enter your current blood pressure (e.g., 120/80 mmHg): ")
        self.player.eating_habits = input("Briefly describe your current eating habits: ")
        print("\nYour Shire adventure begins!")
        self.save_game()

    def display_status(self):
        print("\n--- Your Shire Status ---")
        print(f"Hobbit Name: {self.player.name}")
        print(f"Current Weight: {self.player.weight} lbs")
        print(f"Blood Pressure: {self.player.blood_pressure}")
        print(f"Eating Habits: {self.player.eating_habits}")
        print(f"Shire Pennies: {self.player.shire_pennies} SP")
        print(f"Hobbit-Points: {self.player.hobbit_points} HP")
        self.player._check_shire_status(self.player.hobbit_points) # Re-check and print current status
        print(f"Achievements: {', '.join(self.player.achievements) if self.player.achievements else 'None'}")
        
        if self.player.current_favors:
            print("\n--- Active Quests/Favors ---")
            for char_name, favor_data in self.player.current_favors.items():
                if char_name == "Da Provider":
                    print(f"  Da Provider: {favor_data['favor_name']} - Started {favor_data['start_date']}")
                elif char_name == "Da Struggler":
                    print(f"  Da Struggler: {favor_data['dilemma_name']} - Active")
                elif char_name == "REX":
                    print(f"  REX: {favor_data['impulse_name']} - Active")

    def log_daily_deeds(self):
        print(f"\n--- Log Your Daily Deeds for {self.shire_calendar.get_shire_date(self.today)} ---")
        today_str = self.today.isoformat()
        if today_str not in self.player.daily_deeds_completed:
            self.player.daily_deeds_completed[today_str] = {}

        for category, deeds in self.daily_deeds_list.items():
            print(f"\n** {category} **")
            for i, deed in enumerate(deeds):
                done = self.player.daily_deeds_completed[today_str].get(deed, False)
                status_char = 'X' if done else ' '
                print(f"{i+1}. [{status_char}] {deed} (+{self.daily_deed_points[deed]} SP)")

            while True:
                choices = input("Enter numbers of completed deeds (e.g., 1 3 5), 'all' for category, 'done' to finish, or 'cancel': ").lower().strip()
                if choices == 'done':
                    break
                if choices == 'cancel':
                    return # Exit without saving for this category
                
                selected_deeds = []
                if choices == 'all':
                    selected_deeds = deeds
                else:
                    try:
                        indices = [int(x) - 1 for x in choices.split()]
                        selected_deeds = [deeds[i] for i in indices if 0 <= i < len(deeds)]
                    except ValueError:
                        print("Invalid input. Please enter numbers, 'all', 'done', or 'cancel'.")
                        continue

                for deed_name in selected_deeds:
                    if not self.player.daily_deeds_completed[today_str].get(deed_name):
                        self.player.add_sp(self.daily_deed_points[deed_name])
                        self.player.daily_deeds_completed[today_str][deed_name] = True
                
                # Update display after logging
                for i, deed in enumerate(deeds):
                    done = self.player.daily_deeds_completed[today_str].get(deed, False)
                    status_char = 'X' if done else ' '
                    print(f"{i+1}. [{status_char}] {deed} (+{self.daily_deed_points[deed]} SP)")

        print("\nDaily deeds logged!")
        self.save_game()

    def check_weekly_bounties(self):
        # This would require more complex logic to track weekly progress
        # For simplicity, let's make it a manual check for now, or add specific tracking for each bounty.
        print("\n--- Check Weekly Bounties ---")
        print("This feature requires manual tracking for now. Remember to check if you completed:")
        print("  - The Farmer's Market Haul (+50 HP)")
        print("  - Beyond the Borders Journey (+75 HP)")
        print("  - Master of Provisions (+25 HP)")
        print("  - The Clear Stream Challenge (+50 HP)")
        print("  - The Quiet Meadow (+25 HP)")
        
        bounty_choice = input("Did you complete any weekly bounties? (e.g., 'Farmer', 'Borders', 'None'): ").lower()
        if 'farmer' in bounty_choice:
            self.player.add_hp(50)
            self.player.add_achievement("The Farmer's Market Haul Completed")
        if 'borders' in bounty_choice:
            self.player.add_hp(75)
            self.player.add_achievement("Beyond the Borders Journey Completed")
        # Add more checks as needed

    def interact_with_characters(self):
        print("\n--- Interact with Shire Residents ---")
        for char_name, char_obj in self.characters.items():
            print(f"[{char_name}] - {char_obj.description}")
        
        while True:
            choice = input("Who would you like to interact with? (Da Provider, Da Struggler, REX, or 'done'): ").lower()
            if choice == 'done':
                break
            
            if choice == 'da provider':
                char = self.characters["Da Provider"]
                char.introduce()
                if 'Da Provider' not in self.player.current_favors:
                    print("Da Provider has the following favors:")
                    for f_name, f_details in char.favors_offered.items():
                        print(f"- {f_name}: {f_details['description']}")
                    favor_choice = input("Which favor would you like to attempt? (e.g., 'Smoothie Bar Blueprint'): ")
                    char.offer_favor(self.player, favor_choice)
                else:
                    print("You already have an active favor with Da Provider.")
                
            elif choice == 'da struggler':
                char = self.characters["Da Struggler"]
                char.introduce()
                if 'Da Struggler' not in self.player.current_favors:
                    print("Da Struggler presents the following dilemmas:")
                    for d_name, d_details in char.dilemmas_offered.items():
                        print(f"- {d_name}: {d_details['description']}")
                    dilemma_choice = input("Which dilemma would you like to acknowledge and face? (e.g., 'Stress Snacker'): ")
                    char.present_dilemma(self.player, dilemma_choice)
                else:
                    print("You already have an active dilemma with Da Struggler.")

            elif choice == 'rex':
                char = self.characters["REX"]
                char.introduce()
                if 'REX' not in self.player.current_favors:
                    print("REX presents the following impulses:")
                    for i_name, i_details in char.impulses_offered.items():
                        print(f"- {i_name}: {i_details['description']}")
                    impulse_choice = input("Which impulse would you like to acknowledge and prepare to overcome? (e.g., 'Rebellious Refusal'): ")
                    char.present_impulse(self.player, impulse_choice)
                else:
                    print("You already have an active impulse with REX.")
            else:
                print("Invalid character. Please choose from 'Da Provider', 'Da Struggler', 'REX', or 'done'.")
            
            self.save_game()


    def check_character_scenes(self):
        # This function is called at the start of each new day to check for scene triggers
        triggered_scenes = []
        for char_name, char_obj in self.characters.items():
            if char_name == "Da Provider" and char_obj.check_favor_completion(self.player):
                triggered_scenes.append(char_name)
            elif char_name == "Da Struggler" and char_obj.check_dilemma_completion(self.player):
                 triggered_scenes.append(char_name)
            elif char_name == "REX" and char_obj.check_impulse_completion(self.player):
                 triggered_scenes.append(char_name)
        return triggered_scenes


    def run_daily_cycle(self):
        print(f"\n--- It's {self.shire_calendar.get_shire_date(self.today)} in the Shire! ---")

        # Check for completed character scenes/quests from previous day's actions
        self.check_character_scenes()

        while True:
            print("\n--- Daily Actions ---")
            print("1. Log Daily Deeds")
            print("2. Check Weekly Bounties (Manual)")
            print("3. Interact with Shire Residents")
            print("4. Display Your Shire Status")
            print("5. Advance to Next Day")
            print("6. Save & Exit")

            choice = input("What would you like to do? Enter number: ")

            if choice == '1':
                self.log_daily_deeds()
            elif choice == '2':
                self.check_weekly_bounties()
            elif choice == '3':
                self.interact_with_characters()
            elif choice == '4':
                self.display_status()
            elif choice == '5':
                self.today += datetime.timedelta(days=1)
                self.player.daily_deeds_completed = {} # Reset daily deeds for new day
                print("\n--- A new day dawns in the Shire! ---")
                self.save_game()
                # Check for active favor progress (e.g., consecutive days)
                self.check_character_scenes() # Check again for any passive completions
                print(f"\nIt's now {self.shire_calendar.get_shire_date(self.today)}.")
            elif choice == '6':
                self.save_game()
                print("Farewell, brave Hobbit! Until next time.")
                break
            else:
                print("Invalid choice. Please enter a number between 1 and 6.")

# --- Main Game Loop ---
if __name__ == "__main__":
    game = Game()
    game.run_daily_cycle()
