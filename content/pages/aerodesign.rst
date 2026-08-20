Minerva Aerodesign
------------------

:date: 2024-12-22 13:47
:modified: 2026-08-19 10:00
:slug: aerodesign
:summary: Minerva Aerodesign

Founded in 2001, the Minerva Aerodesign team is responsible for creating
an Unmanned Aerial Vehicle (UAV) capable of carrying the largest
possible load within geometric, propulsion and flight specifications,
determined by the rules of the competition in which the team
participates. The members design and perform tests using software,
structurally test materials and prototypes, and build the model
aircraft.

Hosted by LabMFA since its foundation, Minerva Aerodesign is the oldest
student competition team of UFRJ and has taken part in the SAE Brasil
AeroDesign competition since 2003. The team acts as a strategic link
between undergraduate teaching and the aeronautical sciences, and has
become an important entry door both to graduate studies and to a
professional career in the sector.

|

.. image:: {static}/images/aero.png
   :name: aero
   :width: 100%
   :alt: aero

|

The team's mission is to deepen technical knowledge, develop management
skills and foster new ideas. It provides strong teamwork experience due
to the constant need for collaboration among members to develop the
project and manage the team, and each year seeks to improve project
development and improve results in competitions.

The activities of the team can be followed on `Instagram`_ and `LinkedIn`_.

Technical specialities
======================

The team organises its yearly design cycle around four technical
specialities, which are developed by its macro-areas of flight dynamics,
structural integrity, and systems and performance.

Multidisciplinary design optimization
_____________________________________

The team develops and maintains **Virtus**, an in-house Multidisciplinary
Design Optimization (MDO) framework that integrates all design areas from
the earliest stages of the project. Virtus is fed with parameters from
every macro-area and, following the bonus and penalty criteria of the
yearly competition rules, runs the optimization with `OpenMDAO`_ — a
Python framework for structuring and executing optimization problems —
coupled to `AVL`_ for the estimation of aerodynamic, stability and
control characteristics. The output defines the aircraft configuration
that maximises the competition score while satisfying the regulatory
constraints, and feeds the detailed design of each area up to
manufacturing.

In the 2025 cycle the model was substantially refined, with updated
airfoil libraries, structural masses and component weights, and with the
inclusion of alternative powerplant options in the optimization loop. The
same framework was used to compare different UAV typologies and
configurations against the competition constraints.

Computational simulations
_________________________

Computational Fluid Dynamics (CFD) analyses are carried out with
`OpenFOAM`_ as the high-fidelity complement to the lower-cost methods
used in the early design phases. The simulations resolve the flow around
the aircraft and are decisive for the definition of the winglets, the
fuselage geometry and the aerodynamic behaviour of wing, empennage and
remaining lifting surfaces. Individual discretisation of the components
allows the contribution of each element to the global aerodynamic
performance to be quantified.

Dynamic behaviour is assessed with AVL together with linear-system
analyses implemented in Python, evaluating the aircraft response in the
time and frequency domains and verifying dynamic stability against
consolidated aeronautical standards. On the structural side, MATLAB and
Python are used to quantify and size the loads acting on the airframe,
AVL and `XFLR5`_ provide the aerodynamic loads on the lifting surfaces,
and static, dynamic and modal simulations are performed with `Ansys`_ and
`FEMAP`_. The powerplant is modelled in Python, MATLAB, `Simulink`_ and
`PSIM`_ to evaluate system behaviour, size the operational speeds and
analyse power-limiting strategies required by the competition rules.

.. figure:: {static}/images/aero_cfd.jpg
   :width: 100%
   :alt: CFD analysis of the flow around the aircraft

   Flow around the aircraft computed in OpenFOAM.

.. figure:: {static}/images/aero_fea.jpg
   :width: 100%
   :alt: Finite element analysis of the empennage

   Total deformation field of the empennage obtained by FEA.

Research and development of materials
_____________________________________

The structural integrity macro-area is responsible for the research,
evaluation and development of the materials used in the aircraft.
Mechanical tensile and flexural tests are performed on a wide range of
materials, including carbon-fibre and glass-fibre composites, carbon-fibre
sandwich structures with Divinycell core, balsa wood of different
densities, and polymers obtained by additive manufacturing (3D printing).

The experimental characterisation confirms the mechanical properties
adopted in the design, validating the computational models and increasing
their reliability. The studies developed by the team on composite and
polymeric materials are used as a technical reference by other teams in
the competition and are being organised for submission to a congress
promoted by SAE Brasil.

Electric propulsion systems
___________________________

