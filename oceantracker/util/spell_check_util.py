import difflib
def spell_check(key, key_list , msg_logger,msg, crumbs=None):
    # check if key in key_list and offer suggestions if not
    msg_logger.msg(f'"{key}" is not recognised, ' + msg, crumbs=crumbs,
                          hint=f'Closest matches to "{key}" = {difflib.get_close_matches(key, list(key_list), cutoff=0.4)} ?? ',
                          warning=True)
