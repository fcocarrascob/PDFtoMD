## Page 1

```markdown
## Chapter 3  
Base Selection, Design, and Simulation

### 3.1 OVERVIEW AND ORGANIZATION

As discussed in Chapter 1, column base connections have a diversity of configurations, depending on the type of structural system in which they are used (e.g., moment frame versus braced frame) and the types of loads and actions they are used to resist (e.g., gravity versus lateral—wind or seismic). The combination of the different configurations with design scenarios results in a multitude of loading cases and details, which may further be discussed in the context of design procedures or simulation methods. This Guide addresses these various situations. Against this backdrop, the main objective of this chapter is to provide context for the interpretation and use of material in the Guide that addresses specific details, in terms of their design as well as simulation. It is important to note that the design, detailing, and simulation guidance provided in this Guide is applicable once an overall connection configuration is selected. Consequently, this chapter also outlines considerations for selection of a particular configuration. The chapter is divided into two sections: (1) Section 3.2 discusses different base connection configurations, the factors that drive their selection, the loading conditions they may be subjected to, and where the design guidance for each of these situations may be found in the Guide, and (2) Section 3.3 discusses the structural interaction of the base connection with the frame and directs the user to guidance (provided in this Guide) for appropriate representation of base connections in structural models.

### 3.2 BASE CONNECTION CONFIGURATIONS

Base connections may be classified in various ways. A convenient way to classify them is based on the structural system they are used within, which affects their base configuration. These connections may be categorized as those used when only a column must be attached to a concrete footing versus when a column and another member (typically a diagonal brace) must be attached to the base connection. The former is common in moment-resisting frames, gravity frames, or in cantilever columns (e.g., as used in mezzanines), whereas the latter is common in braced frame structures. Figures 1-1(a) through (c) in Chapter 1 illustrate these basic types of configurations. With reference to these figures, Section 3.2.1 addresses columns without braces, while Section 3.2.2 addresses columns with braces.

#### 3.2.1 Base Connections for Columns without Braces

Base connections for columns without braces represent the most common condition in many structures. In fact, the previous editions of Design Guide 1 have been focused on this condition. Figures 1-1(a) and (b) introduced previously show some generic details for this condition. Column base connections without braces may be broadly classified into two categories—exposed base plate connections and embedded base connections. Exposed base plate connections [Figure 1-1(a)] are by far the most common when large bending moments and shears are not carried by the base connection. This is due to the economy and convenience of fabrication and erection because the concrete installation is completed almost entirely before the steel columns are erected. As a result, they are often used in gravity frames, cantilever columns, or in moment frames in which the base moments are low (e.g., in nonseismic regions or in seismic regions for low- to mid-rise moment frames). When large moments and forces need to be resisted by the base connection, it is most feasible to rely on anchor rods to transfer these moments and forces because these resist in other expressions such as thicker or stiffened base plates, larger or additional anchor rods, or deeper anchorage depths. In these situations, the column may be embedded into the foundation [see Figure 1-1(b)], and resistance is obtained by direct bearing of the column against the concrete or through the attachment of reinforcement to the column flanges. However, this involves additional expense and coordination between the steel erection and concrete installation because multiple concrete pours are necessary, both before and after the erection of the column. Both exposed and embedded base connections are summarized with respect to their details and navigation of this Guide.

#### Exposed Base Plate Connections for Columns without Braces

Exposed base plate connections typically consist of a column welded to a base plate that is then anchored to a concrete footing using anchor rods. Usually, a grout layer is present between the base plate and the footing to ensure a uniform transfer of stresses between the plate and the footing, as shown in Figure 1-1(a). Within this general design concept, variations in detail selection may arise from the following factors:

- **Member type:** Various cross sections may be used for columns; the common ones are W-sections, square or rectangular HSS, channels, and round HSS sections, as shown in Figure 3-1. The shape of the column cross section affects the formation of yield lines in the base plate and the type of welds that can be used. Typically, the selection of the column precedes the design of the base connection. In
```


## Page 2

