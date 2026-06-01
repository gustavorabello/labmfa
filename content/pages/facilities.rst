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

Complementing its experimental tools, LabMFA maintains a strong numerical
modeling infrastructure focused on high-fidelity simulation of complex fluid
flows:

- **High-Performance Computing**:

LabMFA operates a modern computing infrastructure that combines powerful
servers, high-speed networking, and secure data storage, supporting advanced
numerical simulations in fluid mechanics, aerodynamics, and multiphase flows.

The cluster includes 3-noded Dell servers with complementary configurations:

**a)** The first is a Dell R650xs (hostname abeto), equipped with two Intel
Xeon Silver 4316 processors running at 2.30 GHz, each with **20 cores (40
total)**, 50 MB of L2 cache and 60 MB of L3 cache. It provides 256 GB of RAM
(4×64 GB RDIMM, 3200 MT/s, Dual Rank) and **960 GB of SSD storage**, optimized
for multiphysics simulations requiring high memory bandwidth.

**b)** The second, also a Dell R650xs (hostname pinho), features the same dual
Intel Xeon Silver 4316 processors at 2.30 GHz, for a total of **40 cores**,
with 25 MB of L2 cache and 30 MB of L3 cache per processor. Like abeto, it
offers 256 GB of RAM and **960 GB of SSD storage**, ensuring redundancy and
balanced performance across the system.

**c)** The third, a Dell PowerEdge R650 (hostname jacaranda), is configured
with a single Intel Xeon Gold 6348 processor at 2.60 GHz, offering **28
cores**, 35 MB of L2 cache, and 42 MB of L3 cache. It is equipped with 128 GB
of RAM (4×32 GB RDIMM, 3200 MT/s, Dual Rank) and a larger **1.87 TB SSD**,
making it particularly suitable for jobs requiring faster core performance and
expanded storage.

Complementing the servers, LabMFA maintains a Synology NAS system with a
dual-core 2.3 GHz processor, 4 GB of memory, and 24 TB of RAID-configured
storage, dedicated to the safe organization, archiving, and backup of
large-scale scientific datasets.

To guarantee high throughput and efficient communication between nodes and
storage, the infrastructure is interconnected via a 48-port 10 Gbit/s
high-speed switch, enabling fast data transfer, parallel computing scalability,
and seamless integration across the cluster.

Together, these resources form a reliable, scalable, and versatile HPC
environment, enabling researchers and students to tackle complex problems in
computational fluid dynamics, turbulence, multiphase flows, and coupled
fluid-structure interaction.

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

LabMFA maintains two dedicated wind tunnels that allow researchers, students, and collaborators to investigate a wide range of aerodynamic problems. Together, they combine versatility, precision, and accessibility, forming a unique environment for both high-level research and teaching.

Wind Tunnel 1 – High-Speed Subsonic Facility
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Our first wind tunnel is a **low-speed, open-circuit subsonic facility** operating at **ambient laboratory temperature**. It was designed to perform high-fidelity aerodynamic tests and validate numerical models under controlled conditions.

**Main Features:**

**Geometry and Structure**

- Test section: **41 cm × 32 cm**, length **180 cm**
- Blue metallic-wall construction, with **transparent and removable panels** that facilitate optical access and easy model installation

**Flow Conditions**

- Maximum airspeed: **110 km/h** (≈ 30.6 m/s)
- Speed variation achieved with **flux blockers** (without frequency inverters)
- Driven by a **powerful axial fan** ensuring steady and uniform airflow

**Flow Conditioning**

- **Equally spaced screens** minimize turbulence and stabilize the velocity profile in the test section

**Instrumentation**

- **Custom-built 3-component balance** for lift, drag, and moment forces
- **Pitot tube** for velocity calibration
- **Manometers** for static and differential pressure
- **Automation system** for programmed sweeps in **angle of attack, yaw, and pitch**

**Applications**

- Precision aerodynamic testing of airfoils and small-scale devices
- Benchmarking and validation of computational models
- Studies of flow separation, transition, and thin-film formation

Wind Tunnel 2 – Large Cross-Section Facility
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The second wind tunnel was developed to complement the high-speed system. With a **larger cross-section** and **lower maximum speed**, it is particularly suitable for **educational use**, flow visualization, and tests requiring more space.

**Main Features:**

**Geometry and Structure**

- Test section: **100 cm × 100 cm**, length **100 cm**
- Solid **wooden walls** with **transparent and removable panels** for accessibility and visualization

**Flow Conditions**

- Maximum airspeed: **10 km/h** (≈ 2.8 m/s)
- Flow control by **flux blockers**
- Driven by an **axial fan**

**Flow Conditioning**

- **Equally spaced screens** to align and stabilize airflow across the wide section

**Instrumentation**

- **Pitot tube** for velocity measurements
- **Manometer** for pressure readings

**Applications**

- Teaching and training in experimental aerodynamics
- Calibration of instruments and sensors
- Flow visualization at larger scales
- Low-speed studies for conceptual and educational demonstrations

LabMFA Wind Tunnel Capabilities
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

By maintaining **two complementary wind tunnels**, LabMFA offers a flexible platform that serves both **cutting-edge research** and **educational training**:

  - The **first tunnel** provides the **high-speed precision** required for academic and industrial-grade aerodynamic investigations.
  - The **second tunnel** provides a **large workspace** for low-speed flows, making it ideal for teaching, outreach, and practical training of students.

