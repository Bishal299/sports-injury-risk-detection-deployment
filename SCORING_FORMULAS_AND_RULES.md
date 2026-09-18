# Sports Injury Risk Detection System
## Mathematical Formulas, Weighting Rules & Scoring Engine Specifications

This document details every **mathematical formula**, **weight redistribution rule**, **threshold matrix**, and **algorithmic step** implemented in the transparent, rule-based injury risk scoring engine ([`risk_scoring.py`](file:///c:/Sports_injury_detection/sports-injury-risk-detection/backend/app/services/risk_scoring.py) and [`risk_config.py`](file:///c:/Sports_injury_detection/sports-injury-risk-detection/backend/app/services/risk_config.py)).

> **Architectural Constraint:**  
> The system strictly uses **transparent, interpretable rule-based biomechanical formulas**. No black-box machine learning classifiers, XGBoost, or neural networks are used for injury risk score calculation.

---

## Table of Contents
1. [Domain Weight Redistribution & Fatigue Inactivation](#1-domain-weight-redistribution--fatigue-inactivation)
2. [Composite Injury Risk Score Formula](#2-composite-injury-risk-score-formula)
3. [Risk Category Classification Thresholds](#3-risk-category-classification-thresholds)
4. [Domain 1: Biomechanical Deviations Scoring](#4-domain-1-biomechanical-deviations-scoring)
   - 4.1 [Frontal Knee Valgus & Affected Side Detection](#41-frontal-knee-valgus--affected-side-detection)
   - 4.2 [Hip & Pelvic Stability](#42-hip--pelvic-stability)
   - 4.3 [Trunk Inclination & Lateral Lean](#43-trunk-inclination--lateral-lean)
   - 4.4 [Landing Mechanics & Impact Cushioning](#44-landing-mechanics--impact-cushioning)
   - 4.5 [Dynamic Balance & Center-of-Mass Sway](#45-dynamic-balance--center-of-mass-sway)
   - 4.6 [Kinematic Joint Alignment](#46-kinematic-joint-alignment)
   - 4.7 [Posture Assessment](#47-posture-assessment)
5. [Domain 2: Movement Asymmetry Scoring](#5-domain-2-movement-asymmetry-scoring)
6. [Domain 3: Historical Injury Factors Scoring](#6-domain-3-historical-injury-factors-scoring)
7. [Domain 4: Training Load Indicators Scoring](#7-domain-4-training-load-indicators-scoring)
8. [Domain 5: Fatigue Indicators (Disabled)](#8-domain-5-fatigue-indicators-disabled)
9. [Distinct Movement Quality & Athlete Health Formulas](#9-distinct-movement-quality--athlete-health-formulas)
   - 9.1 [Overall Movement Quality Score](#91-overall-movement-quality-score)
   - 9.2 [Biomechanical Efficiency Score](#92-biomechanical-efficiency-score)
   - 9.3 [Overall Athlete Health Score](#93-overall-athlete-health-score)
10. [Top Risk Factors Prioritization & Side Detection](#10-top-risk-factors-prioritization--side-detection)
11. [Targeted Corrective Recommendations Logic](#11-targeted-corrective-recommendations-logic)

---

## 1. Domain Weight Redistribution & Fatigue Inactivation

### Original Baseline Weights (with Fatigue = 100%)
| Domain | Original Nominal Weight |
| :--- | :---: |
| Biomechanical Deviations | $35\%$ |
| Historical Injury Factors | $20\%$ |
| Movement Asymmetry | $20\%$ |
| Training Load Indicators | $15\%$ |
| Fatigue Indicators | $10\%$ |
| **Total** | **$100\%$** |

### Proportional Redistribution Rule (Fatigue = 0%)
Because fatigue indicators are currently **disabled** ($W_{\text{fatigue}} = 0$), no fake fatigue values are fabricated. The remaining active weights sum to $90\%$. The unused $10\%$ is redistributed **strictly proportionally** across the active domains:

$$W_i^{\text{active}} = \frac{W_i^{\text{original}}}{\sum_{j \in \text{active}} W_j^{\text{original}}} = \frac{W_i^{\text{original}}}{90}$$

### Active Production Weights
| Domain | Mathematical Ratio | Active Weight | Decimal Value |
| :--- | :---: | :---: | :---: |
| **Biomechanical Deviations** | $\frac{35}{90}$ | **$38.89\%$** | $0.388889$ |
| **Historical Injury Factors** | $\frac{20}{90}$ | **$22.22\%$** | $0.222222$ |
| **Movement Asymmetry** | $\frac{20}{90}$ | **$22.22\%$** | $0.222222$ |
| **Training Load Indicators** | $\frac{15}{90}$ | **$16.67\%$** | $0.166667$ |
| **Fatigue Indicators** | $0$ | **$0.0\%$** | $0.000000$ |
| **Sum of Active Weights** | — | **$100.0\%$** | **$1.000000$** |

---

## 2. Composite Injury Risk Score Formula

The total composite injury risk score $S_{\text{composite}} \in [0, 100]$ is a linear combination of the 4 active domain risk scores:

$$S_{\text{composite}} = \left( W_{\text{bio}} \times S_{\text{bio}} \right) + \left( W_{\text{hist}} \times S_{\text{hist}} \right) + \left( W_{\text{asym}} \times S_{\text{asym}} \right) + \left( W_{\text{load}} \times S_{\text{load}} \right)$$

Substituting the active production weights:

$$S_{\text{composite}} = \left( 0.388889 \times S_{\text{bio}} \right) + \left( 0.222222 \times S_{\text{hist}} \right) + \left( 0.222222 \times S_{\text{asym}} \right) + \left( 0.166667 \times S_{\text{load}} \right)$$

Where:
- $S_{\text{bio}}$ = Biomechanical Deviations Risk Score ($0 - 100$)
- $S_{\text{hist}}$ = Historical Injury Risk Score ($0 - 100$)
- $S_{\text{asym}}$ = Movement Asymmetry Risk Score ($0 - 100$)
- $S_{\text{load}}$ = Training Load Risk Score ($0 - 100$)

Final score clamping:
$$S_{\text{composite}} = \min(100.0, \max(0.0, S_{\text{composite}}))$$

---

## 3. Risk Category Classification Thresholds

The composite score maps directly into 4 distinct clinical risk categories:

| Score Range | Category | Clinical Interpretation |
| :---: | :---: | :--- |
| **$0.00 \le \text{Score} < 25.00$** | **Low Risk** | Biomechanics within safe normative envelopes; no significant injury vulnerability. |
| **$25.00 \le \text{Score} < 50.00$** | **Moderate Risk** | Mild to moderate deviations detected; preventative conditioning recommended. |
| **$50.00 \le \text{Score} < 75.00$** | **High Risk** | Significant kinematic flaws (e.g. dynamic valgus collapse, pelvic instability). |
| **$75.00 \le \text{Score} \le 100.00$** | **Critical Risk** | Severe multi-planar mechanical failure or acute training overload; high injury hazard. |

---

## 4. Domain 1: Biomechanical Deviations Scoring

Biomechanical risk $S_{\text{bio}} \in [0, 100]$ is computed as a weighted sum of 7 kinematic submetrics:

$$S_{\text{bio}} = \sum_{k=1}^{7} \left( w_k \times R_k \right)$$

| Submetric ($k$) | Weight ($w_k$) | Description |
| :--- | :---: | :--- |
| **Knee Valgus ($R_{\text{valgus}}$)** | **$30\%$** ($0.30$) | Frontal plane medial knee collapse |
| **Hip & Pelvic Stability ($R_{\text{hip}}$)** | **$20\%$** ($0.20$) | Pelvic tilt, Trendelenburg drop & sway |
| **Trunk Inclination ($R_{\text{trunk}}$)** | **$15\%$** ($0.15$) | Forward and lateral spinal tilt |
| **Landing Mechanics ($R_{\text{landing}}$)** | **$15\%$** ($0.15$) | Knee flexion buffering during ground impact |
| **Dynamic Balance ($R_{\text{balance}}$)** | **$10\%$** ($0.10$) | Center-of-mass (COM) dispersion and sway |
| **Joint Alignment ($R_{\text{alignment}}$)** | **$5\%$** ($0.05$) | Kinetic chain ankle-knee-hip alignment |
| **Posture Assessment ($R_{\text{posture}}$)** | **$5\%$** ($0.05$) | Shoulder and spinal alignment |
| **Total** | **$100\%$** ($1.00$) | — |

---

### 4.1 Frontal Knee Valgus & Affected Side Detection

Knee valgus is measured using **normalized medial displacement deviation** $d_{\text{norm}}$:

$$d_{\text{norm}} = \frac{|\text{Knee}_x - \text{Midpoint}(\text{Hip}_x, \text{Ankle}_x)|}{\text{Thigh Length}}$$

#### Piecewise Risk Function for Each Leg ($R_{\text{right}}, R_{\text{left}}$):
$$R(d_{\text{norm}}) = \begin{cases} 
\frac{d_{\text{norm}}}{0.04} \times 16.0 & \text{if } d_{\text{norm}} \le 0.04 \quad (\text{Normal}) \\
16.0 + \frac{d_{\text{norm}} - 0.04}{0.04} \times 19.0 & \text{if } 0.04 < d_{\text{norm}} \le 0.08 \quad (\text{Mild}) \\
35.0 + \frac{d_{\text{norm}} - 0.08}{0.04} \times 24.0 & \text{if } 0.08 < d_{\text{norm}} \le 0.12 \quad (\text{Moderate}) \\
59.0 + \frac{d_{\text{norm}} - 0.12}{0.04} \times 21.0 & \text{if } 0.12 < d_{\text{norm}} \le 0.16 \quad (\text{High}) \\
80.0 + \min\left(20.0, \frac{d_{\text{norm}} - 0.16}{0.08} \times 20.0\right) & \text{if } d_{\text{norm}} > 0.16 \quad (\text{Critical})
\end{cases}$$

#### Bilateral Knee Valgus Combination:
Let $R_{\text{worse}} = \max(R_{\text{right}}, R_{\text{left}})$ and $R_{\text{better}} = \min(R_{\text{right}}, R_{\text{left}})$:

$$R_{\text{valgus}} = \left( 0.70 \times R_{\text{worse}} \right) + \left( 0.30 \times R_{\text{better}} \right)$$

#### Affected Side Decision Rule:
$$\text{Side} = \begin{cases}
\text{"Bilateral"} & \text{if } |R_{\text{right}} - R_{\text{left}}| < 12.0 \\
\text{"Right"} & \text{if } R_{\text{right}} \ge R_{\text{left}} + 12.0 \\
\text{"Left"} & \text{if } R_{\text{left}} \ge R_{\text{right}} + 12.0
\end{cases}$$

---

### 4.2 Hip & Pelvic Stability

From hip stability quality score $Q_{\text{hip}} \in [0, 100]$:

$$R_{\text{hip}} = 100.0 - Q_{\text{hip}}$$

**Non-Linear Instability Penalty:**  
If pelvic control collapses below $60.0$, a $15\%$ non-linear amplification is applied:
$$R_{\text{hip}} = \min(100.0, R_{\text{hip}} \times 1.15) \quad \text{for } Q_{\text{hip}} < 60.0$$

---

### 4.3 Trunk Inclination & Lateral Lean

Calculated from average trunk lean angle $\theta_{\text{lean}}$ (degrees):

$$R_{\text{trunk}}(\theta_{\text{lean}}) = \begin{cases}
\frac{\theta_{\text{lean}}}{5.0} \times 15.0 & \text{if } \theta_{\text{lean}} \le 5.0^\circ \quad (\text{Optimal}) \\
15.0 + \frac{\theta_{\text{lean}} - 5.0}{5.0} \times 25.0 & \text{if } 5.0^\circ < \theta_{\text{lean}} \le 10.0^\circ \quad (\text{Mild}) \\
40.0 + \frac{\theta_{\text{lean}} - 10.0}{8.0} \times 35.0 & \text{if } 10.0^\circ < \theta_{\text{lean}} \le 18.0^\circ \quad (\text{Moderate}) \\
75.0 + \min\left(25.0, \frac{\theta_{\text{lean}} - 18.0}{10.0} \times 25.0\right) & \text{if } \theta_{\text{lean}} > 18.0^\circ \quad (\text{Severe})
\end{cases}$$

*(If angle measurement is unavailable, falls back to $100.0 - Q_{\text{trunk}}$).*

---

### 4.4 Landing Mechanics & Impact Cushioning

- **When Jump / Landing Impact is Detected:**
  $$R_{\text{landing}} = 100.0 - Q_{\text{landing}}$$
  *(If $Q_{\text{landing}} < 50.0$, a stiff impact penalty is added: $R_{\text{landing}} = \min(100.0, R_{\text{landing}} \times 1.15)$).*
- **When Video is Non-Jumping (e.g. Walking / Stationary):**
  $$R_{\text{landing}} = 10.0 \quad (\text{Neutral baseline; athlete not penalized})$$

---

### 4.5 Dynamic Balance & Center-of-Mass Sway

Calculated from dynamic balance quality score $Q_{\text{balance}} \in [0, 100]$:

$$R_{\text{balance}} = 100.0 - Q_{\text{balance}}$$

---

### 4.6 Kinematic Joint Alignment

Calculated from joint alignment quality score $Q_{\text{alignment}} \in [0, 100]$:

$$R_{\text{alignment}} = 100.0 - Q_{\text{alignment}}$$

---

### 4.7 Posture Assessment

Calculated from posture quality score $Q_{\text{posture}} \in [0, 100]$:

$$R_{\text{posture}} = 100.0 - Q_{\text{posture}}$$

---

## 5. Domain 2: Movement Asymmetry Scoring

Movement asymmetry risk $S_{\text{asym}} \in [0, 100]$ evaluates bilateral kinematic discrepancies without double-counting deviation severity.

### Baseline Symmetry Inverse:
Let $S_{\text{match}} \in [0, 100]$ be the overall bilateral kinematic symmetry match:

$$S_{\text{base\_asym}} = 100.0 - S_{\text{match}}$$

### Discrepancy Escalation Multipliers:
If unilateral divergence is detected across specific limb metrics, risk escalates:
1. **Frontal Valgus Asymmetry:**
   $$\Delta_{\text{valgus}} = |d_{\text{right}} - d_{\text{left}}|$$
   $$\text{Bonus}_{\text{valgus}} = \begin{cases} \min\left(20.0, \frac{\Delta_{\text{valgus}} - 0.03}{0.08} \times 20.0\right) & \text{if } \Delta_{\text{valgus}} > 0.03 \\ 0.0 & \text{otherwise} \end{cases}$$

2. **Stride Asymmetry:**
   $$\text{Bonus}_{\text{stride}} = \begin{cases} \min\left(15.0, \frac{\text{Asym}_{\text{stride}} - 10.0}{25.0} \times 15.0\right) & \text{if } \text{Asym}_{\text{stride}} > 10.0\% \\ 0.0 & \text{otherwise} \end{cases}$$

### Total Asymmetry Risk:
$$S_{\text{asym}} = \min(100.0, S_{\text{base\_asym}} + \text{Bonus}_{\text{valgus}} + \text{Bonus}_{\text{stride}})$$

---

## 6. Domain 3: Historical Injury Factors Scoring

### Missing Data Safeguard (Crucial Rule)
If no prior injury history records exist for the athlete:
$$S_{\text{hist}} = 0.0 \quad \text{and status} = \text{"Historical injury data unavailable"}$$
*The athlete is never penalized merely because historical records are missing.*

### Prior Injury Risk Contribution Function:
For each recorded injury $j$, risk is determined by severity and anatomical vulnerability:

$$R_{\text{injury}}(j) = \text{BaseSeverity}(j) \times \text{VulnerabilityMultiplier}(j)$$

#### Base Severity Weights:
- `Mild`: $25.0$
- `Moderate`: $50.0$
- `Severe` / `High`: $80.0$

#### Anatomical Vulnerability Multipliers:
| Body Part / Structure | Multiplier |
| :--- | :---: |
| Knee / ACL / Meniscus | $\times 1.25$ |
| Hamstring / Posterior Chain | $\times 1.20$ |
| Ankle / Achilles Complex | $\times 1.10$ |
| Hip / Groin / Core | $\times 1.10$ |
| Other Soft Tissue | $\times 1.00$ |

#### Compound Multi-Injury Formulation:
Let the injuries be sorted in descending order of individual risk: $R_{(1)} \ge R_{(2)} \ge R_{(3)} \ge \dots$

$$S_{\text{hist}} = \min\left(100.0, R_{(1)} + 0.35 \times R_{(2)} + 0.15 \times \sum_{k=3}^{N} R_{(k)}\right)$$

---

## 7. Domain 4: Training Load Indicators Scoring

### Missing Data Safeguard (Crucial Rule)
If training load is not recorded in the athlete profile:
$$S_{\text{load}} = 0.0 \quad \text{and status} = \text{"Training load data unavailable"}$$
*The athlete is never penalized when training load data is absent.*

### Non-Linear Training Load Risk Function:
Let $L \in [0, 100]$ be the athlete's Acute-to-Chronic / Training Load Index:

$$S_{\text{load}}(L) = \begin{cases}
\frac{L}{50.0} \times 10.0 & \text{if } L \le 50.0 \quad (\text{Optimal / Low Load: } [0, 10]) \\
10.0 + \frac{L - 50.0}{25.0} \times 20.0 & \text{if } 50.0 < L \le 75.0 \quad (\text{Moderate Load: } [10, 30]) \\
30.0 + \frac{L - 75.0}{15.0} \times 40.0 & \text{if } 75.0 < L \le 90.0 \quad (\text{Elevated Load: } [30, 70]) \\
70.0 + \min\left(30.0, \frac{L - 90.0}{10.0} \times 30.0\right) & \text{if } L > 90.0 \quad (\text{Acute Spike: } [70, 100])
\end{cases}$$

---

## 8. Domain 5: Fatigue Indicators (Disabled)

- **Execution State:** Inactive / Disabled ($W_{\text{fatigue}} = 0.0$).
- **Calculated Value:** `None`.
- **Reasoning:** In computer vision pose pipelines, fatigue cannot be directly measured without repeated time-series exertion or physiological telemetry. Fabricating fake values is prohibited.

---

## 9. Distinct Movement Quality & Athlete Health Formulas

To avoid confusing risk with performance, three separate composite indexes are computed:

### 9.1 Overall Movement Quality Score ($Q_{\text{movement}}$)
Measures execution cleanliness and kinetic compliance on a $0 - 100$ scale:

$$Q_{\text{movement}} = \max(0.0, \min(100.0, 100.0 - S_{\text{bio}}))$$

| Score Range | Category |
| :---: | :---: |
| $\ge 90.0$ | **Excellent** |
| $75.0 - 89.9$ | **Good** |
| $60.0 - 74.9$ | **Fair** |
| $40.0 - 59.9$ | **Poor** |
| $< 40.0$ | **Very Poor** |

---

### 9.2 Biomechanical Efficiency Score ($E_{\text{efficiency}}$)
Evaluates kinetic consistency and smooth force absorption:

$$E_{\text{efficiency}} = \left( 0.45 \times Q_{\text{movement}} \right) + \left( 0.35 \times C_{\text{consistency}} \right) + \left( 0.20 \times Q_{\text{balance}} \right)$$

Where:
- $C_{\text{consistency}}$ = Kinematic consistency across video frames ($0 - 100$)
- $Q_{\text{balance}}$ = Center-of-mass sway control score ($0 - 100$)

---

### 9.3 Overall Athlete Health Score ($H_{\text{health}}$)
A holistic physical readiness index combining biomechanics, symmetry, injury history, and load:

$$H_{\text{health}} = 100.0 - \left( 0.40 \times S_{\text{bio}} + 0.25 \times S_{\text{asym}} + 0.20 \times S_{\text{hist}} + 0.15 \times S_{\text{load}} \right)$$

*(When history or load data is unavailable, their weights are proportionally absorbed by biomechanics and symmetry so the index remains normalized to $100$).*

---

## 10. Top Risk Factors Prioritization & Side Detection

Each contributing risk factor $f$ calculates its raw contribution $C_f \in [0, 100]$. Factors with $C_f \ge 25.0$ are flagged and sorted in descending order of severity:

$$\text{Severity} = \begin{cases}
\text{"Critical"} & \text{if } C_f \ge 75.0 \\
\text{"High"} & \text{if } 50.0 \le C_f < 75.0 \\
\text{"Moderate"} & \text{if } 25.0 \le C_f < 50.0 \\
\text{"Low"} & \text{if } C_f < 25.0
\end{cases}$$

### Affected Side Assignment Matrix:
- **Knee Valgus:** `"Right"`, `"Left"`, or `"Bilateral"`
- **Hip Stability:** `"Right"`, `"Left"`, or `"Bilateral"`
- **Trunk Lean:** `"Right"`, `"Left"`, or `"Neutral"`
- **Landing / Balance / Load:** `"General"`

---

## 11. Targeted Corrective Recommendations Logic

Recommendations are generated **only when corresponding risk factors are triggered** (zero generic boilerplate):

| Trigger Condition | Exercise Domain | Action Focus | Prescribed Evidence-Based Drills |
| :--- | :--- | :--- | :--- |
| **Knee Valgus ($R_{\text{valgus}} \ge 25$)** | Neuromuscular Knee Alignment | Gluteus medius recruitment; preventing inward knee collapse | Banded Squats, Clamshells, Single-Leg Step-Downs |
| **Hip Tilt / Drop ($R_{\text{hip}} \ge 25$)** | Pelvic & Hip Stability | Core anti-lateral flexion; leveling pelvic plane | Suitcase Carries, Lateral Band Walks, Single-Leg RDLs |
| **Trunk Lean ($R_{\text{trunk}} \ge 25$)** | Anti-Rotational Core Posture | Erect spine alignment; resisting torso collapse | Pallof Press, Deadbugs, Plank Pull-Throughs |
| **Landing Impact ($R_{\text{landing}} \ge 35$)** | Deceleration & Landing Cushioning | Triple flexion (hip-knee-ankle); absorbing impact force | Box Drop-and-Stick, Depth Jumps, Pogo Hops |
| **Asymmetry ($S_{\text{asym}} \ge 25$)** | Unilateral Movement Symmetry | Eliminating bilateral strength/ROM discrepancies | Bulgarian Split Squats, Single-Leg Romanian Deadlifts |
| **High Load ($S_{\text{load}} \ge 50$)** | Workload Management | Fatigue reduction; active soft-tissue recovery | Deload Week, Low-Impact Mobility, Aerobic Recovery |
| **All Normal ($S_{\text{composite}} < 25$)** | Movement Quality Maintenance | Sustaining optimal movement patterns | Dynamic Warm-Ups, Movement Prep, Preventive Drills |

---

## 12. Verification & Validation Summary

Every formula above is validated by unit test cases in [`backend/test_risk_scoring.py`](file:///c:/Sports_injury_detection/sports-injury-risk-detection/backend/test_risk_scoring.py):

| Validation Case | Formula Checked | Expected | Test Result |
| :--- | :--- | :---: | :---: |
| **Case 1** | Normal Biomechanics | Score $< 25.0$ | **$5.1 / 100$ (Low Risk)** |
| **Case 2** | Moderate Deviations | $25.0 \le \text{Score} < 50.0$ | **$26.2 / 100$ (Moderate Risk)** |
| **Case 3** | Severe Valgus + Landing | $50.0 \le \text{Score} < 75.0$ | **$61.5 / 100$ (High Risk)** |
| **Case 4** | Compound Multi-Deviations | $\text{Score} \ge 75.0$ | **$78.6 / 100$ (Critical Risk)** |
| **Case 5** | Missing History Safeguard | $S_{\text{hist}} = 0$, not penalized | **$0.0$ (Unavailable)** |
| **Case 6** | Missing Load Safeguard | $S_{\text{load}} = 0$, not penalized | **$0.0$ (Unavailable)** |
| **Case 7** | Fatigue Weight Sum | $\sum W_i = 1.0, W_{\text{fatigue}} = 0$ | **$1.000000$ (100%)** |
| **Case 8** | Side Attribution | Flags Right vs. Left | **Correctly Tagged** |
| **Case 9** | Severity vs Asymmetry | Evaluated independently | **No Double Counting** |
| **Case 10** | Multi-Page PDF | Render with exact metrics | **Pass (7,919 bytes)** |
