# -*- coding: utf-8 -*-
"""
@author: Junxiao Song
"""

from __future__ import print_function

import os
import curses
import time

import numpy as np


class Board(object):
    """board for the game"""

    def __init__(self, **kwargs):
        self.width = int(kwargs.get('width', 8))
        self.height = int(kwargs.get('height', 8))
        # board states stored as a dict,
        # key: move as location on the board,
        # value: player as pieces type
        self.states = {}
        # need how many pieces in a row to win
        self.n_in_row = int(kwargs.get('n_in_row', 5))
        self.players = [1, 2]  # player1 and player2

    def init_board(self, start_player=0):
        if self.width < self.n_in_row or self.height < self.n_in_row:
            raise Exception('board width and height can not be '
                            'less than {}'.format(self.n_in_row))
        self.current_player = self.players[start_player]  # start player
        # keep available moves in a list
        self.availables = list(range(self.width * self.height))
        self.states = {}
        self.last_move = -1

    def move_to_location(self, move):
        """
        3*3 board's moves like:
        6 7 8
        3 4 5
        0 1 2
        and move 5's location is (1,2)
        """
        h = move // self.width
        w = move % self.width
        return [h, w]

    def location_to_move(self, location):
        if len(location) != 2:
            return -1
        h = location[0]
        w = location[1]
        move = h * self.width + w
        if move not in range(self.width * self.height):
            return -1
        return move

    def current_state(self):
        """return the board state from the perspective of the current player.
        state shape: 4*width*height
        """

        square_state = np.zeros((4, self.width, self.height))
        if self.states:
            moves, players = np.array(list(zip(*self.states.items())))
            move_curr = moves[players == self.current_player]
            move_oppo = moves[players != self.current_player]
            square_state[0][move_curr // self.width,
                            move_curr % self.height] = 1.0
            square_state[1][move_oppo // self.width,
                            move_oppo % self.height] = 1.0
            # indicate the last move location
            square_state[2][self.last_move // self.width,
                            self.last_move % self.height] = 1.0
        if len(self.states) % 2 == 0:
            square_state[3][:, :] = 1.0  # indicate the colour to play
        return square_state[:, ::-1, :]

    def do_move(self, move):
        self.states[move] = self.current_player
        self.availables.remove(move)
        self.current_player = (
            self.players[0] if self.current_player == self.players[1]
            else self.players[1]
        )
        self.last_move = move

    def has_a_winner(self):
        # 如果步数不足以形成获胜局面，直接返回
        if len(self.availables) > self.width * self.height - self.n_in_row * 2 + 1:
            return False, -1

        # 获取最后一步的落子位置和玩家
        last_move = list(set(range(self.width * self.height)) - set(self.availables))[0]
        player = self.states[last_move]

        # 计算最后一步的坐标
        h, w = last_move // self.width, last_move % self.width

        # 定义检查方向
        directions = [
            (1, 0),  # 垂直向下
            (0, 1),  # 水平向右
            (1, 1),  # 右下对角
            (1, -1)  # 左下对角
        ]

        for dx, dy in directions:
            count = 1  # 从1开始，包括当前落子

            # 正向检查
            for i in range(1, self.n_in_row):
                new_x, new_y = h + i * dx, w + i * dy
                if (0 <= new_x < self.height and
                        0 <= new_y < self.width and
                        self.states.get(new_x * self.width + new_y, -1) == player):
                    count += 1
                else:
                    break

            # 反向检查
            for i in range(1, self.n_in_row):
                new_x, new_y = h - i * dx, w - i * dy
                if (0 <= new_x < self.height and
                        0 <= new_y < self.width and
                        self.states.get(new_x * self.width + new_y, -1) == player):
                    count += 1
                else:
                    break

            # 检查是否获胜
            if count >= self.n_in_row:
                return True, player

        return False, -1

    def game_end(self):
        """Check whether the game is ended or not"""
        win, winner = self.has_a_winner()
        if win:
            return True, winner
        elif not len(self.availables):
            return True, -1
        return False, -1

    def get_current_player(self):
        return self.current_player


class Game(object):
    """game server"""

    def __init__(self, board, **kwargs):
        self.board = board

    def graphic(self, board, player1, player2):
        """Draw the board and show game info"""
        width = board.width
        height = board.height
        # 延迟1秒
        # time.sleep(1)
        # 清屏
        os.system('clear')

        print("Player", player1, "with ●".rjust(3))
        print("Player", player2, "with ○".rjust(3))
        print()
        for x in range(width):
            print("{0:3}".format(x), end='') if x > 0 else print(" {0:3}".format(x), end='')
        print()
        for i in range(height - 1, -1, -1):
            print("{0:1d}|".format(i), end='')
            for j in range(width):
                loc = i * width + j
                p = board.states.get(loc, -1)
                if p == player1:
                    print('●'.center(3), end='')
                elif p == player2:
                    print('○'.center(3), end='')
                else:
                    print('·'.center(3), end='')
            print("|")
        for x in range(width):
            print("{0:3}".format(x), end='') if x > 0 else print(" {0:3}".format(x), end='')
        print()

    def start_play(self, player1, player2, start_player=0, is_shown=1):
        """start a game between two players"""
        if start_player not in (0, 1):
            raise Exception('start_player should be either 0 (player1 first) '
                            'or 1 (player2 first)')
        self.board.init_board(start_player)
        p1, p2 = self.board.players
        player1.set_player_ind(p1)
        player2.set_player_ind(p2)
        players = {p1: player1, p2: player2}
        if is_shown:
            self.graphic(self.board, player1.player, player2.player)
        while True:
            current_player = self.board.get_current_player()
            player_in_turn = players[current_player]
            move = player_in_turn.get_action(self.board)
            self.board.do_move(move)
            if is_shown:
                self.graphic(self.board, player1.player, player2.player)
            end, winner = self.board.game_end()
            if end:
                if is_shown:
                    if winner != -1:
                        print("Game end. Winner is", players[winner])
                    else:
                        print("Game end. Tie")
                return winner

    def start_self_play(self, player, is_shown=0, temp=1e-3):
        """ start a self-play game using a MCTS player, reuse the search tree,
        and store the self-play data: (state, mcts_probs, z) for training
        """
        self.board.init_board()
        p1, p2 = self.board.players
        states, mcts_probs, current_players = [], [], []
        while True:
            move, move_probs = player.get_action(self.board,
                                                 temp=temp,
                                                 return_prob=1)
            # store the data
            states.append(self.board.current_state())
            mcts_probs.append(move_probs)
            current_players.append(self.board.current_player)
            # perform a move
            self.board.do_move(move)
            if is_shown:
                self.graphic(self.board, p1, p2)
            end, winner = self.board.game_end()
            if end:
                # winner from the perspective of the current player of each state
                winners_z = np.zeros(len(current_players))
                if winner != -1:
                    winners_z[np.array(current_players) == winner] = 1.0
                    winners_z[np.array(current_players) != winner] = -1.0
                # reset MCTS root node
                player.reset_player()
                if is_shown:
                    if winner != -1:
                        print("Game end. Winner is player:", winner)
                    else:
                        print("Game end. Tie")
                return winner, zip(states, mcts_probs, winners_z)
