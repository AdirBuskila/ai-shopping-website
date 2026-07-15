# Churn Model — Training Report

**Served model:** `logreg` (chosen by ROC-AUC). Features are standardized; both models compared below.

| Model | Accuracy | ROC-AUC | Precision | Recall | F1 |
|---|---|---|---|---|---|
| logreg ⭐ | 0.786 | 0.849 | 0.785 | 0.668 | 0.722 |
| rf | 0.778 | 0.822 | 0.757 | 0.688 | 0.720 |

## Confusion matrix (served model)

Rows = actual, Cols = predicted `[retain, churn]`.

```
[[254  38]
 [ 69 139]]
```

## Logistic-regression coefficients (feature influence on churn)

| Feature | Coefficient |
|---|---|
| recency_days | +0.759 |
| frequency | -1.434 |
| monetary | +0.336 |
| tenure_days | -0.042 |
| avg_order_value | -0.336 |
| favorites_count | -0.447 |

_Positive coefficient → raises churn risk; negative → lowers it._
