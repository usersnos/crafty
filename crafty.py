import asyncio
import logging
import random
import json
import os
import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from collections import defaultdict

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

# ===================== НАСТРОЙКИ =====================
TOKEN = "8577885014:AAFOGotQn1-0KTReh6bfeOUpeXkiAyTtvyc"  # Замени на свой!
ADMIN_ID = 8174410809
VERSION = "2.0.0"

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

# ===================== ДАННЫЕ ИГРОКОВ =====================
players: Dict[int, 'Player'] = {}

# ===================== ПРЕДМЕТЫ =====================
class ItemType(Enum):
    MATERIAL = "material"
    WEAPON = "weapon"
    ARMOR = "armor"
    FOOD = "food"
    TOOL = "tool"
    POTION = "potion"
    SPECIAL = "special"

@dataclass
class Item:
    id: str
    name: str
    emoji: str
    type: ItemType
    description: str = ""
    damage: int = 0
    defense: int = 0
    heal_amount: int = 0
    durability: int = -1
    stackable: bool = True
    max_stack: int = 64
    rarity: str = "common"
    craftable: bool = True
    level_required: int = 1

ITEMS: Dict[str, Item] = {}

def register_items():
    # ===== МАТЕРИАЛЫ =====
    ITEMS["wood"] = Item("wood", "Древесина", "🪵", ItemType.MATERIAL, "Обычная древесина", rarity="common")
    ITEMS["stick"] = Item("stick", "Палка", "🦯", ItemType.MATERIAL, "Простая палка", stackable=True, max_stack=16, rarity="common")
    ITEMS["cobblestone"] = Item("cobblestone", "Булыжник", "🪨", ItemType.MATERIAL, "Обычный булыжник", rarity="common")
    ITEMS["iron_ore"] = Item("iron_ore", "Железная руда", "⛏️", ItemType.MATERIAL, "Требуется переплавка", rarity="common")
    ITEMS["iron_ingot"] = Item("iron_ingot", "Железный слиток", "🔩", ItemType.MATERIAL, "Выплавлено из руды", rarity="common")
    ITEMS["gold_ore"] = Item("gold_ore", "Золотая руда", "✨", ItemType.MATERIAL, "Редкая руда", rarity="rare")
    ITEMS["gold_ingot"] = Item("gold_ingot", "Золотой слиток", "🪙", ItemType.MATERIAL, "Блестит!", rarity="rare")
    ITEMS["diamond"] = Item("diamond", "Алмаз", "💎", ItemType.MATERIAL, "Самый прочный материал", rarity="epic")
    ITEMS["string"] = Item("string", "Нить", "🧵", ItemType.MATERIAL, "Из пауков", rarity="common")
    ITEMS["leather"] = Item("leather", "Кожа", "🧶", ItemType.MATERIAL, "Из коров", rarity="common")
    ITEMS["coal"] = Item("coal", "Уголь", "⬛", ItemType.MATERIAL, "Топливо", rarity="common")
    
    # Незер материалы
    ITEMS["netherrack"] = Item("netherrack", "Адский камень", "🔥", ItemType.MATERIAL, "Горит вечно", rarity="rare")
    ITEMS["soul_sand"] = Item("soul_sand", "Песок душ", "👻", ItemType.MATERIAL, "Замедляет", rarity="rare")
    ITEMS["glowstone"] = Item("glowstone", "Светокамень", "✨", ItemType.MATERIAL, "Ярко светит", rarity="rare")
    ITEMS["nether_wart"] = Item("nether_wart", "Адский нарост", "🌿", ItemType.MATERIAL, "Для зелий", rarity="rare")
    ITEMS["blaze_rod"] = Item("blaze_rod", "Огненный стержень", "🔥", ItemType.MATERIAL, "Из ифрита", rarity="epic")
    ITEMS["blaze_powder"] = Item("blaze_powder", "Огненный порошок", "⚡", ItemType.MATERIAL, "Из стержней", rarity="epic")
    ITEMS["ender_pearl"] = Item("ender_pearl", "Жемчуг Края", "👁️", ItemType.MATERIAL, "Телепорт", rarity="epic")
    ITEMS["ancient_debris"] = Item("ancient_debris", "Древний обломок", "🏺", ItemType.MATERIAL, "Редчайший материал", rarity="legendary")
    ITEMS["netherite_scrap"] = Item("netherite_scrap", "Незерит-ломик", "🔨", ItemType.MATERIAL, "Переплавленный обломок", rarity="legendary")
    ITEMS["netherite_ingot"] = Item("netherite_ingot", "Незеритовый слиток", "💠", ItemType.MATERIAL, "Сплав древних обломков", rarity="legendary")
    
    # ЕДА
    ITEMS["apple"] = Item("apple", "Яблоко", "🍎", ItemType.FOOD, "Восстанавливает 4 HP", heal_amount=4, rarity="common")
    ITEMS["bread"] = Item("bread", "Хлеб", "🍞", ItemType.FOOD, "Восстанавливает 5 HP", heal_amount=5, rarity="common")
    ITEMS["meat"] = Item("meat", "Мясо", "🥩", ItemType.FOOD, "Восстанавливает 8 HP", heal_amount=8, rarity="common")
    ITEMS["golden_apple"] = Item("golden_apple", "Золотое яблоко", "🍎✨", ItemType.FOOD, "Восстанавливает 10 HP", heal_amount=10, rarity="rare")
    
    # ОРУЖИЕ
    ITEMS["wood_sword"] = Item("wood_sword", "Деревянный меч", "🗡️", ItemType.WEAPON, "Наносит 4 урона", damage=4, stackable=False, rarity="common")
    ITEMS["stone_sword"] = Item("stone_sword", "Каменный меч", "⚔️", ItemType.WEAPON, "Наносит 6 урона", damage=6, stackable=False, rarity="common")
    ITEMS["iron_sword"] = Item("iron_sword", "Железный меч", "🔪", ItemType.WEAPON, "Наносит 8 урона", damage=8, stackable=False, rarity="common")
    ITEMS["diamond_sword"] = Item("diamond_sword", "Алмазный меч", "⚔️💎", ItemType.WEAPON, "Наносит 10 урона", damage=10, stackable=False, rarity="epic")
    ITEMS["netherite_sword"] = Item("netherite_sword", "Незеритовый меч", "⚔️💠", ItemType.WEAPON, "Наносит 14 урона", damage=14, stackable=False, rarity="legendary")
    
    # ИНСТРУМЕНТЫ
    ITEMS["wood_pickaxe"] = Item("wood_pickaxe", "Деревянная кирка", "⛏️", ItemType.TOOL, "Копает камень", stackable=False, rarity="common")
    ITEMS["stone_pickaxe"] = Item("stone_pickaxe", "Каменная кирка", "⛏️", ItemType.TOOL, "Копает железо", stackable=False, rarity="common")
    ITEMS["iron_pickaxe"] = Item("iron_pickaxe", "Железная кирка", "⛏️", ItemType.TOOL, "Копает алмазы", stackable=False, rarity="common")
    ITEMS["diamond_pickaxe"] = Item("diamond_pickaxe", "Алмазная кирка", "⛏️💎", ItemType.TOOL, "Копает всё", stackable=False, rarity="epic")
    
    # БРОНЯ (только незеритовая для краткости, но можешь добавить всю)
