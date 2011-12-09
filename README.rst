JsLint Checker for Sublimt Text 2
====

Almost whole implementation stolen from `sublimetext_python_checker <https://github.com/vorushin/sublimetext_python_checker>`_ by 
**Roman Vorushin**

*Author*: Maksym Klymyshyn

*Blog*: `Django and Other <http://djangoandother.blogspot.com>`_.

Changes
============
#. **December 10, 2011** – JsLint tool execution (*JsLint4Java*) moved to separate thread so now plugin becoming useful for daily usage

Installation
============

#. Clone source into *Sublime Packages Folder* (``Preferences -> Browse Packages``)

#. Change path to *jslint4java* and arguments for it in ``local_settings.py``

#. Restart Sublime

Dependencies
============

JsChecker Package tested only with *jslint4java* but it should work with
other jslint execution methods like *node* or *rhino*. Tested way of execution
of JsLint is quite slow and I will rework it in future to speed up checks.

#. `JsLint4Java <http://code.google.com/p/jslint4java/>`_.