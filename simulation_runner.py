import os
import shutil
import subprocess
import time
import random
from config import *
import ctypes
import msgpackrpc
import threading


def arrange_windows(workers_count):
    """Automatycznie układa okna gry w siatkę wizualną na monitorze panoramicznym."""
    print("[*] Układanie okien na monitorze...")
    EnumWindows = ctypes.windll.user32.EnumWindows
    EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int))
    GetWindowText = ctypes.windll.user32.GetWindowTextW
    GetWindowTextLength = ctypes.windll.user32.GetWindowTextLengthW
    IsWindowVisible = ctypes.windll.user32.IsWindowVisible
    MoveWindow = ctypes.windll.user32.MoveWindow

    # [NOWE] Importujemy funkcję do "klikania" (aktywacji) okna
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

    width = 3200 // 4
    height = 1800 // 3

    for i, hwnd in enumerate(hwnds[:workers_count]):
        row = i // 4
        col = i % 4
        MoveWindow(hwnd, col * width, row * height, width, height, True)

        # [NOWE] Symulujemy kliknięcie użytkownika, by wybudzić silnik
        SetForegroundWindow(hwnd)
        time.sleep(0.05)  # Dajemy silnikowi pół sekundy na załadowanie DirectX w pełnym skupieniu

def emergency_wake_up():
    """Błyskawiczne, awaryjne 'szturchnięcie' wszystkich okien, by wybudzić zahibernowany DirectX."""
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
    print("\n[*] Weryfikacja struktury wielowątkowej (Workerów)...")
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
                symlinks=False,  # Kopiujemy twarde pliki modyfikacji, eliminując błąd uprawnień 1314
                ignore_dangling_symlinks=True,
                ignore=shutil.ignore_patterns('SaveGame', 'Screenshots', 'Campaign')
            )

        # Przygotowanie folderów na logi wewnątrz oficjalnych struktur
        logs_folders = [
            os.path.join(worker_path, "AI", "Logs"),  # <--- POPRAWIONE (Katalog główny AI)
            os.path.join(worker_path, "Age2_x1", "Script.AI", "Logs"),  # Główny folder zapisu dla silnika 1.5c
            os.path.join(worker_path, "Games", "WololoKingdoms", "Script.AI", "Logs")  # <--- WK zostaje bez zmian
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

    print(f"[*] Uruchamianie {workers_count} niezależnych instancji dla {population_size} botów...")

    for i in range(1, workers_count + 1):
        worker_dir = os.path.join(WORKERS_DIR, f"Worker_{i}")
        worker_port = BASE_PORT + i

        # Rotacja map ewolucyjnych (od 1 do 50) i ujednolicanie nazwy docelowej
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

        worker_exe = os.path.join(
            cwd_path,
            "age2_x1.5.exe"
        )

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
            #"-load", "TestEvo",
            "-autogameport", str(worker_port)
        ]

        cwd_path = os.path.join(worker_dir, "Age2_x1")

        print(f"[DEBUG] cwd_path = {cwd_path}")
        print(f"[DEBUG] worker_exe = {worker_exe}")
        print(f"[DEBUG] worker_exe = {worker_exe}")

        full_exe_path = os.path.join(cwd_path, worker_exe)

        print(f"[DEBUG] full_exe_path = {full_exe_path}")
        print(f"[DEBUG] EXISTS? {os.path.exists(full_exe_path)}")

        p = subprocess.Popen(cmd, cwd=cwd_path)
        processes.append((i, p))
        rpc_clients.append((i, worker_port))

        time.sleep(0.05)

    print("[*] Oczekiwanie na uruchomienie pętli silników w oknach (8 sekund)...")
    time.sleep(0.2)

    arrange_windows(workers_count)

    print("[*] Przejmowanie sieciowej kontroli - Wielowątkowy zrzut rozkazów...")

    # [NOWE] Zamykamy logikę konfiguracji w funkcji, aby móc odpalić ją równolegle
    def configure_worker(worker_id, port):
        try:
            client = msgpackrpc.Client(msgpackrpc.Address("127.0.0.1", port))

            connection_established = False
            for attempt in range(100):  # 10 sekund marginesu
                try:
                    client.call('GetGameTime')
                    connection_established = True
                    break
                except Exception:
                    time.sleep(0.1)

            if not connection_established:
                print(f"  [!] CRASH: Worker {worker_id} nie otworzył portu {port} na czas.")
                return

            print(f"RPC OK dla Portu {port} - Serwer połączony!")

            client.call('ResetGameSettings')
            client.call('SetGameType', 3)
            client.call('SetGameScenarioName', 'TestEvo')

            for bot_slot in range(1, 9):
                client.call('SetPlayerComputer', bot_slot, f"Milibot_Evo_{bot_slot}")

            client.call('SetRunFullSpeed', True)
            client.call('SetRunUnfocused', True)
            client.call('SetUseInGameResolution', False)

            # Komenda startu - teraz każdy wątek czeka niezależnie!
            client.call('StartGame')

            print(f"  -> Worker {worker_id} (Port {port}): Konfiguracja zakończona. Symulacja rusza!")
        except Exception as e:
            print(f"  [!] Błąd logiki RPC dla Workera {worker_id} na porcie {port}: {e}")

    # [NOWE] Uruchamianie wątków uderzeniowych
    threads = []
    for worker_id, port in rpc_clients:
        t = threading.Thread(target=configure_worker, args=(worker_id, port))
        threads.append(t)
        t.start()

    # Czekamy ułamek sekundy, aż wszystkie wątki skończą inicjalizację
    for t in threads:
        t.join()

    print("[*] Wszystkie instancje odłączone od czasu rzeczywistego. Trwa ewolucja.")

    # [NOWE] Kontrolne kliknięcie ubezpieczające (Zero opóźnień time.sleep!)
    print("[*] Wykonuję awaryjne wybudzanie okien (Sweep)...")
    emergency_wake_up()

    # [NOWE] Globalny słownik trzymający wyniki z RAM-u
    all_workers_results = {i: [0] * BOTS_PER_MATCH for i in range(1, workers_count + 1)}

    # Tworzymy obiekty klientów RPC dla wszystkich procesów
    active_workers = []
    for worker_id, port in rpc_clients:
        client = msgpackrpc.Client(msgpackrpc.Address("127.0.0.1", port))
        active_workers.append({
            'id': worker_id,
            'client': client,
            'process': processes[worker_id - 1][1],
            'has_started': False,
            'loading_start': time.time()
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

                # Faza 1: Ekran ładowania
                if not worker['has_started']:
                    if in_progress or game_time > 0:
                        worker['has_started'] = True
                        print(f"[Radar] Worker {w_id} załadował mapę! Silnik ruszył.")
                    elif time.time() - worker['loading_start'] > 60:
                        print(f"  [!] Worker {w_id} zawiesił się na ładowaniu. Ubijam.")
                        p.kill()
                        active_workers.remove(worker)

                # Faza 2: Radar
                else:
                    print(f"[Radar] Worker {w_id} | W grze: {in_progress} | Czas gry: {game_time} sekund")

                    # [PRZEŁOM] Jeśli boty zrobiły resign lub minął czas - rwiemy dane przez RPC!
                    if not in_progress or game_time > MATCH_DURATION + 10:
                        print(f"[*] Worker {w_id} zakończył mecz! Pobieram punkty z RAM-u...")

                        scores = []
                        for slot in range(1, BOTS_PER_MATCH + 1):
                            try:
                                score = client.call('GetPlayerScore', slot)
                                scores.append(score)
                            except Exception:
                                scores.append(0)

                        all_workers_results[w_id] = scores
                        print(f"  -> Wyniki Workera {w_id}: {scores}")

                        # [NOWE] Błyskawiczna egzekucja procesu z pominięciem procedur silnika
                        try:
                            p.kill()
                        except Exception:
                            pass

                        active_workers.remove(worker)

            except Exception as e:
                p.kill()
                active_workers.remove(worker)

        time.sleep(0.3)

    # Sprzątanie okien bez opóźnień
    for worker_id, p in processes:
        try:
            p.kill()
        except:
            pass

    print("[*] Twardy reset procesów gry na koniec generacji...")
    os.system("taskkill /F /IM age2_x1.5.exe >nul 2>&1")
    os.system("taskkill /F /IM withdll.exe >nul 2>&1")

    print("[*] Zakończono generację. Przetwarzanie wyników...")

    # [NOWE] Zbieranie odczytanych punktów do jednej listy
    all_raw_scores = []
    for i in range(1, workers_count + 1):
        all_raw_scores.extend(all_workers_results[i])

    return all_raw_scores