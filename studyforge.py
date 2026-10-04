import json
import math
import tkinter as tk
from datetime import datetime
from tkinter import ttk, messagebox


# ============================================================
# STUDYFORGE — STUDY RATING APP
# ============================================================
#
# FORMULA
#
# base = hours
#        × (questions / 15)       if questions != 0
#        × lectures               if lectures != 0
#        × chapters               if chapters != 0
#        × days_since_previous
#
# Missing questions / lectures / chapters are NOT multiplied
# by zero. Instead, each omitted category applies a penalty.
#
# Penalty:
#     questions missing  -> × 0.50
#     lectures missing   -> × 0.50
#     chapters missing   -> × 0.50
#
# Therefore:
#
#     0 missing categories -> × 1
#     1 missing category    -> × 0.5
#     2 missing categories  -> × 0.25
#     3 missing categories  -> × 0.125
#
#
# RATING
#
# Today's rating is based on TODAY'S BASE compared to the
# TOTAL RATING BEFORE TODAY'S GAIN.
#
#     rating = base × sqrt(base / total_rating)
#
# For the first day, total_rating = 0, so:
#
#     rating = base
#
#
# WEEKDAY / WEEKEND
#
#     D (weekday) -> × 2
#     E (weekend) -> × 1
#
#
# TOTAL RATING
#
#     total_rating += today's rating
#
#
# RANK SYSTEM
#
# Every rank requires ADDITIONAL rating points.
#
# Requirements increase by 1 within a division.
# Entering a new division has an additional +2 increase.
#
# Example:
#
#     WOOD 1 -> WOOD 2 = 10
#     WOOD 2 -> WOOD 3 = 11
#     WOOD 3 -> COPPER 1 = 13
#     COPPER 1 -> COPPER 2 = 14
#     COPPER 2 -> COPPER 3 = 15
#     COPPER 3 -> BRASS 1 = 17
#
# ============================================================


DATA_FILE = "study_rating_data.json"


# ============================================================
# RANKS
# ============================================================

DIVISIONS = [
    "WOOD",
    "COPPER",
    "BRASS",
    "CARBON",
    "BRONZE",
    "SILVER",
    "GOLD",
    "PLATINUM",
    "SILICON",
    "DIAMOND",
    "ANTIMATTER",
]


DIVISION_SYMBOLS = {
    "WOOD": "🪵",
    "COPPER": "🔶",
    "BRASS": "🟡",
    "CARBON": "⬛",
    "BRONZE": "🥉",
    "SILVER": "🥈",
    "GOLD": "🥇",
    "PLATINUM": "💠",
    "SILICON": "◈",
    "DIAMOND": "◆",
    "ANTIMATTER": "✦",
}


# ============================================================
# RANK REQUIREMENTS
# ============================================================
#
# Each number is the ADDITIONAL rating required to promote.
#
# They increase by 1 inside a division.
#
# At the transition between divisions there is an additional
# +2 increase.
#
# Example:
#
# 10, 11, 13,
# 14, 15, 17,
# 18, 19, 21,
# ...
#
# ============================================================


RANK_REQUIREMENTS = []

current_requirement = 10

for division_index in range(len(DIVISIONS)):

    # Three promotions exist inside each division except
    # the final division.
    #
    # rank 1 -> rank 2
    # rank 2 -> rank 3
    # rank 3 -> next division rank 1

    for promotion in range(3):

        # The final rank, ANTIMATTER 3, has no promotion.
        if (
            division_index == len(DIVISIONS) - 1
            and promotion == 2
        ):
            break

        RANK_REQUIREMENTS.append(current_requirement)

        if promotion == 2:
            # New division: +2 instead of +1
            current_requirement += 2
        else:
            # Same division: +1
            current_requirement += 1


TOTAL_RANKS = len(DIVISIONS) * 3


# ============================================================
# RANK HELPERS
# ============================================================

def rank_from_index(index):

    if index >= TOTAL_RANKS:
        index = TOTAL_RANKS - 1

    if index < 0:
        index = 0

    division_index = index // 3
    rank = (index % 3) + 1

    return DIVISIONS[division_index], rank


