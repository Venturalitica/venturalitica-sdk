"""
Practical Examples: Multi-class and Causal Fairness Analysis

Demonstrates real-world usage of new fairness metrics.
"""

import pandas as pd
import numpy as np
from venturalitica.metrics.multiclass import (
    calc_multiclass_fairness_report,
    calc_weighted_demographic_parity_multiclass,
    calc_macro_equal_opportunity_multiclass,
)
from venturalitica.metrics.causal import (
    calc_causal_fairness_diagnostic,
    calc_path_decomposition,
)


def example_1_loan_approval_multiclass():
    """
    Scenario: Bank uses ML model to assign loan approval to three categories:
    - 0: Reject
    - 1: Approve (standard terms)
    - 2: Approve (premium terms)
    
    Check: Is the distribution of approvals fair across genders?
    """
    print("=" * 80)
    print("EXAMPLE 1: Loan Approval Fairness (3-class Classification)")
    print("=" * 80)
    
    # Synthetic data
    np.random.seed(42)
    n = 300
    
    df = pd.DataFrame({
        'applicant_id': range(n),
        'gender': np.random.choice(['Male', 'Female'], n),
        'income': np.random.normal(50000, 20000, n),
        'credit_score': np.random.normal(700, 100, n),
        'employment_years': np.random.exponential(5, n),
    })
    
    # Biased model: females less likely to get premium approvals
    y_pred = np.zeros(n, dtype=int)
    for i, row in df.iterrows():
        if row['credit_score'] > 750:
            if row['gender'] == 'Male':
                y_pred[i] = 2  # Premium approval more likely for males
            else:
                y_pred[i] = 1  # Standard approval for females
        elif row['credit_score'] > 650:
            y_pred[i] = 1  # Standard approval
        # else: 0 (rejection)
    
    y_pred = pd.Series(y_pred)
    y_true = pd.Series(np.random.choice([0, 1, 2], n))  # Dummy true labels
    
    # Analyze fairness
    report = calc_multiclass_fairness_report(y_true, y_pred, df['gender'])
    
    print("\n📊 Multi-class Fairness Analysis:")
    print("-" * 80)
    for metric, value in report.items():
        if value <= 0.1:
            status = "✓ PASS"
        elif value <= 0.15:
            status = "⚠️ WARN"
        else:
            status = "❌ FAIL"
        print(f"{status} | {metric:40s}: {value:.4f}")
    
    # Breakdown by gender
    print("\n📈 Approval Rate by Gender and Class:")
    print("-" * 80)
    for gender in ['Male', 'Female']:
        mask = df['gender'] == gender
        rates = y_pred[mask].value_counts(normalize=True).sort_index()
        print(f"\n{gender}:")
        for class_label, rate in rates.items():
            class_names = {0: 'Reject', 1: 'Standard Approval', 2: 'Premium Approval'}
            print(f"  {class_names[class_label]:20s}: {rate:5.1%}")
    
    return df, y_true, y_pred