```
this Guide, the focus is on W-sections and rectangular or square HSS sections. Round cross sections and nonrectangular base plates are outside the scope of this Guide. For these, finite element simulations (Appendix D provides guidelines), other design guides (e.g., Horn, 2011) for monopole bases, or research findings (Horváth et al., 2011) may be more appropriate.

- **Anchor rod pattern:** Anchor rods may be used in various patterns, some of which are shown in Figure 3-2; these patterns may be necessitated by the magnitude of loads to be resisted in conjunction with the base plate size and type of attached column section.

- **Anchor rod type:** The Guide focuses on pre-installed (cast-in-place) anchor rods; these may be headed or hooked at the bottom. At the top, various details may be used. Plate washers welded to the base plate may be specified if shear is intended to be carried through the anchor rods; this allows for simultaneous engagement of all anchor rods in shear.

- **Shear lug:** If large shear forces must be transferred into the footing, a shear lug (see Figure 3-3) is often provided on the underside of the base plate.

- **Welds:** Welds between the column section and the base plate may be fillet welds or partial-joint-penetration (PJP) or CJP groove welds, depending on the type of column to be attached, and the strength and detailing requirements.

- **Stiffening:** Base plates may be stiffened with haunches to increase the flexural capacity; these are outside the scope of this Guide. The design of stiffened bases could use an elastic approach with an established load path or a yield line approach similar to connections discussed in AISC Design Guide 29, *End-Plate Moment Connections* (Easton and Murray, 2023).

- **Seismic details:** If connection ductility is required in addition to strength (to meet seismic requirements), additional detailing may be specified. This may include the use of upset thread anchor rods, or the use of chairs on top of the base plate, to increase the stretch length and deformation capacity of the anchor rods. Such details are discussed at length in Chapter 6.

### Embedded Base Connections

Embedded base connections consist of the bottom portion of column embedded within the concrete footing as shown previously in Figure 1-1(b) and in Figure 3-4. Usually, a column support slab is provided below the base of the column for erection purposes, after which the footing is poured around the column. Flexure is typically resisted through a combination of two mechanisms: (1) horizontal bearing of the concrete against the column flange in conjunction with development of a shear panel and (2) vertical bearing of the embedded base plate against the footing. Variations to this basic detail—discussed at length in Chapter 5—depend on the magnitudes of applied loads (see Figure 3-4).

- **Attachment of reinforcement to the column flange,** or running the reinforcement through the column flanges, to supplement the concrete bearing and overall flexural strength.

![Fig. 3-1. Common base plate details based on type of column attached.](#)

![Fig. 3-2. Common anchor rod patterns.](#)

12 / BASE CONNECTION DESIGN / AISC DESIGN GUIDE 1, 3rd EDITION
```

## Page 3

```
- Hoops or stirrups to supplement shear strength of the footing, especially if vertical bearing of the embedded plate is an active mechanism.

- Installation of plates at the top of the footing (with grout) to transfer compressive loads through the footing. This may be similar to a stiffener plate between the column web and flanges, or a larger plate, if axial loads are high. The latter requires significantly more fabrication and welding.

- Typically, the base plate at the bottom (designed for erection forces) also resists uplift in the column; however, its size may be adjusted for this purpose.

- Other aspects of the embedded base connection detailing (e.g., reinforcement patterns) may depend on the type of foundation system (e.g., pile caps, mat foundations, or grade beams), and the load path from the column to the soil.

It is relevant to note here that while embedded base connections are often designed to obtain additional strength from the concrete, in some cases the embedment may be incidental. This is common, for example, in "blockout" connections wherein a slab-on-grade is cast on top of the base plate (see Figure 3-5). To achieve this, the column is first connected to the footing as in a conventional exposed base plate connection but through a diamond shaped blockout as shown in Figure 3-5. This blockout allows for the installation of the remainder of the slab-on-grade prior to the installation of any structural steel (minimizing/eliminating the overlap of concrete and steel workers on the job site). Subsequently, the blockout is filled with unreinforced concrete, grout, or felt strips, creating a cold joint between the blockout concrete and the remainder of the slab. The blockout, and the surrounding slab, create a base connection that has a shallow embedment, which provides supplemental flexural strength.

![Fig. 3-3. Shear lug to resist large shear forces.](path/to/fig3-3.png)

![Fig. 3-4. Embedded base connection showing details.](path/to/fig3-4.png)

AISC DESIGN GUIDE 1, 3rd EDITION / BASE CONNECTION DESIGN / 13
```

