from . import lennyai
import aioodbc
import asyncio
import logging

# https://github.com/jreese/aiosqlite

logging.basicConfig(level=logging.INFO, format='%(levelname)s-%(name)s-%(message)s')
logger = logging.getLogger(__name__)

_MEMORY = ':memory:'

# TODO: make an ABC instead of subclassing from TextModel
class DBTextModel(lennyai.TextModel):

    def __init__(self, chars):
        super().__init__(chars)
        self._db = None


    # need create() because you can't make __init__() async
    @classmethod
    async def create(cls, chars, db=_MEMORY):
        self = cls(chars)
        dsn = 'Driver=SQLite;Database=%s' % db
        self._db = await aioodbc.connect(dsn=dsn, )
        # self._db.row_factory = sqlite3.Row  # from saltybetter, but what does it do?
        # self._db._conn.row_factory = sqlite3.Row  # ?
        await self._db.executescript('''
            CREATE TABLE IF NOT EXISTS counts(
                chunk       TEXT PRIMARY KEY,
                next_char   TEXT PRIMARY KEY,
                count       INT NOT NULL DEFAULT 0
            );
            
            CREATE TABLE IF NOT EXISTS probabilities(
                chunk       TEXT PRIMARY KEY,
                next_char   TEXT PRIMARY KEY,
                p           REAL NOT NULL DEFAULT 0
            );
            
            DROP VIEW IF EXISTS v_probabilities;
            CREATE VIEW v_probabilities AS
            SELECT chunk,
                next_char,
                CAST(count AS REAL) / (SELECT SUM(count) FROM counts c2 WHERE c1.chunk = c2.chunk) AS p
            FROM counts c1;
            
        ''')
        await self._db.commit()
        return self

    def ready(self):
        pass

    def reset(self, permutations):
        pass

    def size(self):
        pass

    def get_p(self, chunk, next_char):
        pass

    def p_vals(self, chunk):
        pass

    def recalc_probabilities(self):
        pass

    def increment_count(self, chunk, next_char):
        pass


if __name__ == '__main__':
    async def test():
        chars = [chr(i) for i in range(65, 91)]  # A-Z: 65-90
        await DBTextModel.create(chars)
        logger.info('done')

    asyncio.get_event_loop().run_until_complete(test())
