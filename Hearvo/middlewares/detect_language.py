
import tldextract
from Hearvo.models import Country
from Hearvo.apis.logger_api import logger_api

subdomain_dict = {
  'jp': 'jp',
  'us': 'us',
  'uk': 'uk',
}

# def get_lang_id(base_url):
#   """
#   get lang_id by extracting the subdomain of the request url. e.g. jp.hearvo.vo >> jp

#   For now this works fine. But for the future iOS and Android releases, we need to change this to use header instead of dechiphering the subdomain of the request url.
  
#   And also, we may not need Lang table since we can just set the one-to-one relation in Python dict like the above subdomain_dict.

#   request.headers["Language"]
#   """
#   ext = tldextract.extract(base_url)
#   subdomain = ext.subdomain

#   logger_api("ext", ext)

#   if subdomain == '' or subdomain is None:
#     subdomain = 'jp'

#   try:
#     lang_setting = subdomain_dict[subdomain]
#   except:
#     lang_setting = 'jp'
  
#   lang_obj = Lang.query.filter_by(language=lang_setting).first()
#   country_id = lang_obj.id
#   return country_id



def get_country_id(request):
  country = request.headers["Country"] if "Country" in request.headers.keys() else "jp"
  country = Country.query.filter_by(country=country).first()
  if country is None:
    country_id = 1 # jp
  else:
    country_id = country.id

  logger_api("country",country)
  logger_api("country_id",country_id)

  return country_id
