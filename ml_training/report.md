# Churn Model — Training Report

**Served model:** `logreg` (chosen by ROC-AUC). Features are standardized; both models compared below.

| Model | Accuracy | ROC-AUC | Precision | Recall | F1 |
|---|---|---|---|---|---|
| logreg ⭐ | 0.788 | 0.852 | 0.780 | 0.683 | 0.728 |
| rf | 0.776 | 0.837 | 0.764 | 0.668 | 0.713 |

## Confusion matrix (served model)

Rows = actual, Cols = predicted `[retain, churn]`.

```
[[252  40]
 [ 66 142]]
```

## Logistic-regression coefficients (feature influence on churn)

| Feature | Coefficient |
|---|---|
| recency_days | +0.748 |
| frequency | -0.992 |
| monetary | -0.239 |
| tenure_days | -0.045 |
| favorites_count | -0.443 |

_Positive coefficient → raises churn risk; negative → lowers it._
