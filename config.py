import os

# Scieżki i pliki
TESSERACT_CMD = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
TEMPLATE_FILE = "template.per"
AOE2_AI_FOLDER = r"D:\Steam\steamapps\common\AoE2DE\resources\_common\ai"
CSV_FILENAME = "historia_ewolucji.csv"
GOLDEN_MASTER_DIR = r"D:\Age2 classic"
WORKERS_DIR = r"D:\AoE2_Evo\Workers"
WITHDLL_PATH = r"D:\Detours\Detours-main\bin.X86\withdll.exe"
HOOK_DLL_PATH = r"C:\Users\kalla\source\repos\Aoe2MutexHook\Release\AoE2MutexHook.dll"
AUTO_GAME_DLL_PATH = r"D:\AoE2_Evo\aoc-auto-game.dll"
BASE_PORT = 64720

# Parametry Symulacji
NUM_WORKERS = 12           # Liczba równoległych okien (wątków)
BOTS_PER_MATCH = 8        # Liczba botów walczących naraz na jednej mapie TestEvo
GENERATIONS = 3000
MATCH_DURATION = 2000
MUTATION_RATE = 0.15
