# Analyzing LAPD Vehical Stop Data 
The following analysis is based on the dataset found [here](https://data.lacity.org/A-Safe-City/Vehicle-and-Pedestrian-Stop-Data-2010-to-Present/ci25-wgt7)

## Motivation
At the heart of this analysis is trying to understand whether police officers influence each others' policing behaviors. Specifically, this work investigates whether when a police officer works with other officers, does he/she incorporate the biases in how the other officers stop different demographics into his/her future policing.

## Problem Design
We can attempt to answer this question with the following design:

(insert image here)

At any point in time, we can calculate the distribution of how an officer stops demographics (sex or race/descent) over some time period. If we calculate this type of distribution at two different non-overlapping time periods (a "past period" and a "future period"), there will be some period in between that I will call the "influencing period". Let's assume action(s) can take place in the "influencing" period that will relate to an observable difference between the "past period" and "future period" distributions. The hypothesis here is that an officer making vehical stops with other officers, thereby working among officers with varying stops distributions, can be a kind of influencing action. For this problem design, the influencing officers' distributions are calculated during the "past period", so that they are comparable to the "past period" distribution of the officer being evaluated.  

### Notes
Regard stops demographic distributions: In the case of sex, this is a distribution over male and female, since the dataset only contains those labels. In the case of race / descent, we only include groups with more than 10k sample rows. Those include Hispanic/Latin/Mexican (H), Black (B), White (W), Other (O), Other Asian (A). 

Additionally, there are some assumptions made. It is possible that an officer changes which areas he/she operates in between "past period" and "future period". Different areas can have different demographic distributions, which can confound the design above. A rudimentary and non-perfect way I control for this by only considering cases where the distribution of an officer's reporting districts does not change too much, specifically only allow each district to change +/-10%. This can fail dramatically though, especially if an officer works in many different districts, each with a small percentage. Given the data we have to work with, a better sanity check for this is actually to perform our analysis on our sex stop distributions first. It is a reasonable assumption that the population distribution of M:F should not vary too much between districts. Therefore, the change in underlying population distribution is controlled for.

One final constraint involves how stop distributions are calculated. Just to ensure that vehical stops contributing to an officer's distribution truly reflect the actions of the officer being evaluated, and not his/her partner, we calculate our stop distributions only using vehical stops when an officer is alone / without another officer involved. 

## Code Walkthrough
Explain here

## Results
To analyze our results, we can make use of SHAP plots. For each demographic X, there are two SHAP plots constructed from our model predicting whether an officer's propensity to stop demographic X will increase/decrease. First, the summary plot shows the impact of each model feature on the output prediction. For each demographic X's summary plot, we are most concerned with the effect of the X_influencing feature, since this describes how our model relates policing behavior of an officer to the influence of other officers. Second, the dependence plot gives us a more detailed look into how X_influencing with X_officer_past jointly affects an officer's propensity to stop demographic X. For the first demographic analyzed, I will spend more time explaining the analysis process than subsequent demographics, since subsequent ones will follow a similar pattern.

### SHAP Female (F)
First it's importance the check whether our model has some degree of predictive power. This model's accuracy on our evaluation set comes out to 64.6%, on a set where our class 0 vs. class 1 split is 46.7% vs 53.3%. We should not expect 100% accuracy, since there are certainly other explanatory variables; however, an accuracy of 64.6% is definitely an improvement over the best naive guess of the majority class that would yield 53.3% accuracy. 

Regarding the summary plot, F_officer_past has the largest impact. This should be expected, since low F_officer_past values do not have too much room to go lower (likewise with high values going higher). F_influencing, however, does generally show that our prediction increases as influencing officers' propensity to stop demographic F increases, which is our initial hypothesis. 
![female SHAP summary plot](https://github.com/ptjames/analysis_lapd/blob/master/analysis/plots/F_alone_shap_summary.png)

Diving a bit deeper, the dependence plot shows a key detail related to our hypothesis. Not all dots with low F_officer_past are treated the same. We can see that holding F_officer_past relatively constant, F_influencing still has a large effect on the SHAP value. The same can be said about dots with high F_officer_past not all be treated the same.
![female SHAP dependence plot](https://github.com/ptjames/analysis_lapd/blob/master/analysis/plots/F_alone_shap_dependence.png)

### SHAP Male (M)
The M model accuracy comes out to 65%, which is reasonably better than the naive guess at 54.5% accuracy. The SHAP summary plot generally shows that our prediction increases as M_influencing increases.
![female SHAP summary plot](https://github.com/ptjames/analysis_lapd/blob/master/analysis/plots/M_alone_shap_summary.png)

Additionally, holding M_officer_past relatively constant, M_influencing still has a large effect on the SHAP value.
![female SHAP dependence plot](https://github.com/ptjames/analysis_lapd/blob/master/analysis/plots/M_alone_shap_dependence.png)

### SHAP Hispanic/Latin/Mexican (H)
Next we move onto racial demographics. Remember that we have to maintain stronger assumptions with these, since different areas of the city have different racial distributions. I will revisit this point one more time in the Future Work section below. 

Model accuracy for H comes out to 64.7%, which is an improvement over the naive guess at 56.5% accuracy. The SHAP summary plot generally shows that our prediction increases as H_influencing increases.
![female SHAP summary plot](https://github.com/ptjames/analysis_lapd/blob/master/analysis/plots/H_alone_shap_summary.png)

For the dependence, holding H_officer_past relatively constant, H_influencing still has a large effect on the SHAP value.
![female SHAP dependence plot](https://github.com/ptjames/analysis_lapd/blob/master/analysis/plots/H_alone_shap_dependence.png)

### SHAP Black (B)
![female SHAP summary plot](https://github.com/ptjames/analysis_lapd/blob/master/analysis/plots/B_alone_shap_summary.png)
![female SHAP dependence plot](https://github.com/ptjames/analysis_lapd/blob/master/analysis/plots/B_alone_shap_dependence.png)

### SHAP White (W)
![female SHAP summary plot](https://github.com/ptjames/analysis_lapd/blob/master/analysis/plots/W_alone_shap_summary.png)
![female SHAP dependence plot](https://github.com/ptjames/analysis_lapd/blob/master/analysis/plots/W_alone_shap_dependence.png)

### SHAP Other (O)
![female SHAP summary plot](https://github.com/ptjames/analysis_lapd/blob/master/analysis/plots/O_alone_shap_summary.png)
![female SHAP dependence plot](https://github.com/ptjames/analysis_lapd/blob/master/analysis/plots/O_alone_shap_dependence.png)

### SHAP Asian (A)
![female SHAP summary plot](https://github.com/ptjames/analysis_lapd/blob/master/analysis/plots/A_alone_shap_summary.png)
![female SHAP dependence plot](https://github.com/ptjames/analysis_lapd/blob/master/analysis/plots/A_alone_shap_dependence.png)


## Future Work
Future work here



