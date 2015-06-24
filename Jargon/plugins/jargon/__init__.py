import random
from boltons.cacheutils import LRU

from system.command_manager import CommandManager

import system.plugin as plugin

from system.storage.formats import YAML
from system.storage.manager import StorageManager


__author__ = 'Sean'


JARGON_PERM = "jargon.jargon"
JARGON_LIST_PERM = "jargon.jargonlist"
JARGON_CATEGORY_PERM = JARGON_PERM + ".%s"


class JargonException(Exception):
    """
    Generic exception for the Jargon plugin.
    """
    pass


class InvalidCategory(JargonException):
    """
    Invalid Jargon category.
    """
    pass


class JargonPlugin(plugin.PluginObject):

    commands = None
    storage = None

    _file_config = None
    _config = None
    _word_cache = None

    def setup(self):
        ### Grab important shit
        self.commands = CommandManager()
        self.storage = StorageManager()

        ### Initial config load
        try:
            self._file_config = self.storage.get_file(
                self,
                "config",
                YAML,
                "plugins/jargon.yml"
            )
        except Exception:
            self.logger.exception("Error loading configuration!")
            self.logger.error("Disabling...")
            self._disable_self()
            return
        if not self._file_config.exists:
            self.logger.error("Unable to find config/plugins/jargon.yml")
            self.logger.error("Disabling...")
            self._disable_self()
            return

        self._file_config.add_callback(self.load)
        self.load()

        ### Register commands
        self.commands.register_command(
            "jargon",
            self.jargon_cmd,
            self,
            JARGON_PERM,
            aliases=["generatesentence", "generate"],
            default=True
        )
        self.commands.register_command(
            "jargonlist",
            self.jargonlist_cmd,
            self,
            JARGON_LIST_PERM,
            aliases=["generatesentencelist", "generatelist"],
            default=True
        )
        # TODO: jargonlist command for themes

    def reload(self):
        try:
            self._file_config.reload()
        except Exception:
            self.logger.exception("Error reloading configuration!")
            return False
        self.load()
        return True

    def load(self):
        self._config = convert_config(self._file_config)
        self._word_cache = LRU(self.cache_size)

    def _respond(self, target, message):
        if self.prefix_response:
            message = "[Jargon] " + message
        target.respond(message)

    @property
    def per_category_permissions(self):
        return self._config.get("per_category_permissions", False)

    @property
    def prefix_response(self):
        return self._config.get("prefix_response", False)

    @property
    def cache_size(self):
        # This cache should pretty much never miss unless someone has a heck of
        # a lot of categories, but hey, it's just as easy to implement as a
        # limitless dict thanks to the boltons package, and some people are
        # running Ultros in very low memory environments where every little
        # helps.
        return self._config.get("cache_size", 64)

    @property
    def _categories(self):
        return self._config.get("categories", {})

    def _get_category(self, category):
        try:
            return self._categories[category]
        except LookupError:
            self.logger.trace(
                'Invalid category "{}" - trying aliases',
                category
            )
            for k, v in self._categories.iteritems():
                if category in v.get("names", []):
                    return v

        self.logger.warning('Invalid category "{}" given', category)
        raise InvalidCategory()

    def _get_format_args(self, category, category_name):
        # This is what happens when you adds things as an after thought rather
        # than planning shit out...
        # Make sure we always use the same name to cache the category
        category_name = category.get("names", [category_name])[0]
        try:
            return self._word_cache[category_name]
        except KeyError:
            self.logger.debug("Word cache miss")
        words = {}
        for k, v in category["words"].iteritems():
            if k == "noun":
                words[k] = Nouns(v)
            elif k == "verb":
                words[k] = Verbs(v)
            else:
                words[k] = WordClass(v)
        self._word_cache[category_name] = words
        return words

    def _check_category_perm(self, category, caller, source, protocol,
                             cat=None):
        if cat is None:
            cat = self._get_category(category)
        category = cat.get("names", [category])[0]
        self.logger.debug('Checking permission for category "{}"', category)
        return self.commands.perm_handler.check(
            JARGON_CATEGORY_PERM % category,
            caller,
            source,
            protocol
        )

    def jargon_cmd(self, protocol, caller, source, command, raw_args,
                   parsed_args):
        if len(raw_args) > 0:
            cat = raw_args.lower()
        else:
            cat = None
        if self.per_category_permissions:
            if cat is None:
                try:
                    cat = self._config["default"]
                except KeyError:
                    self.logger.error(
                        "Cannot have per_category_permissions without default"
                    )
                    return
            if not self._check_category_perm(cat, caller, source, protocol):
                caller.respond("You don't have permission to do that")
                return
        gen_kwargs = {}
        if cat:
            gen_kwargs["category"] = cat
        try:
            self._respond(source, self.generate_sentence(**gen_kwargs))
        except InvalidCategory:
            caller.respond("I don't know any jargon for that")

    def jargonlist_cmd(self, protocol, caller, source, command, raw_args,
                       parsed_args):
        categories = self._config.get("categories", {}).iteritems()
        if self.per_category_permissions:
            # Perm check spam time!
            def _cat_filter(cat):
                return self._check_category_perm(cat[0], caller, source,
                                                 protocol, cat[1])
            categories = filter(_cat_filter, categories)
        categories = map(lambda c: c[1].get("names", [c[0]])[0], categories)
        self._respond(source, "Categories: " + ", ".join(categories))

    def generate_sentence(self, category=None):
        if category is None:
            category = self._config.get("default", None)
            if category is None:
                category = random.choice(self._config["categories"].keys())
        cat = self._get_category(category)
        fmt = random.choice(cat["formats"])
        fmt_args = self._get_format_args(cat, category)
        sentence = fmt.format(**fmt_args)
        if cat.get("options", {}).get("capitalise_start", True):
            sentence = sentence[0].upper() + sentence[1:]
        return sentence