def example_2_hiring_causal():
    """
    Scenario: HR department hires for three levels:
    - 0: Entry level
    - 1: Mid-level
    - 2: Senior level
    
    Question: Is salary gap between genders due to discrimination or job level?
    Answer: Path decomposition separates direct vs mediated effects.
    """
    print("\n" + "=" * 80)
    print("EXAMPLE 2: Hiring & Salary Fairness (Causal Analysis)")
    print("=" * 80)
    
    np.random.seed(42)
    n = 200
    
    # Create synthetic hiring data
    df = pd.DataFrame({
        'gender': np.random.choice(['M', 'F'], n),
        'education_years': np.random.normal(16, 2, n),
        'years_experience': np.random.normal(8, 5, n),
        'job_level': np.random.choice([0, 1, 2], n),
        'salary': np.random.normal(60000, 20000, n),
    })
    
    # Add gender bias: females earn less on average
    df.loc[df['gender'] == 'F', 'salary'] -= 5000
    
    # And are less likely to be hired at senior levels
    senior_females = df[(df['gender'] == 'F') & (df['job_level'] == 2)]
    df.loc[senior_females.index, 'job_level'] = 1
    
    print("\n🔬 Causal Path Decomposition Analysis:")
    print("-" * 80)
    print("\nQuestion: Does gender affect salary directly, or through job level?")
    print("(Job level is a legitimate mediator - higher level justifies higher salary)\n")
    
    # Analyze paths
    effects = calc_path_decomposition(
        df, 'gender', 'salary',
        mediators=['job_level', 'years_experience']
    )
    
    for comparison, effect in effects.items():
        print(f"{comparison}:")
        print(f"  Total salary difference:     ${effect.total_effect:,.0f}")
        print(f"  Direct (discrimination?):   ${effect.direct_effect:,.0f}")
        print(f"  Indirect (via job/exp):     ${effect.indirect_effect:,.0f}")
        print(f"  Proportion mediated:        {effect.proportion_mediated:.1%}")
        
        if effect.direct_effect > 2000:
            print(f"  ⚠️ Significant direct effect detected (potential discrimination)")
        else:
            print(f"  ✓ Direct effect minimal; differences explained by job level/experience")
        print()


def example_3_healthcare_multiclass_and_causal():
    """
    Scenario: Hospital ML model predicts patient risk level for intervention:
    - 0: Low risk (routine care)
    - 1: Medium risk (monitoring)
    - 2: High risk (intensive intervention)
    
    Check 1: Are risk categories fair across racial groups? (multi-class)
    Check 2: Is the protected attribute effect direct or mediated? (causal)
    """
    print("\n" + "=" * 80)
    print("EXAMPLE 3: Healthcare Risk Prediction (Multi-class + Causal)")
    print("=" * 80)
    
    np.random.seed(42)
    n = 500
    
    df = pd.DataFrame({
        'patient_id': range(n),
        'race': np.random.choice(['White', 'Black', 'Hispanic'], n, p=[0.5, 0.3, 0.2]),
        'age': np.random.normal(60, 15, n),
        'bmi': np.random.normal(27, 5, n),
        'blood_pressure': np.random.normal(130, 15, n),
        'comorbidities': np.random.randint(0, 4, n),
    })
    
    # Create risk predictions with racial bias
    y_pred = np.zeros(n, dtype=int)
    for i, row in df.iterrows():
        risk_score = (
            row['age'] / 100 + 
            row['bmi'] / 30 + 
            row['blood_pressure'] / 150 + 
            row['comorbidities'] / 3
        )
        
        # Add racial bias: lower threshold for Black patients
        race_adjustment = {
            'White': 0.0,
            'Black': -0.2,  # Bias: lower threshold (more likely to be labeled high risk)
            'Hispanic': -0.1,
        }
        risk_score += race_adjustment.get(row['race'], 0.0)
        
        if risk_score > 2.0:
            y_pred[i] = 2
        elif risk_score > 1.0:
            y_pred[i] = 1
        # else: 0
    
    y_pred = pd.Series(y_pred)
    y_true = pd.Series(np.random.choice([0, 1, 2], n))
    
    # 1. Multi-class fairness
    print("\n1️⃣  Multi-class Risk Distribution Fairness:")
    print("-" * 80)
    
    report = calc_multiclass_fairness_report(y_true, y_pred, df['race'])
    
    for metric, value in report.items():
        if value <= 0.1:
            status = "✓"
        elif value <= 0.15:
            status = "⚠️"
        else:
            status = "❌"
        print(f"{status} {metric:40s}: {value:.4f}")
    
    # Show distribution
    print("\n📊 Risk Category Distribution by Race:")
    print("-" * 80)
    for race in df['race'].unique():
        mask = df['race'] == race
        rates = y_pred[mask].value_counts(normalize=True).sort_index()
        print(f"\n{race} patients:")
        risk_names = {0: 'Low risk', 1: 'Medium risk', 2: 'High risk'}
        for class_label, rate in rates.items():
            print(f"  {risk_names[class_label]:12s}: {rate:5.1%}")
    
    # 2. Causal analysis
    print("\n\n2️⃣  Causal Fairness Analysis:")
    print("-" * 80)
    print("Question: Does race directly affect risk, or through health factors?\n")
    
    # Convert race to binary for causal analysis (Black vs Others)
    df_binary = df.copy()
    df_binary['is_black'] = (df['race'] == 'Black').astype(int)
    df_binary['risk_pred'] = y_pred
    
    diagnostic = calc_causal_fairness_diagnostic(
        df_binary, 'is_black', 'risk_pred',
        mediators=['age', 'bmi', 'blood_pressure', 'comorbidities']
    )
    
    print(f"Verdict: {diagnostic['causal_fairness_verdict']}\n")
    
    for comp, effect in diagnostic['path_decomposition'].items():
        print(f"{comp}:")
        print(f"  Total effect:          {effect.total_effect:.4f}")
        print(f"  Direct (race alone):   {effect.direct_effect:.4f}")
        print(f"  Indirect (via health): {effect.indirect_effect:.4f}")
        print(f"  Proportion mediated:   {effect.proportion_mediated:.1%}")
        
        if effect.direct_effect > 0.1:
            print("  ⚠️ Race has direct effect beyond health factors")
        else:
            print("  ✓ Race effect fully mediated by health factors")
    
    return df, y_true, y_pred


