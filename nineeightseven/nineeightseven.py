"""Welcome to Reflex! This file outlines the steps to create a basic app."""

from __future__ import annotations

import dataclasses
import enum
import random
from typing import Union

from reflex_global_hotkey import global_hotkey_watcher
from reflex_motion import animate_presence, motion
from reflex_swipe import swipeable

import reflex as rx
from reflex.vars.sequence import LiteralArrayVar

CELL = tuple[int, int]

GROUP = tuple[CELL, ...]
BOARD = tuple[GROUP, ...]


class Direction(enum.Enum):
    """Directions for the game."""

    UP = "ArrowUp"
    DOWN = "ArrowDown"
    LEFT = "ArrowLeft"
    RIGHT = "ArrowRight"


def pad_values(v: list[CELL]) -> GROUP:
    """Pad values with zeros."""
    if len(v) > BOARD_SIZE:
        raise ValueError(f"Values cannot have more than {BOARD_SIZE} elements.")
    return tuple(v + [(0, get_random_key()) for _ in range(BOARD_SIZE - len(v))])


def combine_values(group: GROUP) -> tuple[list[CELL], int]:
    """Combine values in a list."""
    values = list(filter(lambda cell: cell[0], group))

    new_values: list[CELL] = []
    values_counter = 0
    score = 0
    for i in range(len(values)):
        if values_counter == i + 1:
            continue
        values_counter = values_counter + 1
        if i + 1 < len(values):
            if values[i][0] == values[i + 1][0] == 1:
                new_values.append((2, values[i + 1][1]))
                values_counter = values_counter + 1
                score += 2
            elif abs(values[i][0] - values[i + 1][0]) == 1:
                new_values.append(
                    (max(values[i][0], values[i + 1][0]) + 1, values[i + 1][1])
                )
                score += values[i][0] + values[i + 1][0]
                values_counter = values_counter + 1
            else:
                new_values.append(values[i])
        else:
            new_values.append(values[i])

    return new_values, score


def reverse(group: GROUP) -> GROUP:
    """Reverse a group."""
    return group[::-1]


def ith_column(board: BOARD, i: int) -> GROUP:
    """Get the ith column of a board."""
    return tuple(board[j][i] for j in range(BOARD_SIZE))


def ith_row(board: BOARD, i: int) -> GROUP:
    """Get the ith row of a board."""
    return board[i]


def transpose(board: BOARD) -> BOARD:
    """Transpose a board."""
    return tuple(ith_column(board, i) for i in range(BOARD_SIZE))


def get_random_key() -> int:
    """Get a random key."""
    return random.randint(0, 1000000)


def insert_value_row(row: GROUP, i: int, value: int) -> GROUP:
    """Insert a value into a row."""
    random_value = get_random_key()

    return tuple((value, random_value) if i == j else row[j] for j in range(BOARD_SIZE))


def insert_value(board: BOARD, i: int, j: int, value: int) -> BOARD:
    """Insert a value into a board."""
    return tuple(
        insert_value_row(board[k], j, value) if i == k else board[k]
        for k in range(BOARD_SIZE)
    )


BOARD_SIZE = 4


