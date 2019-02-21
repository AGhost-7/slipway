# -*- coding: utf-8 -*-
import math
from sys import stdout


MB_RATIO = 1024 * 1024


class MultiBytesBar(object):
    """
    Accepts a dictionary of the different progress bars.
    progress = ProgressBar({
        'downloaded': {
            'max': 50000,
            'title': 'Downloaded'
        },
        'extracted': {
            'max': 50000,
            'title': 'Extacted'
        }
    })
    """
    EMPTY_CHAR = '□'
    FULL_CHAR = '■'
    BAR_WIDTH = 30

    def __init__(self, bars, file=stdout):
        self._started = False
        self._bars = bars
        self._bar_states = {}
        self._formatted_titles = {}
        for bar_name in self._bars:
            self._bar_states[bar_name] = 0
            self._formatted_titles[bar_name] = self._format_title(bar_name)

        self._file = file

    def _put(self, chars):
        self._file.write(chars)

    def start(self):
        """
        Sets the terminal in the correct mode to start the progress bar.
        """
        self._hide_cursor()
        self.draw()
        self._started = True

    def _format_title(self, bar_name):
        bar = self._bars[bar_name]
        state = self._bar_states[bar_name]
        title = bar['title']
        state_mb = math.floor((state / MB_RATIO) * 10) / 10
        max_mb = math.floor((bar['max'] / MB_RATIO) * 10) / 10
        formatted = title.format(
            state=state_mb,
            max=max_mb)
        return formatted

    def _pad_title(self, bar_name):
        max_len = 0
        formatted = self._formatted_titles[bar_name]
        for bar_name in self._bars:
            formatted_len = len(self._formatted_titles[bar_name])
            max_len = max(formatted_len, max_len)
        difference = max_len - len(formatted)
        padded = formatted + (' ' * difference)
        return padded

    def _draw_bar(self, bar_name):
        bar = self._bars[bar_name]
        state = float(self._bar_states[bar_name])
        max = float(bar['max'])
        self._put(self._pad_title(bar_name))
        full_chars = int(math.floor((state / max) * self.BAR_WIDTH))
        empty_chars = self.BAR_WIDTH - full_chars
        for i in range(full_chars):
            self._put(self.FULL_CHAR)
        for i in range(empty_chars):
            self._put(self.EMPTY_CHAR)
        self._put('\n')

    def _show_cursor(self):
        self._put('\x1b[?25h')

    def _hide_cursor(self):
        self._put('\x1b[?25l')

    def _clear_line(self):
        self._put('\x1b[0K')

    def end(self):
        """
        Returns the terminal to the original mode.
        """
        self._show_cursor()
        self._file.flush()

    def increment(self, bar_name, bytes):
        """
        Increment the number by number of bytes the given bar.
        """
        self._bar_states[bar_name] += bytes
        self._formatted_titles[bar_name] = self._format_title(bar_name)

    def draw(self):
        """
        Draw all bars.
        """
        for bar_name in self._bars:
            if self._started:
                print('\033[0K', end='', file=self._file)
                # self._put('\r\x1b[K')
            self._draw_bar(bar_name)
        self._file.flush()


if __name__ == "__main__":
    bar = MultiBytesBar({
        'downloaded': {
            'max': 100 * 1024 * 1024,
            'title': 'Downloaded [{state} / {max} MB]: '
        }
        # ,
        # 'extracted': {
        #     'max': 100 * 1024 * 1024,
        #     'title': 'Extracted [{state} / {max} MB]: '
        # }
    })
    #bar._hide_cursor()
    #bar._file.flush()
    #bar.start()
    import time
    time.sleep(1)
    try:
        bar._put('hello!\n\r')
        bar._file.flush()
        time.sleep(1)

        bar._put('world!\r')
        bar._file.flush()
        time.sleep(1)

        bar._put('\x1b[1A')
        bar._file.flush()
        time.sleep(1)

        bar._clear_line()
        bar._file.flush()
        time.sleep(1)

        bar._put('\x1b[1B')
        bar._file.flush()
        time.sleep(1)

        bar._clear_line()
        bar._file.flush()
        time.sleep(1)
        # bar.increment('downloaded', 10 * MB_RATIO)
        #bar.draw()
        #time.sleep(1)
        # bar.increment('downloaded', 10 * MB_RATIO)
        # bar.increment('extracted', 33.3 * MB_RATIO)
        #bar.draw()
    finally:
        bar._show_cursor()
        bar._file.flush()