## Page 4

```markdown
and stiffness. This flexural resistance is usually discounted in design (except for shear transfer through base plate bearing) but becomes important in the context of performance assessment. As a result, the blockout connection is discussed in this Guide only in the context of its simulation within structural models. This guidance can be found in Appendix C.

## Loading Conditions Considered and Navigation of the Guide

In general, base connections without a brace may be subjected to a combination of axial force, biaxial moments (with respect to the column cross-section axes), and biaxial shears. These may be applied in a static sense or in a seismic sense. The Guide contains comprehensive guidance for the design of these connections. Specifically, the design guidance is organized as follows:

- For exposed base plate connections without a brace:
  - Strength design guidance may be found in Chapter 4. This chapter provides guidance for design under 11 common loading scenarios, featuring various combinations of axial tension and compression, along with moments (in both directions) and shear.
  - Seismic design guidance may be found in Chapter 6. This chapter defers to Chapter 4 for strength design guidance but outlines detailing and additional considerations that are relevant in a seismic context.

- For embedded base connections without a brace:
  - Strength design guidance may be found in Chapter 5. This chapter exclusively focuses on embedded base connections without a brace. Given the relatively limited research on this topic, only in-plane loading cases are considered, with axial compression and tension combined with uniaxial flexure and shear.

  Supplementary information for seismic design may be found in Chapter 6.

In either case, torsion on the column is not in the scope of the Guide owing to the lack of research in this area and assuming that torsion in the column will be low relative to other forces. It is noted here that torsion in the column may produce shear in the anchors and also induce tension in the anchors if significant warping is present in the column along with the torsion.

### 3.2.2 Base Connections for Columns with Braces

Column bracing is commonly used in various types of structures, with the brace directly connected to the base connection and the column, typically through a gusset plate as shown in Figure 1-1(c). These connections are used in both nonseismic as well as seismic contexts. In a nonseismic context, they may be used for stability bracing or for bracing systems to resist lateral loads such as wind. In a seismic context, they form an integral part of lateral load-resisting systems, including ordinary and special concentrically braced frames as well as eccentrically braced frames and buckling restrained braced frames (AISC, 2022b). Similar to base connections without braces, these connections may be constructed as exposed base plate or embedded base plate connections; the latter is used when it is unfeasible to carry the large base forces through the anchor rods alone. However, as in the case of base connections without a brace, this involves additional expense and coordination between the steel erection and concrete installation. Within the generic configuration shown in Figure 1-1(c), numerous variations are possible in the detail. Some common variations along with factors that influence their selection are:

- Exposed versus embedded connections: Although exposed base plate connections with a brace [Figure 1-1(c)]

| Illustration | Description |
|--------------|-------------|
| ![Blockout connection illustration](data:image/png;base64) | Cold joint between slab and blockout |
| ![Footing/foundation illustration](data:image/png;base64) | Footing/foundation Diamond blockout (filled with unreinforced concrete) |
| Slab-on-grade/overtopping slab | Construction control joints |

_Fig. 3-5. Blockout connections resulting in shallow embedment of base plate connections._

14 / BASE CONNECTION DESIGN / AISC DESIGN GUIDE 1, 3rd EDITION
```

## Page 5

