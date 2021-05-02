def concat_realname(first_name, middle_name, last_name):
  
  def none_to_str(name):
    if name is None:
      return ""
    else:
      return name

  name = none_to_str(first_name) + " " + none_to_str(middle_name) + " " + none_to_str(last_name)
  return name