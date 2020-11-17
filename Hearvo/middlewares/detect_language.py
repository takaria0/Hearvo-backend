
import tldextract
from Hearvo.models import Lang
from Hearvo.apis.logger_api import logger_api

subdomain_dict = {
  'ja': 'ja',
  'en': 'en',
}

def get_lang_id(base_url):
  ext = tldextract.extract(base_url)
  subdomain = ext.subdomain

  logger_api("ext", ext)

  if subdomain is '' or subdomain is None:
    subdomain = 'ja'

  try:
    lang_setting = subdomain_dict[subdomain]
  except:
    lang_setting = 'ja'
  
  lang_obj = Lang.query.filter_by(language=lang_setting).first()
  lang_id = lang_obj.id
  return lang_id