The systems and performance macro-area continuously improves the electric
propulsion system, modelling and simulating the powerplant in Simulink
and PSIM in order to reproduce the motor behaviour throughout all flight
phases. Complementary studies address the design and manufacture of the
team's own propellers, covering modelling, simulation and fabrication.

The 2025 aircraft also carried an embedded telemetry system developed
entirely by the team, together with a dedicated electronic board designed,
assembled, soldered and functionally validated in-house — from the circuit
architecture and the selection of components to the final integration.
Both activities include ensuring the electrical compatibility between
subsystems and keeping the operation of the aircraft within the
established safety limits.

.. figure:: {static}/images/aero_telemetry.jpg
   :width: 100%
   :alt: Main dashboard of the embedded telemetry system

   Main dashboard of the telemetry system developed by the team, monitoring
   battery voltage and current, servo currents, airspeed, angle of attack,
   acceleration, altitude and the trajectory of the aircraft.

Recent projects and results
===========================

After the interruption caused by the pandemic, the team re-entered the
main competition through the 2021 access tournament and has since shown a
consistent recovery: 46th place in 2023, 32nd place in 2024 with the
*Noctua* project, and 22nd place out of 53 teams in 2025 with the
*Jacurutu* project — a gain of 24 positions in two seasons and the fifth
best result in the 25-year history of the team.

In the 2025 edition the team reached **17th place in the overall design
report stage**, placing among the twenty best teams of the competition,
with **4th place in structures and drawings**, 12th in electrical systems
and safety assessment (17.84 out of 25 points), and 15th in loads and
aeroelasticity. The integration report, supported by the MDO framework,
scored 11.40 points, an increase of 3.08 points with respect to 2024. The
*Jacurutu* aircraft performed two flights carrying a payload equal to or
greater than 7 kg, taking off and landing safely; the flights were
nevertheless invalidated by the technical committee due to a detail in the
tail-wheel connection. Even so, the power limitation that had penalised
the team in previous editions was overcome. In the same edition the team
was again recognised as the best team of the state of Rio de Janeiro in the
SAE Brasil AeroDesign competition.

.. figure:: {static}/images/aero_team_2025.jpg
   :width: 100%
   :alt: The team and the Jacurutu aircraft at SAE Brasil AeroDesign 2025

   The team and the *Jacurutu* aircraft at the SAE Brasil AeroDesign 2025
   competition, in São José dos Campos.

Competition record
==================

Results obtained in each edition of the SAE Brasil AeroDesign competition.

.. list-table::
   :widths: 15 30 55
   :header-rows: 1

   * - Year
     - Result
     - Highlights
   * - 2003
     - 28th of 48
     - First participation (*Darth Vader*)
   * - 2004
     - 23rd and 32nd of 51
     - Honourable mention for innovative design (*Cafifa* and *Júnior*)
   * - 2005
     - 36th of 46
     - First use of glass fibre (*FOCA*)
   * - 2006
     - 44th of 55
     - Conventional configuration in balsa wood
   * - 2007
     - 35th of 59
     - Top 10 performance reports (*AL*)
   * - 2009
     - 63rd of 84
     - 26th best report (*Duas Caras*)
   * - 2010
     - 37th of 66
     - Blended wing-body configuration (*Kinder Ovo*)
   * - 2011
     - 49th of 70
     - First in-house aerodynamic optimization program
   * - 2012
     - 21st of 73
     - Highest reliability bonus; best team of the state of Rio de Janeiro
   * - 2014
     - 21st of 59
     - *Omitizva*
   * - 2015
     - 17th of 62
     - Best result of the team; shortest cargo removal time (2.8 s), *Cavaco*
   * - 2016
     - 20th of 60
     - *Caveirão II*
   * - 2017
     - 23rd of 59
     - Best team of the state of Rio de Janeiro
   * - 2018
     - 45th of 60
     - Only maximum score in the drawings and structures report (*Jokozo*)
   * - 2021
     - 10th of 23
     - Access tournament; qualification to the 2022 main competition
   * - 2022
     - 53rd of 55
     - Recovery of techniques and knowledge after the pandemic
   * - 2023
     - 46th of 56
     - Return to the flight stage in São José dos Campos
   * - 2024
     - 32nd
     - *Noctua*
   * - 2025
     - 22nd of 53
     - Best team of the state of Rio de Janeiro; 17th in design reports and
       4th in structures (*Jacurutu*)

Results of the 2008 and 2013 editions could not be recovered. The team did
not compete in 2019 and 2020.

