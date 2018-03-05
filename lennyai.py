import logging
import copy
import asyncio
import random

logging.basicConfig(level=logging.INFO, format='%(levelname)s-%(name)s-%(message)s')
logger = logging.getLogger(__name__)

# http://www.stat.purdue.edu/~mdw/CSOI/MarkovLab.html

##TODO: self._count and self._probabilities get very big very fast. need to use db
    # https://github.com/jreese/aiosqlite
# could use send_typing() to signify still processing?


class TextPredictor():

    def __init__(self):
        self._counts = None
        self._probabilities = None

        ##TODO: add more later or think of a better way. just list all of some char set?
        self._chars = [chr(i) for i in range(65, 91)]  # A-Z: 65-90
        self._chars += [chr(i) for i in range(97, 123)]  # a-z: 97-122
        self._chars += [str(i) for i in range(10)]
        self._chars += [' ', '.', '!', '?', ',']

    @classmethod
    async def create(cls, order=1):
        self = cls()
        await self.reset(order)
        return self

    def predict(self, seed, length):
        seed = self.clean(seed)
        if length <= 0:
            raise ValueError('Length must be > 0. Cleaned seed length: %s' % len(seed))
        if len(seed) < self._order:
            raise ValueError('Seed is not long enough. Order: %s, Cleaned seed length: %s' % (self._order, len(seed)))
        if len(seed) >= length:
            return seed

        while len(seed) < length:
            curr_chunk = seed[-1 * self._order: len(seed)]

            # if there is a tie, it should choose randomly between them
            choices = dict((p, [char for char in self._chars if self._probabilities[curr_chunk][char] == p]) for p in self._probabilities[curr_chunk].values())
            next_char = random.choice(choices[max(choices.keys())])
            seed += next_char
        return seed

    def clean(self, s):
        return ''.join(filter(lambda x: x in self._chars, s))

    async def train(self, data, reset=False, order=1):
        logger.info('Training... This may take a few minutes.')
        if not self._counts or not self._probabilities or reset:
            await self.reset(order)
        data = self.clean(data)
        for i in range(len(data) - self._order):
            curr_chunk = data[i:i + self._order]
            next_char = data[i + self._order]
            self._counts[curr_chunk][next_char] += 1

        for curr_chunk in self._counts.keys():
            s = float(sum(self._counts[curr_chunk].values()))
            for next_char in self._counts[curr_chunk].keys():
                try:
                    self._probabilities[curr_chunk][next_char] = self._counts[curr_chunk][next_char] / s
                except ZeroDivisionError as e:
                    logger.debug('No transitions found from %s to %s. Setting p=0.' % (curr_chunk, next_char))
                    self._probabilities[curr_chunk][next_char] = 0

    async def reset(self, order):
        logger.info('Resetting TextPredictor model. This may take a few minutes.')
        if order <= 0:
            raise ValueError('Order must be >= 1')
        self._order = order
        # Run this async because it can take a while
        permutations = await asyncio.get_event_loop().run_in_executor(None, self.build_permutations, self._chars, order)
        self._counts = dict((perm, dict((char, 0) for char in self._chars)) for perm in permutations)
        self._probabilities = await asyncio.get_event_loop().run_in_executor(None, copy.deepcopy, self._counts)
        logger.info('Reset TextPredictor matrices to {0}x{1}'.format(len(self._counts), len(self._chars)))

    @staticmethod
    def build_permutations(chars, length):
        permutations = chars[:]
        for i in range(length - 1):
            next_perm = []
            for perm in permutations:
                next_perm += [perm + char for char in chars]
            permutations = next_perm
        return permutations

class TextModel():

    def __init__():
        pass

    def reset(self):
        pass


if __name__ == '__main__':
    async def test():
        import glob
        predictor = await TextPredictor.create(3)
        files = glob.glob('ai_training/*.txt')

        for file in files:
            training_data = ''
            with open(file, 'r') as f:
                training_data = f.read()
            logger.info('Loaded training data file: %s (%s)' % (file, len(training_data)))
            await predictor.train(training_data)

        print(predictor.predict('I am Lenny', 100))

    asyncio.get_event_loop().run_until_complete(test())
