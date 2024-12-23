import multiprocessing
from multiprocessing import Pool
import logging

logger = logging.getLogger(__name__)

class PoolManager:
    _pool = None

    @classmethod
    def initialize_pool(cls):
        if cls._pool is None:
            cls._pool = Pool(processes=1)
            logger.info("Pool initialized.")

    @classmethod
    def get_pool(cls):
        return cls._pool

    @classmethod
    def terminate_pool(cls):
        if cls._pool is not None:
            cls._pool.terminate()
            cls._pool = None
            logger.info("Pool terminated.")

if __name__ == "__main__":
    PoolManager.initialize_pool()
