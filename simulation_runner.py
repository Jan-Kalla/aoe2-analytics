import os
import shutil
import subprocess
import time
import random
import logging
from config import *
import ctypes
import msgpackrpc
import threading

# [NOWE] Uciszamy wbudowane ostrzeżenia Tornado (msgpackrpc) o zamkniętych portach
logging.getLogger('tornado.general').setLevel(logging.ERROR)
logging.getLogger('tornado.application').setLevel(logging.ERROR)


def arrange_windows(workers_count):
    print("[*] Aktywowanie okien (bez zmiany rozmiaru)...")
    EnumWindows = ctypes.windll.user32.EnumWindows
    EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int))
    GetWindowText = ctypes.windll.user32.GetWindowTextW
    GetWindowTextLength = ctypes.windll.user32.GetWindowTextLengthW
    IsWindowVisible = ctypes.windll.user32.IsWindowVisible
    SetForegroundWindow = ctypes.windll.user32.SetForegroundWindow

    hwnds = []

    def foreach_window(hwnd, lParam):
        if IsWindowVisible(hwnd):
            length = GetWindowTextLength(hwnd)
            buff = ctypes.create_unicode_buffer(length + 1)
            GetWindowText(hwnd, buff, length + 1)
            if "Age of Empires II Expansion" in buff.value:
                hwnds.append(hwnd)
        return True

    EnumWindows(EnumWindowsProc(foreach_window), 0)

    # Iterujemy tylko po znalezionych uchwytach i sprowadzamy je na wierzch
    for hwnd in hwnds[:workers_count]:
        SetForegroundWindow(hwnd)
        time.sleep(0.05)

def emergency_wake_up():
    EnumWindows = ctypes.windll.user32.EnumWindows
    EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int))
    GetWindowText = ctypes.windll.user32.GetWindowTextW
    GetWindowTextLength = ctypes.windll.user32.GetWindowTextLengthW
    IsWindowVisible = ctypes.windll.user32.IsWindowVisible
    SetForegroundWindow = ctypes.windll.user32.SetForegroundWindow

    def foreach_window(hwnd, lParam):
        if IsWindowVisible(hwnd):
            length = GetWindowTextLength(hwnd)
            buff = ctypes.create_unicode_buffer(length + 1)
            GetWindowText(hwnd, buff, length + 1)
            if "Age of Empires II Expansion" in buff.value:
                SetForegroundWindow(hwnd)
        return True

    EnumWindows(EnumWindowsProc(foreach_window), 0)

def setup_workers(workers_count):
    # Usunięto print, żeby zachować czystą konsolę, zostawiamy tylko istotne komunikaty naprawcze
    if not os.path.exists(WORKERS_DIR):
        os.makedirs(WORKERS_DIR)

    for i in range(1, workers_count  + 1):
        worker_path = os.path.join(WORKERS_DIR, f"Worker_{i}")
        worker_exe = os.path.join(worker_path, "Age2_x1", "age2_x1.5.exe")

        if os.path.exists(worker_path) and not os.path.exists(worker_exe):
            print(f"  [!] Formatowanie uszkodzonego Workera {i}...")
            shutil.rmtree(worker_path)

        if not os.path.exists(worker_path):
            print(f"  -> Przygotowuję Workera {i} (Klonowanie plików gry)...")
            shutil.copytree(
                GOLDEN_MASTER_DIR, worker_path,
                symlinks=False,
                ignore_dangling_symlinks=True,
                ignore=shutil.ignore_patterns('SaveGame', 'Screenshots', 'Campaign')
            )

        logs_folders = [
            os.path.join(worker_path, "AI", "Logs"),
            os.path.join(worker_path, "Age2_x1", "Script.AI", "Logs"),
            os.path.join(worker_path, "Games", "WololoKingdoms", "Script.AI", "Logs")
        ]
        for logs_dir in logs_folders:
            os.makedirs(logs_dir, exist_ok=True)
            for log_file in os.listdir(logs_dir):
                log_path = os.path.join(logs_dir, log_file)
                if os.path.isfile(log_path):
                    os.remove(log_path)

