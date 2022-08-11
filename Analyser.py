from stockfish import Stockfish
import tkinter as tk
from tkinter import ttk
import numpy as np
import chess

sf = Stockfish(path='C:/Users/Jamie Phelps/Documents/stockfish_14.1_win_x64_avx2/stockfish_14.1_win_x64_avx2.exe',
               depth=20, parameters={'Threads': 10, 'Hash': 64})


def fen_to_array(fen):
    fen = fen.split(' ')
    fen = fen[0].replace('/', '')
    start_array = [i for i in range(64)]
    k = 0
    for i in range(len(fen)):
        if fen[i].isdigit():
            for j in range(int(fen[i])):
                start_array[k] = 0
                k += 1
            k -= 1
        else:
            start_array[k] = fen_dict[fen[i]]
        k += 1
    return start_array


def to_img(x):
    return tk.PhotoImage(file=x)


def transpose_board(new_position, white=True):
    a = np.array(new_position).reshape((8, 8))
    a = np.transpose(a)
    a = np.flip(np.flip(a, axis=-1), axis=0) if not white else a
    a = np.reshape(a, 64).tolist()
    return a


def update(t_pos, white):
    new_pos_t = transpose_board(t_pos, white=white)
    [item.config(image=img_dict[new_pos_t[i]]) for i, item in enumerate(board)]


def get_move_class(prev_info, curr_info, move):
    if prev_info[0]['Move'] == move:
        return 'Best'
    if prev_info[0]['Centipawn'] is not None and curr_info[0]['Centipawn'] is not None:
        if abs(prev_info[0]['Centipawn'] - curr_info[0]['Centipawn']) >= 20:
            return "Excellent"
        if abs(prev_info[0]['Centipawn'] - curr_info[0]['Centipawn']) >= 100:
            return 'Good'
        return 'Inaccurate'


def get_move_list(pgn):
    pgn = pgn.split(']')[-1]
    pgn = pgn.rsplit(' ', 1)[0]
    pgn = pgn.replace('\n', ' ')
    pgn = pgn.split('. ')[1:]
    pgn = [i.rsplit(' ', 1)[0] for i in pgn]
    pgn = [i.split(' ') for i in pgn]
    pgn = [item for sublist in pgn for item in sublist]

    b = chess.Board()
    move_list = []
    for i in pgn:
        move_list.append(b.uci(b.parse_san(i)))
        b.push_uci(move_list[-1])
    return move_list


def eval_pgn(move_list):
    global pb
    pb_interval = 100 // len(move_list)
    sf.set_fen_position('rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1')
    sf.set_depth(int(depth_entry.get()))
    move_eval = [['start', 0.0, None]]
    sf.make_moves_from_current_position([move_list[0]])
    info = sf.get_top_moves(5)
    pb['value'] += pb_interval
    root.update()
    move_eval.append([move_list[0], eval_from_info(info), info[0]['Move'], fen_to_array(sf.get_fen_position())])
    for i in range(1, len(move_list)):
        sf.make_moves_from_current_position([move_list[i]])
        info = sf.get_top_moves(5)
        pb['value'] += pb_interval
        root.update()
        if not info:
            move_eval.append([move_list[i], 'Mate', 'a1a1', fen_to_array(sf.get_fen_position())])
        else:
            move_eval.append([move_list[i], eval_from_info(info), info[0]['Move'], fen_to_array(sf.get_fen_position())])
    pb.stop()
    return move_eval


def eval_from_info(info):
    return str(info[0]['Centipawn'] / 100) if info[0]['Centipawn'] is not None else 'M' + str(info[0]['Mate'])


def check_entries():
    if depth_entry.get() == '':
        return True, 'Depth field is empty.'
    if not depth_entry.get().isdigit():
        return True, 'Depth field must be an Integer.'
    if pgn_entry.get() == '':
        return True, 'PGN field is empty.'
    move_list = get_move_list(pgn_entry.get())
    if not move_list:
        return True, 'Invalid PGN.'
    return False, move_list


def analysis():
    global game_data, index, curr_state
    index = 0
    cond, info = check_entries()
    if cond:
        error_label.config(text='Error: ' + info, bg='red')
        return
    error_label.config(text='No Errors', bg='white')
    curr_state = fen_to_array('rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1')
    update(curr_state, white_is_player)
    game_data = eval_pgn(info)


def next_move():
    global index
    if index < len(game_data) - 1:
        index += 1
    update_game()


def prev_move():
    global index
    if index >= 1:
        index -= 1
    else:
        index = 0
    update_game()


def eval_update(eval):
    if eval[0] == 'M':
        if eval[1] == '-':
            value = 0
        else:
            value = 100
    else:
        value = min(max(float(eval) * 5 + 50, 0), 100)
    eval_bar['value'] = value


def update_game():
    global index, game_data, best_label, white_is_player, curr_state, eval_label
    curr_state = game_data[index][-1]
    update(curr_state, white_is_player)
    highlight(game_data[index][2])
    eval_update(game_data[index][1])
    best_label.config(text='Best Move:\n' + game_data[index][2])
    eval_label.config(text='Evaluation:\n' + game_data[index][1])