# ===== КОЖАНАЯ БРОНЯ =====
    ITEMS["leather_helmet"] = Item("leather_helmet", "Кожаный шлем", "🧢", ItemType.ARMOR, "Защита: 1", defense=1, stackable=False, rarity="common")
    ITEMS["leather_chestplate"] = Item("leather_chestplate", "Кожаный нагрудник", "🧥", ItemType.ARMOR, "Защита: 3", defense=3, stackable=False, rarity="common")
    ITEMS["leather_leggings"] = Item("leather_leggings", "Кожаные поножи", "👖", ItemType.ARMOR, "Защита: 2", defense=2, stackable=False, rarity="common")
    ITEMS["leather_boots"] = Item("leather_boots", "Кожаные ботинки", "👞", ItemType.ARMOR, "Защита: 1", defense=1, stackable=False, rarity="common")

# ===== ЖЕЛЕЗНАЯ БРОНЯ =====
    ITEMS["iron_helmet"] = Item("iron_helmet", "Железный шлем", "⛑️", ItemType.ARMOR, "Защита: 2", defense=2, stackable=False, rarity="common")
    ITEMS["iron_chestplate"] = Item("iron_chestplate", "Железный нагрудник", "🦺", ItemType.ARMOR, "Защита: 6", defense=6, stackable=False, rarity="common")
    ITEMS["iron_leggings"] = Item("iron_leggings", "Железные поножи", "👖", ItemType.ARMOR, "Защита: 5", defense=5, stackable=False, rarity="common")
    ITEMS["iron_boots"] = Item("iron_boots", "Железные ботинки", "👢", ItemType.ARMOR, "Защита: 2", defense=2, stackable=False, rarity="common")

# ===== АЛМАЗНАЯ БРОНЯ =====
    ITEMS["diamond_helmet"] = Item("diamond_helmet", "Алмазный шлем", "💎⛑️", ItemType.ARMOR, "Защита: 3", defense=3, stackable=False, rarity="epic")
    ITEMS["diamond_chestplate"] = Item("diamond_chestplate", "Алмазный нагрудник", "💎🦺", ItemType.ARMOR, "Защита: 8", defense=8, stackable=False, rarity="epic")
    ITEMS["diamond_leggings"] = Item("diamond_leggings", "Алмазные поножи", "💎👖", ItemType.ARMOR, "Защита: 6", defense=6, stackable=False, rarity="epic")
    ITEMS["diamond_boots"] = Item("diamond_boots", "Алмазные ботинки", "💎👢", ItemType.ARMOR, "Защита: 3", defense=3, stackable=False, rarity="epic")
    ITEMS["netherite_helmet"] = Item("netherite_helmet", "Незеритовый шлем", "💠⛑️", ItemType.ARMOR, "Защита: 4", defense=4, stackable=False, rarity="legendary")
    ITEMS["netherite_chestplate"] = Item("netherite_chestplate", "Незеритовый нагрудник", "💠🦺", ItemType.ARMOR, "Защита: 10", defense=10, stackable=False, rarity="legendary")
    ITEMS["netherite_leggings"] = Item("netherite_leggings", "Незеритовые поножи", "💠👖", ItemType.ARMOR, "Защита: 8", defense=8, stackable=False, rarity="legendary")
    ITEMS["netherite_boots"] = Item("netherite_boots", "Незеритовые ботинки", "💠👢", ItemType.ARMOR, "Защита: 4", defense=4, stackable=False, rarity="legendary")
    
    # ЗЕЛЬЯ
    ITEMS["healing_potion"] = Item("healing_potion", "Зелье лечения", "🧪", ItemType.POTION, "Восстанавливает 10 HP", heal_amount=10, stackable=False, rarity="rare")

register_items()

# ===================== РЕЦЕПТЫ КРАФТА =====================
@dataclass
class Recipe:
    result_id: str
    result_count: int
    ingredients: Dict[str, int]
    level_required: int = 1
    station: str = "crafting_table"

RECIPES: List[Recipe] = []

def register_recipes():
    RECIPES.append(Recipe("stick", 4, {"wood": 1}))
    RECIPES.append(Recipe("wood_sword", 1, {"wood": 2, "stick": 2}))
    RECIPES.append(Recipe("stone_sword", 1, {"cobblestone": 3, "stick": 2}))
    RECIPES.append(Recipe("iron_sword", 1, {"iron_ingot": 3, "stick": 2}))
    RECIPES.append(Recipe("diamond_sword", 1, {"diamond": 3, "stick": 2}))
    RECIPES.append(Recipe("netherite_sword", 1, {"netherite_ingot": 2, "diamond_sword": 1}))
    RECIPES.append(Recipe("netherite_ingot", 1, {"netherite_scrap": 4, "gold_ingot": 4}))
    RECIPES.append(Recipe("healing_potion", 1, {"nether_wart": 1, "glowstone": 1, "apple": 1}))
# Кожаная броня
    RECIPES.append(Recipe("leather_helmet", 1, {"leather": 5}))
    RECIPES.append(Recipe("leather_chestplate", 1, {"leather": 8}))
    RECIPES.append(Recipe("leather_leggings", 1, {"leather": 7}))
    RECIPES.append(Recipe("leather_boots", 1, {"leather": 4}))

# Железная броня
    RECIPES.append(Recipe("iron_helmet", 1, {"iron_ingot": 5}))
    RECIPES.append(Recipe("iron_chestplate", 1, {"iron_ingot": 8}))
    RECIPES.append(Recipe("iron_leggings", 1, {"iron_ingot": 7}))
    RECIPES.append(Recipe("iron_boots", 1, {"iron_ingot": 4}))

# Алмазная броня
    RECIPES.append(Recipe("diamond_helmet", 1, {"diamond": 5}))
    RECIPES.append(Recipe("diamond_chestplate", 1, {"diamond": 8}))
    RECIPES.append(Recipe("diamond_leggings", 1, {"diamond": 7}))
    RECIPES.append(Recipe("diamond_boots", 1, {"diamond": 4}))