@dataclasses.dataclass(
    frozen=True,
)
class TwentyFourtyEightBoard:
    """A 2048 board."""

    board: BOARD = tuple(
        tuple((0, get_random_key()) for _ in range(BOARD_SIZE))
        for _ in range(BOARD_SIZE)
    )

    def is_game_over(self) -> bool:
        """Check if the game is over."""
        return all(self.move(direction) is None for direction in Direction)

    def move(self, direction: Direction) -> tuple[TwentyFourtyEightBoard | None, int]:
        """Move the board in a direction."""
        match direction:
            case Direction.UP:
                board, score = self._move_up()
            case Direction.DOWN:
                board, score = self._move_down()
            case Direction.LEFT:
                board, score = self._move_left()
            case Direction.RIGHT:
                board, score = self._move_right()

        assert board is not None

        if self._just_values() == board._just_values():
            return None, 0
        return board, score

    def best_move(self, depth: int, breadth: int) -> tuple[Direction, int]:
        """Find the best move."""
        if self.is_game_over():
            return Direction.UP, -123456789
        best_score = -1
        best_direction = Direction.UP
        for direction in Direction:
            new_board, score = self.move(direction)
            if new_board is not None:
                if depth > 0:
                    average_additional_score = (
                        sum(
                            new_board.with_random_tile().best_move(depth - 1, breadth)[
                                1
                            ]
                            for _ in range(breadth)
                        )
                        // breadth
                    )
                    score += average_additional_score
                if score > best_score:
                    best_score = score
                    best_direction = direction
        return best_direction, best_score

    def _move_up(self) -> tuple[TwentyFourtyEightBoard, int]:
        new_board = []
        total_score = 0
        for i in range(BOARD_SIZE):
            values, score = combine_values(ith_column(self.board, i))
            total_score += score
            new_board.append(pad_values(values))

        return TwentyFourtyEightBoard(transpose(tuple(new_board))), total_score

    def _move_down(self) -> tuple[TwentyFourtyEightBoard, int]:
        new_board = []
        total_score = 0
        for i in range(BOARD_SIZE):
            values, score = combine_values(reverse(ith_column(self.board, i)))
            total_score += score
            new_board.append(reverse(pad_values(values)))

        return TwentyFourtyEightBoard(transpose(tuple(new_board))), total_score

    def _move_left(self) -> tuple[TwentyFourtyEightBoard | None, int]:
        new_board = []
        total_score = 0
        for i in range(BOARD_SIZE):
            values, score = combine_values(ith_row(self.board, i))
            total_score += score
            new_board.append(pad_values(values))

        return TwentyFourtyEightBoard(tuple(new_board)), total_score

    def _move_right(self) -> tuple[TwentyFourtyEightBoard | None, int]:
        new_board = []
        total_score = 0
        for i in range(BOARD_SIZE):
            values, score = combine_values(reverse(ith_row(self.board, i)))
            total_score += score
            new_board.append(reverse(pad_values(values)))

        return TwentyFourtyEightBoard(tuple(new_board)), total_score

    def _just_values(self) -> list[int]:
        return [cell[0] for row in self.board for cell in row]

    def with_random_tile(self) -> TwentyFourtyEightBoard:
        """Add a random tile to the board."""
        empty_tiles = [
            (i, j)
            for i in range(BOARD_SIZE)
            for j in range(BOARD_SIZE)
            if self.board[i][j][0] == 0
        ]
        if not empty_tiles:
            return self
        i, j = random.choice(empty_tiles)
        value = 1 if random.random() < 0.9 else 2

        return TwentyFourtyEightBoard(
            insert_value(self.board, i, j, value),
        )


class State(rx.State):
    """State for the game."""

    _board: TwentyFourtyEightBoard = TwentyFourtyEightBoard()
    score: int = 0

    @rx.event
    def on_load(self):
        """Load the game."""
        if all(cell[0] == 0 for row in self._board.board for cell in row):
            self._board = self._board.with_random_tile()
            self.score = 0
        # return State.computer_play

    @rx.event
    def on_reset(self):
        """Reset the game."""
        self._board = TwentyFourtyEightBoard().with_random_tile()
        self.score = 0

    @rx.var
    def is_lost(self) -> bool:
        """Check if the game is lost."""
        return self._board.is_game_over()

    @rx.var
    def board(self) -> list[list[tuple[int, int]]]:
        """Get the board."""
        return [list(row) for row in self._board.board]

    @rx.event
    def on_key(self, key):
        """Handle key press."""
        direction = {
            "ArrowUp": Direction.UP,
            "ArrowDown": Direction.DOWN,
            "ArrowLeft": Direction.LEFT,
            "ArrowRight": Direction.RIGHT,
        }[key]
        new_board, score = self._board.move(direction)
        if new_board is not None:
            self._board = new_board.with_random_tile()
            self.score += score

    @rx.event(background=True)
    async def computer_play(self):
        """Computer play."""
        async with self:
            self.on_key(self._board.best_move(depth=3, breadth=4)[0].value)
            yield
        # await asyncio.sleep(0.5)
        yield State.computer_play