def get_rank_progress(total_rating):

    if total_rating < 0:
        total_rating = 0

    remaining_rating = total_rating
    rank_index = 0

    for requirement in RANK_REQUIREMENTS:

        if remaining_rating < requirement:

            division, rank = rank_from_index(
                rank_index
            )

            return {
                "division": division,
                "rank": rank,
                "rank_index": rank_index,
                "progress": remaining_rating,
                "requirement": requirement,
                "remaining": requirement - remaining_rating,
                "maxed": False,
            }

        remaining_rating -= requirement
        rank_index += 1

    # ANTIMATTER 3
    division, rank = rank_from_index(
        TOTAL_RANKS - 1
    )

    return {
        "division": division,
        "rank": rank,
        "rank_index": TOTAL_RANKS - 1,
        "progress": 0,
        "requirement": 0,
        "remaining": 0,
        "maxed": True,
    }


# ============================================================
# DATA
# ============================================================

def load_data():

    try:

        with open(
            DATA_FILE,
            "r",
            encoding="utf-8"
        ) as f:

            data = json.load(f)

        if not isinstance(data, dict):
            raise ValueError

        data.setdefault(
            "entries",
            []
        )

        data.setdefault(
            "total_rating",
            0
        )

        return data

    except (
        FileNotFoundError,
        json.JSONDecodeError,
        ValueError
    ):

        return {
            "entries": [],
            "total_rating": 0
        }


def save_data(data):

    with open(
        DATA_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            data,
            f,
            indent=2
        )


# ============================================================
# FORMULA
# ============================================================

def calculate_base(
    hours,
    questions,
    lectures,
    chapters,
    day_difference
):

    if day_difference < 1:
        day_difference = 1

    base = hours

    # --------------------------------------------------------
    # Questions
    # --------------------------------------------------------

    if questions != 0:

        base *= questions / 15.0

    else:

        base *= 0.5


    # --------------------------------------------------------
    # Lectures
    # --------------------------------------------------------

    if lectures != 0:

        base *= lectures

    else:

        base *= 0.5


    # --------------------------------------------------------
    # Chapters
    # --------------------------------------------------------

    if chapters != 0:

        base *= chapters

    else:

        base *= 0.5


    # --------------------------------------------------------
    # Date difference
    # --------------------------------------------------------

    base *= day_difference

    return base


def calculate_rating(
    base,
    total_rating_before,
    day_type
):

    # First-ever rating
    if total_rating_before <= 0:

        rating = base

    else:

        ratio = base / total_rating_before

        rating = base * math.sqrt(
            ratio
        )


    # Weekday = 2×
    # Weekend = 1×
    if day_type == "D":

        rating *= 2

    else:

        rating *= 1


    return rating


# ============================================================
# APP
# ============================================================