class WordClass(object):

    aliases = {}

    def __init__(self, words, base_form="base"):
        self.words = words
        self.base_form = base_form

    @property
    def base(self):
        return self.get_form(self.base_form)

    def __getattr__(self, item):
        if item.startswith("generate_form_"):
            raise AttributeError()
        return self.get_form(item)

    def get_form(self, form):
        word = random.choice(self.words)
        if isinstance(word, dict):
            # Word is a collection of forms
            if form in word:
                return word[form]
            elif form in self.aliases and self.aliases[form] in word:
                return word[self.aliases[form]]
            else:
                # Unknown form - select base
                return self._generate_form(word[self.base_form], form)
        else:
            # Word is base form only
            return self._generate_form(word, form)

    def __str__(self):
        return self.base

    def _generate_form(self, word, form):
        generator_name = "generate_form_%s" % form
        if hasattr(self, generator_name):
            return getattr(self, generator_name)(word)
        else:
            return word


class Nouns(WordClass):

    def __init__(self, words, base_form="singular"):
        super(Nouns, self).__init__(words=words, base_form=base_form)

    @staticmethod
    def generate_form_plural(word):
        if word[-1] == "s":
            suffix = "es"
        else:
            suffix = "s"
        return word + suffix


class Verbs(WordClass):

    aliases = {
        "s": "present",
        "ing": "present_participle",
        "ed": "past"
    }

    @staticmethod
    def generate_form_past(word):
        if word[-1] == "e":
            suffix = "d"
        else:
            suffix = "ed"
        return word + suffix
    generate_form_ed = generate_form_past
    # Past participle is same as past for regular verbs, and the naive form
    # generation here is for regular verbs anyway.
    generate_form_past_participle = generate_form_past

    @staticmethod
    def generate_form_present(word):
        if word[-1] == "s":
            suffix = "es"
        else:
            suffix = "s"
        return word + suffix
    generate_form_s = generate_form_present

    @staticmethod
    def generate_form_present_participle(word):
        if word[-1] == "e":
            word = word[:-1]
        return word + "ing"
    generate_form_ing = generate_form_present_participle


def convert_config(config, **kwargs):
    config_version = config.get("version", 1)
    if config_version == 2:
        return config
    if config_version not in (1,):
        raise ValueError(
            "Cannot convert config of version %s" % config_version
        )
    # Set some defaults for version 1 config
    theme = kwargs.get("theme", "technology")
    new_config = {
        "version": 2,
        "default": theme,
        "categories": {
            theme: {
                "formats": [],
                "words": {
                    "abbreviation": [],
                    "adjective": [],
                    "noun": [],
                    "verb": []
                }
            }
        }
    }
    new_theme = new_config["categories"][theme]
    new_formats = new_theme["formats"]
    new_words = new_theme["words"]
    for old_format in config["formats"]:
        types = []
        for type in old_format["types"]:
            if type == "verbing":
                type = "verb.ing"
            types.append("{%s}" % type)
        new_formats.append(
            old_format["format"] % tuple(types)
        )

    for word in config["abbreviations"]:
        new_words["abbreviation"].append(word)

    for word in config["adjectives"]:
        new_words["adjective"].append(word)

    for word in config["nouns"]:
        new_words["noun"].append(word)

    for word in config["verbs"]:
        new_word = {}
        if "plain" in word:
            new_word["plain"] = word["plain"]  # Backwards compatible
            new_word["base"] = word["plain"]  # Correct
        else:
            raise ValueError('Invalid verb "%s" has no "plain" form' % word)
        if "ing" in word:
            new_word["ing"] = word["ing"]  # Backwards compatible
            new_word["present_participle"] = word["ing"]  # Correct
        if len(new_word) == 1 and "base" in new_word:
            new_word = new_word["base"]
        new_words["verb"].append(new_word)

    return new_config
