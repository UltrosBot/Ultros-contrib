Ultros-contrib
==============

This repo contains packages for Ultros that have either been contributed by people other than the core development team,
or that the core team considers to be extra functionality.

Packages may contain plugins, protocols, utils, and otherwise pretty much any files the developer requires.

Installing packages
-------------------

To install packages from this repository, please use the `packages.py` program which is included with the
main Ultros distribution, [here](https://github.com/UltrosBot/Ultros). Please note that this package
manager is not complete or well-written; we'll be rewriting it when we have time. Usage is as follows:

`$ python packages.py <command> [options]`

The package manager requires Pip, but you should already have installed that if you followed the
[setup instructions in the wiki](https://github.com/UltrosBot/Ultros/wiki/Requirements) over on the main
Ultros repository.

**Note: Package names are case-sensitive and usually start with a capital letter**

* Management commands
    * `install <package>` - Installs a package, provided it's not already installed.
    * `update <package>` - Update (reinstall) a currently installed package.
    * `update all` - Update (reinstall) all currently installed packages.
    * `uninstall <package>` - Uninstall a currently installed package.
* Informational operations
    * `list` - List all available packages.
    * `list-installed` - List all installed packages.
    * `info <package>` - Show information for a single package.
* Other operations
    * `help` - Shows a help message similar to this list of commands.

Contributing
------------

If you'd like to add to this repository, please take note of the following guidelines..

* Packages must have a file structure that matches Ultros' file structure - making installation a simple copy and paste of a set of files.
* Every package must contain a README.md file, written using GitHub-flavored Markdown.
* Every package must include a LICENSE file. The license doesn't have to match the Ultros core license.
  * Be sure to reference the file or license in your plugin's .plug files, if you have any.
  * Licenses must be open-source licenses; a good place to find these licenses is [the Open Source Initiative](http://opensource.org/licenses)
* Every package must include both a package.yml and versions.yml file.
  * These yaml-based files will be used by the package installation script. There'll be more info on this when the script is finished.
    * Contact one of the repo maintainers if you need help with these files.
* If your plugin needs configuration, include an example configuration file.
* Do not commit libraries if you didn't develop them. List them in your package.yml, if they're available from pip.
  * If that's not the case, list them in your README.md file.
* Test your code. Make sure it works. You don't have to supply a test suite, but we will be manually testing all submitted code.
* Obviously, don't submit anything malicious. Don't bother trying to wreck our computers with malicious code either; we do our testing in VMs.

Other than that, your package has no restrictions. It can contain plugins, protocols, a mixture of both, or even a set of dev tools for your other packages.

The best way to submit a package is to fork this repo, modify your copy of it, and then submit a pull request with your changes.
A member of the core dev team will look over your code and test it, and will either approve or deny it within a couple days.

