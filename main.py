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

with open("sprites/rocket_frame_1.txt", "r") as my_file:
    rocket_1 = my_file.read()

with open("sprites/rocket_frame_2.txt", "r") as my_file:
    rocket_2 = my_file.read()

frames = [rocket_1, rocket_2]

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
    x_max, y_max = canvas.getmaxyx()
    for text in cycle(frames):
        draw_frame(canvas, start_row, start_column, text, negative=False)
        await asyncio.sleep(0)
        draw_frame(canvas, start_row, start_column, text, negative=True)
        canvas.nodelay(True)
        rows_direction, columns_direction, space_pressed = read_controls(canvas)
        row_add, column_add = get_frame_size(text)
        start_row += rows_direction
        start_column += columns_direction
        if start_row <=0:
            start_row -= rows_direction
        if start_row + row_add >= x_max:
            start_row -=rows_direction
        if start_column <=0:
            start_column -= columns_direction
        if start_column + column_add >= y_max:
            start_column -= columns_direction


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

async def blink(canvas, row, column, symbol='*'):
    rand = random.randint(0,31)
    while True:
        canvas.addstr(row, column, symbol, curses.A_DIM)
        for _ in range(20):
            await asyncio.sleep(0)
        for _ in range(rand):
            await asyncio.sleep(0)

        canvas.addstr(row, column, symbol)
        for _ in range(3):
            await asyncio.sleep(0)
        for _ in range(rand):
            await asyncio.sleep(0)

        canvas.addstr(row, column, symbol, curses.A_BOLD)
        for _ in range(5):
            await asyncio.sleep(0)
        for _ in range(rand):
            await asyncio.sleep(0)

        canvas.addstr(row, column, symbol)
        for _ in range(3):
            await asyncio.sleep(0)
        for _ in range(rand):
            await asyncio.sleep(0)

def coroutine_maker(canvas, x_max, y_max):
    number_stars = random.randint(50,200)
    symbols = ['*', "+", ".", ":"]
    d = {}
    for i in range(0,number_stars):
        x_random = random.randint(2, x_max-2)
        y_random = random.randint(2, y_max-2)
        rand_symbol = random.choice(symbols)
        d["star_{0}".format(i)] = blink(canvas, x_random, y_random, symbol=rand_symbol)
    coroutines = []
    for key in d.keys():
        coroutines.append(d[key])
    return coroutines

def draw(canvas):
    with open("sprites/rocket_frame_1.txt", "r") as my_file:
        rocket_1 = my_file.read()

    with open("sprites/rocket_frame_2.txt", "r") as my_file:
        rocket_2 = my_file.read()

    frames = [rocket_1, rocket_2]
    curses.curs_set(False)
    #row, column = (5, 20)
    x_max, y_max = canvas.getmaxyx()
    canvas.border()
    coroutines = coroutine_maker(canvas, x_max, y_max)
    fire_ball = fire(canvas, x_max/2, y_max/2, rows_speed=-0.3, columns_speed=0)
    spaceship = animate_spaceship(canvas, x_max/2-0.5, y_max/2-2, frames)
    coroutines.append(fire_ball)
    coroutines.append(spaceship)
    while True:
        for coroutine in coroutines.copy():
            try:
                coroutine.send(None)
            except StopIteration:
                coroutines.remove(coroutine)
        canvas.refresh()
        time.sleep(TIC_TIMEOUT)
        if len(coroutines) == 0:
            break

if __name__ == '__main__':
    curses.update_lines_cols()
    curses.wrapper(draw)