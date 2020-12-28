from ..app import logger, cache



def cache_delete_latest_posts():
    cache.delete_many(*['latest_posts_page_{}'.format(page) for page in range(1,21)])
    return


def cache_delete_popular_posts():
  POPULAR_CACHE_LIST = []
  for page in range(1,21):
    for time in ["now", "today", "week", "month"]:
      POPULAR_CACHE_LIST.append('popular_posts_page_{}_time_{}'.format(page, time))
  cache.delete_many(*POPULAR_CACHE_LIST)
  return


def cache_delete_all_posts():
  POPULAR_CACHE_LIST = []
  for page in range(1,21):
    for time in ["now", "today", "week", "month"]:
      POPULAR_CACHE_LIST.append('popular_posts_page_{}_time_{}'.format(page, time))
  cache.delete_many(*POPULAR_CACHE_LIST)
  cache.delete_many(*['latest_posts_page_{}'.format(page) for page in range(1,21)])
  return