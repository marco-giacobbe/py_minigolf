import pygame

from modules.game import Game

if __name__ == "__main__":
    pygame.init()
    game = Game()
    if not game.run():
        pygame.quit()