def run_match_and_evaluate_parallel(workers_count):
    setup_workers(workers_count)
    processes = []
    rpc_clients = []

    population_size = workers_count * BOTS_PER_MATCH

    print(f"[*] Uruchamianie {workers_count} niezależnych instancji dla {population_size} botów (Tryb Cichy)...")

    for i in range(1, workers_count + 1):
        worker_dir = os.path.join(WORKERS_DIR, f"Worker_{i}")
        worker_port = BASE_PORT + i

        map_id = random.randint(1, 50)
        source_map = os.path.join(GOLDEN_MASTER_DIR, "Scenario", f"TestEvo_{map_id}.scx")

        possible_destinations = [
            os.path.join(worker_dir, "Scenario", "TestEvo.scx"),
            os.path.join(worker_dir, "Games", "WololoKingdoms", "Scenario", "TestEvo.scx")
        ]

        for dest_map in possible_destinations:
            os.makedirs(os.path.dirname(dest_map), exist_ok=True)
            if os.path.exists(source_map):
                shutil.copyfile(source_map, dest_map)

        cwd_path = os.path.join(worker_dir, "Age2_x1")
        worker_exe = os.path.join(cwd_path, "age2_x1.5.exe")

        cmd = [
            WITHDLL_PATH,
            f"/d:{HOOK_DLL_PATH}",
            f"/d:{AUTO_GAME_DLL_PATH}",
            worker_exe,
            "-window",
            "-nomovie",
            "-nostartup",
            "-nosound",
            "-no-desktop-resolution",
            "-ai-log",
            "-AILog",
            "-autogameport", str(worker_port)
        ]

        # [NOWE] Usunięte printy [DEBUG]. Przekierowanie strumieni z withdll.exe w próżnię, żeby nie śmieciło konsoli.
        p = subprocess.Popen(cmd, cwd=cwd_path, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        processes.append((i, p))
        rpc_clients.append((i, worker_port))

        time.sleep(0.05)

    print("[*] Oczekiwanie na inicjalizację i nawiązanie połączeń RPC...")
    time.sleep(0.2)
    arrange_windows(workers_count)

    def configure_worker(worker_id, port):
        try:
            client = msgpackrpc.Client(msgpackrpc.Address("127.0.0.1", port), timeout=10)
            connection_established = False
            for attempt in range(100):
                try:
                    client.call('GetGameTime')
                    connection_established = True
                    break
                except Exception:
                    time.sleep(0.1)

            if not connection_established:
                return

            client.call('ResetGameSettings')
            client.call('SetGameType', 3)
            client.call('SetGameScenarioName', 'TestEvo')

            # [NOWE] Dławienie zapytań RPC (Throttling) chroniące przed gubieniem pakietów
            for bot_slot in range(1, 9):
                client.call('SetPlayerComputer', bot_slot, f"Milibot_Evo_{bot_slot}")
                time.sleep(0.02)  # Dajemy silnikowi 20 milisekund na przetworzenie komendy!

            client.call('SetRunFullSpeed', True)
            client.call('SetRunUnfocused', True)
            client.call('SetUseInGameResolution', False)

            time.sleep(0.05)
            client.call('StartGame')

        except Exception as e:
            pass # Tryb cichy - ignorujemy błędy komunikacji pobocznej

    threads = []
    for worker_id, port in rpc_clients:
        t = threading.Thread(target=configure_worker, args=(worker_id, port))
        threads.append(t)
        t.start()

    for t in threads:
        t.join(timeout=15)

    print("[*] Start symulacji zsynchronizowany. Trwa ewolucja...")
    emergency_wake_up()

    # [NAPRAWIONE] Domyślne wartości jako pełne słowniki, by uniknąć błędu TypeError przy Crashu
    all_workers_results = {
        i: [{'base': 0, 'bonus': 0, 'penalty': 0, 'mil': 0, 'age': 0, 'exp': 0, 'win': 0, 'tech': 0, 'lose_tc': 0} for _
            in range(BOTS_PER_MATCH)]
        for i in range(1, workers_count + 1)
    }

    active_workers = []
    for worker_id, port in rpc_clients:
        client = msgpackrpc.Client(msgpackrpc.Address("127.0.0.1", port), timeout=5)
        active_workers.append({
            'id': worker_id,
            'client': client,
            'process': processes[worker_id - 1][1],
            'has_started': False,
            'loading_start': time.time(),
            'last_radar_print': 0  # [NOWE] Zmienna śledząca czas dla radaru
        })

    start_real_time = time.time()

    while active_workers:
        if time.time() - start_real_time > 300:
            print("[CRASH] Przekroczono maksymalny czas! Ubijam pozostałe instancje.")
            break

        for worker in active_workers[:]:
            w_id = worker['id']
            client = worker['client']
            p = worker['process']

            try:
                in_progress = client.call('GetGameInProgress')
                game_time = client.call('GetGameTime')

                if not worker['has_started']:
                    if in_progress or game_time > 0:
                        worker['has_started'] = True
                    elif time.time() - worker['loading_start'] > 60:
                        print(f"  [!] Worker {w_id} zawiesił się na ładowaniu. Ubijam.")
                        p.kill()
                        active_workers.remove(worker)

                else:
                    # [NOWE] Throttle radaru: raportuje tylko co 300 sekund wewnątrz gry
                    if game_time - worker['last_radar_print'] >= 300:
                        print(f"  [Radar] Worker {w_id} | Czas gry: {game_time} sek.")
                        worker['last_radar_print'] = game_time

                    if not in_progress or game_time > MATCH_DURATION + 10:
                        print(f"[*] Worker {w_id} zakończył mecz! Wyciągam punkty...")

                        scores = []
                        for slot in range(1, BOTS_PER_MATCH + 1):
                            try:
                                # 1. Wynik ogólny
                                base_score = client.call('GetPlayerScore', slot)

                                # 2. Odczyt logów telemetrycznych (Kuloodporny)
                                max_mil = 0
                                max_age = 0
                                max_exp = 0
                                win_flag = 0
                                lose_tc = 0
                                tec_blk = 0
                                tec_uni = 0
                                tec_cst = 0
                                tec_mar = 0
                                tec_mon = 0  # <--- TEGO BRAKOWAŁO
                                max_relics = 0  # <--- TEGO BRAKOWAŁO

                                worker_dir = os.path.join(WORKERS_DIR, f"Worker_{w_id}")
                                active_log = None

                                for root_dir, _, files in os.walk(worker_dir):
                                    for file in files:
                                        if file.endswith(".txt"):
                                            test_path = os.path.join(root_dir, file)
                                            try:
                                                with open(test_path, "rb") as f:
                                                    content = f.read().replace(b'\x00', b'').decode('utf-8', errors='ignore')
                                                    if f"SLOT:{slot}|" in content:
                                                        active_log = test_path
                                                        for line in content.splitlines():
                                                            if f"SLOT:{slot}|TEC_MON:" in line:
                                                                try:
                                                                    tec_mon = max(tec_mon, int(
                                                                        line.split(f"SLOT:{slot}|TEC_MON:")[1].strip()))
                                                                except:
                                                                    pass
                                                            if f"SLOT:{slot}|RELIC_C:" in line:
                                                                try:
                                                                    max_relics = max(max_relics, int(
                                                                        line.split(f"SLOT:{slot}|RELIC_C:")[1].strip()))
                                                                except:
                                                                    pass
                                                            if f"SLOT:{slot}|MIL:" in line:
                                                                try: max_mil = max(max_mil, int(line.split(f"SLOT:{slot}|MIL:")[1].strip()))
                                                                except: pass
                                                            if f"SLOT:{slot}|AGE:" in line:
                                                                try: max_age = max(max_age, int(line.split(f"SLOT:{slot}|AGE:")[1].strip()))
                                                                except: pass
                                                            if f"SLOT:{slot}|EXP:" in line:
                                                                try: max_exp = max(max_exp, int(line.split(f"SLOT:{slot}|EXP:")[1].strip()))
                                                                except: pass

                                                            # [NOWE] Budynki (Czytamy dynamicznie, tak samo jak MIL!)
                                                            if f"SLOT:{slot}|TEC_BLK:" in line:
                                                                try: tec_blk = max(tec_blk, int(line.split(f"SLOT:{slot}|TEC_BLK:")[1].strip()))
                                                                except: pass
                                                            if f"SLOT:{slot}|TEC_UNI:" in line:
                                                                try: tec_uni = max(tec_uni, int(line.split(f"SLOT:{slot}|TEC_UNI:")[1].strip()))
                                                                except: pass
                                                            if f"SLOT:{slot}|TEC_CST:" in line:
                                                                try: tec_cst = max(tec_cst, int(line.split(f"SLOT:{slot}|TEC_CST:")[1].strip()))
                                                                except: pass
                                                            if f"SLOT:{slot}|TEC_MAR:" in line:
                                                                try: tec_mar = max(tec_mar, int(line.split(f"SLOT:{slot}|TEC_MAR:")[1].strip()))
                                                                except: pass

                                                            if f"SLOT:{slot}|WIN:" in line: win_flag = 1
                                                            if f"SLOT:{slot}|LOSE_TC:1" in line: lose_tc = 1
                                                        break
                                            except Exception:
                                                pass
                                    if active_log:
                                        break

                                if not active_log:
                                    print(f"  [UWAGA] Radar nie znalazł telemetrii dla slota {slot}!")

                                # [NOWE] Zabezpieczenie przed farmieniem (Capping na 1)
                                # Jeśli bot zbuduje 5 Rynków, to tec_mar i tak wyniesie 1, dając nagrodę tylko raz!
                                tec_blk = min(1, tec_blk)
                                tec_uni = min(1, tec_uni)
                                tec_cst = min(1, tec_cst)
                                tec_mar = min(1, tec_mar)
                                tec_mon = min(1, tec_mon)  # <--- TEGO ZABEZPIECZENIA BRAKOWAŁO

                                # Zliczamy Klasztor (+600) oraz Czas Relikwii (0.2 pkt za każdego "ticka" czasu - 10 min 1 relikwii to ok. +1200 pkt)
                                bonus_score = (max_mil * 1) + (max_age * max_age * 250) + (max_exp * 20) + (
                                            tec_blk * 100) + (tec_uni * 300) + (tec_cst * 1000) + (tec_mar * 1000) + (
                                                          tec_mon * 300) + (max_relics * 1000) + (win_flag * 5000)
                                penalty_score = lose_tc * 5000

                                scores.append({
                                    'base': base_score,
                                    'bonus': bonus_score,
                                    'penalty': penalty_score,
                                    'mil': max_mil,
                                    'age': max_age,
                                    'exp': max_exp,
                                    'win': win_flag,
                                    'tech': tec_blk + tec_uni + tec_cst + tec_mar + tec_mon,
                                    'lose_tc': lose_tc
                                })


                            except Exception:

                                # [NAPRAWIONE] Kompletny słownik ratunkowy

                                scores.append(
                                    {'base': 0, 'bonus': 0, 'penalty': 0, 'mil': 0, 'age': 0, 'exp': 0, 'win': 0,
                                     'tech': 0, 'lose_tc': 0})

                        all_workers_results[w_id] = scores
                        print(f"  -> Wyniki Workera {w_id}: pobrano pakiet danych telemetrycznych.")

                        try:
                            p.kill()
                        except Exception:
                            pass

                        active_workers.remove(worker)

            except Exception as e:
                p.kill()
                active_workers.remove(worker)

        time.sleep(0.3)

    for worker_id, p in processes:
        try:
            p.kill()
        except:
            pass

    os.system("taskkill /F /IM age2_x1.5.exe >nul 2>&1")
    os.system("taskkill /F /IM withdll.exe >nul 2>&1")

    all_raw_scores = []
    for i in range(1, workers_count + 1):
        all_raw_scores.extend(all_workers_results[i])

    return all_raw_scores