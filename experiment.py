import re
import os
import vlc
import json
import time
import queue
import pygame
import shutil
import random
import logging
import threading
import webbrowser
import pandas as pd
import tkinter as tk
from datetime import datetime
from model import AttentionModel 
from moviepy import VideoFileClip
from tkinter import font as tkfont
from typing import Text, Dict, List
 

class Experiment:
    def __init__(self, MOBY_DICK_PATH: Text="mobydick/moby_dick_1-6.pdf",
                 MEMES_PATH: Text="mobydick/memes/",
                 NUDGE_PATH: Text="mobydick/goalrelated_nudge.txt",
                 NUDGE_THRESHOLD: float=0.01, GRACE_PERIOD: int=60,
                 QUESTIONS_PATH: Text="mobydick/questions.json",
                 cap_visible: bool=False):
        # --- Paths & parameters ---
        self.MOBY_DICK_PATH = MOBY_DICK_PATH
        self.MEMES_PATH    = MEMES_PATH
        self.NUDGE_PATH    = NUDGE_PATH
        self.QUESTIONS_PATH = QUESTIONS_PATH
        self.NUDGE_THRESHOLD = NUDGE_THRESHOLD
        self.GRACE_PERIOD    = GRACE_PERIOD

        # --- State ---
        self.attn: float                     = 0.0
        self.last_nudge_ts: float            = 0.0
        self.nudge_queue: queue.Queue[float] = queue.Queue()
        
        # --- Tk root (hidden) & poll interval ---
        self.root = tk.Tk()
        self.root.withdraw()
        self.POLL_MS = 200

        # --- Model & logging setup ---
        self.cap_visible = cap_visible

        self.NUDGES = []
        self.LAST_NUDGE = None
        self.FLAG_TO_OPEN_NUDGE = False
        self.NUDGE_IS_OPEN = False
        self.attn_data = {}

        self.RAW_MEMES = [file for file in os.listdir(self.MEMES_PATH) if file.endswith(".mp4")]
        self.MEMES = [(file, re.sub(r'[\ufe00-\ufe0f]', '', file)) for file in self.RAW_MEMES]

        self.attn = 0

        self.cap_visible = cap_visible
    
    def start(self):
        try:
            self.initial_setup()
            webbrowser.open_new(f"file://{os.path.abspath(self.MOBY_DICK_PATH)}")
            # init pygame once
            pygame.mixer.init()
            # start measure thread
            threading.Thread(target=self._measure_loop, daemon=True).start()
            # start polling
            self.root.after(self.POLL_MS, self._poll_queue)
            self.root.mainloop()
        except:
            print("quitting...")
            self.model.stop_event.set()
        finally:
            self.reading_questions()

    def _measure_loop(self):
        """Worker thread: measures attention, enqueues nudge events."""
        gen = self.model.measure()
        self.last_nudge_ts = time.time()
        try:
            for attn_val in gen:
                if self.model.stop_event.is_set(): break
                self.attn = attn_val
                self.log_attn()
                now = time.time()
                if (now - self.last_nudge_ts > self.GRACE_PERIOD
                    and self.attn < self.NUDGE_THRESHOLD):
                    self.last_nudge_ts = now
                    # enqueue a nudge
                    if self.experiment_type != "3":
                        self.nudge_queue.put(self.experiment_type)
        finally:
            self.model.save()
            self.save_log_attn()

    def _poll_queue(self):
        """Main thread: check for events and display popups."""
        try:
            exp_type = self.nudge_queue.get_nowait()
        except queue.Empty:
            pass
        else:
            if exp_type == "1":
                self._show_text_nudge()
            elif exp_type == "2":
                self._show_meme()
        finally:
            self.root.after(self.POLL_MS, self._poll_queue)

    def _show_text_nudge(self):
        """Spawns Toplevel for text nudge with sound."""
        with open(self.NUDGE_PATH, 'r', encoding='utf-8') as f:
            nudges = f.readlines()
        nudge = random.choice(nudges)
        self.log(f"Nudge on:\n{nudge.strip()}")

        top = tk.Toplevel(self.root)
        self.NUDGE_IS_OPEN = True
        top.title("Attention Nudge")
        self._place_window_random(top, 600, 200)

        frame = tk.Frame(top, bg="#f0f0f0", padx=20, pady=20)
        frame.pack(fill="both", expand=True)
        tk.Label(
            frame, text=nudge.strip(),
            font=tkfont.Font(size=14, weight="bold"),
            wraplength=550, justify="center", bg="#f0f0f0"
        ).pack(expand=True)
        btn = tk.Button(frame, text="OK", width=10, command=lambda: cleanup())
        btn.pack(pady=10)

        def cleanup():
            pygame.mixer.music.stop()
            if top.winfo_exists():
                top.destroy()
            self.NUDGE_IS_OPEN = False
            self.log("Nudge off")

        top.protocol("WM_DELETE_WINDOW", cleanup)

        def sound_loop(window):
            pygame.mixer.music.load("mobydick/nudge.mp3")
            pygame.mixer.music.play(-1)   # loop indefinitely
            # block here until window closes
            while window.winfo_exists():
                time.sleep(0.1)
            # after loop exits, ensure stop
            pygame.mixer.music.stop()

        threading.Thread(target=sound_loop, args=(top,), daemon=True).start()

    def _show_meme(self):
        """Spawns Toplevel to play looping meme video."""
        file = random.choice(self.RAW_MEMES)
        path = os.path.join(self.MEMES_PATH, file)
        clip = VideoFileClip(path)

        top = tk.Toplevel(self.root)
        self.NUDGE_IS_OPEN = True
        top.title("Meme Nudge")
        w, h = clip.size
        sw = top.winfo_screenwidth()
        FIX_W = sw // 6
        FIX_H = int(h * (FIX_W / w))
        self._place_window_random(top, FIX_W, FIX_H + 40)

        instance = vlc.Instance('--no-video-title-show','--avcodec-hw=none')
        player = instance.media_player_new()
        media = instance.media_new(path)
        media.add_option('input-repeat=-1')
        player.set_media(media)

        frame = tk.Frame(top, width=FIX_W, height=FIX_H)
        frame.pack()
        top.update_idletasks()
        hwnd = frame.winfo_id()
        if os.name=='nt': player.set_hwnd(hwnd)
        else:             player.set_xwindow(hwnd)

        btn = tk.Button(top, text="OK", width=10, command=lambda: cleanup())
        btn.pack(pady=5)

        def cleanup():
            player.stop()
            if top.winfo_exists():
                top.destroy()
            self.NUDGE_IS_OPEN = False
            self.log("Meme Nudge off")

        top.protocol("WM_DELETE_WINDOW", cleanup)

        threading.Thread(target=lambda: player.play(), daemon=True).start()

    def _place_window_random(self, window, w, h):
        """Place `window` at a random on-screen position within bounds."""
        sw = window.winfo_screenwidth()
        sh = window.winfo_screenheight()
        # Compute safe ranges
        max_x = max(sw - w, 0)
        max_y = max(sh - h, 0)
        # Randomize
        x = random.randint(0, max_x)
        y = random.randint(0, max_y)
        window.geometry(f"{w}x{h}+{x}+{y}")

    def log(self, s):
        """Log a timestamped message."""
        self.logger.info(f"{datetime.now().strftime('%Y-%m-%d-%H-%M-%S')} - {s}")

    def log_attn(self):
        """Record attention + nudge state."""
        self.log(f"EXP: nudge = {self.nudge_queue.qsize()>0}, attn = {self.attn}")
        self.attn_data[time.time()] = (self.NUDGE_IS_OPEN, self.attn)

    def save_log_attn(self):
        """Dump attention log to CSV."""
        records = [
            {'timestamp': ts, 'nudge': nudge, 'attn': attn}
            for ts, (nudge, attn) in self.attn_data.items()
        ]
        df = pd.DataFrame(records)
        df.to_csv(f"{self.attn_save_path.removesuffix('.csv')}-2.csv", index=False)

    def initial_setup(self):
        """Prompt for initials/type, set up folders, logger, model."""
        def copy_nudge_file(nudge_path, initials: str, folder_name: str) -> str:
            if self.experiment_type != "1": pass
            new_nudge = f"{folder_name}/nudge_{initials}.txt"
            shutil.copy2(nudge_path, new_nudge)
            return new_nudge

        def setup_logger(self):
            fn = f"{self.folder_name}/experiment_{datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}_{self.initials}.log"
            logging.basicConfig(filename=fn, level=logging.INFO)
            return logging.getLogger(__name__)

        print("This is a research experiment on attention...")
        self.initials = "-".join(input("Enter your initials: ").upper().split())
        self.experiment_type = input("Experiment type (1/2/3): ")
        self.folder_name = f"collected_data/EX_{self.initials}_{self.experiment_type}"
        os.makedirs(self.folder_name, exist_ok=True)
        self.logger = setup_logger(self)

        if self.experiment_type == "1":
            input("Confirm nudge file is filled, then press Enter.")
            self.NUDGE_PATH = copy_nudge_file(self.NUDGE_PATH, self.initials, self.folder_name)

        self.attn_save_path = f"{self.folder_name}/attn_{datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}_{self.initials}.csv"
        self.model = AttentionModel(save_path=self.attn_save_path, cap_visible=self.cap_visible)

        input("Pre-experiment questionnaire done? Press Enter.")
        input("Ready to start? Press Enter.")
        print("Starting experiment...")

    def reading_questions(self):
        """Load JSON questions, prompt answers, log results."""
        self.log("Reading questions")
        with open(self.QUESTIONS_PATH, 'r') as f:
            questions = json.load(f)

        self.answers_list = []
        for chapter, qdict in questions.items():
            print(chapter, "\n")
            for idx, elem in enumerate(qdict.values()):
                print(elem["question"])
                print(elem["options"])
                ans = input("Enter your answer: ").upper().strip()
                if ans == "" or ans == "X":
                    self.log(f"{idx}. - Skipped")
                    self.answers_list.append(-1)
                elif ans == elem["correct"]:
                    self.log(f"{idx}. - Correct")
                    self.answers_list.append(1)
                else:
                    self.log(f"{idx}. - Incorrect")
                    self.answers_list.append(0)
                print()

        pd.DataFrame({
            'question_number': range(1, len(self.answers_list) + 1),
            'correct': self.answers_list
        }).to_csv(f"{self.folder_name}/questionnaire_{self.initials}.csv", index=False)
        self.log("Reading questions data saved")
        print(f"\nExperiment completed! Data saved in {self.folder_name}")


if __name__ == "__main__":
    exp = Experiment(GRACE_PERIOD=60, cap_visible=True)
    try:
        exp.start()
    except:
        print("something happened")
        exp.model.stop_event.set()
        exp.save_log_attn()