```
common, embedded (or encased) connections for base
connections with a brace may become necessary if the
loads (especially the base shear) are large and cannot be
resisted effectively through the anchor rods or a shear lug
(see Figure 3-6).

- **Shear lug**: If large shear forces must be transferred into
  the footing, a shear lug (see Figure 3-3) is often provided
  on the underside of the base plate.

- **Drag strut**: Drag struts or grade beams are often used
  to carry horizontal forces from the brace into adjacent
  footings.

- **Anchor rod patterns**: The shape of the column, gusset
  plate, and the loads affect anchor rod patterns.

- **Vertical stiffeners**: These are often provided to increase
  the flexural strength of the base plate. Gusset plates inci-
  dentally provide vertical stiffening.

**Loading Conditions Considered and  
Navigation of the Guide**

In general, base connections with a brace may be subjected
to similar types of loadings as those without a brace—that is,
a combination of axial force, biaxial moments (with respect
to the column cross-section axes), and biaxial shears. These
may be applied in a static sense or in a seismic sense. How-
ever, in base connections with a brace, the vertical and hori-
zontal forces (i.e., axial forces and shear) are likely to be
significantly higher relative to the moments, in contrast to
connections without a brace. These moments in connec-
tions with a brace arise due to fixity of the base connections
(which results in a deviation from the truss assumptions) or
to an eccentricity between the working point of the connec-
tion and the centroid of the base plate. In either case, as far

as the design of the base connection itself is concerned, the
main difference is in the relative magnitudes of the forces,
rather than the design procedure itself. The design guidance
for base connections with a brace is included in Chapter 4 for
exposed base plate connections and Chapter 5 for embedded
base connections. In Chapter 4, specific design examples are
provided for two loading cases (Section 4.3.4)—Design for
Combined Tension and Shear, and Section 4.3.5)—Design
for Combined Compression and Shear) that are considered
to be commonly applicable to base connections with braces.

### 3.3 INTERACTION OF BASE CONNECTIONS
WITH FRAMES

The flexibility and load-deformation response of base con-
nections influence the internal force and moment distri-
bution of the entire structure in addition to the structural
deformations. As a result, it is important to appropriately
represent the base connection in structural models. These
interactions are particularly important in moment frames.
These connections are often represented as either pinned
or fixed in structural models, both of which introduce error
into estimation of structural response. The discussion in this
Guide is restricted to the moment-rotation response of base
connections in moment frames (including the initial rota-
tional stiffness and the subsequent yielding and hysteretic
behavior). This section is divided into three subsections:
Section 3.3.1 provides a general qualitative commentary
of the load deformation response of base connections, with
implications for the response of moment frames, and Sec-
tions 3.3.2 and 3.3.3 address simulation of base connections
for seismic performance assessment for two different types
of design—one in which the base connection remains elastic
(a strong-base design) versus one in which it is expected to

![Figure 3-6: Embedded plate brace connection.](figure.jpg)

```

