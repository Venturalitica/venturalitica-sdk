import pandas as pd
from ucimlrepo import fetch_ucirepo
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
import venturalitica as vl
import os

# 1. Load Data
print("\n--- 1. LOADING DATA ---")
dataset = fetch_ucirepo(id=144)
df = dataset.data.features.copy()
df['class'] = dataset.data.targets

# Raw split for pre-training audit
train_df, test_df = train_test_split(df, test_size=0.2, random_state=42)

# 2. Pre-Training Audit (Data Bias)
print("\n--- 2. PRE-TRAINING AUDIT (Data Bias) ---")
policy_content = """
assessment-plan:
  metadata:
    title: "Training Tutorial Policy"
  reviewed-controls:
    control-implementations:
      - description: "Bias rules"
        implemented-requirements:
          - control-id: class-balance
            description: "Minority class > 20%"
            props:
              - name: metric_key
                value: class_imbalance
              - name: threshold
                value: "0.2"
              - name: operator
                value: gt
          - control-id: gender-disparate
            description: "Gender disparate impact > 0.8"
            props:
              - name: metric_key
                value: disparate_impact
              - name: threshold
                value: "0.8"
              - name: operator
                value: gt
              - name: "input:dimension"
                value: gender
          - control-id: age-disparate
            description: "Age disparate impact > 0.5"
            props:
              - name: metric_key
                value: disparate_impact
              - name: threshold
                value: "0.5"
              - name: operator
                value: gt
              - name: "input:dimension"
                value: age
"""
with open("tutorial_policy.yaml", "w") as f:
    f.write(policy_content)

# Note: enforce() mapping keys (gender, age, target) must match policy "input:X" variable names (gender, age, target)
# The default target variable in enforce is 'target'
vl.enforce(
    data=train_df,
    target="class",       # 'target' role in metrics will use 'class' column
    gender="Attribute9",  # 'gender' role in metrics will use 'Attribute9' column
    age="Attribute13",    # 'age' role in metrics will use 'Attribute13' column
    policy="tutorial_policy.yaml"
)

# 3. Train Model
print("\n--- 3. TRAINING MODEL ---")
df_encoded = pd.get_dummies(df.drop(columns=['class']))
X_train, X_test, y_train, y_test = train_test_split(
    df_encoded, 
    df['class'].values.ravel(), 
    test_size=0.2, 
    random_state=42
)

model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)
print("Model trained successfully.")

# 4. Post-Training Audit (Fairness + Performance)
print("\n--- 4. POST-TRAINING AUDIT (Fairness + Performance) ---")
# Update policy to include performance with CORRECT registry names
full_policy_content = """
assessment-plan:
  metadata:
    title: "Full Audit Policy"
  reviewed-controls:
    control-implementations:
      - description: "Bias and Performance rules"
        implemented-requirements:
          - control-id: gender-disparate
            description: "Gender disparate impact > 0.8"
            props:
              - name: metric_key
                value: disparate_impact
              - name: threshold
                value: "0.8"
              - name: operator
                value: gt
              - name: "input:dimension"
                value: gender
          - control-id: age-disparate
            description: "Age disparate impact > 0.5"
            props:
              - name: metric_key
                value: disparate_impact
              - name: threshold
                value: "0.5"
              - name: operator
                value: gt
              - name: "input:dimension"
                value: age
          - control-id: accuracy-check
            description: "Accuracy > 70%"
            props:
              - name: metric_key
                value: accuracy_score
              - name: threshold
                value: "0.7"
              - name: operator
                value: gt
"""
with open("tutorial_policy.yaml", "w") as f:
    f.write(full_policy_content)

predictions = model.predict(X_test)
test_audit_df = df.iloc[X_test.index].copy() # Ensure index matching
test_audit_df['prediction'] = predictions

vl.enforce(
    data=test_audit_df,
    target="class",
    prediction="prediction",
    gender="Attribute9",
    age="Attribute13",
    policy="tutorial_policy.yaml"
)

# Clean up
if os.path.exists("tutorial_policy.yaml"):
    os.remove("tutorial_policy.yaml")
