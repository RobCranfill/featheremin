"""
    adapted by cran from https://code.activestate.com/recipes/577537-banner/
    With the idea that this could perhaps be used to display simple error messages on the LCD display.
"""
class Banner:

    LETTERFORMS = '''\
        |       |       |       |       |       |       | |
    XXX  |  XXX  |  XXX  |   X   |       |  XXX  |  XXX  |!|
    X  X |  X  X |  X  X |       |       |       |       |"|
    X X  |  X X  |XXXXXXX|  X X  |XXXXXXX|  X X  |  X X  |#|
    XXXXX |X  X  X|X  X   | XXXXX |   X  X|X  X  X| XXXXX |$|
    XXX   X|X X  X |XXX X  |   X   |  X XXX| X  X X|X   XXX|%|
    XX   | X  X  |  XX   | XXX   |X   X X|X    X | XXX  X|&|
    XXX  |  XXX  |   X   |  X    |       |       |       |'|
    XX  |  X    | X     | X     | X     |  X    |   XX  |(|
    XX   |    X  |     X |     X |     X |    X  |  XX   |)|
        | X   X |  X X  |XXXXXXX|  X X  | X   X |       |*|
        |   X   |   X   | XXXXX |   X   |   X   |       |+|
        |       |       |  XXX  |  XXX  |   X   |  X    |,|
        |       |       | XXXXX |       |       |       |-|
        |       |       |       |  XXX  |  XXX  |  XXX  |.|
        X|     X |    X  |   X   |  X    | X     |X      |/|
    XXX  | X   X |X     X|X     X|X     X| X   X |  XXX  |0|
    X   |  XX   | X X   |   X   |   X   |   X   | XXXXX |1|
    XXXXX |X     X|      X| XXXXX |X      |X      |XXXXXXX|2|
    XXXXX |X     X|      X| XXXXX |      X|X     X| XXXXX |3|
    X      |X    X |X    X |X    X |XXXXXXX|     X |     X |4|
    XXXXXXX|X      |X      |XXXXXX |      X|X     X| XXXXX |5|
    XXXXX |X     X|X      |XXXXXX |X     X|X     X| XXXXX |6|
    XXXXXX |X    X |    X  |   X   |  X    |  X    |  X    |7|
    XXXXX |X     X|X     X| XXXXX |X     X|X     X| XXXXX |8|
    XXXXX |X     X|X     X| XXXXXX|      X|X     X| XXXXX |9|
    X   |  XXX  |   X   |       |   X   |  XXX  |   X   |:|
    XXX  |  XXX  |       |  XXX  |  XXX  |   X   |  X    |;|
        X  |   X   |  X    | X     |  X    |   X   |    X  |<|
        |       |XXXXXXX|       |XXXXXXX|       |       |=|
    X    |   X   |    X  |     X |    X  |   X   |  X    |>|
    XXXXX |X     X|      X|   XXX |   X   |       |   X   |?|
    XXXXX |X     X|X XXX X|X XXX X|X XXXX |X      | XXXXX |@|
    X   |  X X  | X   X |X     X|XXXXXXX|X     X|X     X|A|
    XXXXXX |X     X|X     X|XXXXXX |X     X|X     X|XXXXXX |B|
    XXXXX |X     X|X      |X      |X      |X     X| XXXXX |C|
    XXXXXX |X     X|X     X|X     X|X     X|X     X|XXXXXX |D|
    XXXXXXX|X      |X      |XXXXX  |X      |X      |XXXXXXX|E|
    XXXXXXX|X      |X      |XXXXX  |X      |X      |X      |F|
    XXXXX |X     X|X      |X  XXXX|X     X|X     X| XXXXX |G|
    X     X|X     X|X     X|XXXXXXX|X     X|X     X|X     X|H|
    XXX  |   X   |   X   |   X   |   X   |   X   |  XXX  |I|
        X|      X|      X|      X|X     X|X     X| XXXXX |J|
    X    X |X   X  |X  X   |XXX    |X  X   |X   X  |X    X |K|
    X      |X      |X      |X      |X      |X      |XXXXXXX|L|
    X     X|XX   XX|X X X X|X  X  X|X     X|X     X|X     X|M|
    X     X|XX    X|X X   X|X  X  X|X   X X|X    XX|X     X|N|
    XXXXXXX|X     X|X     X|X     X|X     X|X     X|XXXXXXX|O|
    XXXXXX |X     X|X     X|XXXXXX |X      |X      |X      |P|
    XXXXX |X     X|X     X|X     X|X   X X|X    X | XXXX X|Q|
    XXXXXX |X     X|X     X|XXXXXX |X   X  |X    X |X     X|R|
    XXXXX |X     X|X      | XXXXX |      X|X     X| XXXXX |S|
    XXXXXXX|   X   |   X   |   X   |   X   |   X   |   X   |T|
    X     X|X     X|X     X|X     X|X     X|X     X| XXXXX |U|
    X     X|X     X|X     X|X     X| X   X |  X X  |   X   |V|
    X     X|X  X  X|X  X  X|X  X  X|X  X  X|X  X  X| XX XX |W|
    X     X| X   X |  X X  |   X   |  X X  | X   X |X     X|X|
    X     X| X   X |  X X  |   X   |   X   |   X   |   X   |Y|
    XXXXXXX|     X |    X  |   X   |  X    | X     |XXXXXXX|Z|
    XXXXX | X     | X     | X     | X     | X     | XXXXX |[|
    X      | X     |  X    |   X   |    X  |     X |      X|\|
    XXXXX |     X |     X |     X |     X |     X | XXXXX |]|
    X   |  X X  | X   X |       |       |       |       |^|
        |       |       |       |       |       |XXXXXXX|_|
        |  XXX  |  XXX  |   X   |    X  |       |       |`|
        |   XX  |  X  X | X    X| XXXXXX| X    X| X    X|a|
        | XXXXX | X    X| XXXXX | X    X| X    X| XXXXX |b|
        |  XXXX | X    X| X     | X     | X    X|  XXXX |c|
        | XXXXX | X    X| X    X| X    X| X    X| XXXXX |d|
        | XXXXXX| X     | XXXXX | X     | X     | XXXXXX|e|
        | XXXXXX| X     | XXXXX | X     | X     | X     |f|
        |  XXXX | X    X| X     | X  XXX| X    X|  XXXX |g|
        | X    X| X    X| XXXXXX| X    X| X    X| X    X|h|
        |    X  |    X  |    X  |    X  |    X  |    X  |i|
        |      X|      X|      X|      X| X    X|  XXXX |j|
        | X    X| X   X | XXXX  | X  X  | X   X | X    X|k|
        | X     | X     | X     | X     | X     | XXXXXX|l|
        | X    X| XX  XX| X XX X| X    X| X    X| X    X|m|
        | X    X| XX   X| X X  X| X  X X| X   XX| X    X|n|
        |  XXXX | X    X| X    X| X    X| X    X|  XXXX |o|
        | XXXXX | X    X| X    X| XXXXX | X     | X     |p|
        |  XXXX | X    X| X    X| X  X X| X   X |  XXX X|q|
        | XXXXX | X    X| X    X| XXXXX | X   X | X    X|r|
        |  XXXX | X     |  XXXX |      X| X    X|  XXXX |s|
        |  XXXXX|    X  |    X  |    X  |    X  |    X  |t|
        | X    X| X    X| X    X| X    X| X    X|  XXXX |u|
        | X    X| X    X| X    X| X    X|  X  X |   XX  |v|
        | X    X| X    X| X    X| X XX X| XX  XX| X    X|w|
        | X    X|  X  X |   XX  |   XX  |  X  X | X    X|x|
        |  X   X|   X X |    X  |    X  |    X  |    X  |y|
        | XXXXXX|     X |    X  |   X   |  X    | XXXXXX|z|
    XXX  | X     | X     |XX     | X     | X     |  XXX  |{|
    X   |   X   |   X   |       |   X   |   X   |   X   |||
    XXX  |     X |     X |     XX|     X |     X |  XXX  |}|
    XX    |X  X  X|    XX |       |       |       |       |~|
    '''.splitlines()

    def __init__(self):
        self.table = {}
        for form in self.LETTERFORMS:
            if '|' in form:
                self.table[form[-2]] = form[:-3].split('|')

        # original code:
        # ROWS = len(table.values()[0])


        # print(f"ROWS: {self.table.values()[0]}")
        self.ROWS = 80
        self.ROWS = len(list(self.table).values()[0])

    def horizontal(self, word):
        for row in range(self.ROWS):
            for c in word:
                print(self.table[c][row],)
            print()
        print()

    def vertical(self, word):
        for c in word:
            for row in zip(*self.table[c]):
                print(' '.join(reversed(row)))
            print()

    def test(self, message):
        print(f"PRINTING: {message}\n")
        self.horizontal(message)

if __name__ == '__main__':
  b = Banner()
  b.horizontal('Monty')
  b.vertical('Python')
