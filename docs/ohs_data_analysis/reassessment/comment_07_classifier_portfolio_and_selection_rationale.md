# Reassessment — Comment 7: verify the classifier portfolio and justify model-family selection

## Reviewer comment
`Sadece bu üç yöntem mi kullanıldı? Eğer öyleyse neden bu üçü, birer ikişer cümleyle bu yöntemlerin seçimlerinin sebeplerini verelim.`

## Anchored manuscript wording
`ML algorithms including Adaboost, extremly randomized trees (ERT), and GBDT were evaluated via 5-fold cross-validation with optional repeats.`

## Evidence review
The project outputs for Risk 01, Risk 02, and Risk 03 consistently identify a default candidate portfolio of nine supervised classifiers:

1. Logistic Regression (LR)
2. Support Vector Machine (SVM)
3. K-Nearest Neighbors (KNN)
4. Multilayer Perceptron (MLP)
5. Random Forest
6. Extra Trees / Extremely Randomized Trees
7. AdaBoost
8. Gradient Boosting Decision Trees (GBDT)
9. Histogram-Based Gradient Boosting

A `DummyMajority` classifier was also evaluated as a non-informative reference baseline. Therefore, the manuscript statement listing only AdaBoost, Extra Trees, and GBDT is incomplete and creates the false impression that only three algorithms were examined.

The wording must distinguish the **candidate portfolio** from the algorithms that appeared as selected leaders in a particular feature, analysis, or figure. The project records also show that some model–resampling combinations were skipped in specific runs because of preprocessing or compatibility constraints; the manuscript must not claim that every candidate completed every possible configuration unless the execution matrix confirms this.

## Final editorial decision
The Methods section will list all nine supervised classifiers and the DummyMajority baseline. The algorithms will be grouped by their modeling assumptions rather than presented as an arbitrary list. The rationale is comparative: the portfolio was intended to test whether linear, margin-based, local, neural-network, bagged-tree, randomized-tree, and boosting approaches behaved differently under the same structured predictor set and outcome definitions.

The manuscript will not claim that these algorithms were selected because they are universally superior. Selection was made to provide a controlled comparison of complementary inductive biases commonly used for tabular classification.

## Algorithm-specific rationale

### Logistic Regression
Logistic regression provides a transparent linear reference for determining whether a simple additive decision boundary is sufficient. Its inclusion helps quantify whether more flexible nonlinear models provide meaningful improvement over a conventional parametric classifier.

### Support Vector Machine
SVM provides a margin-based alternative that can model nonlinear class boundaries when an appropriate kernel and preprocessing pipeline are used. It was included to test whether separation in the transformed predictor space could outperform linear and tree-based approaches.

### K-Nearest Neighbors
KNN is an instance-based method that makes few assumptions about the functional form of the decision boundary. It was included as a local-pattern benchmark, with the understanding that its performance depends strongly on scaling, encoding, dimensionality, and class imbalance.

### Multilayer Perceptron
MLP provides a flexible nonlinear function approximator capable of learning interactions among encoded predictors. It was included to compare a neural-network approach with classical linear, distance-based, and tree-based classifiers on the same tabular data.

### Random Forest
Random Forest combines many decorrelated decision trees through bootstrap aggregation and random feature selection. It was included because it can represent nonlinearities and interactions while reducing the instability of a single decision tree.

### Extra Trees / Extremely Randomized Trees
Extra Trees introduces additional randomization in split selection and therefore provides a useful contrast to Random Forest. It was included to assess whether stronger randomization changes the bias–variance trade-off for the structured accident data.

### AdaBoost
AdaBoost sequentially increases attention to observations that are difficult to classify. It was included to test whether iterative reweighting of errors improves discrimination relative to single-stage and bagged models.

### Gradient Boosting Decision Trees
GBDT builds trees sequentially to reduce the residual error of the current ensemble. It was included because gradient boosting can capture nonlinear effects and higher-order interactions in heterogeneous tabular predictors.

### Histogram-Based Gradient Boosting
Histogram-based gradient boosting discretizes continuous values into bins to improve computational efficiency while retaining the nonlinear modeling capacity of boosted trees. It was included as a scalable boosting alternative for the larger analysis datasets.

### DummyMajority baseline
DummyMajority predicts according to the majority-class rule and is not a substantive predictive model. It was included to show whether a trained classifier provides signal beyond the class distribution alone and to prevent weak models from being interpreted as useful merely because of imbalanced outcomes.

