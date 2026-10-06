MinervaMesh
-----------

:date: 2026-10-06 17:00
:modified: 2026-10-06 17:00
:slug: minervamesh
:summary: MinervaMesh, an in-browser platform for numerical simulation in engineering education

**MinervaMesh** is an educational web platform for numerical simulations in
heat transfer, fluid mechanics and structural analysis. Every simulation runs
entirely in the browser: the Python solvers (NumPy, SciPy, Matplotlib) are
executed client-side through PyScript and Pyodide, so there is no backend,
no installation and no account. Open a module, set the physical and numerical
parameters, run it and compare the result with the analytical or reference
solution. The source code of each solver can be inspected directly from the
page.

**→** `Open MinervaMesh <{static}/minervamesh/app/index.html>`_

|

The current modules, based on the finite element and finite difference
methods, range from 1D conduction and beams to 2D potential flow and
incompressible Navier-Stokes. Each module is a self-contained page (HTML, a Python solver and a package
list), so new simulations can be added without touching the rest of the
platform.

|

About
_____

MinervaMesh was developed by **Luiz Gustavo Santos Farias** as his undergraduate
final project in Mechanical Engineering at Escola Politécnica, UFRJ,
supervised by Prof. Gustavo Rabello dos Anjos. It is open source under the
MIT license. Source code: `github.com/lgsfarias/minervamesh`_ (the version
served here is recorded in ``VERSION``).

.. _github.com/lgsfarias/minervamesh: https://github.com/lgsfarias/minervamesh