def highlight(coords):
    global prev_highlights
    if not white_is_player:
        flipped = [0, 0, 0, 0]
        flipped[0] = flip[coords[0]]
        flipped[2] = flip[coords[2]]
        flipped[1] = int(coords[1]) + int(2 * (4.5 - int(coords[1])))
        flipped[3] = int(coords[3]) + int(2 * (4.5 - int(coords[3])))
        coords = ''.join([str(i) for i in flipped])
    sq1, sq2 = coords[:2], coords[2:]
    if prev_highlights:
        num1, num2 = prev_highlights
        board[num1].config(background='green' if (num1 % 2 - 1 if num1 % 16 >= 8 else num1 % 2) else 'white')
        board[num2].config(background='green' if (num2 % 2 - 1 if num2 % 16 >= 8 else num2 % 2) else 'white')
    num1 = 8 * (1 + column_dict[sq1[0]]) - int(sq1[1])
    num2 = 8 * (1 + column_dict[sq2[0]]) - int(sq2[1])
    prev_highlights = [num1, num2]
    board[num1].config(background='orange')
    board[num2].config(background='orange')


def switch_player():
    global white_is_player, curr_state, number_labels, letter_labels
    white_is_player = not white_is_player
    update(curr_state, white_is_player)
    if white_is_player:
        [item.place(y=50 + i * 80, x=15, width=20, height=60) for i, item in enumerate(number_labels)]
        [item.place(y=685, x=50 + i * 80, width=60, height=20) for i, item in enumerate(letter_labels)]
    else:
        [item.place(y=685, x=abs(i - 8) * 80 - 30, width=60, height=20) for i, item in enumerate(letter_labels)]
        [item.place(y=abs(i - 8) * 80 - 30, x=15, width=20, height=60) for i, item in enumerate(number_labels)]


root = tk.Tk()
root.title('Chess Game Analyzer')
root.geometry('1175x720+50+50')
root.resizable(False, False)
root.iconbitmap('./assets/icon.ico')
root.configure(bg='black')

black_dir = './assets/black_'
white_dir = './assets/white_'

img_dict = {0: to_img('./assets/empty.png'),
            1: to_img(black_dir + 'rook.png'), 2: to_img(black_dir + 'knight.png'),
            3: to_img(black_dir + 'bishop.png'), 4: to_img(black_dir + 'queen.png'),
            5: to_img(black_dir + 'king.png'), 6: to_img(black_dir + 'pawn.png'),
            7: to_img(white_dir + 'pawn.png'), 8: to_img(white_dir + 'rook.png'),
            9: to_img(white_dir + 'knight.png'), 10: to_img(white_dir + 'bishop.png'),
            11: to_img(white_dir + 'queen.png'), 12: to_img(white_dir + 'king.png')}

fen_dict = {'r': 1, 'n': 2, 'b': 3, 'q': 4, 'k': 5, 'p': 6, 'P': 7, 'R': 8, 'N': 9, 'B': 10, 'Q': 11,
            'K': 12}

column_dict = {'a': 0, 'b': 1, 'c': 2, 'd': 3, 'e': 4, 'f': 5, 'g': 6, 'h': 7}

flip = {'e': 'd', 'f': 'c', 'g': 'b', 'a': 'h',
        'd': 'e', 'c': 'f', 'b': 'g', 'h': 'a'}

curr_fen = 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1'
curr_state = fen_to_array(curr_fen)
white_is_player = True
index = 0
game_data = []
prev_highlights = []

start_position_t = transpose_board(curr_state)

board_frame = tk.Frame(root)
board = [tk.Label(board_frame, image=img_dict[start_position_t[i]], borderwidth=10,
                  background='green' if (i % 2 - 1 if i % 16 >= 8 else i % 2) else 'white') for i in range(64)]
[item.grid(column=i // 8, row=i % 8) for i, item in enumerate(board)]

board_frame.place(x=40, y=40)

number_labels = [tk.Label(root, text=str(i + 1)) for i in reversed(range(8))]
[item.place(y=50 + i * 80, x=15, width=20, height=60) for i, item in enumerate(number_labels)]

letters = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
letter_labels = [tk.Label(root, text=letters[i]) for i in range(8)]
[item.place(y=685, x=50 + i * 80, width=60, height=20) for i, item in enumerate(letter_labels)]

pgn_label = tk.Label(root, text='Enter PGN:')
pgn_label.place(x=700, y=39, width=400, height=18)

pgn_entry = tk.Entry(root, text='PGN')
pgn_entry.place(x=700, y=60, width=400, height=50)

analyse_button = tk.Button(root, text='Analyse', command=analysis)
analyse_button.place(x=700, y=120, width=400, height=75)

depth_label = tk.Label(root, text='Depth:')
depth_label.place(x=700, y=200, width=50, height=20)
depth_entry = tk.Entry(root)
depth_entry.place(x=755, y=200, width=50, height=20)

next_button = tk.Button(root, text='Next', command=next_move)
next_button.place(x=700, y=250, width=195, height=50)

prev_button = tk.Button(root, text='Prev', command=prev_move)
prev_button.place(x=905, y=250, width=195, height=50)

best_label = tk.Label(root, text='Best Move:')
best_label.place(x=700, y=320, width=95, height=50)

eval_label = tk.Label(root, text='Evaluation:')
eval_label.place(x=800, y=320, width=95, height=50)

player_button = tk.Button(root, text='Rotate Board', command=switch_player)
player_button.place(x=905, y=320, width=195, height=50)

error_label = tk.Label(root, text='No Errors')
error_label.place(x=700, y=400, width=400, height=25)

pb = ttk.Progressbar(root, orient='horizontal', length=400, mode='determinate')
pb.place(x=700, y=500)

eval_bar = ttk.Progressbar(root, orient='vertical', length=640, mode='determinate')
eval_bar.place(x=1125, y=40)

root.mainloop()