AISC DESIGN GUIDE 1, 3rd EDITION / BASE CONNECTION DESIGN / 15
```

## Page 6

## 3.3.1 General Observations about Base Connection Load-Deformation Response

Figure 3-7 shows the typical moment-rotation response (experiment by Gomez et al., 2010) of an exposed base plate type connection subjected to a cyclic loading increasing rotation in the presence of axial compression. Referring to the figure, it is evident that:

1. Even before the connection yields, there is significant rotation in the base connection. In fact, if it is assumed that design moments occur at ~70–80% of capacity (owing to safety factors) and sizing considerations, a rotation of 0.01–0.02 rad is obtained at yield. This type of response is observed across different types of base connections, both exposed and embedded. This suggests that the base connections possess partial fixity and cannot be assumed as fixed or free without further analysis or context.

2. Even during this initial "elastic" response of the connection, there is some nonlinearity in the load-deformation response. This occurs due to effects such as uplift of the base plate from the footing and nonlinearity in the concrete stress-strain response in bearing. The implication of this is that a secant stiffness is usually measured at the point of yielding of the base connection (see Figure 3-7) or at a fixed fraction of ultimate capacity is more appropriate for representation of the base plate stiffness.

3. The base connections possess significant ductility under both monotonic and cyclic conditions. As an example, the base connection response shown in Figure 3-7 showed anchor rod fracture at a rotation of over 0.08 rad. While the precise degree of deformation capacity is sensitive to detailing, a review of experimental data indicates that both exposed and embedded base connections (tested since 1984) in general, have rotation capacities well above 0.04 rad.

## 3.3.2 Modeling Base Connections for Strong-Base Design

In a vast majority of design scenarios (with exceptions noted in Section 3.3.3), base connections are expected to remain elastic. This includes almost all static/gravity and wind load situations, as well as most situations for seismic design (wherein the base connection is capacity designed to fully develop the plastic moment capacity of the attached column—see Chapter 6). As a result, the only attribute of the base connection that participates in interaction with the frame is its elastic (or initial) rotational stiffness—shown in Figure 3-7. In these cases, the base rotational flexibility (reciprocal of rotational stiffness) influences the structural response in three ways:

- Under lateral (e.g., seismic) loading, the rotational flexibility of the base connection lowers the point of inflection in the column with respect to the fixed base assumption. This increases the moment at the top of the column, increasing the susceptibility of the frame to weak-story collapse.

- Under lateral loading, the rotational flexibility increases the interstory drift in the first story with respect to the fixed base assumption.

- The base flexibility may influence the column end fixity, affecting its effective length, and consequently its compressive strength.

![Moment rotation response](attachment://figure3-7.png)

**Fig. 3-7. Moment rotation response of an exposed base plate connection (from Gomez et al., 2010) showing rotational stiffness.**

---

*16 / BASE CONNECTION DESIGN / AISC DESIGN GUIDE 1, 3rd EDITION*

## Page 7

While it is known that base connections are not rigid, approaches to estimate their flexibility are not commonly used in the design and performance assessment process, and they are often represented as pinned or fixed in structural models. Representing them as pinned in structural models is a conservative assumption, which results in increased estimates of story drifts and column moments; this in turn leads to the selection of heavier or larger members and an increase in steel tonnage. On the other hand, sometimes these connections are considered to be fixed in structural models because they are designed to be stronger than the column. While this may appear to be a reasonable assumption, it indicates a conflation of strength and stiffness. In contrast, experimental data suggests that even base connections that are significantly stronger than the attached column (including embedded base connections) exhibit significant rotational flexibility, such that simulating them as fixed may be erroneous and may lead to unconservative characterization of performance. That said, the influence of the base rotation stiffness on overall structural response is highly dependent on the remainder of the structure—for example, a frame with highly stiff beams and columns will show low base rotations regardless of base flexibility. Thus, modeling the most accurate estimate of base connection flexibility is the best option to avoid unnecessary conservatism or unconservatism. To this end, stiffness estimation methods for column base connections of various configurations have been developed. These have been extensively validated against both experimental data as well as recorded seismic response data from instrumented buildings. Moreover, these methods are fairly straightforward to apply. Given this, it is desirable to represent the elastic stiffness of base connections (and the foundation system generally) in the same manner as the remainder of the structure is represented in simulation. Approaches to estimate the elasticities of various types of base connections are provided in Appendix C.

### 3.3.3 Modeling Base Connections for Weak-Base Design

Designing the base connections to be stronger than the attached column (i.e., designing them to have a higher moment capacity as compared to the strain-hardened plastic moment capacity of the column) is costly. As a result, weak base design may become desirable in which the column base connection is designed to yield in an inelastic cyclic manner (in a manner similar to that illustrated in Figure 3-7) while the column remains elastic. This type of response is explicitly allowed by the AISC *Seismic Provisions* as long as ductile response can be achieved in the base connection. Design methods that leverage the ductility of base connections in this manner are currently under development along with details that provide such ductility (outlined in Chapter 6). However, performance assessment of such structures requires simulation of the hysteretic response of base connections. Referring to Figure 3-7, this response is somewhat complex, showing characteristics such as cyclic degradation, pinching, and loss of strength. Appendix C (Section C.3) provides guidelines for simulating this type of response in structural models.

---

*AISC DESIGN GUIDE 1, 3rd EDITION / BASE CONNECTION DESIGN / 17*

## Page 8

""

## Page 9

```markdown
# Chapter 4  
Design of Exposed Column Base Connections

## 4.1 OVERVIEW AND ORGANIZATION

This chapter provides the design requirements for exposed column bases, such as those shown in Figures 1-1(a) and (c). Several different design load cases and combinations in exposed column base connections are discussed in Section 4.3:

- Section 4.3.1 Design for Axial Compression
- Section 4.3.2 Design for Axial Tension
- Section 4.3.3 Design for Shear
- Section 4.3.4 Design for Combined Axial Tension and Shear
- Section 4.3.5 Design for Combined Axial Compression and Shear
- Section 4.3.6 Design for Bending
- Section 4.3.7 Design for Combined Axial Compression and Bending
- Section 4.3.8 Design for Combined Axial Tension and Bending
- Section 4.3.9 Design for Combined Axial Compression, Bending, and Shear
- Section 4.3.10 Design for Combined Axial Tension, Bending, and Shear
- Section 4.3.11 Design for Combined Axial Compression and Biaxial Bending