Main achievements
=================

 - Innovative Project Award (2004)
 - Reliability Award (2012)
 - Best Team Placement – 17th position (2015)
 - Embraer Award for Shortest Time to Remove Cargo from the Aircraft (2015)
 - Best team in the state of Rio de Janeiro in the SAE Brasil AeroDesign competition (2012, 2017, 2018 and 2025)
 - Maximum score in the drawings and structures report (2018)
 - 4th place in structures and 17th place in the design report stage (2025)

Engineering courses involved
============================

The team has a markedly multidisciplinary composition, gathering students
from eight undergraduate engineering courses of UFRJ — most of them at the
Escola Politécnica — and seeking support from different departments of the
university.

.. list-table::
   :widths: 72 28
   :header-rows: 1

   * - Course
     - Members
   * - Mechanical Engineering (`DEM|Poli|UFRJ`_)
     - 16
   * - Metallurgical and Materials Engineering (`DMM|Poli|UFRJ`_)
     - 5
   * - Electrical Engineering (`DEE|Poli|UFRJ`_)
     - 3
   * - Civil Engineering (`DCC|Poli|UFRJ`_)
     - 3
   * - Electronic Engineering (`DEL|Poli|UFRJ`_)
     - 2
   * - Control and Automation Engineering (`ECA|Poli|UFRJ`_)
     - 2
   * - Chemical Engineering
     - 1
   * - Naval Engineering (`DENO|Poli|UFRJ`_)
     - 1
   * - **Total**
     - **33**

Sponsors and Acknowledgments
============================

.. |faperj| image:: {static}/images/faperj.png
   :width: 250px
   :alt: FAPERJ - Fundacao Carlos Chagas Filho de Amparo a Pesquisa do Estado do Rio de Janeiro
   :target: https://www.faperj.br

.. |reditus| image:: {static}/images/reditus.png
   :width: 78px
   :alt: Instituto Reditus

.. class:: logo-row

|faperj| |reditus|

|

Sponsors and funding bodies:

 - **FAPERJ** – Fundação Carlos Chagas Filho de Amparo à Pesquisa do Estado
   do Rio de Janeiro, process SEI-260003/012046/2024 – Minerva Aerodesign
   (see below)
 - **Instituto Reditus** – Innovation Programme for UFRJ projects (see below)
 - **ANSYS**
 - **Woodpecker Balsa Wood**
 - **Decania do Centro de Tecnologia**, UFRJ

Institutional and infrastructure partners:

 - **LabMFA** – space for meetings, scientific computing, storage of
   materials and construction of the aircraft
 - **AMA UFRJ** – Associação de Modelismo dos Amigos da UFRJ, which provides
   the runway used for flight tests
 - **MUSAL** – Museu Aeroespacial, of the Brazilian Air Force
 - **LPCM**, UFRJ
 - **NIDF** – Núcleo Interdisciplinar de Dinâmica dos Fluidos, UFRJ

FAPERJ funding
==============

Since 2024 the team has been supported by `FAPERJ`_ through the call
**E_06/2024 – Apoio a Equipes Discentes em Projetos de Base Tecnológica
para Competições** (Support to Student Teams in Technology-Based Projects
for Competitions), under the *Minerva Aerodesign* project coordinated by
`Prof. Gustavo Rabello dos Anjos`_, of the Department of Mechanical
Engineering, Centro de Tecnologia, UFRJ. The team has no fixed annual
budget and depends on external support for materials, tooling and
equipment, as well as for the travel to the presential stage of the
competition in São José dos Campos.

Grant details
_____________

.. list-table::
   :widths: 35 65
   :class: borderless

   * - Programme
     - E_06/2024 – Apoio a Equipes Discentes em Projetos de Base Tecnológica
       para Competições
   * - Project
     - Minerva Aerodesign
   * - Process
     - SEI-260003/012046/2024 – ADT 1 (ref. E-26/290.059/2024)
   * - Deliberation
     - 2024/6825
   * - Grantee
     - Prof. Gustavo Rabello dos Anjos – UFRJ, Centro de Tecnologia,
       Mechanical Engineering
   * - Awarded amount
     - R$ 85,808.41, single instalment
   * - Duration
     - 12 months from the deposit of the last instalment, with technical
       report and accounting due within 60 days of its end

Results of the funded project
_____________________________

The funding was fully executed in the first year of the biennium. Most of
the acquired goods are long-lasting items that remain in use in the
following design cycles — among them the radio controller, the powerplant
group, the servo kit, the nylon propellers, the monitor and the receiver.

