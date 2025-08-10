Facilities
----------

:date: 2022-08-23 17:47
:modified: 2022-08-23 17:47
:slug: facilities
:summary: Facilities in LabMFA

The Fluid Mechanics and Aerodynamics Laboratory (LabMFA) at COPPE/UFRJ provides
a state-of-the-art infrastructure that supports both experimental and numerical
research in fluid dynamics, aerodynamics, heat transfer, and multiphase flow
simulations.

Numerical Facilities
====================

Complementing its experimental tools, LabMFA maintains a strong numerical modeling infrastructure focused on high-fidelity simulation of complex fluid flows:

- **High-Performance Computing**:
  LabMFA utilizes the computational infrastructure of COPPE/UFRJ, with access to high-performance clusters for parallel computing.

- **In-House Simulation Tools**:
  The group develops custom solvers implemented in C++ and Python, integrating:
  - Finite Element Methods (FEM)
  - Arbitrary Lagrangian–Eulerian (ALE) mesh motion
  - High-order semi-Lagrangian advection
  - Explicit interface-tracking with curvature estimation via Laplace–Beltrami operators

- **Simulation Capabilities**:
  - Single- and two-phase flows with deformable interfaces
  - Non-Newtonian and viscoelastic models
  - Fluid-structure interaction including rigid body motion
  - Conjugate heat transfer and thermal convection

- **Applications Include**:
  - Microbubble coalescence and breakup
  - Biomedical and industrial flow modeling
  - Wind energy simulations
  - CO₂ capture, transport, and sequestration in porous media

Images and graphs include:
- Photographs of the Dell and SGI high-performance computing clusters used for parallel simulations.
- Rack-mounted server systems highlighting the lab’s computing infrastructure.
- A SGI - Sylicon Graphics International - cluster used to perform
multiprocessor/multicore parallel simulations is shown in the figure above.
This cluster has been bought for a P&D project of the oil&gas industry in
Brazil

.. list-table::
   :widths: 50 50
   :align: center
   :class: borderless

   * - .. image:: {static}/images/sgi.png
         :width: 100%
         :alt: A SGI - Sylicon Graphics International - cluster
     - .. image:: {static}/images/dell_1.png
         :width: 100%
         :alt: Dell cluster with 3 Xeon nodes
   * - .. image:: {static}/images/dell_2.png
         :width: 100%
         :alt: back of the Dell cluster
     - .. image:: {static}/images/dell_2.png
         :width: 100%
         :alt: back of the Dell cluster

Experimental Facilities
=======================

LabMFA houses a low-speed, open-circuit wind tunnel designed for academic and research applications. Key features include:

- **Custom-Built 3-Component Balance**:
  Developed in-house to enable precise measurement of aerodynamic forces (lift, drag, and pitching moment) acting on various test bodies.

- **Aerodynamic Testing**:
  Several profiles can be tested, including NACA and GOE airfoils. Results have been validated through benchmark comparisons against standard datasets such as Blevins (1984).

- **Multirange Flow Control**:
  The wind tunnel supports continuous and precise adjustment of airflow velocities, allowing a wide spectrum of test conditions.

- **Data Visualization and Analysis**:
  Lift (Cl) and drag (Cd) coefficients are measured across varying angles of attack, producing curves that match well with theoretical expectations and experimental benchmarks.

- **Research Applications**:
  - Airfoil performance and optimization
  - Flow separation and transition studies
  - Small-scale wind energy systems

Images and graphs include:
- General and front views of the wind tunnel test section and balance setup.
- Plots comparing experimental lift and drag coefficients with standard
reference data.

.. list-table::
   :widths: 50 50
   :align: center
   :class: borderless

   * - .. image:: {static}/images/tunelAzul-rendered.png
         :width: 100%
         :alt: Wind tunnel Rendered
     - .. image:: {static}/images/tunnel_1.png
         :width: 100%
         :alt: Detailed view of wind tunnel test section

   * - .. image:: {static}/images/tunnel_2.png
         :width: 100%
         :alt: Front view of the aerodynamic balance
     - .. image:: {static}/images/balance.png
         :width: 100%
         :alt: General view of the balance setup

   * - .. image:: {static}/images/data_comparison_1.png
         :width: 100%
         :alt: Angle of attack vs Lift coefficient
     - .. image:: {static}/images/data_comparison_2.png
         :width: 100%
         :alt: Angle of attack vs Drag coefficient


Location and Integration
========================

LabMFA is located within the Technology Center of the Federal University of Rio
de Janeiro (UFRJ), on Ilha do Fundão. The lab benefits from a collaborative
research environment and is integrated into a wider network of engineering
research laboratories at COPPE.

.. Place your references here
.. _Finite Element Method: https://en.wikipedia.org/wiki/Finite_element_method
