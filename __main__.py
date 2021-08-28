# import sys
# import os.path as ospath

from gofish.game_logic import GoFish


# path = ospath.dirname(ospath.realpath(ospath.abspath(__file__)))
# print(path)
# sys.path.insert(0, path)

def main():
    gof = GoFish()
    again = True
    while again:
        gof.play()
        again = gof.prompts.play_again()
    print('Goodbye!')


if __name__ == '__main__':
    main()