For loading cases or combinations where bending is considered, two conditions are discussed—low moment and high moment. In each section, the design methodology is outlined. Detailed design examples follow in the Section 4.7.

Section 4.4 provides methodologies available for the design of anchorage reinforcement. The anchor rods for base connections are designed for steel strength and concrete strength. In many situations, either due to the concrete thickness or the closeness of the anchor rods to the edge of the concrete, the concrete breakout strength is reduced, and the required anchor strength cannot be achieved. For such cases, anchor reinforcement is typically added to transfer the design load from the anchors into the structural concrete member.

In addition, the chapter provides information related to fabrication and installation in Section 4.5 and repair and field fixes in Section 4.6.

## 4.2 OVERALL DESIGN PROCESS AND FLOW

The general behavior and distribution of forces for a column base connection with anchor rods will be elastic until either a plastic hinge forms in the column, a plastic mechanism forms in the base plate, the concrete crushes in bearing, the column to base plate weld fractures, the anchor rods yield in tension, or the concrete strength of the anchor rod group is reached. If the concrete strength of the anchor rod group is larger than the lowest of the other limit states, the behavior generally will be ductile, not withstanding weld fracture, if it occurs. However, it is not always necessary or even possible to design a foundation that prevents concrete failure.

The overall base connection design process includes six steps: (1) base plate footprint selection; (2) determination of appropriate distribution of internal forces; (3) base plate thickness selection; (4) anchor rod, anchor group, and reinforcement design; (5) considerations for footing design; and (6) welding design and detailing.

The regulations of the Occupational Safety and Health Administration (OSHA) Safety Standards for Steel Erection (2020) require a minimum of four anchor rods in column base plate connections. The requirements exclude post-type columns that weigh less than 300 lb. Columns, base plates, and their foundations must have sufficient moment strength to resist a minimum eccentric gravity load of 300 lb located 18 in. from the extreme outer face of the column in each direction.

The OSHA criteria can be met with even the smallest of anchor rods (¾ in. diameter) on a 4 in. by 4 in. pattern. If one considers only the moments from the eccentric loads (because including the gravity loads results in no tensile force in the anchor rods), and
```

## Page 10

## 4.3 LOAD COMBINATIONS

### 4.3.1 Design for Axial Compression

**Overview of Mechanics and Method**

When a column base resists only compressive column axial loads, the base plate must be large enough to resist the bearing forces transferred from the base plate (concrete bearing limit), and the base plate must be of sufficient thickness (base plate yielding limit).

**Concrete Bearing Limit**

The nominal bearing strength of column bases bearing on concrete is defined in ACI 318, Section 22.8.3.2, as $B_r = 0.85f'_cA_1$ when the supporting surface is not larger than the base plate. When the supporting surface is wider on all sides than the loaded area, the design bearing strength above is permitted to be multiplied by $\sqrt{A_2/A_1} \leq 2$. The relationship between $A_2$ and $A_1$ is illustrated in ACI 318, Figure R22.8.3.2,

where

- $A_1 =$ area of the base plate, in.$^2$
- $A_2 =$ area of the lower base of the largest frustum of a pyramid, cone, or tapered wedge contained wholly within the support and having its upper base equal to the loaded area, in.$^2$
- $f'_c =$ specified compressive strength of concrete, ksi

The increase of the concrete bearing capacity associated with the term $\sqrt{A_2/A_1}$ accounts for the beneficial effects of the concrete confinement. Note that $A_2$ is the largest area that is geometrically similar to (having the same aspect ratio as) the base plate and can be inscribed on the horizontal top surface of the concrete footing, pier, or beam without going beyond the edges of the concrete.

There is a limit to the beneficial effects of confinement, which is reflected by the limit on $A_2$ (to a maximum of four times $A_1$) or by the inequality limit. Thus, for a column base plate bearing on a footing far from edges or openings, $\sqrt{A_2/A_1} = 2$.

AISC Specification Section J8 provides the nominal bearing strength, $P_p$, as follows:

- On the full area of a concrete support:

  $$P_p = 0.85f'_cA_1 \quad \text{(Spec. Eq. J8-1)}$$

- On less than the full area of a concrete support:

  $$P_p = 0.85f'_cA_1\sqrt{A_2/A_1} \leq 1.7f'_cA_1 \quad \text{(Spec. Eq. J8-2)}$$

These equations are multiplied by the resistance factor, $\phi_b$, for LRFD or divided by the safety factor, $\Omega_b$, for ASD. Section J8 stipulates the $\phi_b$ and $\Omega_b$ factors for bearing on concrete as follows:

- $\phi_b = 0.65$ (LRFD)
- $\Omega_b = 2.31$ (ASD)

ACI 318, Section 21.2.1, also stipulates a resistance factor of $\phi = 0.65$ for bearing on concrete.

The nominal bearing strength can be converted to a nominal pressure format by dividing out the area term such that:

- On the full area of a concrete support:

  $$f_{b(nom)} = 0.85f'_c \quad (4-1)$$

---

20 / BASE CONNECTION DESIGN / AISC DESIGN GUIDE 1, 3rd EDITION

## Page 11

```markdown
When the concrete base is larger than the loaded area on all four sides:

