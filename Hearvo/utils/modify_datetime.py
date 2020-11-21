from datetime import datetime, timedelta

lang_time = {
  1: 9,
  2: 13,
}


def modify_from_utc(original_time, diff_time):
  modified_time = original_time + timedelta(hours=diff_time)
  return modified_time