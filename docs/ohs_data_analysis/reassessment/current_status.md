# OHS Manuscript Revision — Reassessment Status

- Total reviewer comments: 32
- Reassessed through: Comment 7
- Reassessed: 7/32 = 21.875%
- Fully finalized in reassessment: 7/32 = 21.875%
- Next item: Comment 8

## Latest decision — Comment 7
The Methods section incorrectly listed only AdaBoost, Extra Trees, and GBDT. The verified candidate portfolio contains nine supervised classifiers—Logistic Regression, SVM, KNN, MLP, Random Forest, Extra Trees, AdaBoost, GBDT, and Histogram-Based Gradient Boosting—plus a DummyMajority reference baseline.

## Selection rationale
- Logistic Regression: linear parametric reference.
- SVM: margin-based classifier.
- KNN: local instance-based benchmark.
- MLP: flexible neural nonlinear model.
- Random Forest: bagged tree ensemble.
- Extra Trees: strongly randomized tree ensemble.
- AdaBoost: sequential error-reweighting ensemble.
- GBDT: gradient-based sequential tree ensemble.
- Histogram-Based Gradient Boosting: computationally efficient boosted-tree alternative.
- DummyMajority: non-informative majority-class reference.

## Reporting boundary
The complete candidate portfolio must be distinguished from the smaller subset of algorithms that emerged as leaders in a particular feature, analysis, figure, or table. The manuscript will not claim that every model–resampling combination completed successfully when project logs document skipped configurations.

## Approved concise wording
`Nine supervised classifiers were evaluated: logistic regression, support vector machine, k-nearest neighbors, multilayer perceptron, random forest, extremely randomized trees, AdaBoost, gradient boosting decision trees, and histogram-based gradient boosting. A majority-class dummy classifier was included as a non-informative baseline. The portfolio was selected to compare complementary linear, margin-based, local, neural-network, bagged-tree, randomized-tree, and boosting approaches under a common preprocessing and evaluation framework.`

## Next item
Comment 8 — determine the exact meaning of the undefined target abbreviation and replace it with the verified data-field and outcome terminology.