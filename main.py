import time
import asyncio
import curses
import random
from curses_tools import draw_frame, read_controls, get_frame_size
from physics import update_speed
from obstacles import Obstacle
from explosion import explode
from game_scenario import get_garbage_delay_tics, PHRASES


TIC_TIMEOUT = 0.02
STARS_SYMBOLS = "+*.:"
NUMBER_STARS = 100
LEVEL_TICS = 50

year = 1957

coroutines = []
obstacles = []
obstacles_in_last_collisions = []


async def show_gameover(canvas, row, column):  
    with open("sprites/game_over.txt", "r") as f:
          game_over_frame = f.read()
    while True:
        draw_frame(canvas, row, column, game_over_frame, negative=False)
        await sleep(1)


async def blink(canvas, row, column, symbol="*"):
    """Blink functiton for the sky animations"""
    ticks_before_start = random.randint(0, 10)
    ticks_with_dim = 20
    ticks_with_original_1 = 3
    ticks_with_bold = 3
    ticks_with_original_2 = 5
    while True:
        await sleep(ticks_before_start)
        canvas.addstr(row, column, symbol, curses.A_DIM)
        await sleep(ticks_with_dim)
        canvas.addstr(row, column, symbol)
        await sleep(ticks_with_original_1)
        canvas.addstr(row, column, symbol, curses.A_BOLD)
        await sleep(ticks_with_bold)
        canvas.addstr(row, column, symbol)
        await sleep(ticks_with_original_2)


async def fire(canvas, start_row, start_column, rows_speed=-1, columns_speed=0):
    """Display animation of gun shot. Direction and speed can be specified."""
    global coroutines, obstacles, obstacles_in_last_collisions
    row, column = start_row, start_column
    canvas.addstr(round(row), round(column), "*")
    await asyncio.sleep(0)
    canvas.addstr(round(row), round(column), "O")
    await asyncio.sleep(0)
    canvas.addstr(round(row), round(column), " ")
    row += rows_speed
    column += columns_speed
    symbol = "-" if columns_speed else "|"
    rows, columns = canvas.getmaxyx()
    max_row, max_column = rows - 1, columns - 1
    curses.beep()
    while 0 < row < max_row and 0 < column < max_column:
        canvas.addstr(round(row), round(column), symbol)
        await asyncio.sleep(0)
        canvas.addstr(round(row), round(column), " ")
        row += rows_speed
        column += columns_speed
        for obstacle in obstacles:
            if obstacle.has_collision(row, column):
                obstacles_in_last_collisions.append(obstacle)
                return


async def animate_spaceship(canvas, row, column, frames):
    """Spaceship animation with keyboard control and limitts"""
    global coroutines, year
    rows, columns = canvas.getmaxyx()
    indent_row = 3
    indent_column = 1
    max_row, max_column = rows - indent_row, columns - indent_column 
    row_speed, column_speed = 0, 0
    frame_row, frame_column = get_frame_size(frames[0])
    game_over_indent_column = 20
    fire_indent_row = 1
    fire_indent_column = 2
    while True:
        for frame in frames:
            row = min(row, max_row - frame_row)
            row = max(1, row)
            column = min(column, max_column -frame_column)
            column = max(1, column)
            draw_frame(canvas, row, column, frame, negative=False)
            await sleep(2)
            draw_frame(canvas, row, column, frame, negative=True)
            rows_direction, columns_direction, fire_press = read_controls(canvas)
            row_speed, column_speed = update_speed(row_speed, column_speed, rows_direction, columns_direction)
            row += row_speed
            column += column_speed
            if year >= 2020:
                if fire_press:
                    fire_coroutine = fire(canvas, row-fire_indent_row, column+fire_indent_column)
                    coroutines.append(fire_coroutine )
                    await sleep(0)
            for obstacle in obstacles:
                if obstacle.has_collision(row, column):
                    await show_gameover(canvas, round(max_row/2), round(max_column/2)-game_over_indent_column)


