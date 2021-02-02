👩‍🏫 Introduction
====================
Hammurabi[hmrb] is a system designed to efficiently execute rules on sequences of data. Its rule syntax is simple and human-readable but also very expressive.

As input, the system takes a sequence of hash tables (Python ``dict``) and is capable of matching any combination of key-value pairs in order. It was designed as a task agnostic framework applicable to a variety of tasks, for instance, intent recognition, text annotation and log monitoring.

Features
---------

- Attribute level rule definitions using key-values pairs
- Efficient matching of sequence using hash tables with no limit on length
- Support for nested boolean expressions and wildcard operators similar to regular expressions
- Variables can be side-loaded and reused throughout different rule sets
- User-defined rule-level callback functions triggered by a match
- Labels to tag and retrieve matched sequence segments

Rationale
----------
Rules and heuristics are often used to kick start a project which has insufficient data for a machine learning solution. Hammurabi was built to abstract away these rules and heuristics and make them simple, reliable and explainable. This reduces the effort of building, testing and maintaining early-stage products.


Release History
---------------
:Version: ``v1.1.0 (02.02.2021)``

          ``v1.0.0 (29.04.2020)``