Selected Student Work
~~~~~~~~~~~~~~~~~~~~~

Selected undergraduate final projects supervised by **Prof. Gustavo R. Anjos**
or **Prof. Gustavo Cesar Rachid Bodstein** and associated with the LabMFA wind
tunnel activities include:

**Directly related to the LabMFA wind tunnels and force-balance infrastructure**

- `Projeto e Construção de um Túnel de Vento Subsônico de Baixo Custo`_ (Ana Maria Dantas Balmant, 2025), focused on the design and construction of a low-cost subsonic wind tunnel.
- `Projeto de um Túnel de Vento Subsônico do Tipo Soprador`_ (Felipe Rodrigues Coutinho, 2014), documenting the design of a blower-type subsonic wind tunnel.
- `Desenvolvimento de um Sistema de Aquisição de Dados e Instrumentação de uma Balança de Três Graus de Liberdade para Túnel de Vento`_ (Henrique Martins Lima, 2007), covering the data-acquisition system and instrumentation of a three-degree-of-freedom wind-tunnel balance.
- `Concepção e Projeto de uma Balança de Três Graus de Liberdade para Medição de Esforços Aerodinâmicos sobre Corpos no Túnel de Vento I do LABMFA`_ (Marcelo de Carvalho Bonniard and Patrick Paquelet Pereira, 2004), dedicated to the conception and design of the balance used in Wind Tunnel I.

**Related aerodynamic studies**

- `Modelagem e Análise Aerodinâmica de Corpos Bidimensionais via Método dos Elementos Finitos`_ (Vinicius Waldileme Coelho Mota, 2026), a recent aerodynamic study supervised by Prof. Gustavo R. Anjos and aligned with the laboratory's wind-tunnel and CFD activities.
- `Projeto e Otimização Aerodinâmica de uma Aeronave Blended Wing Body para Aviação Comercial`_ (Victor Patzi Lavina Duran, 2024), a recent aerodynamic design study aligned with the laboratory's wind-tunnel and CFD interests.
- `Projeto Aerodinâmico de um Avião de Treinamento Primário e Acrobático`_ (Luiz Gustavo Merçon Oliveira Costa, 2013), addressing aerodynamic aircraft design methods.
- `Estudo de Desempenho do Planador ASTIR III Classe Standard pelo Método da Colocação a Partir da Teoria da Linha de Sustentação de Prandtl`_ (Bruno Henrique Salvador Amorim, 2013), a related aerodynamic performance study.

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

The **experimental facilities**, combined with LabMFA’s **advanced numerical
infrastructure**, provide an integrated environment where **experiments and
simulations complement each other seamlessly**. This synergy enables
high-precision validation of computational models and fosters innovative
research in multiphase flows, aerodynamics, and heat transfer. Together, these
capabilities establish LabMFA as a national reference center and a **unique hub
in Brazil for fluid mechanics and aerodynamics**, open to collaboration with
academic institutions, industry partners, and outreach initiatives that bring
science closer to society.

LabMFA is strategically located within the **Technology Center of the Federal
University of Rio de Janeiro (UFRJ)**, on Ilha do Fundão. Positioned inside
COPPE, one of Latin America’s largest graduate engineering institutes, the
laboratory benefits from a **dynamic collaborative ecosystem** and close
integration with a wide network of specialized research groups and
laboratories. This environment not only strengthens interdisciplinary projects
but also provides researchers and students with direct access to **cutting-edge
resources** and an international academic community.

.. Place your references here
.. _Projeto e Construção de um Túnel de Vento Subsônico de Baixo Custo: /documents/anaMariaBalmant-tcc-tunel-vento.pdf
.. _Projeto de um Túnel de Vento Subsônico do Tipo Soprador: /documents/felipeCoutinho-tcc-tunel-vento.pdf
.. _Desenvolvimento de um Sistema de Aquisição de Dados e Instrumentação de uma Balança de Três Graus de Liberdade para Túnel de Vento: /documents/henriqueMartinsLima-tcc-aquisicao-balanca-tunel-vento.pdf
.. _Concepção e Projeto de uma Balança de Três Graus de Liberdade para Medição de Esforços Aerodinâmicos sobre Corpos no Túnel de Vento I do LABMFA: /documents/marceloBonniard-patrickPereira-tcc-balanca-tunel-vento.pdf
.. _Modelagem e Análise Aerodinâmica de Corpos Bidimensionais via Método dos Elementos Finitos: /documents/viniciusMota-tcc-corpos-bidimensionais-aerodinamica.pdf
.. _Projeto e Otimização Aerodinâmica de uma Aeronave Blended Wing Body para Aviação Comercial: /documents/victorPatzi-tcc-bwb-aerodinamica.pdf
.. _Projeto Aerodinâmico de um Avião de Treinamento Primário e Acrobático: /documents/luizGustavoCosta-tcc-aviao-aerodinamico.pdf
.. _Estudo de Desempenho do Planador ASTIR III Classe Standard pelo Método da Colocação a Partir da Teoria da Linha de Sustentação de Prandtl: /documents/brunoAmorim-tcc-planador-astir.pdf
.. _Finite Element Method: https://en.wikipedia.org/wiki/Finite_element_method