async def fly_garbage(canvas, column, garbage_frame, speed=0.5):
    """Animate garbage, flying from top to bottom. Сolumn position will stay same, as specified on start."""
    global obstacles, coroutines, obstacles_in_last_collisions
    rows_number, columns_number = canvas.getmaxyx()
    indent_row = 4
    indent_column = 1
    rows_number = rows_number - indent_row
    column = max(column, 0)
    column = min(column, columns_number - indent_column)
    row = 0
    row_size, column_size = get_frame_size(garbage_frame)
    obstacle = Obstacle(row, column, row_size, column_size)
    obstacles.append(obstacle)
    try:
        while row < rows_number:
            draw_frame(canvas, row, column, garbage_frame)
            await asyncio.sleep(0)
            draw_frame(canvas, row, column, garbage_frame, negative=True)
            row += speed
            obstacle.row+=speed
            if obstacle in obstacles_in_last_collisions:
                obstacles_in_last_collisions.remove(obstacle)
                await explode(canvas, obstacle.row, obstacle.column)
                break
    finally:
        obstacles.remove(obstacle)


async def fill_orbit_with_garbage(canvas, max_column, garbage_frames):
    global year
    global coroutines
    while True:
        if get_garbage_delay_tics(year):
            garbage_frame = random.choice(garbage_frames)
            _, frame_column = get_frame_size(garbage_frame)
            column = random.randint(frame_column, max_column-frame_column)
            coroutines.append(fly_garbage(canvas, column=column, garbage_frame=garbage_frame))
            await sleep(get_garbage_delay_tics(year))
        else:
            await sleep(1)


async def sleep(tics=1):
    for _ in range(tics):
        await asyncio.sleep(0)


async def update_level():
    global year
    while True:
        await sleep(LEVEL_TICS)
        year+=1


async def sub_window_information(window, column):
    global year
    description = PHRASES.get(year)
    text = "{} year - {}".format(year, description)
    text_row = 1
    while True:
        window.border()
        if year in PHRASES:
            description = PHRASES.get(year)
            draw_frame(window, 1, column-round(len(text)/2), text, negative=True)
        text = "{} year - {}".format(year, description)
        draw_frame(window, text_row, column-round(len(text)/2), text)
        window.refresh()
        await sleep(1)


def main(canvas):
    """Main fraw functions"""
    curses.curs_set(False)
    canvas.nodelay(True)
    canvas.refresh()
    frames = []
    with open("sprites/rocket_frame_1.txt", "r") as f:
          frames.append(f.read())
    with open("sprites/rocket_frame_2.txt", "r") as f:
          frames.append(f.read())    
    garbage_frames = []
    with open("sprites/trash_large.txt", "r") as f:
          garbage_frames.append(f.read())
    with open("sprites/trash_small.txt", "r") as f:
          garbage_frames.append(f.read())
    with open("sprites/trash_xl.txt", "r") as f:
          garbage_frames.append(f.read())   
    max_row, max_column = canvas.getmaxyx()
    middle_row = round(max_row/2)
    middle_column = round(max_column/2)
    subwindow_indent_row = 3
    subwindow_indent_column = 0
    derived_window = canvas.derwin(max_row-subwindow_indent_row, subwindow_indent_column)
    indent_row, indent_column = 4, 1
    global coroutines
    for _ in range(NUMBER_STARS):
          row = random.randint(1, max_row-indent_row)
          column = random.randint(1, max_column-indent_column)
          star_symbol = random.choice(STARS_SYMBOLS)
          coroutines.append(blink(canvas, row, column,symbol=star_symbol))
    coroutines.append(sub_window_information(derived_window, middle_column))
    coroutines.append(animate_spaceship(canvas, middle_row, middle_column, frames))
    coroutines.append(fill_orbit_with_garbage(canvas, max_column-indent_column, garbage_frames))
    coroutines.append(update_level())
    while True:
        for coroutine in coroutines.copy():
            try:
                coroutine.send(None)
            except StopIteration:
                coroutines.remove(coroutine)
        canvas.refresh()
        time.sleep(TIC_TIMEOUT)


if __name__ == "__main__":
    curses.update_lines_cols()
    curses.wrapper(main)