register_recipes()

# ===================== МОБЫ =====================
@dataclass
class Mob:
    id: str
    name: str
    emoji: str
    health: int
    damage: int
    drops: Dict[str, Tuple[int, int]]
    xp: int
    rarity: str = "common"

MOBS: Dict[str, Mob] = {}

def register_mobs():
    MOBS["zombie"] = Mob("zombie", "Зомби", "🧟", 20, 4, {"meat": (0, 2), "iron_ingot": (0, 1)}, 5)
    MOBS["skeleton"] = Mob("skeleton", "Скелет", "💀", 20, 5, {"bone": (0, 2)}, 5)
    MOBS["spider"] = Mob("spider", "Паук", "🕷️", 16, 3, {"string": (0, 2)}, 5)
    MOBS["creeper"] = Mob("creeper", "Крипер", "💥", 20, 6, {"gunpowder": (0, 2)}, 5)
    MOBS["zombie_pigman"] = Mob("zombie_pigman", "Зомби-свин", "🐷🧟", 25, 6, {"gold_ingot": (0, 2)}, 8)
    MOBS["blaze"] = Mob("blaze", "Ифрит", "🔥", 30, 8, {"blaze_rod": (0, 2)}, 10)
    MOBS["enderman"] = Mob("enderman", "Эндермен", "👾", 40, 7, {"ender_pearl": (0, 2)}, 20)
    MOBS["dragon"] = Mob("dragon", "Дракон Края", "🐉", 200, 15, {"dragon_egg": (1, 1), "diamond": (3, 7)}, 100)

register_mobs()

# ===================== ЛОКАЦИИ =====================
@dataclass
class Location:
    id: str
    name: str
    emoji: str
    description: str
    mobs: List[str]
    resources: Dict[str, Tuple[int, int]]
    requires: Optional[str] = None
    min_level: int = 1
    danger_level: int = 1

LOCATIONS: Dict[str, Location] = {}

def register_locations():
    LOCATIONS["forest"] = Location(
        "forest", "Лес", "🌳", "Мирный лес",
        ["zombie", "spider"],
        {"wood": (80, 5), "apple": (40, 3), "stick": (60, 4)},
        min_level=1, danger_level=1
    )
    LOCATIONS["mountains"] = Location(
        "mountains", "Горы", "⛰️", "Каменистая местность",
        ["skeleton"],
        {"cobblestone": (90, 8), "iron_ore": (40, 4), "coal": (50, 5)},
        min_level=2, danger_level=2
    )
    LOCATIONS["cave"] = Location(
        "cave", "Пещера", "🕳️", "Тёмная пещера",
        ["zombie", "skeleton", "spider", "creeper"],
        {"cobblestone": (90, 10), "iron_ore": (60, 6), "gold_ore": (30, 3), "diamond": (15, 2)},
        min_level=5, danger_level=5
    )
    
    LOCATIONS["nether"] = Location(
        "nether", "Незер", "🔥", "Адское измерение, полно враждебных мобов и редких ресурсов",
        ["zombie_pigman", "blaze", "wither_skeleton", "ghast"], 
        {
            "netherrack": (90, 16),      # Адский камень — основа всего
            "soul_sand": (50, 8),        # Песок душ — для замедления
            "glowstone": (40, 6),        # Светокамень — для крафта
            "nether_wart": (30, 4),      # Адский нарост — для зелий
            "blaze_rod": (20, 2),        # Огненный стержень — из ифритов
            "ancient_debris": (5, 1)     # Древний обломок — для незерита (редко!)
        },
        requires="diamond_pickaxe",      # Нужна алмазная кирка чтобы войти
        min_level=10, 
        danger_level=8
    )
    
    LOCATIONS["end"] = Location(
        "end", "Край", "🌌", "Измерение дракона. Здесь обитают эндермены и сам Дракон Края!",
        ["enderman", "dragon"], 
        {
            "ender_pearl": (40, 3),       # Жемчуг Края — для телепортации
            "obsidian": (60, 8),          # Обсидиан — для порталов
            "chorus_fruit": (50, 4)       # Корус — странный фрукт
        },
        requires="netherite_sword",       # Нужен незеритовый меч чтобы войти
        min_level=20, 
        danger_level=10
    )

register_locations()