The impact of the support is visible across the whole 2025 cycle:

 - **Competition performance.** The team gained 10 positions with respect
   to 2024, reaching 22nd place out of 53 teams, with 17th place in the
   design report stage and 4th place in structures.
 - **Systems and electronics.** The new radio controller, responsible for
   the control of the aircraft in flight and on the ground and for the
   motor power limiter, removed the power-excess penalty that had been
   invalidating the flights of the team in previous editions. The
   electrical and safety assessment area obtained an unprecedented 12th
   place, with 17.84 out of 25 points.
 - **Multidisciplinary optimization.** The acquisition of adequate
   computational equipment made the execution of the Virtus MDO possible;
   running it on the personal computers of the members would not have
   allowed its full development. The integration report score rose by 3.08
   points with respect to 2024.
 - **Materials and simulation.** The investment in appropriate material
   and in electronic components supported the mechanical testing campaign
   and the licences and training in simulation software (Ansys, Abaqus,
   FEMAP), consolidating the team as a technical reference and benchmark
   for other teams of the competition.
 - **Outreach and self-funding.** In parallel, the team developed its first
   own fundraising plan, selling products manufactured by its members at
   two events held at the Museu Aeroespacial of the Brazilian Air Force, in
   Campo dos Afonsos, Rio de Janeiro. Its `Instagram`_ profile reached 2,000
   followers in December 2025, a growth of 33% over the year and more than
   300 thousand accumulated views, while the `LinkedIn`_ page exceeded its
   target of 150 followers.

Instituto Reditus funding
=========================

The team is also supported by the **Innovation Programme** of Instituto
Reditus, which funds projects of UFRJ. The 2025 edition supported the
*Jacurutu* project across five goals: the electro-electronic design, the
construction of the aircraft, the infrastructure of the laboratory, the
participation in the competition and the communication of the team. The
team is applying to the programme again in 2026.

.. list-table::
   :widths: 35 65
   :class: borderless

   * - Programme
     - Programa de Inovação 2025 – Instituto Reditus
   * - Project
     - Minerva Aerodesign
   * - Transferred amount
     - R$ 20,261.85

Results reported at the end of the programme:

 - Increase in the score of the reports of most areas of the team, reaching
   the 4th best structures report of the category
 - Full execution of the structural test campaign and complete development
   of the telemetry system
 - Improvement of the electrical system and further development of the power
   controller of the aircraft
 - Deeper study and full adoption of MATLAB in at least one area of the team
 - Wider networking with other teams and professionals of the aeronautical
   sector
 - Greater visibility of the team through participation in medium and large
   events

Within the funded period the team took part in the Santos Dumont anniversary
and in the MUSAL Airshow, both held at the Museu Aeroespacial, in the SAE
Brasil AeroDesign competition and in VarandaLab.

.. Place your references here
.. _DEM|Poli|UFRJ: http://www.mecanica.ufrj.br/en/index.php/pt/
.. _DEE|Poli|UFRJ: https://www.poli.ufrj.br/departamentos/dee-departamento-de-engenharia-eletrica/
.. _DMM|Poli|UFRJ: https://www.poli.ufrj.br/departamentos/dmm-departamento-de-engenharia-metalurgica-e-de-materiais/
.. _DCC|Poli|UFRJ: https://www.poli.ufrj.br/departamentos/dcc-departamento-de-construcao-civil/
.. _DEL|Poli|UFRJ: https://www.poli.ufrj.br/departamentos/del-departamento-de-engenharia-eletronica-e-de-computacao/
.. _DENO|Poli|UFRJ: https://www.poli.ufrj.br/departamentos/deno-departamento-de-engenharia-naval-e-oceanica/
.. _ECA|Poli|UFRJ: https://www.poli.ufrj.br/graduacao/controle-e-automacao/
.. _FAPERJ: https://www.faperj.br
.. _Prof. Gustavo Rabello dos Anjos: /person/gustavoRabello
.. _OpenMDAO: https://openmdao.org
.. _AVL: https://web.mit.edu/drela/Public/web/avl/
.. _OpenFOAM: https://www.openfoam.com
.. _XFLR5: http://www.xflr5.tech/xflr5.htm
.. _Ansys: https://www.ansys.com
.. _FEMAP: https://plm.sw.siemens.com/en-US/simcenter/mechanical-simulation/femap/
.. _Simulink: https://www.mathworks.com/products/simulink.html
.. _PSIM: https://powersimtech.com/products/psim/
.. _Instagram: https://www.instagram.com/minerva_aerodesign/
.. _LinkedIn: https://br.linkedin.com/company/minerva-aerodesign-ufrj