colors = [
    ["#FFE0C2", "#000000"],
    ["#FFA500", "#000000"],
    ["#FF4500", "#FFFFFF"],
    ["#800080", "#FFFF00"],
    ["#FFD700", "#000000"],
    ["#4B0082", "#FFFFFF"],
    ["#A52A2A", "#FFFFFF"],
    ["#228B22", "#FFFFFF"],
    ["#C71585", "#FFFFFF"],
    ["#FF6347", "#FFFFFF"],
    ["#FF8C00", "#000000"],
    ["#2E8B57", "#FFFFFF"],
    ["#800000", "#FFFFFF"],
    ["#D2691E", "#FFFFFF"],
    ["#DAA520", "#000000"],
    ["#DC143C", "#FFFFFF"],
    ["#4B0082", "#FFD700"],
    ["#808080", "#FFFFFF"],
    ["#F0E68C", "#000000"],
    ["#FF1493", "#FFFFFF"],
]


def generate_fibonacci(n: int) -> list[int]:
    """Generate Fibonacci sequence."""
    a, b = 1, 1
    result = [a, b]
    for _ in range(n - 2):
        a, b = b, a + b
        result.append(b)
    return result


fibonacci = generate_fibonacci(30)
fibonacci_var = rx.vars.LiteralArrayVar.create(fibonacci)

SQUARE_SIZE = "min(100px, 20vw)"
GAP_SIZE = "min(10px, 2vw)"


def svg_logo(color: Union[str, rx.Var[str]] = rx.color_mode_cond("#110F1F", "white")):
    """A Reflex logo SVG.

    Args:
        color: The color of the logo.

    Returns:
        The Reflex logo SVG.
    """

    def logo_path(d):
        return rx.el.svg.path(
            d=d,
        )

    paths = [
        "M0 11.5999V0.399902H8.96V4.8799H6.72V2.6399H2.24V4.8799H6.72V7.1199H2.24V11.5999H0ZM6.72 11.5999V7.1199H8.96V11.5999H6.72Z",
        "M11.2 11.5999V0.399902H17.92V2.6399H13.44V4.8799H17.92V7.1199H13.44V9.3599H17.92V11.5999H11.2Z",
        "M20.16 11.5999V0.399902H26.88V2.6399H22.4V4.8799H26.88V7.1199H22.4V11.5999H20.16Z",
        "M29.12 11.5999V0.399902H31.36V9.3599H35.84V11.5999H29.12Z",
        "M38.08 11.5999V0.399902H44.8V2.6399H40.32V4.8799H44.8V7.1199H40.32V9.3599H44.8V11.5999H38.08Z",
        "M47.04 4.8799V0.399902H49.28V4.8799H47.04ZM53.76 4.8799V0.399902H56V4.8799H53.76ZM49.28 7.1199V4.8799H53.76V7.1199H49.28ZM47.04 11.5999V7.1199H49.28V11.5999H47.04ZM53.76 11.5999V7.1199H56V11.5999H53.76Z",
    ]

    return rx.el.svg(
        *[logo_path(d) for d in paths],
        width="56",
        height="12",
        viewBox="0 0 56 12",
        fill=color,
        xmlns="http://www.w3.org/2000/svg",
    )


def render_tile(value: int, key: int, i: int, j: int):
    """Render a tile."""
    text = fibonacci_var[value]

    style = rx.Style(
        {
            "width": f"{SQUARE_SIZE}",
            "height": f"{SQUARE_SIZE}",
            "border_radius": "5px",
            "display": "flex",
            "justify_content": "center",
            "align_items": "center",
            "font_size": "min(36px, 6vw)",
            "color": "black",
            "position": "absolute",
            "top": f"calc({i} * ({SQUARE_SIZE} + {GAP_SIZE}))",
            "left": f"calc({j} * ({SQUARE_SIZE} + {GAP_SIZE}))",
            "z_index": value,
        }
    )

    return motion(
        rx.cond(
            value == 0,
            "",
            text,
        ),
        key=key,
        layout=value != 0,
        transition={
            "delay": 0.2,
            "duration": 0.2,
            "ease": "easeInOut",
            "layout": {"delay": 0},
            "exit": {"delay": 0.2},
        },
        initial=rx.cond(
            value == 0,
            {},
            {
                "opacity": 0,
                "scale": 0,
            },
        ),
        animate=rx.cond(
            value == 0,
            {},
            {
                "opacity": 1,
                "scale": 1,
            },
        ),
        exit=rx.cond(
            value == 0,
            {},
            {
                "opacity": [1, 1, 0],
                "scale": [1, 1.25, 0],
            },
        ),
        background_color=rx.match(
            value,
            *[(i, color) for i, (color, _) in enumerate(colors)],
            "#FF1493",
        ),
        color=rx.match(
            value,
            *[(i, color) for i, (_, color) in enumerate(colors)],
            "#ffffff",
        ),
        style=style,
    )