# ===================== КЛАСС ИГРОКА =====================
class Player:
    def __init__(self, user_id: int):
        self.user_id = user_id
        self.inventory: Dict[str, int] = {"stick": 1, "apple": 2}  # Стартовые предметы
        self.health: int = 20
        self.max_health: int = 20
        self.level: int = 1
        self.xp: int = 0
        self.xp_to_next: int = 100
        self.location: str = "forest"
        self.equipped: Dict[str, Optional[str]] = {
            "weapon": None,
            "helmet": None,
            "chestplate": None,
            "leggings": None,
            "boots": None
        }
        self.quests: List[str] = []
        self.quest_progress: Dict[str, int] = {}
        self.in_battle: bool = False
        self.current_mob: Optional[str] = None
        self.mob_health: int = 0
        self.buffs: Dict[str, int] = {}  # Временные баффы
        self.total_damage_dealt: int = 0
        self.total_mobs_killed: int = 0
        self.play_time: float = time.time()
        self.last_save: float = time.time()
        
    def add_item(self, item_id: str, count: int = 1) -> bool:
        """Добавляет предмет в инвентарь"""
        item = ITEMS.get(item_id)
        if not item:
            return False
            
        if item_id in self.inventory:
            if item.stackable:
                self.inventory[item_id] += count
            else:
                self.inventory[item_id] += count
        else:
            self.inventory[item_id] = count
        return True
        
    def remove_item(self, item_id: str, count: int = 1) -> bool:
        """Удаляет предмет из инвентаря"""
        if item_id not in self.inventory or self.inventory[item_id] < count:
            return False
        self.inventory[item_id] -= count
        if self.inventory[item_id] <= 0:
            del self.inventory[item_id]
        return True
        
    def has_items(self, items: Dict[str, int]) -> bool:
        """Проверяет наличие предметов"""
        for item_id, count in items.items():
            if self.inventory.get(item_id, 0) < count:
                return False
        return True
        
    def get_defense(self) -> int:
        """Суммарная защита"""
        defense = 0
        for slot in ["helmet", "chestplate", "leggings", "boots"]:
            item_id = self.equipped[slot]
            if item_id and item_id in ITEMS:
                defense += ITEMS[item_id].defense
        return defense
        
    def get_damage(self) -> int:
        """Урон с учётом баффов"""
        base_damage = 1  # Руки
        weapon_id = self.equipped["weapon"]
        if weapon_id and weapon_id in ITEMS:
            base_damage = ITEMS[weapon_id].damage
            
        # Бафф от зелья силы
        if "strength_potion" in self.buffs:
            base_damage += 5
            
        return base_damage
        
    def heal(self, amount: int) -> int:
        """Лечение"""
        old_health = self.health
        self.health = min(self.max_health, self.health + amount)
        return self.health - old_health
        
    def use_food(self, item_id: str) -> bool:
        """Использовать еду в бою или вне боя"""
        if item_id not in ITEMS or ITEMS[item_id].type != ItemType.FOOD:
            return False
        if self.inventory.get(item_id, 0) <= 0:
            return False
            
        item = ITEMS[item_id]
        healed = self.heal(item.heal_amount)
        self.remove_item(item_id, 1)
        
        # Особые эффекты
        if item_id == "nether_fruit":
            self.health = max(1, self.health - 2)  # Обжигает
            
        return True
        
    def use_potion(self, item_id: str) -> bool:
        """Использовать зелье"""
        if item_id not in ITEMS or ITEMS[item_id].type != ItemType.POTION:
            return False
        if self.inventory.get(item_id, 0) <= 0:
            return False
            
        item = ITEMS[item_id]
        
        if "healing" in item_id:
            self.heal(item.heal_amount)
        elif "strength" in item_id:
            self.buffs["strength_potion"] = 3  # На 3 боя
        elif "fire_resistance" in item_id:
            self.buffs["fire_resistance"] = 3
            
        self.remove_item(item_id, 1)
        return True
        
    def take_damage(self, damage: int) -> int:
        """Получить урон с учётом защиты и баффов"""
        defense = self.get_defense()
        
        # Защита от огня
        if "fire_resistance" in self.buffs and damage > 10:
            damage = damage // 2
            
        # Формула урона
        reduction = defense / (defense + 20)  # Макс ~55% защиты
        actual_damage = max(1, int(damage * (1 - reduction)))
        self.health -= actual_damage
        
        # Проверка тотема
        if self.health <= 0 and "totem" in self.inventory:
            self.health = 1
            self.remove_item("totem", 1)
            return actual_damage
            
        return actual_damage
        
    def add_xp(self, amount: int):
        """Добавить опыт"""
        self.xp += amount
        self.total_damage_dealt += amount
        
        while self.xp >= self.xp_to_next:
            self.level += 1
            self.xp -= self.xp_to_next
            self.xp_to_next = int(self.xp_to_next * 1.5)
            self.max_health += 5
            self.health = self.max_health
            
    def end_battle(self):
        """Завершить бой"""
        self.in_battle = False
        self.current_mob = None
        self.mob_health = 0
        
        # Уменьшаем баффы
        for buff in list(self.buffs.keys()):
            self.buffs[buff] -= 1
            if self.buffs[buff] <= 0:
                del self.buffs[buff]
                
    def to_dict(self) -> dict:
        """Сериализация"""
        return {
            "user_id": self.user_id,
            "inventory": self.inventory,
            "health": self.health,
            "max_health": self.max_health,
            "level": self.level,
            "xp": self.xp,
            "xp_to_next": self.xp_to_next,
            "location": self.location,
            "equipped": self.equipped,
            "quests": self.quests,
            "quest_progress": self.quest_progress,
            "total_damage_dealt": self.total_damage_dealt,
            "total_mobs_killed": self.total_mobs_killed,
            "play_time": self.play_time
        }
        
    @classmethod
    def from_dict(cls, data: dict) -> 'Player':
        """Десериализация"""
        player = cls(data["user_id"])
        player.inventory = data["inventory"]
        player.health = data["health"]
        player.max_health = data["max_health"]
        player.level = data["level"]
        player.xp = data["xp"]
        player.xp_to_next = data["xp_to_next"]
        player.location = data["location"]
        player.equipped = data["equipped"]
        player.quests = data["quests"]
        player.quest_progress = data["quest_progress"]
        player.total_damage_dealt = data.get("total_damage_dealt", 0)
        player.total_mobs_killed = data.get("total_mobs_killed", 0)
        player.play_time = data.get("play_time", time.time())
        return player

# ===================== СОХРАНЕНИЕ =====================
SAVE_FILE = "minecraft_save.json"