## Approved Methods wording
`A controlled candidate portfolio of nine supervised classifiers was evaluated: logistic regression, support vector machine, k-nearest neighbors, multilayer perceptron, random forest, extremely randomized trees, AdaBoost, gradient boosting decision trees, and histogram-based gradient boosting. These methods were selected to compare complementary modeling assumptions within a common preprocessing and evaluation framework, including linear, margin-based, instance-based, neural-network, bagged-tree, randomized-tree, and boosting approaches. A majority-class dummy classifier was included as a non-informative reference to determine whether each fitted model provided predictive signal beyond the observed class distribution. The candidate portfolio should be distinguished from the subset of models that emerged as leaders for particular predictors or analyses.`

## Recommended concise version for the manuscript
If space is limited, the following two-paragraph version is preferred:

`Nine supervised classifiers were evaluated: logistic regression, support vector machine, k-nearest neighbors, multilayer perceptron, random forest, extremely randomized trees, AdaBoost, gradient boosting decision trees, and histogram-based gradient boosting. A majority-class dummy classifier was included as a non-informative baseline.`

`The portfolio was selected to compare complementary modeling assumptions under a common preprocessing and evaluation framework. Logistic regression provided a linear reference; SVM and KNN represented margin-based and local-pattern approaches; MLP represented a neural nonlinear model; Random Forest and Extra Trees represented bagged and randomized tree ensembles; and AdaBoost, GBDT, and histogram-based gradient boosting represented sequential boosting strategies.`

## Recommended reviewer response
`Thank you for highlighting this ambiguity. The previous wording listed only three algorithms and therefore did not reflect the full comparative analysis. We revised the Methods section to report all nine supervised classifiers evaluated—logistic regression, support vector machine, k-nearest neighbors, multilayer perceptron, random forest, extremely randomized trees, AdaBoost, gradient boosting decision trees, and histogram-based gradient boosting—together with a majority-class dummy baseline. We also added a concise rationale explaining that the portfolio was selected to compare linear, margin-based, local, neural-network, bagged-tree, randomized-tree, and boosting approaches within a common preprocessing and evaluation framework. The revised text now distinguishes the complete candidate portfolio from the smaller subset of algorithms that emerged as leaders in particular analyses.`

## Turkish explanation for the tracking workbook
`Önceki metin yalnızca AdaBoost, Extra Trees ve GBDT’yi saydığı için çalışmada sadece üç algoritmanın kullanıldığı izlenimini veriyordu. Risk 01, Risk 02 ve Risk 03 proje çıktıları incelendiğinde aday portföyün dokuz denetimli sınıflandırıcıdan oluştuğu doğrulanmıştır: Logistic Regression, SVM, KNN, MLP, Random Forest, Extra Trees, AdaBoost, GBDT ve Histogram-Based Gradient Boosting. Ayrıca çoğunluk sınıfını tahmin eden DummyMajority modeli anlamsız referans düzeyi olarak kullanılmıştır. Yöntemler, tek bir model ailesine öncelik vermeden doğrusal, marj-temelli, yerel, sinir ağı, bagging, rastgeleleştirilmiş ağaç ve boosting yaklaşımlarını aynı veri işleme ve değerlendirme çerçevesinde karşılaştırmak amacıyla seçilmiştir. Metinde aday portföy ile belirli analizlerde lider çıkan sınırlı model grubu birbirinden ayrılacaktır.`

## Manuscript-wide consistency actions
- Replace the three-algorithm sentence in Methods with the complete candidate portfolio.
- Correct `extremly randomized trees` to `extremely randomized trees`.
- Use one consistent naming convention: `Extra Trees (extremely randomized trees)` at first mention, then `Extra Trees`.
- Ensure the abbreviation note includes only algorithms actually used and uses `MLP`, not a generic `ANN`, where the implemented model is an MLP classifier.
- Reconcile Figure 8, Figure 10, captions, tables, and Discussion with the full candidate portfolio.
- Clearly label any displayed subset as `top-performing models`, not `models evaluated`.
- Retain DummyMajority as a baseline, not as a candidate substantive classifier.
- Do not add Decision Tree, XGBoost, LightGBM, CatBoost, or other algorithms to the study unless their executed outputs are available.
- Do not state that all model–resampling combinations ran successfully when project logs document skipped combinations.
- Align the primary performance terminology with Comment 11 and the validation wording with Comments 6 and 25.

## Status
Fully finalized. The source outputs are sufficient to identify the complete classifier portfolio and provide a defensible selection rationale.