def color_mode_switcher():
    """Color mode switcher."""
    return rx.color_mode_cond(
        rx.icon_button(
            "sun",
            variant="outline",
            color_scheme="purple",
            size="4",
            on_click=rx.toggle_color_mode,
        ),
        rx.icon_button(
            "moon",
            variant="outline",
            color_scheme="purple",
            size="4",
            on_click=rx.toggle_color_mode,
        ),
    )


def reset_button():
    """Reset button."""
    return rx.icon_button(
        "rotate_ccw",
        variant="outline",
        color_scheme="purple",
        size="4",
        on_click=State.on_reset,
    )


def built_with_reflex():
    """Built with Reflex."""
    return rx.link(
        rx.hstack(
            "Built with ",
            svg_logo(),
            align="center",
            justify="center",
        ),
        href="https://reflex.dev",
        target="_blank",
        font_family="monospace",
        margin_block_start="1em",
        width="100%",
    )


def source_code():
    """Source code link."""
    return rx.link(
        "Source code on GitHub",
        href="https://github.com/adhami3310/987",
        target="_blank",
        font_family="monospace",
        width="100%",
        text_align="center",
    )


def board():
    """Get the board."""
    return swipeable(
        animate_presence(
            rx.foreach(
                rx.Var.range(BOARD_SIZE**2),
                lambda x: render_tile(
                    State.board[x // BOARD_SIZE][x % BOARD_SIZE][0],
                    State.board[x // BOARD_SIZE][x % BOARD_SIZE][1],
                    x // BOARD_SIZE,
                    x % BOARD_SIZE,
                ),
            )
        ),
        position="relative",
        width=f"calc({BOARD_SIZE} * {SQUARE_SIZE} + {GAP_SIZE} * ({BOARD_SIZE} - 1))",
        height=f"calc({BOARD_SIZE} * {SQUARE_SIZE} + {GAP_SIZE} * ({BOARD_SIZE} - 1))",
        on_swiped_left=State.on_key("ArrowLeft"),
        on_swiped_right=State.on_key("ArrowRight"),
        on_swiped_up=State.on_key("ArrowUp"),
        on_swiped_down=State.on_key("ArrowDown"),
    )


def index() -> rx.Component:
    """Index page."""
    return rx.fragment(
        rx.vstack(
            rx.center(
                rx.vstack(
                    rx.hstack(
                        motion(
                            rx.heading("Score: ", State.score, size="8"),
                        ),
                        rx.hstack(
                            color_mode_switcher(),
                            reset_button(),
                        ),
                        width="100%",
                        align="center",
                        justify="between",
                    ),
                    board(),
                    built_with_reflex(),
                    source_code(),
                ),
                width="100%",
                min_height="100dvh",
                font_family="Helvetica",
                font_weight="bold",
            ),
            background_color=rx.color_mode_cond("#fffaf7", "#2d3748"),
            color=rx.color_mode_cond("#57331b", "#edf2f7"),
        ),
        global_hotkey_watcher(
            on_key_down=lambda key: rx.cond(
                LiteralArrayVar.create(
                    ["ArrowUp", "ArrowDown", "ArrowLeft", "ArrowRight"]
                ).contains(key),
                State.on_key(key),
                rx.noop(),
            )
        ),
    )


app = rx.App(
    theme=rx.theme(
        color_mode="light",
    ),
    stylesheets=[
        "style.css",
    ],
)
app.add_page(index, on_load=State.on_load, title="987")