class StudyRatingApp:

    BG = "#0b1020"
    PANEL = "#121a2d"
    PANEL_2 = "#18223a"
    TEXT = "#edf2ff"
    MUTED = "#8f9bb8"
    ACCENT = "#7c5cff"
    ACCENT_2 = "#35d0ba"
    RED = "#ff6b81"
    GOLD = "#ffd166"


    def __init__(self, root):

        self.root = root

        self.root.title(
            "StudyForge — Study Rating"
        )

        self.root.geometry(
            "1180x760"
        )

        self.root.minsize(
            1000,
            680
        )

        self.root.configure(
            bg=self.BG
        )

        self.data = load_data()

        self.entries = self.data.get(
            "entries",
            []
        )

        self.total_rating = float(
            self.data.get(
                "total_rating",
                0
            )
        )

        # Reconstruct old files if needed
        if "total_rating" not in self.data:

            self.total_rating = sum(
                entry.get(
                    "rating",
                    0
                )
                for entry in self.entries
            )

        self.setup_style()

        self.build_ui()

        self.refresh()


    # ========================================================
    # STYLE
    # ========================================================

    def setup_style(self):

        style = ttk.Style()

        style.theme_use("clam")

        style.configure(
            "TEntry",
            fieldbackground=self.PANEL_2,
            foreground=self.TEXT,
            insertcolor=self.TEXT,
            borderwidth=0,
            padding=10,
        )

        style.configure(
            "Accent.TButton",
            background=self.ACCENT,
            foreground="white",
            padding=(16, 11),
            borderwidth=0,
            font=(
                "Helvetica",
                11,
                "bold"
            ),
        )

        style.map(
            "Accent.TButton",
            background=[
                (
                    "active",
                    "#9278ff"
                )
            ]
        )


    # ========================================================
    # UI
    # ========================================================

    def build_ui(self):

        # ----------------------------------------------------
        # HEADER
        # ----------------------------------------------------

        header = tk.Frame(
            self.root,
            bg=self.BG,
            height=82
        )

        header.pack(
            fill="x",
            padx=28,
            pady=(22, 8)
        )

        tk.Label(
            header,
            text="STUDYFORGE",
            bg=self.BG,
            fg=self.TEXT,
            font=(
                "Helvetica",
                26,
                "bold"
            ),
        ).pack(
            side="left"
        )

        tk.Label(
            header,
            text="  turn study time into XP.",
            bg=self.BG,
            fg=self.MUTED,
            font=(
                "Helvetica",
                12
            ),
        ).pack(
            side="left",
            pady=(9, 0)
        )

        self.streak_top = tk.Label(
            header,
            text="🔥 0 day streak",
            bg=self.BG,
            fg=self.GOLD,
            font=(
                "Helvetica",
                13,
                "bold"
            ),
        )

        self.streak_top.pack(
            side="right",
            pady=10
        )


        # ----------------------------------------------------
        # MAIN
        # ----------------------------------------------------

        main = tk.Frame(
            self.root,
            bg=self.BG
        )

        main.pack(
            fill="both",
            expand=True,
            padx=28,
            pady=10
        )

        main.grid_columnconfigure(
            0,
            weight=3
        )

        main.grid_columnconfigure(
            1,
            weight=2
        )

        main.grid_rowconfigure(
            1,
            weight=1
        )


        # ----------------------------------------------------
        # HERO
        # ----------------------------------------------------

        hero = tk.Frame(
            main,
            bg=self.PANEL,
            height=170
        )

        hero.grid(
            row=0,
            column=0,
            columnspan=2,
            sticky="ew",
            pady=(0, 14)
        )

        hero.grid_propagate(False)

        self.badge = tk.Label(
            hero,
            text="?",
            bg=self.ACCENT,
            fg="white",
            font=(
                "Helvetica",
                30,
                "bold"
            ),
            width=4,
            height=2,
        )

        self.badge.pack(
            side="left",
            padx=22,
            pady=22
        )

        info = tk.Frame(
            hero,
            bg=self.PANEL
        )

        info.pack(
            side="left",
            fill="y",
            pady=20
        )

        self.rank_label = tk.Label(
            info,
            text="WOOD 1",
            bg=self.PANEL,
            fg=self.TEXT,
            font=(
                "Helvetica",
                23,
                "bold"
            ),
        )

        self.rank_label.pack(
            anchor="w"
        )

        self.threshold_label = tk.Label(
            info,
            text="10.00 rating to WOOD 2",
            bg=self.PANEL,
            fg=self.MUTED,
            font=(
                "Helvetica",
                10
            ),
        )

        self.threshold_label.pack(
            anchor="w",
            pady=(5, 0)
        )

        rating_box = tk.Frame(
            hero,
            bg=self.PANEL_2
        )

        rating_box.pack(
            side="right",
            padx=24,
            pady=20,
            ipadx=24,
            ipady=12
        )

        tk.Label(
            rating_box,
            text="TOTAL RATING",
            bg=self.PANEL_2,
            fg=self.MUTED,
            font=(
                "Helvetica",
                9,
                "bold"
            ),
        ).pack()

        self.rating_label = tk.Label(
            rating_box,
            text="0.00",
            bg=self.PANEL_2,
            fg=self.ACCENT_2,
            font=(
                "Helvetica",
                27,
                "bold"
            ),
        )

        self.rating_label.pack()


        # ----------------------------------------------------
        # INPUT CARD
        # ----------------------------------------------------

        input_card = tk.Frame(
            main,
            bg=self.PANEL
        )

        input_card.grid(
            row=1,
            column=0,
            sticky="nsew",
            padx=(0, 8)
        )

        input_card.grid_columnconfigure(
            0,
            weight=1
        )

        input_card.grid_columnconfigure(
            1,
            weight=1
        )

        tk.Label(
            input_card,
            text="TODAY'S STATS",
            bg=self.PANEL,
            fg=self.TEXT,
            font=(
                "Helvetica",
                15,
                "bold"
            ),
        ).grid(
            row=0,
            column=0,
            columnspan=2,
            sticky="w",
            padx=22,
            pady=(20, 4)
        )

        tk.Label(
            input_card,
            text="Study quantities may be integers or decimals.",
            bg=self.PANEL,
            fg=self.MUTED,
            font=(
                "Helvetica",
                9
            ),
        ).grid(
            row=1,
            column=0,
            columnspan=2,
            sticky="w",
            padx=22,
            pady=(0, 14)
        )


        self.vars = {}

        fields = [

            (
                "Hours studied",
                "hours",
                "e.g. 3.5"
            ),

            (
                "Lectures watched",
                "lectures",
                "e.g. 2"
            ),

            (
                "Questions done",
                "questions",
                "e.g. 45"
            ),

            (
                "Chapters completed",
                "chapters",
                "e.g. 0.5"
            ),

            (
                "Date",
                "date",
                "DD/MM/YY"
            ),

        ]


        row = 2

        for title, key, placeholder in fields:

            tk.Label(
                input_card,
                text=title,
                bg=self.PANEL,
                fg=self.TEXT,
                font=(
                    "Helvetica",
                    10,
                    "bold"
                ),
            ).grid(
                row=row,
                column=0,
                sticky="w",
                padx=(22, 10),
                pady=(8, 3)
            )

            var = tk.StringVar()

            self.vars[key] = var

            entry = ttk.Entry(
                input_card,
                textvariable=var
            )

            entry.grid(
                row=row + 1,
                column=0,
                sticky="ew",
                padx=(22, 10),
                pady=(0, 8)
            )

            tk.Label(
                input_card,
                text=placeholder,
                bg=self.PANEL,
                fg=self.MUTED,
                font=(
                    "Helvetica",
                    8
                ),
            ).grid(
                row=row + 1,
                column=1,
                sticky="w",
                padx=(0, 10)
            )

            row += 2


        # ----------------------------------------------------
        # E / D
        # ----------------------------------------------------

        tk.Label(
            input_card,
            text="E / D",
            bg=self.PANEL,
            fg=self.TEXT,
            font=(
                "Helvetica",
                10,
                "bold"
            ),
        ).grid(
            row=2,
            column=1,
            sticky="w",
            padx=(10, 10),
            pady=(8, 3)
        )

        self.day_type = tk.StringVar(
            value="D"
        )

        selector = tk.Frame(
            input_card,
            bg=self.PANEL
        )

        selector.grid(
            row=3,
            column=1,
            sticky="w",
            padx=(10, 10),
            pady=(0, 8)
        )

        for value, text in [
            ("D", "Weekday"),
            ("E", "Weekend")
        ]:

            tk.Radiobutton(
                selector,
                text=text,
                value=value,
                variable=self.day_type,
                bg=self.PANEL,
                fg=self.TEXT,
                selectcolor=self.PANEL_2,
                activebackground=self.PANEL,
                activeforeground=self.TEXT,
                font=(
                    "Helvetica",
                    9
                ),
            ).pack(
                side="left",
                padx=(0, 12)
            )


        ttk.Button(
            input_card,
            text="⚡  LOG STUDY DAY",
            style="Accent.TButton",
            command=self.submit,
        ).grid(
            row=13,
            column=0,
            columnspan=2,
            sticky="ew",
            padx=22,
            pady=(20, 20)
        )


        # ----------------------------------------------------
        # RIGHT SIDE
        # ----------------------------------------------------

        right = tk.Frame(
            main,
            bg=self.BG
        )

        right.grid(
            row=1,
            column=1,
            sticky="nsew",
            padx=(8, 0)
        )

        right.grid_rowconfigure(
            1,
            weight=1
        )


        # ----------------------------------------------------
        # PREVIOUS DAY
        # ----------------------------------------------------

        previous = tk.Frame(
            right,
            bg=self.PANEL
        )

        previous.grid(
            row=0,
            column=0,
            sticky="ew",
            pady=(0, 8)
        )

        tk.Label(
            previous,
            text="PREVIOUS DAY",
            bg=self.PANEL,
            fg=self.TEXT,
            font=(
                "Helvetica",
                13,
                "bold"
            ),
        ).pack(
            anchor="w",
            padx=18,
            pady=(16, 8)
        )

        self.previous_text = tk.Label(
            previous,
            text="No previous entry yet.",
            bg=self.PANEL,
            fg=self.MUTED,
            justify="left",
            anchor="w",
            font=(
                "Helvetica",
                9
            ),
        )

        self.previous_text.pack(
            fill="x",
            padx=18,
            pady=(0, 16)
        )


        # ----------------------------------------------------
        # DIVISION LADDER
        # ----------------------------------------------------

        flow = tk.Frame(
            right,
            bg=self.PANEL
        )

        flow.grid(
            row=1,
            column=0,
            sticky="nsew"
        )

        tk.Label(
            flow,
            text="DIVISION LADDER",
            bg=self.PANEL,
            fg=self.TEXT,
            font=(
                "Helvetica",
                13,
                "bold"
            ),
        ).pack(
            anchor="w",
            padx=18,
            pady=(12, 2)
        )

        tk.Label(
            flow,
            text="Your progression",
            bg=self.PANEL,
            fg=self.MUTED,
            font=(
                "Helvetica",
                9
            ),
        ).pack(
            anchor="w",
            padx=18
        )

        self.canvas = tk.Canvas(
            flow,
            bg=self.PANEL,
            highlightthickness=0
        )

        self.canvas.pack(
            fill="both",
            expand=True,
            padx=10,
            pady=8
        )

        self.canvas.bind(
            "<Configure>",
            lambda e: self.draw_flowchart()
        )


    # ========================================================
    # FLOWCHART
    # ========================================================

    def draw_flowchart(self):

        c = self.canvas

        c.delete("all")

        width = max(
            c.winfo_width(),
            300
        )

        height = max(
            c.winfo_height(),
            300
        )


        progress = get_rank_progress(
            self.total_rating
        )

        current_division = (
            progress["division"]
        )

        current_rank = (
            progress["rank"]
        )


        # ----------------------------------------------------
        # Compact responsive layout
        # ----------------------------------------------------

        # Keep the ladder inside the visible canvas.
        # The entire ladder is scaled according to the available
        # height and width.

        left_margin = 78
        right_margin = 8

        top_margin = 28
        bottom_margin = 8

        available_width = (
            width
            - left_margin
            - right_margin
        )

        available_height = (
            height
            - top_margin
            - bottom_margin
        )


        column_width = max(
            48,
            min(
                65,
                available_width / 3
            )
        )

        row_height = max(
            22,
            min(
                31,
                available_height / len(DIVISIONS)
            )
        )


        # ----------------------------------------------------
        # Column headers
        # ----------------------------------------------------

        for rank in range(1, 4):

            x = (
                left_margin
                + (rank - 0.5) * column_width
            )

            c.create_text(
                x,
                12,
                text=str(rank),
                fill=self.TEXT,
                font=(
                    "Helvetica",
                    9,
                    "bold"
                )
            )


        # ----------------------------------------------------
        # Division rows
        # ----------------------------------------------------

        for division_index, division in enumerate(
            DIVISIONS
        ):

            y = (
                top_margin
                + division_index * row_height
                + row_height / 2
            )


            # Division name

            c.create_text(
                left_margin - 8,
                y,
                text=division,
                anchor="e",
                fill=self.TEXT,
                font=(
                    "Helvetica",
                    7,
                    "bold"
                )
            )


            # ------------------------------------------------
            # Rank cells
            # ------------------------------------------------

            for rank in range(1, 4):

                x = (
                    left_margin
                    + (rank - 0.5)
                    * column_width
                )

                active = (
                    division
                    == current_division
                    and rank
                    == current_rank
                )


                # Small cells with lots of breathing room

                radius = (
                    7
                    if active
                    else 5
                )


                c.create_oval(
                    x - radius,
                    y - radius,
                    x + radius,
                    y + radius,
                    fill=(
                        self.ACCENT
                        if active
                        else "#33415f"
                    ),
                    outline=""
                )


                # Current rank ring

                if active:

                    c.create_oval(
                        x - radius - 3,
                        y - radius - 3,
                        x + radius + 3,
                        y + radius + 3,
                        outline=self.ACCENT,
                        width=1
                    )


            # ------------------------------------------------
            # Horizontal separator
            # ------------------------------------------------

            if (
                division_index
                < len(DIVISIONS) - 1
            ):

                line_y = (
                    y
                    + row_height / 2
                )

                c.create_line(
                    left_margin,
                    line_y,
                    left_margin
                    + 3 * column_width,
                    line_y,
                    fill="#263451",
                    width=1
                )


        # ----------------------------------------------------
        # Vertical separators
        # ----------------------------------------------------

        for i in range(4):

            x = (
                left_margin
                + i * column_width
            )

            c.create_line(
                x,
                top_margin - 5,
                x,
                top_margin
                + len(DIVISIONS)
                * row_height,
                fill="#263451",
                width=1
            )


        # ----------------------------------------------------
        # No scrolling required
        # ----------------------------------------------------

        c.configure(
            scrollregion=(
                0,
                0,
                width,
                height
            )
        )


    # ========================================================
    # PREVIOUS ENTRY
    # ========================================================

    def get_previous(self):

        if not self.entries:
            return None

        return self.entries[-1]


    # ========================================================
    # SUBMIT
    # ========================================================

    def submit(self):

        try:

            hours = float(
                self.vars["hours"].get()
            )

            lectures = float(
                self.vars["lectures"].get()
            )

            questions = float(
                self.vars["questions"].get()
            )

            chapters = float(
                self.vars["chapters"].get()
            )

            date_text = (
                self.vars["date"]
                .get()
                .strip()
            )


            # ------------------------------------------------
            # Validate date
            # ------------------------------------------------

            try:

                current_date = (
                    datetime.strptime(
                        date_text,
                        "%d/%m/%y"
                    ).date()
                )

            except ValueError:

                raise ValueError(
                    "Date must be entered in DD/MM/YY format.\n\n"
                    "Example: 16/08/26"
                )


            # ------------------------------------------------
            # Validate numbers
            # ------------------------------------------------

            values = [
                hours,
                lectures,
                questions,
                chapters
            ]

            if any(
                not math.isfinite(x)
                for x in values
            ):

                raise ValueError(
                    "Study values must be finite numbers."
                )

            if any(
                x < 0
                for x in values
            ):

                raise ValueError(
                    "Study quantities cannot be negative."
                )


            # ------------------------------------------------
            # Previous entry
            # ------------------------------------------------

            previous = self.get_previous()


            # ------------------------------------------------
            # Date difference
            # ------------------------------------------------

            if previous:

                previous_date = (
                    datetime.strptime(
                        previous["date"],
                        "%d/%m/%y"
                    ).date()
                )

                if current_date <= previous_date:

                    raise ValueError(
                        "The date must be after your previous entry "
                        f"({previous['date']})."
                    )

                day_difference = (
                    current_date
                    - previous_date
                ).days

            else:

                day_difference = 1


            # ------------------------------------------------
            # IMPORTANT:
            #
            # Save the total BEFORE today's rating.
            #
            # This is what the formula compares today's base
            # against.
            # ------------------------------------------------

            total_rating_before = (
                self.total_rating
            )


            # ------------------------------------------------
            # Calculate base
            # ------------------------------------------------

            base = calculate_base(
                hours,
                questions,
                lectures,
                chapters,
                day_difference
            )


            # ------------------------------------------------
            # Calculate rating
            # ------------------------------------------------

            daily_rating = calculate_rating(
                base,
                total_rating_before,
                self.day_type.get()
            )


            if not math.isfinite(
                daily_rating
            ):

                raise ValueError(
                    "The calculated rating is not finite."
                )


            # ------------------------------------------------
            # Add rating
            # ------------------------------------------------

            self.total_rating += (
                daily_rating
            )


            # ------------------------------------------------
            # Save entry
            # ------------------------------------------------

            entry = {

                "date":
                    current_date.strftime(
                        "%d/%m/%y"
                    ),

                "type":
                    self.day_type.get(),

                "hours":
                    hours,

                "lectures":
                    lectures,

                "questions":
                    questions,

                "chapters":
                    chapters,

                "day_difference":
                    day_difference,

                "base":
                    base,

                "rating":
                    daily_rating,

            }


            self.entries.append(
                entry
            )

            self.data["entries"] = (
                self.entries
            )

            self.data["total_rating"] = (
                self.total_rating
            )


            save_data(
                self.data
            )


            # ------------------------------------------------
            # Refresh
            # ------------------------------------------------

            self.refresh()


            # ------------------------------------------------
            # NO SUCCESS POPUP
            #
            # Just clear the input fields.
            # ------------------------------------------------

            for var in self.vars.values():

                var.set("")


        except ValueError as e:

            messagebox.showerror(
                "Check your input",
                str(e)
            )


    # ========================================================
    # REFRESH
    # ========================================================

    def refresh(self):

        progress = get_rank_progress(
            self.total_rating
        )


        # ----------------------------------------------------
        # Hero
        # ----------------------------------------------------

        division = (
            progress["division"]
        )

        rank = (
            progress["rank"]
        )


        self.badge.config(
            text=DIVISION_SYMBOLS[
                division
            ]
        )


        self.rank_label.config(
            text=f"{division} {rank}"
        )


        if progress["maxed"]:

            self.threshold_label.config(
                text=(
                    "MAX DIVISION — ANTIMATTER 3"
                )
            )

        else:

            self.threshold_label.config(
                text=(
                    f"{progress['remaining']:.2f} "
                    f"rating to next rank"
                )
            )


        self.rating_label.config(
            text=f"{self.total_rating:.2f}"
        )


        # ----------------------------------------------------
        # Streak
        # ----------------------------------------------------

        streak = (
            self.calculate_streak()
        )

        self.streak_top.config(
            text=f"🔥 {streak} day streak"
        )


        # ----------------------------------------------------
        # Previous entry
        # ----------------------------------------------------

        previous = (
            self.get_previous()
        )


        if previous:

            self.previous_text.config(

                text=(

                    f"{previous['date']}  •  "

                    f"{'Weekend' if previous['type'] == 'E' else 'Weekday'}\n"

                    f"Hours: "
                    f"{previous['hours']:g}\n"

                    f"Lectures: "
                    f"{previous['lectures']:g}\n"

                    f"Questions: "
                    f"{previous['questions']:g}\n"

                    f"Chapters: "
                    f"{previous['chapters']:g}\n"

                    f"Days since previous: "
                    f"{previous.get('day_difference', 1)}\n"

                    f"Base: "
                    f"{previous['base']:.2f}\n"

                    f"Rating gained: "
                    f"{previous['rating']:.2f}\n"

                    f"Total rating: "
                    f"{self.total_rating:.2f}"
                ),

                fg=self.TEXT
            )

        else:

            self.previous_text.config(
                text="No previous entry yet.",
                fg=self.MUTED
            )


        # ----------------------------------------------------
        # Ladder
        # ----------------------------------------------------

        self.draw_flowchart()


    # ========================================================
    # STREAK
    # ========================================================

    def calculate_streak(self):

        if not self.entries:
            return 0


        streak = 1


        for i in range(
            len(self.entries) - 1,
            0,
            -1
        ):

            current = datetime.strptime(
                self.entries[i]["date"],
                "%d/%m/%y"
            ).date()

            previous = datetime.strptime(
                self.entries[i - 1]["date"],
                "%d/%m/%y"
            ).date()


            if (
                current - previous
            ).days == 1:

                streak += 1

            else:

                break


        return streak


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    root = tk.Tk()

    app = StudyRatingApp(
        root
    )

    root.mainloop()