def example_4_interpretation_guide():
    """Show how to interpret metric thresholds and take action."""
    print("\n" + "=" * 80)
    print("INTERPRETATION GUIDE: When Metrics Are High")
    print("=" * 80)
    
    scenarios = [
        {
            'metric': 'Weighted Demographic Parity',
            'value': 0.25,
            'meaning': 'Approval rates differ by 25% across groups',
            'actions': [
                '1. Check: Is this difference in actual class labels or predictions?',
                '2. If predictions: Retrain with fairness constraints',
                '3. Add more mediators to causal analysis',
                '4. Review: Are threshold different for each group?',
            ]
        },
        {
            'metric': 'Equal Opportunity (high)',
            'value': 0.20,
            'meaning': 'One group has 20% higher recall for positive class',
            'actions': [
                '1. This may be problematic if recall is critical (e.g., medical)',
                '2. Check: Is one group underrepresented in positive class?',
                '3. Consider: Threshold adjustment per group',
                '4. Explore: Can we improve model on minority class?',
            ]
        },
        {
            'metric': 'Direct Effect (high)',
            'value': 0.15,
            'meaning': 'Protected attr directly affects outcome (not mediated)',
            'actions': [
                '1. Investigate: What are unmeasured mediators?',
                '2. Add more legitimate features to mediators list',
                '3. If still high: Direct discrimination likely',
                '4. Solution: Fairness constraints during training',
            ]
        },
        {
            'metric': 'Information Leakage',
            'value': 0.35,
            'meaning': 'Features correlate with protected attribute (35%)',
            'actions': [
                '1. Are these features legitimate proxies?',
                '2. Example: College education correlated with race',
                '3. Decision: Include if explaining (avoid proxies)',
                '4. Remove if features are discriminatory proxies',
            ]
        }
    ]
    
    for scenario in scenarios:
        print(f"\n❓ {scenario['metric']}: {scenario['value']:.4f}")
        print(f"   → {scenario['meaning']}")
        print("   Actions:")
        for action in scenario['actions']:
            print(f"     {action}")


if __name__ == '__main__':
    # Run all examples
    df1, y_true1, y_pred1 = example_1_loan_approval_multiclass()
    example_2_hiring_causal()
    df3, y_true3, y_pred3 = example_3_healthcare_multiclass_and_causal()
    example_4_interpretation_guide()
    
    print("\n" + "=" * 80)
    print("✅ All examples completed")
    print("=" * 80)
