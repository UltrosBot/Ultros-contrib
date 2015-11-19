Handler Formatting
==================

This plugin uses the same formatting constructs as URL-tools. If you understand how that
works, then continue on to the individual handler formatting below - Otherwise,
[click here](https://github.com/UltrosBot/Ultros-contrib/blob/master/URL-tools/FORMATTING.md) 
for documentation.

Handler formatting
==================

Currently, the handlers that this plugin supports for customization are:

* [F-List](#f-list)

More of these will be added over time.

To change a formatting string, open your `urltools-nsfw.yml`, find the section for
the handler you want to customize, and add the corresponding key and value to
the `formatting` section.

Most handler sections below will contain a sample URL to be matched, as well as
links to the API documentation that point to up-to-date data samples.

F-List
------

Each formatting string below has a key named `given` available to it, which refers
to a dictionary that itself contains some keys. You can access this using `[` 
square brackets `]`, like so: `{given[key]}`

### Key: user

* **Example URL**: `https://f-list.net/c/<character-name>`
* **API documentation**: N/A, unfortunately - see below
* `given`: `user`

**Default string**:

```
!!python/unicode "[GitHub user] {name} ({login}) - {public_repos} repos / {public_gists} gists - {followers} followers / {following} following - {blog}"
```

**Sample data**:

Unfortunately F-List's v1 API is quite nasty, so this plugin flattens the data and 
makes it reasonable for use. For that reason, the data below is not what the API provides,
it contains a set of keys you can use in your formatting string.

* `general_details`: *This is not an exhaustive list; note that the API omits anything the user didn't fill in*
    * `apparent_age`
    * `orientation`
    * `relationship`
    * `fur/scale/skin_color`
    * `gender`
    * `age`
    * `eye_color`
    * `weight`
    * `height/length`
    * `hair`
    * `body_type`
    * `build`
    * `personality`
    * `species`
    * `location`
* `rping_preferences`: *This is not an exhaustive list; note that the API omits anything the user didn't fill in*
    * `desired_post_length`
    * `language_preference`
    * `post_perspective`
    * `furry_preference`
    * `currently_looking_for`
    * `grammar_competence_required`
    * `desired_rp_length`
    * `desired_rp_method`
    * `grammar_competence`
* `sample_kinks`: *Random samples of kinks*
    * `fave`
    * `yes`
    * `maybe`
    * `no`

If we've missed something important here, feel free to submit a pull request. You may be able to deduce some keys
from the profile pages on the site as well.
