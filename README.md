dlen
====

dlen for a world with less code.

Check the length of the method (maximum 20 lines) and
the class (maximum 500 lines). To keep your code clean and clear
you should always try to avoid having too many lines of code.
Also recommended to use pep8, isort, pydocstyle pack.

Getting Started
===============

Supports Python 2.7+

Installing
==========

```
git clone git@github.com:Endika/dlen.git
cd dlen
python setup.py install
```

Or

```
pip install dlen
```

Using dlen
==========

```
dlen my_script.py
```

Output

```
[ERROR] 'my_script.py' big_function function too long (25 > 20 lines)
[WARN] 'my_script.py' my_function function too long (13 > 12 lines)
```

Or

```
dlen .
dlen /path/project
```

Authors
=======

* **Endika Iglesias** - https://github.com/Endika
