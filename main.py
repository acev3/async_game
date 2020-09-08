import time
import curses
import asyncio
import random
from itertools import cycle

TIC_TIMEOUT = 0.01

SPACE_KEY_CODE = 32
LEFT_KEY_CODE = 260
RIGHT_KEY_CODE = 261
UP_KEY_CODE = 259
DOWN_KEY_CODE = 258

def read_controls(canvas):
    """Read keys pressed and returns tuple witl controls state."""

    rows_direction = columns_direction = 0
    space_pressed = False

    while True:
        pressed_key_code = canvas.getch()

        if pressed_key_code == -1:
            # https://docs.python.org/3/library/curses.html#curses.window.getch
            break

        if pressed_key_code == UP_KEY_CODE:
            rows_direction = -1

        if pressed_key_code == DOWN_KEY_CODE:
            rows_direction = 1

        if pressed_key_code == RIGHT_KEY_CODE:
            columns_direction = 1

        if pressed_key_code == LEFT_KEY_CODE:
            columns_direction = -1

        if pressed_key_code == SPACE_KEY_CODE:
            space_pressed = True

    return rows_direction, columns_direction, space_pressed


def draw_frame(canvas, start_row, start_column, text, negative=False):
    """Draw multiline text fragment on canvas, erase text instead of drawing if negative=True is specified."""

    rows_number, columns_number = canvas.getmaxyx()

    for row, line in enumerate(text.splitlines(), round(start_row)):
        if row < 0:
            continue

        if row >= rows_number:
            break

        for column, symbol in enumerate(line, round(start_column)):
            if column < 0:
                continue

            if column >= columns_number:
                break

            if symbol == ' ':
                continue

            # Check that current position it is not in a lower right corner of the window
            # Curses will raise exception in that case. Don`t ask why…
            # https://docs.python.org/3/library/curses.html#curses.window.addch
            if row == rows_number - 1 and column == columns_number - 1:
                continue

            symbol = symbol if not negative else ' '
            canvas.addch(row, column, symbol)


def get_frame_size(text):
    """Calculate size of multiline text fragment, return pair — number of rows and colums."""

    lines = text.splitlines()
    rows = len(lines)
    columns = max([len(line) for line in lines])
    return rows, columns

async def animate_spaceship(canvas, start_row, start_column, frames):

    height, width = canvas.getmaxyx()
    for text in cycle(frames):
        draw_frame(canvas, start_row, start_column, text, negative=False)
        await asyncio.sleep(0)
        draw_frame(canvas, start_row, start_column, text, negative=True)
        rows_direction, columns_direction, space_pressed = read_controls(canvas)
        frame_height, frame_width = get_frame_size(text)
        start_row += rows_direction
        start_column += columns_direction
        start_row = max(1,min(start_row, height - frame_height -1))
        start_column = max(1,min(start_column, width - frame_width -1))

async def fire(canvas, start_row, start_column, rows_speed=-0.3, columns_speed=0):
    """Display animation of gun shot, direction and speed can be specified."""

    row, column = start_row, start_column

    canvas.addstr(round(row), round(column), '*')
    await asyncio.sleep(0)

    canvas.addstr(round(row), round(column), 'O')
    await asyncio.sleep(0)
    canvas.addstr(round(row), round(column), ' ')

    row += rows_speed
    column += columns_speed

    symbol = '-' if columns_speed else '|'

    rows, columns = canvas.getmaxyx()
    max_row, max_column = rows - 1, columns - 1

    curses.beep()

    while 0 < row < max_row and 0 < column < max_column:
        canvas.addstr(round(row), round(column), symbol)
        await asyncio.sleep(0)
        canvas.addstr(round(row), round(column), ' ')
        row += rows_speed
        column += columns_speed

async def blink(canvas, row, column, delay, symbol='*'):
    while True:
        canvas.addstr(row, column, symbol, curses.A_DIM)
        for _ in range(delay):
            await asyncio.sleep(0)

        canvas.addstr(row, column, symbol)
        for _ in range(delay):
            await asyncio.sleep(0)

        canvas.addstr(row, column, symbol, curses.A_BOLD)
        for _ in range(delay):
            await asyncio.sleep(0)

        canvas.addstr(row, column, symbol)
        for _ in range(delay):
            await asyncio.sleep(0)

def create_coroutines(canvas, height, width, border_width):
    stars_number = random.randint(50,200)
    symbols = ['*', "+", ".", ":"]
    coroutines = []
    for _ in range(0,stars_number):
        random_x = random.randint(border_width, height - border_width)
        random_y = random.randint(border_width, width - border_width)
        rand_symbol = random.choice(symbols)
        offset_tics = random.randint(1, 30)
        coroutines.append(blink(canvas, random_x, random_y, offset_tics, symbol=rand_symbol))
    return coroutines

def draw(canvas):
    with open("sprites/rocket_frame_1.txt", "r") as my_file:
        rocket_1 = my_file.read()

    with open("sprites/rocket_frame_2.txt", "r") as my_file:
        rocket_2 = my_file.read()

    frames = [rocket_1, rocket_1, rocket_2, rocket_2]
    curses.curs_set(False)
    # getmaxyx() возвращает ширину и высоту окна, а не крайние координаты
    height, width = canvas.getmaxyx()
    canvas.border()
    canvas.nodelay(True)
    border_width = 2
    coroutines = create_coroutines(canvas, height, width, border_width)
    fire_ball = fire(canvas, height/2, width/2, rows_speed=-0.3, columns_speed=0)
    spaceship = animate_spaceship(canvas, height/2-0.5, width/2-2, frames)
    coroutines.append(fire_ball)
    coroutines.append(spaceship)
    while coroutines:
        for coroutine in coroutines.copy():
            try:
                coroutine.send(None)
            except StopIteration:
                coroutines.remove(coroutine)
        canvas.refresh()
        time.sleep(TIC_TIMEOUT)

if __name__ == '__main__':
    curses.update_lines_cols()
    curses.wrapper(draw)