def save_players():
    """Сохранить всех игроков"""
    data = {str(uid): player.to_dict() for uid, player in players.items()}
    with open(SAVE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        
def load_players():
    """Загрузить игроков"""
    if not os.path.exists(SAVE_FILE):
        return
    try:
        with open(SAVE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        for uid_str, player_data in data.items():
            uid = int(uid_str)
            players[uid] = Player.from_dict(player_data)
        print(f"✅ Загружено игроков: {len(players)}")
    except Exception as e:
        logging.error(f"Ошибка загрузки: {e}")

# ===================== КЛАВИАТУРЫ =====================
def main_menu_keyboard() -> InlineKeyboardMarkup:
    """Главное меню"""
    buttons = [
        [InlineKeyboardButton(text="🌍 Исследовать", callback_data="explore")],
        [InlineKeyboardButton(text="⚔️ Инвентарь", callback_data="inventory")],
        [InlineKeyboardButton(text="🔧 Крафт", callback_data="craft")],
        [InlineKeyboardButton(text="👤 Профиль", callback_data="profile")],
        [InlineKeyboardButton(text="📍 Локации", callback_data="locations")],
        [InlineKeyboardButton(text="📜 Квесты", callback_data="quests")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def locations_keyboard(player: Player) -> InlineKeyboardMarkup:
    """Клавиатура локаций"""
    buttons = []
    for loc_id, loc in LOCATIONS.items():
        # Проверка доступа
        available = True
        status = "🔓"
        
        if loc.min_level > player.level:
            available = False
            status = f"🔒 (ур. {loc.min_level})"
        elif loc.requires and loc.requires not in player.inventory:
            available = False
            status = f"🔒 (нужен {ITEMS[loc.requires].name})"
            
        if player.location == loc_id:
            status = "✅"
            
        buttons.append([InlineKeyboardButton(
            text=f"{status} {loc.emoji} {loc.name}",
            callback_data=f"goto_{loc_id}" if available else "no_access"
        )])
        
    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_main")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def inventory_keyboard(player: Player, battle_mode: bool = False) -> InlineKeyboardMarkup:
    """Клавиатура инвентаря"""
    buttons = []
    items = list(player.inventory.items())
    
    # Сортируем: сначала еда/зелья в бою
    if battle_mode:
        items.sort(key=lambda x: (
            0 if ITEMS[x[0]].type in [ItemType.FOOD, ItemType.POTION] else 1,
            -ITEMS[x[0]].heal_amount if ITEMS[x[0]].type == ItemType.FOOD else 0
        ))
    
    # По 2 предмета в ряд
    for i in range(0, len(items), 2):
        row = []
        for j in range(2):
            if i + j < len(items):
                item_id, count = items[i + j]
                item = ITEMS.get(item_id)
                if item:
                    prefix = "🍎 " if battle_mode and item.type in [ItemType.FOOD, ItemType.POTION] else ""
                    row.append(InlineKeyboardButton(
                        text=f"{prefix}{item.emoji} {item.name} x{count}",
                        callback_data=f"use_{item_id}_{int(battle_mode)}"
                    ))
        if row:
            buttons.append(row)
            
    if battle_mode:
        buttons.append([InlineKeyboardButton(text="⚔️ Вернуться в бой", callback_data="battle_back")])
    else:
        buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_main")])
        
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def craft_keyboard(player: Player, page: int = 0) -> InlineKeyboardMarkup:
    """Клавиатура крафта с пагинацией"""
    buttons = []
    per_page = 6
    start = page * per_page
    end = start + per_page
    recipes_page = RECIPES[start:end]
    
    for recipe in recipes_page:
        result = ITEMS.get(recipe.result_id)
        if result:
            can_craft = player.has_items(recipe.ingredients)
            emoji = "✅" if can_craft else "❌"
            
            # Показываем требования
            req_text = ""
            if recipe.level_required > player.level:
                emoji = "🔒"
                req_text = f" (ур.{recipe.level_required})"
                
            buttons.append([InlineKeyboardButton(
                text=f"{emoji} {result.emoji} {result.name} x{recipe.result_count}{req_text}",
                callback_data=f"craft_{RECIPES.index(recipe)}"
            )])
    
    # Пагинация
    nav_row = []
    if page > 0:
        nav_row.append(InlineKeyboardButton(text="◀️", callback_data=f"craft_page_{page-1}"))
    if end < len(RECIPES):
        nav_row.append(InlineKeyboardButton(text="▶️", callback_data=f"craft_page_{page+1}"))
    if nav_row:
        buttons.append(nav_row)
        
    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_main")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def battle_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура боя"""
    buttons = [
        [InlineKeyboardButton(text="⚔️ Атаковать", callback_data="battle_attack")],
        [InlineKeyboardButton(text="🍎 Использовать предмет", callback_data="battle_use_item")],
        [InlineKeyboardButton(text="🏃 Сбежать", callback_data="battle_run")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def admin_keyboard() -> InlineKeyboardMarkup:
    """Админская клавиатура"""
    buttons = [
        [InlineKeyboardButton(text="💎 Выдать алмазы (10)", callback_data="admin_give_diamond")],
        [InlineKeyboardButton(text="🔥 Выдать незерит", callback_data="admin_give_netherite")],
        [InlineKeyboardButton(text="🍎 Выдать еду", callback_data="admin_give_food")],
        [InlineKeyboardButton(text="⚔️ Выдать меч", callback_data="admin_give_sword")],
        [InlineKeyboardButton(text="🛡️ Выдать броню", callback_data="admin_give_armor")],
        [InlineKeyboardButton(text="🧪 Выдать зелья", callback_data="admin_give_potions")],
        [InlineKeyboardButton(text="🩸 Исцелить всех", callback_data="admin_heal")],
        [InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats")],
        [InlineKeyboardButton(text="💾 Сохранить", callback_data="admin_save")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_main")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# ===================== ОБРАБОТЧИКИ =====================
@dp.message(Command("start"))
async def cmd_start(message: Message):
    """Старт"""
    user_id = message.from_user.id
    
    if user_id not in players:
        players[user_id] = Player(user_id)
        save_players()
        
    await message.answer(
        f"🔥 <b>Minecraft 2.0 Quest Bot</b>\n\n"
        f"👤 Твой ID: {user_id}\n"
        f"🦯 Стартовая палка: есть\n"
        f"🍎 Яблоки для лечения: 2 шт\n\n"
        f"<b>Что нового:</b>\n"
        f"• ❌ Голод убран\n"
        f"• 🍎 Еда лечит HP\n"
        f"• 🔥 Незерит добавлен\n"
        f"• 🧪 Зелья работают\n"
        f"• ⚔️ Можно жрать в бою!",
        reply_markup=main_menu_keyboard()
    )

@dp.message(Command("admin"))
async def cmd_admin(message: Message):
    """Админка"""
    if message.from_user.id != ADMIN_ID:
        await message.answer("🚫 Доступ запрещён!")
        return
        
    await message.answer(
        "👑 <b>Админ-панель</b>\n"
        f"Версия: {VERSION}\n"
        f"Игроков: {len(players)}",
        reply_markup=admin_keyboard()
    )

@dp.callback_query(F.data == "back_to_main")
async def back_to_main(callback: CallbackQuery):
    """Назад в главное меню"""
    await callback.message.edit_text(
        "🔥 <b>Главное меню</b>",
        reply_markup=main_menu_keyboard()
    )
    await callback.answer()

@dp.callback_query(F.data == "profile")
async def show_profile(callback: CallbackQuery):
    """Профиль"""
    user_id = callback.from_user.id
    if user_id not in players:
        players[user_id] = Player(user_id)
        
    player = players[user_id]
    location = LOCATIONS.get(player.location, LOCATIONS["forest"])
    
    defense = player.get_defense()
    damage = player.get_damage()
    
    # Время в игре
    play_time = int(time.time() - player.play_time)
    hours = play_time // 3600
    minutes = (play_time % 3600) // 60
    
    text = (
        f"👤 <b>Профиль игрока</b>\n\n"
        f"❤️ Здоровье: {player.health}/{player.max_health}\n"
        f"📊 Уровень: {player.level} (XP: {player.xp}/{player.xp_to_next})\n"
        f"📍 Локация: {location.emoji} {location.name}\n"
        f"⚔️ Урон: {damage}\n"
        f"🛡️ Защита: {defense}\n\n"
        f"📦 Предметов: {len(player.inventory)}\n"
        f"💀 Мобов убито: {player.total_mobs_killed}\n"
        f"⏱️ В игре: {hours}ч {minutes}м\n\n"
    )
    
    # Показать баффы
    if player.buffs:
        text += "✨ Активные баффы:\n"
        for buff, turns in player.buffs.items():
            if buff == "strength_potion":
                text += f"  • 💪 Сила: {turns} боя\n"
            elif buff == "fire_resistance":
                text += f"  • 🔥 Огнестойкость: {turns} боя\n"
                
    await callback.message.edit_text(text, reply_markup=main_menu_keyboard())
    await callback.answer()

@dp.callback_query(F.data == "locations")
async def show_locations(callback: CallbackQuery):
    """Список локаций"""
    user_id = callback.from_user.id
    if user_id not in players:
        players[user_id] = Player(user_id)
        
    player = players[user_id]
    
    await callback.message.edit_text(
        "📍 <b>Доступные локации</b>\n\n"
        "✅ - текущая\n🔓 - доступно\n🔒 - закрыто",
        reply_markup=locations_keyboard(player)
    )
    await callback.answer()

@dp.callback_query(F.data.startswith("goto_"))
async def goto_location(callback: CallbackQuery):
    """Перемещение"""
    user_id = callback.from_user.id
    if user_id not in players:
        players[user_id] = Player(user_id)
        
    player = players[user_id]
    loc_id = callback.data.replace("goto_", "")
    
    if loc_id not in LOCATIONS:
        await callback.answer("Локация не найдена!")
        return
        
    loc = LOCATIONS[loc_id]
    
    # Проверки
    if loc.min_level > player.level:
        await callback.answer(f"❌ Нужен уровень {loc.min_level}!")
        return
        
    if loc.requires and loc.requires not in player.inventory:
        item = ITEMS[loc.requires]
        await callback.answer(f"❌ Нужен {item.name}!")
        return
        
    player.location = loc_id
    save_players()
    
    await callback.message.edit_text(
        f"📍 <b>Вы переместились в {loc.emoji} {loc.name}</b>\n\n"
        f"{loc.description}\n"
        f"⚡ Уровень опасности: {loc.danger_level}/10",
        reply_markup=main_menu_keyboard()
    )
    await callback.answer()

@dp.callback_query(F.data == "explore")
async def explore_location(callback: CallbackQuery):
    """Исследование"""
    user_id = callback.from_user.id
    if user_id not in players:
        players[user_id] = Player(user_id)
        
    player = players[user_id]
    loc = LOCATIONS.get(player.location, LOCATIONS["forest"])
    
    # Шанс встретить моба (зависит от опасности)
    mob_chance = loc.danger_level * 10  # 10-100%
    if random.randint(1, 100) <= mob_chance and loc.mobs:
        mob_id = random.choice(loc.mobs)
        mob = MOBS[mob_id]
        
        player.in_battle = True
        player.current_mob = mob_id
        player.mob_health = mob.health
        
        await callback.message.edit_text(
            f"⚠️ <b>ВЫ ВСТРЕТИЛИ {mob.emoji} {mob.name.upper()}!</b>\n\n"
            f"❤️ Здоровье: {mob.health}\n"
            f"⚔️ Урон: {mob.damage}\n"
            f"✨ Редкость: {mob.rarity}\n\n"
            f"Что делаем?",
            reply_markup=battle_keyboard()
        )
        await callback.answer()
        return
        
    # Добыча ресурсов
    resources_found = []
    for res_id, (chance, max_count) in loc.resources.items():
        if random.randint(1, 100) <= chance:
            count = random.randint(1, max_count)
            player.add_item(res_id, count)
            res_name = ITEMS[res_id].name
            resources_found.append(f"{ITEMS[res_id].emoji} {res_name} x{count}")
            
    save_players()
    
    text = f"🌍 <b>Исследование {loc.emoji} {loc.name}</b>\n\n"
    if resources_found:
        text += "🔍 Найдено:\n" + "\n".join(resources_found)
    else:
        text += "😕 Ничего не найдено..."
        
    text += f"\n\n❤️ HP: {player.health}/{player.max_health}"
    
    await callback.message.edit_text(text, reply_markup=main_menu_keyboard())
    await callback.answer()

@dp.callback_query(F.data == "inventory")
async def show_inventory(callback: CallbackQuery):
    """Инвентарь"""
    user_id = callback.from_user.id
    if user_id not in players:
        players[user_id] = Player(user_id)
        
    player = players[user_id]
    
    if not player.inventory:
        await callback.message.edit_text(
            "🎒 <b>Инвентарь пуст</b>",
            reply_markup=main_menu_keyboard()
        )
        await callback.answer()
        return
        
    await callback.message.edit_text(
        "🎒 <b>Инвентарь</b>\n"
        "🍎 - можно использовать в бою",
        reply_markup=inventory_keyboard(player, battle_mode=False)
    )
    await callback.answer()

@dp.callback_query(F.data.startswith("use_"))
async def use_item(callback: CallbackQuery):
    """Использовать предмет"""
    user_id = callback.from_user.id
    if user_id not in players:
        players[user_id] = Player(user_id)
        
    player = players[user_id]
    parts = callback.data.split("_")
    item_id = parts[1]
    battle_mode = len(parts) > 2 and parts[2] == "1"
    
    if item_id not in player.inventory:
        await callback.answer("Предмет не найден!")
        return
        
    item = ITEMS[item_id]
    
    # Использование
    if item.type == ItemType.FOOD:
        player.use_food(item_id)
        save_players()
        await callback.answer(f"🍎 Съедено! ❤️ +{item.heal_amount}")
        
    elif item.type == ItemType.POTION:
        player.use_potion(item_id)
        save_players()
        await callback.answer(f"🧪 Зелье выпито!")
        
    elif item.type == ItemType.WEAPON:
        player.equipped["weapon"] = item_id
        save_players()
        await callback.answer(f"⚔️ Меч экипирован!")
        
    elif item.type == ItemType.ARMOR:
        if "helmet" in item_id:
            player.equipped["helmet"] = item_id
        elif "chestplate" in item_id:
            player.equipped["chestplate"] = item_id
        elif "leggings" in item_id:
            player.equipped["leggings"] = item_id
        elif "boots" in item_id:
            player.equipped["boots"] = item_id
        save_players()
        await callback.answer(f"🛡️ Броня надета!")
        
    else:
        await callback.answer("Этот предмет нельзя использовать")
        return
        
    # Возврат
    if battle_mode:
        await battle_screen(callback)
    else:
        await show_inventory(callback)

@dp.callback_query(F.data == "craft")
async def show_craft(callback: CallbackQuery):
    """Крафт"""
    user_id = callback.from_user.id
    if user_id not in players:
        players[user_id] = Player(user_id)
        
    player = players[user_id]
    
    await callback.message.edit_text(
        "🔧 <b>Крафт</b>\n\n"
        "✅ - можно скрафтить\n"
        "❌ - не хватает ресурсов\n"
        "🔒 - низкий уровень",
        reply_markup=craft_keyboard(player, 0)
    )
    await callback.answer()

@dp.callback_query(F.data.startswith("craft_page_"))
async def craft_page(callback: CallbackQuery):
    """Пагинация крафта"""
    user_id = callback.from_user.id
    if user_id not in players:
        players[user_id] = Player(user_id)
        
    player = players[user_id]
    page = int(callback.data.replace("craft_page_", ""))
    
    await callback.message.edit_text(
        "🔧 <b>Крафт</b>",
        reply_markup=craft_keyboard(player, page)
    )
    await callback.answer()

@dp.callback_query(F.data.startswith("craft_"))
async def craft_item(callback: CallbackQuery):
    """Скрафтить"""
    user_id = callback.from_user.id
    if user_id not in players:
        players[user_id] = Player(user_id)
        
    player = players[user_id]
    recipe_index = int(callback.data.replace("craft_", ""))
    
    if recipe_index >= len(RECIPES):
        await callback.answer("Рецепт не найден!")
        return
        
    recipe = RECIPES[recipe_index]
    
    # Проверка уровня
    if recipe.level_required > player.level:
        await callback.answer(f"❌ Нужен уровень {recipe.level_required}!")
        return
        
    # Проверка ресурсов
    if not player.has_items(recipe.ingredients):
        await callback.answer("❌ Не хватает ресурсов!")
        return
        
    # Крафт
    for item_id, count in recipe.ingredients.items():
        player.remove_item(item_id, count)
        
    player.add_item(recipe.result_id, recipe.result_count)
    save_players()
    
    result = ITEMS[recipe.result_id]
    await callback.answer(f"✅ Скрафчено: {result.name} x{recipe.result_count}")
    
    # Обновляем
    await show_craft(callback)

# ===================== БОЙ =====================
async def battle_screen(callback: CallbackQuery):
    """Обновление экрана боя"""
    user_id = callback.from_user.id
    player = players[user_id]
    mob = MOBS[player.current_mob]
    
    text = (
        f"⚔️ <b>БОЙ!</b>\n\n"
        f"Противник: {mob.emoji} {mob.name}\n"
        f"❤️ Моб: {player.mob_health}/{mob.health}\n"
        f"❤️ Ты: {player.health}/{player.max_health}\n"
        f"⚔️ Твой урон: {player.get_damage()}\n"
    )
    
    # Баффы
    if player.buffs:
        text += "\n✨ Баффы:\n"
        for buff, turns in player.buffs.items():
            if buff == "strength_potion":
                text += f"  • 💪 Сила: {turns} боя\n"
            elif buff == "fire_resistance":
                text += f"  • 🔥 Огнестойкость: {turns} боя\n"
                
    await callback.message.edit_text(text, reply_markup=battle_keyboard())

@dp.callback_query(F.data == "battle_back")
async def battle_back(callback: CallbackQuery):
    """Вернуться в бой"""
    await battle_screen(callback)
    await callback.answer()

@dp.callback_query(F.data == "battle_use_item")
async def battle_use_item(callback: CallbackQuery):
    """Использовать предмет в бою"""
    user_id = callback.from_user.id
    player = players[user_id]
    
    # Фильтруем только еду и зелья
    usable_items = {
        item_id: count for item_id, count in player.inventory.items()
        if ITEMS[item_id].type in [ItemType.FOOD, ItemType.POTION]
    }
    
    if not usable_items:
        await callback.answer("❌ Нет еды или зелий!")
        return
        
    # Создаём временную клавиатуру
    buttons = []
    items = list(usable_items.items())
    for i in range(0, len(items), 2):
        row = []
        for j in range(2):
            if i + j < len(items):
                item_id, count = items[i + j]
                item = ITEMS[item_id]
                row.append(InlineKeyboardButton(
                    text=f"{item.emoji} {item.name} x{count}",
                    callback_data=f"use_{item_id}_1"
                ))
        buttons.append(row)
    buttons.append([InlineKeyboardButton(text="⚔️ Назад в бой", callback_data="battle_back")])
    
    await callback.message.edit_text(
        "🍎 <b>Использовать предмет в бою</b>\n\n"
        "Еда лечит мгновенно\n"
        "Зелья дают баффы",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )
    await callback.answer()

@dp.callback_query(F.data == "battle_attack")
async def battle_attack(callback: CallbackQuery):
    """Атака"""
    user_id = callback.from_user.id
    if user_id not in players:
        players[user_id] = Player(user_id)
        
    player = players[user_id]
    
    if not player.in_battle or not player.current_mob:
        await callback.answer("Бой не активен!")
        return
        
    mob = MOBS[player.current_mob]
    
    # Игрок атакует
    player_damage = player.get_damage()
    player_damage = random.randint(max(1, player_damage-2), player_damage+2)
    player.mob_health -= player_damage
    player.total_damage_dealt += player_damage
    
    text = f"⚔️ Ты нанёс {player_damage} урона!\n"
    
    if player.mob_health <= 0:
        # Победа
        player.total_mobs_killed += 1
        player.add_xp(mob.xp)
        
        # Дроп
        drops = []
        for drop_id, (min_c, max_c) in mob.drops.items():
            count = random.randint(min_c, max_c)
            if count > 0:
                player.add_item(drop_id, count)
                item = ITEMS[drop_id]
                drops.append(f"{item.emoji} {item.name} x{count}")
                
        player.end_battle()
        save_players()
        
        text += f"\n🎉 <b>ПОБЕДА!</b>\n"
        text += f"✨ +{mob.xp} XP\n"
        if drops:
            text += "📦 Дроп:\n" + "\n".join(drops)
            
        await callback.message.edit_text(text, reply_markup=main_menu_keyboard())
        await callback.answer()
        return
        
    # Моб атакует
    mob_damage = random.randint(max(1, mob.damage-2), mob.damage+2)
    actual_damage = player.take_damage(mob_damage)
    
    text += f"💥 {mob.emoji} нанёс {actual_damage} урона!\n\n"
    text += f"❤️ Твоё HP: {player.health}/{player.max_health}\n"
    text += f"❤️ Моб HP: {player.mob_health}/{mob.health}\n"
    
    if player.health <= 0:
        # Смерть
        if "totem" in player.inventory:
            player.health = 1
            player.remove_item("totem", 1)
            text += "\n🗿 Тотем сработал! Ты воскрес!"
        else:
            player.health = player.max_health // 2
            player.end_battle()
            text += "\n💀 Ты погиб... Возродился с половинным HP!"
            
        save_players()
        await callback.message.edit_text(text, reply_markup=main_menu_keyboard())
        await callback.answer()
        return
        
    save_players()
    await callback.message.edit_text(text, reply_markup=battle_keyboard())
    await callback.answer()

@dp.callback_query(F.data == "battle_run")
async def battle_run(callback: CallbackQuery):
    """Побег"""
    user_id = callback.from_user.id
    if user_id not in players:
        players[user_id] = Player(user_id)
        
    player = players[user_id]
    
    if not player.in_battle:
        await callback.answer("Бой не активен!")
        return
        
    # Шанс побега 60%
    if random.randint(1, 100) <= 60:
        player.end_battle()
        save_players()
        await callback.message.edit_text(
            "🏃 Ты сбежал!",
            reply_markup=main_menu_keyboard()
        )
        await callback.answer()
    else:
        # Не убежал, моб атакует
        mob = MOBS[player.current_mob]
        mob_damage = random.randint(max(1, mob.damage-2), mob.damage+2)
        actual_damage = player.take_damage(mob_damage)
        
        text = f"❌ Не удалось сбежать!\n"
        text += f"💥 {mob.emoji} нанёс {actual_damage} урона!\n"
        text += f"❤️ Твоё HP: {player.health}/{player.max_health}\n"
        
        if player.health <= 0:
            if "totem" in player.inventory:
                player.health = 1
                player.remove_item("totem", 1)
                text += "\n🗿 Тотем сработал!"
            else:
                player.health = player.max_health // 2
                player.end_battle()
                text += "\n💀 Ты погиб..."
                
        save_players()
        await callback.message.edit_text(text, reply_markup=battle_keyboard())
        await callback.answer()

@dp.callback_query(F.data == "quests")
async def show_quests(callback: CallbackQuery):
    """Квесты"""
    user_id = callback.from_user.id
    if user_id not in players:
        players[user_id] = Player(user_id)
        
    player = players[user_id]
    
    # Заглушка для квестов
    text = "📜 <b>Квесты</b>\n\n"
    text += "⚔️ Убить 10 мобов: "
    if player.total_mobs_killed >= 10:
        text += "✅ ВЫПОЛНЕНО"
    else:
        text += f"{player.total_mobs_killed}/10"
        
    text += "\n\n🔥 Скоро будут новые квесты!"
    
    await callback.message.edit_text(text, reply_markup=main_menu_keyboard())
    await callback.answer()

# ===================== АДМИНКА =====================
@dp.callback_query(F.data == "admin_give_diamond")
async def admin_give_diamond(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("🚫")
        return
        
    for player in players.values():
        player.add_item("diamond", 10)
    save_players()
    await callback.answer("✅ Всем по 10 алмазов!")

@dp.callback_query(F.data == "admin_give_netherite")
async def admin_give_netherite(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("🚫")
        return
        
    for player in players.values():
        player.add_item("netherite_ingot", 5)
        player.add_item("ancient_debris", 3)
    save_players()
    await callback.answer("✅ Всем незерит!")

@dp.callback_query(F.data == "admin_give_food")
async def admin_give_food(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("🚫")
        return
        
    for player in players.values():
        player.add_item("bread", 10)
        player.add_item("meat", 10)
        player.add_item("golden_apple", 5)
    save_players()
    await callback.answer("✅ Еда выдана!")

@dp.callback_query(F.data == "admin_give_sword")
async def admin_give_sword(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("🚫")
        return
        
    for player in players.values():
        player.add_item("netherite_sword", 1)
        player.add_item("diamond_sword", 1)
    save_players()
    await callback.answer("✅ Мечи выданы!")

@dp.callback_query(F.data == "admin_give_armor")
async def admin_give_armor(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("🚫")
        return
        
    for player in players.values():
        player.add_item("netherite_helmet", 1)
        player.add_item("netherite_chestplate", 1)
        player.add_item("netherite_leggings", 1)
        player.add_item("netherite_boots", 1)
    save_players()
    await callback.answer("✅ Броня выдана!")

@dp.callback_query(F.data == "admin_give_potions")
async def admin_give_potions(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("🚫")
        return
        
    for player in players.values():
        player.add_item("healing_potion", 3)
        player.add_item("strength_potion", 2)
        player.add_item("fire_resistance_potion", 2)
    save_players()
    await callback.answer("✅ Зелья выданы!")

@dp.callback_query(F.data == "admin_heal")
async def admin_heal(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("🚫")
        return
        
    for player in players.values():
        player.health = player.max_health
    save_players()
    await callback.answer("✅ Все исцелены!")

@dp.callback_query(F.data == "admin_save")
async def admin_save(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("🚫")
        return
        
    save_players()
    await callback.answer("💾 Сохранено!")

@dp.callback_query(F.data == "admin_stats")
async def admin_stats(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("🚫")
        return
        
    total_items = sum(len(p.inventory) for p in players.values())
    total_damage = sum(p.total_damage_dealt for p in players.values())
    total_mobs = sum(p.total_mobs_killed for p in players.values())
    
    top_player = max(players.values(), key=lambda p: p.level)
    
    text = "📊 <b>Статистика сервера</b>\n\n"
    text += f"👥 Игроков: {len(players)}\n"
    text += f"📦 Всего предметов: {total_items}\n"
    text += f"⚔️ Урона нанесено: {total_damage}\n"
    text += f"💀 Мобов убито: {total_mobs}\n\n"
    text += f"🏆 Топ игрок: ID {top_player.user_id}\n"
    text += f"   Уровень: {top_player.level}\n"
    text += f"   ❤️ HP: {top_player.max_health}"
    
    await callback.message.edit_text(text, reply_markup=admin_keyboard())
    await callback.answer()

@dp.callback_query(F.data == "no_access")
async def no_access(callback: CallbackQuery):
    """Нет доступа к локации"""
    await callback.answer("❌ Нет доступа!")

# ===================== ЗАПУСК =====================
async def main():
    """Запуск"""
    load_players()
    print("=" * 50)
    print("🤖 MINECRAFT 2.0 QUEST BOT")
    print(f"📦 Версия: {VERSION}")
    print(f"🔥 Незерит загружен")
    print(f"🧪 Зелья активированы")
    print(f"🦯 Палка-символ: да")
    print(f"👥 Игроков загружено: {len(players)}")
    print("=" * 50)
    
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

# КОНЕЦ КОДА
# 🦯 ПАЛКА ВЕЧНА
# 🔥 НЕЗЕРИТ ТОП
# ❤️ ЕДА ЛЕЧИТ
# ⚔️ МОЖНО ЖРАТЬ В БОЮ
# 🐉 ДРАКОН БУДЕТ НАШ