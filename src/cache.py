from datetime import datetime

from utils import BotU

from .config import CLEAR_CACHE_HOURS
from .logger import Logger


class Cache:
    logger: Logger
    cache = {}

    def __init__(self, logger, bot: BotU):
        self.logger = logger
        self.bot = bot
        pass

    async def get(self, query: str) -> dict:
        # em = wiki.parse(query, False)

        if query in self.cache:
            self.logger.info(f'Found cache for {query}')
            hours_since_cache = (datetime.now() - self.cache[query]['time']).total_seconds() / 3600
            
            self.logger.info(f'Hours since cache: {hours_since_cache} (mins: {hours_since_cache * 60})')
            if hours_since_cache > CLEAR_CACHE_HOURS:
                self.logger.info(f'Clearing cache for {query}')
                del self.cache[query]
                return await self.get(query)
            
            emb = self.cache[query]['embed']
            try: return emb.build()
            except: return emb
        
        cog = self.bot.get_cog('Farm Computer')
        self.cache[query] = {
            'embed': await cog.parse(query, False),# type: ignore
            'time': datetime.now()
        }
        self.logger.info(f'Cached {query}')
        emb = self.cache[query]['embed']
        try: 
            return emb.build()
        except Exception: 
            return emb

async def setup(bot: BotU):
    pass