$$
f_{p(max)} = 0.85 \frac{f'_c A_2}{A_1} \leq 1.7 f'_c
$$

(4-2)

The conversion of the generic nominal pressure to an available bearing stress is:

| LRFD                                          | ASD                           |
|-----------------------------------------------|-------------------------------|
| $f_{p(ucn)} = \phi_b f_{p(nom)}$              | $f_{p(ucn)} = \frac{f_{p(nom)}}{Q}$ |
| (4-3a)                                        | (4-3b)                        |

The bearing stress on the concrete must not be greater than $f_{p(ucn)}$:

| LRFD                        | ASD                         |
|-----------------------------|-----------------------------|
| $\frac{P_u}{A_1} \leq f_{p(ucn)}$ | $\frac{P_u}{A_1} \leq f_{p(ucn)}$ |
| (4-4a)                      | (4-4b)                      |

Thus,

| LRFD                                          | ASD                                        |
|-----------------------------------------------|--------------------------------------------|
| $A_{1(req)} = \frac{P_u}{f_{p(ucn)}}$         | $A_{1(req)} = \frac{P_u}{f_{p(ucn)}}$      |
| (4-5a)                                        | (4-5b)                                     |

When $A_2 = A_1$, the required minimum base plate area can be determined as:

| LRFD                                                    | ASD                                               |
|---------------------------------------------------------|---------------------------------------------------|
| $A_{1(req)} = \frac{P_u}{\phi_b 0.85 f'_c}$             | $A_{1(req)} = \frac{\Omega P_u}{0.85 f'_c}$       |
| (4-6a)                                                  | (4-6b)                                            |

When $A_2 > 4A_1$, the required minimum base plate area can be determined as:

| LRFD                                          | ASD                                                 |
|-----------------------------------------------|-----------------------------------------------------|
| $A_{1(req)} = \frac{P_u}{(0.85 f'_c)}$        | $A_{1(req)} = \frac{1}{2} \frac{\Omega P_u}{0.85 f'_c}$ |
| (4-7a)                                        | (4-7b)                                              |

Many column base plates bear directly on a layer of grout. The grout compressive strength should always be higher than the concrete compressive strength. Because the grout compressive strength is always specified higher than the concrete strength, the concrete compressive strength, $f'_c$, must be used in the preceding equations. The previous edition of this Design Guide recommended that the grout strength be specified as two times the concrete strength. Lower grout strengths may be justified if the bearing strength of the grout is checked against the required strength. The important dimensions of the column-base connection are shown in Figure 4-1.

**Base Plate Yielding Limit (W-Shapes)**

For axially loaded base plates, the required bearing stress under the base plate is assumed uniformly distributed and can be expressed as:

---

*AISC DESIGN GUIDE 1, 3rd EDITION / BASE CONNECTION DESIGN / 21*
```

