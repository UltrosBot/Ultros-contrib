__author__ = 'bw5'


def not_found_error():
    return {
        "error": "not_found",
        "error_msg": "Route not found"
    }


def permissions_error(perm):
    return {
        "error": "permissions",
        "permission": perm,
        "error_msg": "Missing permission: %s" % perm
    }


def invalid_key_error():
    return {
        "error": "invalid_key",
        "error_msg": "Invalid API key"
    }
